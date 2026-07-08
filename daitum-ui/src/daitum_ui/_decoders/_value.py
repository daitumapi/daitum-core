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
Typed value decoding for the UI package.

UI instance attributes carry no annotations, so a value's target type is learned from a
**reference template** (the typed default the constructor assigns) and, for empty-list or
``None`` attributes whose element type the template cannot reveal, a small declared
``elem_type``. Every value is decoded to its proper type — enums to enum members, nested
Buildables (by ``@type`` or by the declared element class) to their classes — so a decoded
object is genuinely typed and re-editable. Nothing is replayed verbatim.
"""

from __future__ import annotations

from enum import Enum
from typing import Any

from daitum_model.decoding import LoadContext, LoadError, decode_fields
from daitum_model.serialisation import Buildable


def decode_value(  # noqa: PLR0911
    value: Any, template: Any, elem_type: Any, ctx: LoadContext
) -> Any:
    """Decode a built ``value`` to its typed form, guided by ``template`` and ``elem_type``.

    ``elem_type`` is the element Buildable/enum class for a list/Optional/map attribute, or a
    :class:`~daitum_ui._decoders._template.MapOf` marker for a (possibly nested) Buildable map.
    """
    from daitum_ui._decoders._template import MapOf

    if value is None:
        return None

    if isinstance(elem_type, MapOf):
        return _decode_map(value, elem_type, ctx)

    if isinstance(template, Enum):
        return type(template)(value)
    if _is_enum_type(elem_type):
        return elem_type(value)  # type: ignore[misc]

    if isinstance(value, list):
        inner = template[0] if isinstance(template, list) and template else None
        return [decode_value(item, inner, elem_type, ctx) for item in value]

    if isinstance(value, dict):
        # An empty-dict template marks a map attribute (e.g. ``dict[str, Card]``): the element
        # type applies to the *values*, not to the dict itself, so never decode the whole dict
        # as a single Buildable here.
        if isinstance(template, dict):
            inner = _map_value_template(template)
            return {k: decode_value(v, inner, elem_type, ctx) for k, v in value.items()}
        target = _buildable_target(value, template, elem_type)
        if target is not None:
            return _decode_buildable(target, value, ctx)
        # A plain (e.g. CSS / domain-keyed) dict: decode values, keep keys verbatim.
        return {k: decode_value(v, None, None, ctx) for k, v in value.items()}

    return value


def _decode_map(value: Any, marker: Any, ctx: LoadContext) -> Any:
    """Decode a ``depth``-level Buildable map declared by a :class:`MapOf` marker."""
    from daitum_ui._decoders._template import MapOf

    if not isinstance(value, dict):
        raise LoadError(f"Expected a map for {marker.element.__name__}, got {type(value).__name__}")
    if marker.depth <= 1:
        return {k: decode_value(v, None, marker.element, ctx) for k, v in value.items()}
    inner = MapOf(marker.element, depth=marker.depth - 1)
    return {k: _decode_map(v, inner, ctx) for k, v in value.items()}


def _map_value_template(template: dict[Any, Any]) -> Any:
    """The representative value-template of a populated map, or None if empty."""
    return next(iter(template.values()), None)


def _is_enum_type(cls: type | None) -> bool:
    return isinstance(cls, type) and issubclass(cls, Enum)


def _buildable_target(value: dict[str, Any], template: Any, elem_type: type | None) -> type | None:
    """Pick the Buildable class to decode ``value`` into, or None for a plain dict.

    Priority: an ``@type`` discriminator (polymorphic) > the template's concrete class >
    the declared element class.
    """
    from daitum_ui._decoders.leaves import resolve_at_type

    discriminator = value.get("@type")
    if discriminator is not None:
        cls = resolve_at_type(discriminator)
        if cls is None:
            raise LoadError(f"Unsupported UI @type: {discriminator!r}")
        return cls
    if isinstance(template, Buildable):
        return type(template)
    if isinstance(elem_type, type) and issubclass(elem_type, Buildable):
        return elem_type
    return None


def _decode_buildable(cls: type, data: dict[str, Any], ctx: LoadContext) -> Any:
    """Decode ``data`` into ``cls`` via a registered leaf decoder or the generic walk."""
    from daitum_ui._decoders.leaves import LEAF_DECODERS

    decoder = LEAF_DECODERS.get(cls)
    if decoder is not None:
        return decoder(data, ctx)
    return decode_fields(cls, data, ctx)
