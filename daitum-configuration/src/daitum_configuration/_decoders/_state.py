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
``decode_with_state``: decode a config Buildable whose attributes are set after construction.

Many configuration classes take only a few required constructor arguments and populate the
rest through ``set_*``/``add_*`` methods. ``build()`` emits all of those attributes, so the
constructor-signature walk (which rejects keys with no matching parameter) cannot reconstruct
them. This helper constructs with the required arguments, then restores every remaining built
key as a typed attribute — recovering enums/dates/references/nested Buildables via the same
``coerce`` the generic walk uses, learning each attribute's type from a reference instance.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from daitum_model.decoding import LoadContext, LoadError, coerce, resolved_field_types
from daitum_model.serialisation import camel_to_snake, snake_to_camel


@dataclass(frozen=True)
class ListOf:
    """Element-spec marker: the attribute is a ``list`` of the wrapped Buildable class."""

    element: type


@dataclass(frozen=True)
class DictOf:
    """Element-spec marker: the attribute is a ``dict`` whose values are the wrapped class."""

    element: type


def decode_with_state(  # noqa: PLR0913 - a parameterised construction seam, not a leaf API
    cls: type,
    data: dict[str, Any],
    ctx: LoadContext,
    *,
    ctor_args: tuple[str, ...] = (),
    ctor_overrides: dict[str, Any] | None = None,
    elements: dict[str, Any] | None = None,
) -> Any:
    """Decode ``data`` into ``cls`` by constructing with ``ctor_args`` then restoring state.

    Args:
        cls: The concrete class to reconstruct.
        data: The built dict (camelCase keys).
        ctx: Load context for reference resolution.
        ctor_args: snake_case names of the required constructor parameters, taken (decoded)
            from ``data`` and passed positionally in the given order.
        ctor_overrides: Fixed constructor kwargs NOT taken from ``data`` — used as placeholders
            when a required argument's serialised form differs from its constructor type (e.g.
            a constructor that takes tuples but stores wrapped objects). The real attribute is
            restored afterwards from ``data`` via ``elements``.
        elements: For attributes whose value is a nested Buildable, the element class to decode
            into — keyed by snake_case attribute name. A bare ``type`` means a single nested
            Buildable; wrap it in :class:`ListOf`/:class:`DictOf` for a list/dict of them.
            Primitive, enum, date and ``!!!`` reference values need no entry (``coerce``
            recovers those from the value itself); only nested Buildables, whose target class
            the raw dict cannot reveal, must be declared here.
    """
    elements = elements or {}
    kwargs = dict(ctor_overrides or {})
    hints = resolved_field_types(cls)
    for name in ctor_args:
        camel = snake_to_camel(name)
        if camel not in data:
            raise LoadError(f"{cls.__name__}: required constructor key {camel!r} absent from data")
        # Coerce the argument to its declared constructor type so enums become enum members
        # and nested Buildables are decoded before construction (which may validate them).
        kwargs[name] = coerce(data[camel], hints.get(name, Any), ctx)

    instance = cls(**kwargs)

    # Restore the remaining attributes. Constructor arguments are skipped — the constructor
    # already set them from their properly-typed coercion above; re-coercing them here as
    # ``Any`` (without their declared type) could strip nested Buildables back to raw dicts.
    consumed = set(ctor_args)
    for camel_key, value in data.items():
        if camel_key == "@type":
            continue
        snake = camel_to_snake(camel_key)
        if snake in consumed:
            continue
        setattr(instance, snake, _decode_attr(snake, value, elements, ctx))
    return instance


def _decode_attr(snake: str, value: Any, elements: dict[str, Any], ctx: LoadContext) -> Any:
    spec = elements.get(snake)
    if spec is None:
        return coerce(value, Any, ctx)
    if value is None:
        return None
    if isinstance(spec, ListOf):
        return [coerce(v, spec.element, ctx) for v in value]
    if isinstance(spec, DictOf):
        return {k: coerce(v, spec.element, ctx) for k, v in value.items()}
    # A bare type: the attribute is a single nested Buildable.
    return coerce(value, spec, ctx)
