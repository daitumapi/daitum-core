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
Decoder for the data-type family (:class:`DataType`, :class:`ObjectDataType`,
:class:`MapDataType`).

``build()`` erases the data-type identity in two ways. A bare :class:`DataType` serialises
to its ``.value`` string (e.g. ``"DECIMAL"``); the composite types serialise to a dict
whose ``type`` field names the concrete shape (``"OBJECT"`` / ``"OBJECT_ARRAY"`` for an
:class:`ObjectDataType`, ``"<PRIMITIVE>_MAP"`` for a :class:`MapDataType`). The composite
types also carry a ``tableId`` referencing a model table, resolved here through the load
context's symbol table.
"""

from __future__ import annotations

from typing import Any

from daitum_model.data_types import BaseDataType, DataType, MapDataType, ObjectDataType
from daitum_model.decoding import LoadContext, LoadError

#: Suffix marking the ``type`` field of a serialised :class:`MapDataType`.
_MAP_SUFFIX = "_MAP"


def decode_data_type(value: Any, ctx: LoadContext) -> BaseDataType:
    """Recover the typed data type ``build()`` erased.

    A string body is a :class:`DataType` enum value; a dict body is an
    :class:`ObjectDataType` or :class:`MapDataType` resolved against ``ctx``.
    """
    if isinstance(value, str):
        return DataType(value)
    if isinstance(value, dict):
        return _decode_composite(value, ctx)
    raise LoadError(f"Cannot decode data type from {value!r}")


def _decode_composite(value: dict[str, Any], ctx: LoadContext) -> BaseDataType:
    type_str = value.get("type")
    table_id = value.get("tableId")
    if type_str is None or table_id is None:
        raise LoadError(f"Composite data type missing 'type'/'tableId': {value!r}")

    source_table = ctx.resolve_table(table_id)

    if type_str in ("OBJECT", "OBJECT_ARRAY"):
        return ObjectDataType(source_table, is_array=type_str == "OBJECT_ARRAY")

    if type_str.endswith(_MAP_SUFFIX):
        primitive = type_str[: -len(_MAP_SUFFIX)]
        return MapDataType(DataType(primitive), source_table)

    raise LoadError(f"Unknown composite data type {type_str!r}")
