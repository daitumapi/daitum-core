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
Decoders for the field hierarchy (:class:`DataField`, :class:`CalculatedField`,
:class:`ComboField`), dispatched on the ``@type`` discriminator.

Fields cannot be reconstructed by the generic constructor walk: their ``build()`` emits a
``tableId`` and a ``dataType``, but the field constructors take a live ``table`` object (and
calculated/combo fields take a ``formula`` rather than a ``dataType``). Each decoder therefore
resolves the owning table from the load context, builds the field directly, and registers it
under its id so later references resolve.
"""

from __future__ import annotations

from typing import Any

from daitum_model._decoders.data_types import decode_data_type
from daitum_model._decoders.formula import defer_formula, placeholder_formula
from daitum_model.decoding import LoadContext, LoadError, register_decoder, register_type
from daitum_model.fields import CalculatedField, ComboField, DataField, Field
from daitum_model.tables import Table


def _resolve_table(data: dict[str, Any], ctx: LoadContext) -> Table:
    table_id = data.get("tableId")
    if table_id is None:
        raise LoadError(f"Field missing 'tableId': {data!r}")
    table = ctx.resolve(table_id)
    if not isinstance(table, Table):
        raise LoadError(f"Field references {table_id!r} which is not a table")
    return table


def _apply_common(field: Field, data: dict[str, Any]) -> None:
    if data.get("orderIndex") is not None:
        field.set_order_index(data["orderIndex"])
    if data.get("description") is not None:
        field.set_description(data["description"])
    if data.get("trackingGroups"):
        field.set_tracking_groups(data["trackingGroups"])


def decode_data_field(data: dict[str, Any], ctx: LoadContext) -> DataField:
    """Reconstruct a :class:`DataField` from its built dict."""
    table = _resolve_table(data, ctx)
    data_type = decode_data_type(data["dataType"], ctx)
    field = DataField(data["id"], table, data_type)
    _apply_common(field, data)
    if data.get("defaultValue") is not None:
        field.set_default_value(data["defaultValue"])
    if data.get("importFormat") is not None:
        field.set_import_format(data["importFormat"])
    if data.get("unique") is not None:
        field.set_unique(data["unique"])
    if data.get("nullable") is not None:
        field.set_nullable(data["nullable"])
    return field


def decode_calculated_field(data: dict[str, Any], ctx: LoadContext) -> CalculatedField:
    """Reconstruct a :class:`CalculatedField` from its built dict.

    The formula is parsed in phase 2 (deferred) so its references resolve regardless of decode
    order; the field is constructed now with a typed placeholder carrying the correct data type, and
    the parsed tree replaces it once every symbol is registered.
    """
    table = _resolve_table(data, ctx)
    field = CalculatedField(data["id"], table, placeholder_formula(data["formula"], ctx))
    defer_formula(data["formula"], ctx, table, lambda f: setattr(field, "formula", f))
    _apply_common(field, data)
    return field


def decode_combo_field(data: dict[str, Any], ctx: LoadContext) -> ComboField:
    """Reconstruct a :class:`ComboField` from its built dict (formula parsed in phase 2)."""
    table = _resolve_table(data, ctx)
    field = ComboField(
        data["id"], table, placeholder_formula(data["formula"], ctx), data["calculateInOptimiser"]
    )
    defer_formula(data["formula"], ctx, table, lambda f: setattr(field, "formula", f))
    _apply_common(field, data)
    if data.get("defaultValue") is not None:
        field.set_default_value(data["defaultValue"])
    if data.get("importFormat") is not None:
        field.set_import_format(data["importFormat"])
    return field


#: Recognised field-build keys (camelCase) the decoder consumes.
_KNOWN_KEYS = {
    "@type",
    "id",
    "tableId",
    "dataType",
    "formula",
    "calculateInOptimiser",
    "orderIndex",
    "description",
    "defaultValue",
    "importFormat",
    "unique",
    "nullable",
    "trackingGroups",
}

#: Read-only/derived field metadata a model generated elsewhere (the platform) emits but this
#: library does not model. These are tolerated — skipped, not mapped — so a foreign model still
#: decodes; they are not reproduced on re-build. The unmapped-key guard still rejects any key
#: outside both sets, so a genuinely unexpected key (a real decoder gap) still fails loudly.
#: Shared with the union-field populator, which applies the same tolerance.
_IGNORED_FIELD_KEYS = frozenset(
    {
        "userEditable",
        "derivedField",
        "aggregatedField",
        "dependsOnDecision",
        "requiredByOutput",
        "transientData",
    }
)


def _guard_unmapped_keys(data: dict[str, Any]) -> None:
    extra = set(data) - _KNOWN_KEYS - _IGNORED_FIELD_KEYS
    if extra:
        raise LoadError(f"Field: unmapped key(s) {sorted(extra)!r}")


def _wrap(decoder):
    def decode(data: dict[str, Any], ctx: LoadContext):
        _guard_unmapped_keys(data)
        return decoder(data, ctx)

    return decode


def register() -> None:
    """Register the field decoders and their ``@type`` discriminators."""
    register_type(Field, "data", DataField)
    register_type(Field, "calculated", CalculatedField)
    register_type(Field, "combo", ComboField)
    register_decoder(DataField, _wrap(decode_data_field))
    register_decoder(CalculatedField, _wrap(decode_calculated_field))
    register_decoder(ComboField, _wrap(decode_combo_field))
