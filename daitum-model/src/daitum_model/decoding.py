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
Decoder core: reconstruct typed Python objects from ``Buildable.build()`` output.

This module is the deserialisation counterpart to
:mod:`daitum_model.serialisation`. It holds the cross-object load state
(:class:`LoadContext`), the error type (:class:`LoadError`), and the registries and
generic walk that invert ``build()``. Decoders live here (and in each package's
``_decoders`` subpackage), separate from the data classes, because deserialisation needs
a target type, a discriminator, and a symbol table for references — none of which belong
on the JSON or the data class.
"""

from __future__ import annotations

import datetime as _datetime
import types
import typing
from collections.abc import Callable
from dataclasses import dataclass, field
from enum import Enum
from typing import TYPE_CHECKING, Any, Protocol, TypeVar, Union, get_args, get_origin

from daitum_model.serialisation import Buildable, camel_to_snake

if TYPE_CHECKING:
    from daitum_model.model import ModelBuilder
    from daitum_model.tables import Table

T = TypeVar("T")
T_co = TypeVar("T_co", covariant=True)

#: Number of type args on a fully-parameterised ``dict[K, V]``.
_DICT_ARG_COUNT = 2


class LoadError(Exception):
    """Raised when JSON cannot be decoded into the expected object graph."""


def require(data: dict[str, Any], key: str, owner: str) -> Any:
    """Return ``data[key]`` or raise a :class:`LoadError` naming the missing key and owner.

    Use for *required* build keys whose absence means malformed input. This keeps the layer's
    error contract consistent (a clean :class:`LoadError`) instead of leaking a bare
    ``KeyError`` from deep inside a decoder.
    """
    if key not in data:
        raise LoadError(f"{owner}: missing required key {key!r}")
    return data[key]


def optional(data: dict[str, Any], key: str, default: T) -> T:
    """Return ``data[key]``, falling back to ``default`` when the key is missing *or* ``null``.

    ``dict.get(key, default)`` applies its default only when the key is absent; an exported
    model may carry an explicit ``"key": null``, which ``get`` returns verbatim. Use this for
    optional scalar keys whose ``null`` means "unset" and should decode as the default (e.g. a
    boolean flag or an enum with a sentinel value).
    """
    value = data.get(key)
    return default if value is None else value


def optional_seq(data: dict[str, Any], key: str) -> list[Any]:
    """Return ``data[key]`` as a list, treating a missing *or* ``null`` value as empty.

    ``dict.get(key, [])`` only applies its default when the key is absent; an exported
    model may carry an explicit ``"key": null``, which ``get`` returns verbatim and which
    is not iterable. Use this for optional collection keys to coerce both cases to ``[]``.
    """
    return data.get(key) or []


def optional_map(data: dict[str, Any], key: str) -> dict[str, Any]:
    """Return ``data[key]`` as a dict, treating a missing *or* ``null`` value as empty.

    The mapping counterpart to :func:`optional_seq` — see its note on why ``dict.get`` with
    a default is not enough when the JSON carries an explicit ``null``.
    """
    return data.get(key) or {}


@dataclass
class LoadContext:
    """Cross-object state for a single load.

    Args:
        symbols: Maps a model-object id to the live decoded object, used to resolve
            ``!!!``-prefixed references.
        model: The decoded model, set when loading a configuration or UI that references it.
        deferred_formulas: Formula-parse tasks queued during phase 1 (construct + register) and run
            in phase 2 once every table, field and named value is registered, so a formula's
            references always resolve regardless of decode order. Each task parses a formula string
            into its structured tree and attaches it to its owner.
    """

    symbols: dict[str, Any] = field(default_factory=dict)
    model: ModelBuilder | None = None
    deferred_formulas: list[Callable[[], None]] = field(default_factory=list)

    def register(self, identifier: str, obj: Any) -> None:
        """Record ``obj`` under ``identifier`` so later references can resolve it."""
        self.symbols[identifier] = obj

    def resolve(self, identifier: str) -> Any:
        """Return the object registered under ``identifier``, or raise :class:`LoadError`."""
        if identifier not in self.symbols:
            raise LoadError(f"Unresolved reference: {identifier!r}")
        return self.symbols[identifier]

    def find_table(self, table_id: str) -> Table | None:
        """Return the :class:`Table` with ``table_id``, or ``None`` if there is no such table.

        Tables and fields share the symbol table, and a field, calculation or parameter may be
        named after a table elsewhere in the model (an object-reference field, or a calculated
        field/named value that happens to share a table's id), so reading the symbol table directly
        can return the shadowing non-table. When a model is present its table registry is the
        authoritative, field-free source; otherwise (standalone-table decode) fall back to the
        symbol table, keeping the result only when it is actually a table. This never raises — it is
        the shadow-proof primitive behind both :meth:`resolve_table` and table lookups in the
        formula resolver.
        """
        from daitum_model.tables import Table  # noqa: PLC0415 - avoid an import cycle

        if self.model is not None:
            return next((t for t in self.model.get_tables() if t.id == table_id), None)
        obj = self.symbols.get(table_id)
        return obj if isinstance(obj, Table) else None

    def resolve_table(self, table_id: str) -> Table:
        """Return the :class:`Table` with ``table_id``, raising :class:`LoadError` if there is none.

        The raising counterpart to :meth:`find_table`; use it where a missing/shadowed table is a
        hard decode failure.
        """
        table = self.find_table(table_id)
        if table is None:
            raise LoadError(f"{table_id!r} does not resolve to a table")
        return table

    def defer_formula(self, task: Callable[[], None]) -> None:
        """Queue a formula-parse task to run in phase 2 (after all symbols are registered)."""
        self.deferred_formulas.append(task)

    def resolve_deferred_formulas(self) -> None:
        """Run every queued formula-parse task, then clear the queue. Phase 2 of the load."""
        tasks = self.deferred_formulas
        self.deferred_formulas = []
        for task in tasks:
            task()


class Decoder(Protocol[T_co]):
    """Reconstructs an instance of ``T_co`` from a built dict and a load context."""

    def decode(self, data: dict[str, Any], ctx: LoadContext) -> T_co: ...


# --- Registries -----------------------------------------------------------------------

#: For ``@type``-discriminated hierarchies: base class -> {discriminator value -> concrete}.
TYPE_REGISTRY: dict[type, dict[str, type]] = {}

#: Concrete class -> the callable that decodes its built dict.
DECODER_REGISTRY: dict[type, Callable[[dict[str, Any], LoadContext], Any]] = {}


def register_type(base: type, discriminator: str, concrete: type) -> None:
    """Register ``concrete`` as the implementation of ``base`` for a ``@type`` value."""
    TYPE_REGISTRY.setdefault(base, {})[discriminator] = concrete


def register_decoder(concrete: type, decoder: Callable[[dict[str, Any], LoadContext], Any]) -> None:
    """Register the decoder callable for a concrete class."""
    DECODER_REGISTRY[concrete] = decoder


def generic(cls: type) -> Callable[[type], type]:
    """Decorator: register ``cls`` to be decoded by the generic field walk.

    Used on classes whose ``build()`` is (or has become) the default attribute walk.
    """
    register_decoder(cls, lambda data, ctx: decode_fields(cls, data, ctx))
    return lambda c: c


# --- Type resolution ------------------------------------------------------------------


def resolved_field_types(cls: type) -> dict[str, Any]:
    """Return a mapping of constructor parameter name -> declared type for ``cls``.

    Reads the ``__init__`` signature annotations (resolved against the module globals),
    skipping ``self``. This is the inverse key set the generic walk decodes into.
    """
    import inspect

    init = cls.__init__  # type: ignore[misc]
    try:
        hints = typing.get_type_hints(init)
    except (NameError, TypeError):
        # Unresolved forward reference or an un-introspectable annotation: fall back to the
        # raw (string) annotations rather than failing the whole decode.
        hints = dict(getattr(init, "__annotations__", {}))

    sig = inspect.signature(init)
    result: dict[str, Any] = {}
    for name in sig.parameters:
        if name in ("self", "args", "kwargs"):
            continue
        result[name] = hints.get(name, Any)
    return result


def _is_optional(annotation: Any) -> tuple[bool, Any]:
    """If ``annotation`` is ``X | None`` return ``(True, X)``, else ``(False, annotation)``."""
    origin = get_origin(annotation)
    if origin is Union or origin is types.UnionType:
        non_none = [a for a in get_args(annotation) if a is not type(None)]
        if len(non_none) == 1:
            return True, non_none[0]
        return True, Union[tuple(non_none)]  # type: ignore[index] # noqa: UP007
    return False, annotation


# --- Coercion -------------------------------------------------------------------------


def coerce(value: Any, annotation: Any, ctx: LoadContext) -> Any:  # noqa: PLR0911
    """Recover the typed value ``build()`` erased, guided by the declared ``annotation``.

    The annotation-driven inverse of the ``convert()`` step in ``Buildable.build()``.
    """
    from daitum_model.references import Reference, is_reference

    if value is None:
        return None

    # Reference strings ("!!!...") resolve through the context, regardless of annotation.
    if is_reference(value):
        return Reference.decode(value, ctx)

    _, annotation = _is_optional(annotation)
    origin = get_origin(annotation)

    # Enums.
    if isinstance(annotation, type) and issubclass(annotation, Enum):
        return annotation(value)

    # Dates/times serialised as component lists.
    if annotation in (_datetime.datetime, _datetime.date, _datetime.time) and isinstance(
        value, list
    ):
        return annotation(*value)

    # Buildable subclasses (possibly polymorphic via @type).
    if isinstance(annotation, type) and issubclass(annotation, Buildable):
        return decode_into(annotation, value, ctx)

    # Containers.
    if origin is list:
        (elem_type,) = get_args(annotation) or (Any,)
        return [coerce(v, elem_type, ctx) for v in value]
    if origin is dict:
        args = get_args(annotation)
        val_type = args[1] if len(args) == _DICT_ARG_COUNT else Any
        return {k: coerce(v, val_type, ctx) for k, v in value.items()}

    # Unions without a single resolved member: try each Buildable / enum member.
    if origin is Union or origin is types.UnionType:
        return _coerce_union(value, get_args(annotation), ctx)

    # Primitive or unknown — pass through.
    return value


def _coerce_union(value: Any, members: tuple[Any, ...], ctx: LoadContext) -> Any:
    for member in members:
        if member is type(None):
            continue
        try:
            if isinstance(member, type) and issubclass(member, Buildable):
                if isinstance(value, dict):
                    return decode_into(member, value, ctx)
                continue
            if isinstance(member, type) and issubclass(member, Enum):
                return member(value)
        except (ValueError, LoadError):
            continue
    # A dict value can only have come from a Buildable member; if none accepted it, that is a
    # real decode failure, not a primitive to pass through. Fail loudly to match the rest of
    # the layer rather than silently returning the raw dict.
    if isinstance(value, dict):
        names = [m.__name__ for m in members if isinstance(m, type)]
        raise LoadError(f"No union member {names!r} could decode {value!r}")
    return value


# --- The generic walk -----------------------------------------------------------------


def decode_fields(cls: type, data: dict[str, Any], ctx: LoadContext) -> Any:
    """Decode ``data`` into ``cls`` via the default attribute walk (inverse of build())."""
    hints = resolved_field_types(cls)
    kwargs: dict[str, Any] = {}
    for camel_key, value in data.items():
        if camel_key == "@type":
            continue
        snake = camel_to_snake(camel_key)
        if snake not in hints:
            raise LoadError(f"{cls.__name__}: no constructor field for key {camel_key!r}")
        kwargs[snake] = coerce(value, hints[snake], ctx)
    # Construct directly. A class needing builder-factory routing (registration,
    # back-pointers) registers its own decoder rather than relying on this generic walk.
    return cls(**kwargs)


def decode_into(base: type, data: Any, ctx: LoadContext) -> Any:
    """Decode ``data`` into ``base`` (or its concrete subtype, via ``@type`` dispatch)."""
    if not isinstance(data, dict):
        raise LoadError(
            f"Expected a dict to decode into {base.__name__}, got {type(data).__name__}"
        )

    concrete = _resolve_concrete(base, data)
    decoder = DECODER_REGISTRY.get(concrete)
    if decoder is None:
        # Fall back to the generic walk for unregistered-but-regular classes.
        return decode_fields(concrete, data, ctx)
    return decoder(data, ctx)


def _resolve_concrete(base: type, data: dict[str, Any]) -> type:
    discriminator = data.get("@type")
    if discriminator is None:
        return base
    variants = TYPE_REGISTRY.get(base)
    if variants is None:
        # base may itself be the concrete registered under a parent; try a global lookup.
        for mapping in TYPE_REGISTRY.values():
            if discriminator in mapping and issubclass(mapping[discriminator], base):
                return mapping[discriminator]
        return base
    if discriminator not in variants:
        raise LoadError(f"Unknown @type {discriminator!r} for {base.__name__}")
    return variants[discriminator]
