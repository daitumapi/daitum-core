# Copyright 2026 Daitum
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
Template-based decoding for UI Buildables whose ``build()`` is the default attribute walk.

UI classes set their attributes (and their types) inside ``__init__`` rather than via
annotations, and many attributes are populated by ``set_*``/``add_*`` after construction —
so a constructor-signature walk cannot reconstruct them. Instead we build a **reference
template** (a real instance) to learn each attribute's typed default, copy that typed state
onto a fresh instance, then overwrite each built key with its decoded value. The result is a
genuinely typed object: enums are enum members, nested Buildables are their classes, and the
random ``id`` is preserved — never a verbatim JSON replay.
"""

from __future__ import annotations

import inspect
import types
from collections.abc import Callable
from typing import Any, Union, get_args, get_origin, get_type_hints

from daitum_model.decoding import LoadContext, LoadError
from daitum_model.serialisation import Buildable, camel_to_snake

from daitum_ui._decoders._value import decode_value

#: Per-class element/value-type hints for list/Optional/map attributes whose typed default
#: (empty list / None / empty dict) cannot reveal the element class, and whose constructor does
#: not declare it either (body-assigned attributes). Keyed by class, then snake attr name. A
#: value is the element Buildable class, or a :class:`MapOf` for a (possibly nested) map of it.
ELEMENT_SCHEMA: dict[type, dict[str, type | MapOf]] = {}


class MapOf:
    """Schema marker: the attribute is a ``depth``-level ``dict`` map of ``element`` Buildables.

    ``depth=1`` is ``dict[K, element]``; ``depth=2`` is ``dict[K, dict[K, element]]`` (e.g.
    :class:`FixedValueView` ``cells``). Used where the empty-dict template default cannot reveal
    the value class and the constructor does not take it as a parameter.
    """

    def __init__(self, element: type, *, depth: int = 1) -> None:
        self.element = element
        self.depth = depth


#: Per-class factory producing a reference template instance from the built data + context.
#: Returns a fully-initialised instance (typed defaults set); the decoder copies its state.
TEMPLATE_FACTORIES: dict[type, Callable[[dict[str, Any], LoadContext], Any]] = {}


def register_template(
    cls: type,
    *,
    factory: Callable[[dict[str, Any], LoadContext], Any],
    elements: dict[str, type | MapOf] | None = None,
) -> None:
    """Register how to build a reference template for ``cls`` and its element-type hints."""
    TEMPLATE_FACTORIES[cls] = factory
    if elements:
        register_elements(cls, elements)


def register_elements(cls: type, elements: dict[str, type | MapOf]) -> None:
    """Declare the element/value Buildable (or enum) type of ``cls``'s body-assigned attrs.

    Needed for list/Optional/map attributes whose typed default reveals no element class and
    whose constructor does not take them as a parameter (so auto-derivation cannot recover the
    type). Applies to leaves decoded by ``@type`` as well as templated classes.
    """
    ELEMENT_SCHEMA.setdefault(cls, {}).update(elements)


def decode_by_template(
    cls: type,
    data: dict[str, Any],
    ctx: LoadContext,
    *,
    skip_keys: frozenset[str] = frozenset(),
) -> Any:
    """Decode ``data`` into a typed instance of ``cls`` via its reference template.

    Invariant the result relies on: every decoded attribute is given its type either by the
    template's typed default (the value the factory's constructor assigned) or by an
    ``ELEMENT_SCHEMA`` entry (for empty-list / ``None`` attributes whose element class the
    default cannot reveal). An attribute present in ``data`` but absent from both the
    template's ``__dict__`` and the schema would be set untyped — so a class change that adds
    such an attribute must be matched by a factory/schema update. The fragility guard test
    (``test_every_template_factory_constructs``) enforces that the factory still constructs.

    Args:
        cls: The concrete class to reconstruct.
        data: The built dict (camelCase keys, possibly with ``@type``).
        ctx: Load context for reference resolution.
        skip_keys: Built keys handled by the caller (e.g. envelope keys), not set here.
    """
    template = _make_template(cls, data, ctx)
    instance = cls.__new__(cls)  # type: ignore[call-overload]
    instance.__dict__.update(template.__dict__)

    schema = _merged_schema(cls)
    for camel_key, value in data.items():
        if camel_key == "@type" or camel_key in skip_keys:
            continue
        snake = camel_to_snake(camel_key)
        target_attr, elem_type = _resolve_target_attr(cls, snake, schema)
        attr_template = template.__dict__.get(target_attr)
        decoded = decode_value(value, attr_template, elem_type, ctx)
        setattr(instance, target_attr, decoded)
    return instance


def _merged_schema(cls: type) -> dict[str, type | MapOf]:
    """Merge ``ELEMENT_SCHEMA`` entries down the MRO so base-class attrs (e.g. ``BaseView``'s
    ``title``) apply to every subclass, with subclass entries taking precedence."""
    merged: dict[str, type | MapOf] = {}
    for base in reversed(cls.__mro__):
        merged.update(ELEMENT_SCHEMA.get(base, {}))
    return merged


def _resolve_target_attr(
    cls: type, snake: str, schema: dict[str, type | MapOf]
) -> tuple[str, type | MapOf | None]:
    """Map a built key to the writable attribute that holds its typed value.

    The element/value Buildable type is taken from an explicit ``ELEMENT_SCHEMA`` entry when
    present, else auto-derived from the constructor's type hint for the same-named parameter.
    When the key names a read-only ``@property`` (a computed build view of private state), the
    value is written to the backing ``_<name>`` attribute instead.
    """
    descriptor = getattr(cls, snake, None)
    if isinstance(descriptor, property) and descriptor.fset is None:
        backing = f"_{snake}"
        elem = schema.get(backing, schema.get(snake)) or _ctor_buildable_type(cls, snake)
        return backing, elem
    return snake, schema.get(snake) or _ctor_buildable_type(cls, snake)


def _ctor_buildable_type(cls: type, snake: str) -> type | None:
    """Return the Buildable element/value type of ``cls``'s ``snake`` ctor param, if any.

    Reveals nested-Buildable attributes whose typed default is ``None``/``[]``/``{}`` (so the
    template can't show the element class) but whose constructor declares the type — e.g.
    ``ChartSeries(marker: DataPointMarker | None = None)``. Body-assigned attributes that have
    no constructor parameter still need an explicit ``ELEMENT_SCHEMA`` entry.
    """
    hints = _ctor_hints(cls)
    annotation = hints.get(snake)
    return _buildable_in(annotation) if annotation is not None else None


_CTOR_HINTS_CACHE: dict[type, dict[str, Any]] = {}


def _ctor_hints(cls: type) -> dict[str, Any]:
    cached = _CTOR_HINTS_CACHE.get(cls)
    if cached is None:
        try:
            cached = get_type_hints(cls.__init__)  # type: ignore[misc]
        except (NameError, TypeError):
            cached = {}
        _CTOR_HINTS_CACHE[cls] = cached
    return cached


def _buildable_in(annotation: Any) -> type | None:
    """Unwrap ``Optional``/``list[X]``/``dict[K, V]`` to the Buildable subclass inside, if any."""
    if isinstance(annotation, type):
        return annotation if issubclass(annotation, Buildable) else None
    origin = get_origin(annotation)
    if origin in (Union, types.UnionType):
        for arg in get_args(annotation):
            found = _buildable_in(arg)
            if found is not None:
                return found
        return None
    if origin in (list, set, frozenset, tuple):
        args = get_args(annotation)
        return _buildable_in(args[0]) if args else None
    if origin is dict:
        args = get_args(annotation)
        # dict[K, V] -> inspect the value type V.
        return _buildable_in(args[1]) if len(args) == _DICT_ARITY else None
    return None


#: Number of type arguments a ``dict[K, V]`` annotation carries (key and value).
_DICT_ARITY = 2


def _make_template(cls: type, data: dict[str, Any], ctx: LoadContext) -> Any:
    factory = TEMPLATE_FACTORIES.get(cls)
    if factory is not None:
        return factory(data, ctx)
    return _default_template(cls, data, ctx)


def _default_template(cls: type, data: dict[str, Any], ctx: LoadContext) -> Any:
    """Construct a template by filling required ctor args from same-named built keys.

    Works for leaves whose required constructor parameters appear verbatim (camelCased) in
    the built output (e.g. ``ViewField(field_id=...)`` <- ``fieldId``). Classes whose
    constructor needs values not present in ``build()`` must register a factory instead.
    """
    from daitum_ui._decoders._value import decode_value as _dv

    sig = inspect.signature(cls.__init__)  # type: ignore[misc]
    kwargs: dict[str, Any] = {}
    for name, param in sig.parameters.items():
        if name in ("self", "args", "kwargs"):
            continue
        if param.default is not inspect.Parameter.empty:
            continue
        camel = _snake_to_camel(name)
        if camel in data:
            kwargs[name] = _dv(data[camel], None, None, ctx)
        elif _accepts_none(param.annotation):
            # An optional-but-positional arg whose value was None and so omitted by build().
            kwargs[name] = None
        else:
            raise LoadError(
                f"Cannot build a template for {cls.__name__}: required ctor arg {name!r} "
                f"({camel!r}) is absent from build() output; register a template factory."
            )
    return cls(**kwargs)


def _accepts_none(annotation: Any) -> bool:
    """Whether a parameter may be ``None`` — an unannotated arg, or a union including ``None``."""
    if annotation is inspect.Parameter.empty:
        return True
    if get_origin(annotation) in (Union, types.UnionType):
        return type(None) in get_args(annotation)
    return annotation is type(None)


def _snake_to_camel(name: str) -> str:
    parts = name.split("_")
    return parts[0] + "".join(p.capitalize() for p in parts[1:])
