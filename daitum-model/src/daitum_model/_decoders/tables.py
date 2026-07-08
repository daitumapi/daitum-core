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
Decoders for the table hierarchy.

Tables carry no ``@type`` discriminator, so the concrete type is recovered structurally
from which top-level keys ``build()`` emitted:

- ``joinConditions`` -> :class:`JoinedTable`
- ``sourceTables`` -> :class:`UnionTable`
- ``sourceTableId`` -> :class:`DerivedTable`
- otherwise -> :class:`DataTable`

A derived/joined/union table is constructed from its *source tables' fields* (a join
condition names a field of each side; a derived table groups by source fields), and an
object/map field names a target table in its ``dataType``. Either way the referenced table
must be fully built before the dependent table is constructed. Daitum models forbid circular
table dependencies altogether — a table cannot depend on another that (directly or
transitively) depends on it back, through structural sources, object/map references, or
formulas — so the dependency graph is always a DAG. The model decoder uses
:func:`table_dependencies` and :func:`dependency_order` to build tables in an order where
every dependency precedes its dependents, then calls :func:`build_table` once per table, and
raises :class:`LoadError` if the input nonetheless contains a cycle.

``ModelBuilder.write_to_file`` emits ``tableDefinitions`` with ``sort_keys=True``, so the
on-disk order is alphabetical, not insertion order — the dependency sort makes the decoder
independent of definition order.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from daitum_model._decoders.data_types import decode_data_type
from daitum_model._decoders.fields import _IGNORED_FIELD_KEYS
from daitum_model.decoding import (
    LoadContext,
    LoadError,
    decode_into,
    optional_map,
    optional_seq,
    register_decoder,
)
from daitum_model.derived_table import AggregationMethod, DerivedTable, SortDirection
from daitum_model.fields import Field
from daitum_model.joined_table import JoinCondition, JoinedTable, JoinType
from daitum_model.tables import DataTable, Table
from daitum_model.union_table import UnionSource, UnionTable

if TYPE_CHECKING:
    from daitum_model.model import ModelBuilder


def _union_sources(data: dict[str, Any]) -> list[tuple[str, str]]:
    """Return the union's ``(source_table_id, mapping_key)`` pairs, or ``[]`` if not a union.

    Two equivalent serialisations exist. This library emits ``sourceTables`` — an array of
    ``{"sourceTableId", "mappingKey"}`` objects — which carries an explicit mapping key (needed
    when one table is reused under several keys). A model generated elsewhere may instead emit a
    flat ``sourceTableIds`` list of ids, with the mapping keys implied by the ``fieldMappings`` keys
    (mapping key == source table id in that shape). Accept both so either round-trips.
    """
    source_tables = data.get("sourceTables")
    if source_tables:
        return [(s["sourceTableId"], s["mappingKey"]) for s in source_tables]
    source_table_ids = data.get("sourceTableIds")
    if source_table_ids:
        return [(table_id, table_id) for table_id in source_table_ids]
    return []


def resolve_table_type(data: dict[str, Any]) -> type[Table]:
    """Return the concrete table class for a built table dict (structural dispatch).

    Dispatch on the structural key's *value*, not mere presence: a model generated elsewhere may
    emit every type key always, with ``null`` for the ones that do not apply (a union table then
    carries ``"joinConditions": null`` and ``"sourceTableId": null`` alongside its real sources).
    Keying on presence would misclassify such a union as a joined table and then fail iterating its
    ``null`` join conditions — or silently degrade it to a data table. A union is recognised from
    either sources shape (``sourceTables`` or ``sourceTableIds``); see :func:`_union_sources`.
    """
    if data.get("joinConditions") is not None:
        return JoinedTable
    if _union_sources(data):
        return UnionTable
    if data.get("sourceTableId") is not None:
        return DerivedTable
    return DataTable


def _reference_field_dependencies(data: dict[str, Any]) -> set[str]:
    """Return table ids named by composite (object/map) field dataTypes.

    An ``ObjectDataType``/``MapDataType`` field serialises its target table as
    ``dataType.tableId``; decoding the field resolves that table eagerly, so it must be built
    first. This applies to any table type, including a plain data table.
    """
    deps: set[str] = set()
    for field in optional_map(data, "fieldDefinitions").values():
        data_type = field.get("dataType")
        if isinstance(data_type, dict) and data_type.get("tableId") is not None:
            deps.add(data_type["tableId"])
    return deps


def table_dependencies(data: dict[str, Any]) -> set[str]:
    """Return the ids of the tables a built table must be *built after*.

    Derived/joined/union tables name their *structural* sources via
    ``sourceTableId``/``joinConditions``/``sourceTables``; any table type may additionally
    reference another table through an object/map field's dataType. Construction reads those
    tables' fields (or, for references, resolves the live table), so each must be fully built
    first. Daitum forbids circular table dependencies, so these edges always form a DAG.
    """
    deps = _reference_field_dependencies(data)
    table_type = resolve_table_type(data)
    if table_type is DerivedTable:
        deps.add(data["sourceTableId"])
    elif table_type is JoinedTable:
        for cond in data["joinConditions"]:
            deps.add(cond["leftTableId"])
            deps.add(cond["rightTableId"])
    elif table_type is UnionTable:
        deps.update(source_id for source_id, _ in _union_sources(data))
    return deps


def dependency_order(table_defs: dict[str, dict[str, Any]]) -> list[str]:
    """Order table ids so every source precedes its dependents (Kahn's algorithm).

    Dependencies on tables outside ``table_defs`` are ignored (they are resolved from the
    context). Raises :class:`LoadError` if the dependency graph has a cycle.
    """
    known = set(table_defs)
    # A table may reference itself through an object/map field; that self-edge is not a cycle
    # (the table is registered before its own fields are decoded), so drop it.
    pending = {tid: (table_dependencies(data) & known) - {tid} for tid, data in table_defs.items()}
    ordered: list[str] = []
    # Preserve definition order among ready tables for a stable, reproducible result.
    while pending:
        ready = [tid for tid in table_defs if tid in pending and not pending[tid]]
        if not ready:
            raise LoadError(f"Cyclic table dependency among {sorted(pending)!r}")
        for tid in ready:
            ordered.append(tid)
            del pending[tid]
        for deps in pending.values():
            deps.difference_update(ready)
    return ordered


def build_table(
    table_id: str, data: dict[str, Any], model: ModelBuilder, ctx: LoadContext
) -> Table:
    """Fully reconstruct one table: construct it, populate its fields, register field ids.

    Must be called in :func:`dependency_order` so every table this one is built from (or
    references) is already complete in ``ctx``.
    """
    table = construct_table(table_id, data, model, ctx)
    ctx.register(table_id, table)
    decode_table_fields(table, data, ctx)
    return table


def construct_table(
    table_id: str, data: dict[str, Any], model: ModelBuilder, ctx: LoadContext
) -> Table:
    """Create the (empty) table of the right type via the model factory.

    Join conditions and union sources reference other tables by id, so this must run after
    every table id is registered in ``ctx``. Fields are added separately by
    :func:`decode_table_fields`.
    """
    table_type = resolve_table_type(data)
    if table_type is DataTable:
        table: Table = model.add_data_table(table_id)
    elif table_type is DerivedTable:
        table = _construct_derived(table_id, data, model, ctx)
    elif table_type is JoinedTable:
        table = _construct_joined(table_id, data, model, ctx)
    else:
        table = _construct_union(table_id, data, model, ctx)
    _apply_table_metadata(table, data)
    return table


def _source_table(ctx: LoadContext, table_id: str) -> Table:
    """Resolve a source table by id via the context's table-only lookup.

    A field may share a table's id (a joined table's object-reference fields are named after
    their source table, and a calculated field elsewhere may reuse a table id), so resolving
    through the shared symbol table could return the shadowing field.
    :meth:`LoadContext.resolve_table` resolves from the model's field-free table registry,
    falling back to the symbol table only in the standalone-table decode path.
    """
    return ctx.resolve_table(table_id)


def _construct_derived(
    table_id: str, data: dict[str, Any], model: ModelBuilder, ctx: LoadContext
) -> DerivedTable:
    source_table = _source_table(ctx, data["sourceTableId"])
    grouping = data.get("groupingConfiguration")
    group_by = None
    if grouping is not None:
        group_by = [source_table.get_field(fid) for fid in optional_seq(grouping, "groupByFields")]
    filter_field = None
    if data.get("filterField") is not None:
        filter_field = source_table.get_field(data["filterField"])
    table = model.add_derived_table(
        table_id, source_table, group_by=group_by, filter_field=filter_field
    )
    return table


def _construct_joined(
    table_id: str, data: dict[str, Any], model: ModelBuilder, ctx: LoadContext
) -> JoinedTable:
    conditions = []
    for cond in data["joinConditions"]:
        left_table = _source_table(ctx, cond["leftTableId"])
        right_table = _source_table(ctx, cond["rightTableId"])
        # A CROSS join has no match fields, so ``leftTableField`` / ``rightTableField`` are absent.
        left_field_id = cond.get("leftTableField")
        right_field_id = cond.get("rightTableField")
        conditions.append(
            JoinCondition(
                left_table,
                right_table,
                JoinType(cond["joinType"]),
                left_table.get_field(left_field_id) if left_field_id is not None else None,
                right_table.get_field(right_field_id) if right_field_id is not None else None,
            )
        )
    return model.add_joined_table(table_id, conditions)


def _construct_union(
    table_id: str, data: dict[str, Any], model: ModelBuilder, ctx: LoadContext
) -> UnionTable:
    sources: list[Table | UnionSource] = [
        UnionSource(_source_table(ctx, source_id), mapping_key)
        for source_id, mapping_key in _union_sources(data)
    ]
    return model.add_union_table(table_id, sources)


def _apply_table_metadata(table: Table, data: dict[str, Any]) -> None:
    if data.get("keyColumnField") is not None:
        table.set_key_column(data["keyColumnField"])
    if data.get("idField") is not None:
        table.set_id_field(data["idField"])
    if data.get("modelLevel") is not None:
        table.set_model_level(data["modelLevel"])
    if data.get("validationGroup") is not None:
        table.set_validation_group(data["validationGroup"])
    if data.get("exportAsKeyColumn") is not None:
        table.set_export_as_key_column(data["exportAsKeyColumn"])


def decode_table_fields(table: Table, data: dict[str, Any], ctx: LoadContext) -> None:
    """Decode and register every field of an already-constructed table.

    Derived/joined/union tables build their own fields from sources, so for those the field
    set is reconstructed via dedicated paths; data tables decode each field directly.
    """
    if isinstance(table, DerivedTable):
        _populate_derived_fields(table, data, ctx)
    elif isinstance(table, UnionTable):
        _populate_union_fields(table, data, ctx)
    elif isinstance(table, JoinedTable):
        _populate_joined_fields(table, data, ctx)
    else:
        _populate_data_fields(table, data, ctx)

    for field in table.get_fields():
        ctx.register(field.id, field)


def _populate_data_fields(table: Table, data: dict[str, Any], ctx: LoadContext) -> None:
    for field_data in optional_map(data, "fieldDefinitions").values():
        field = decode_into(Field, field_data, ctx)
        table._add_field(field)  # noqa: SLF001 - decoder owns field registration


def _populate_derived_fields(table: DerivedTable, data: dict[str, Any], ctx: LoadContext) -> None:
    grouping = data.get("groupingConfiguration")
    aggregated_ids: set[str] = set()
    if grouping is not None:
        for agg in optional_seq(grouping, "aggregatedFields"):
            source_field = table._source_table.get_field(agg["sourceFieldId"])  # noqa: SLF001
            table.add_aggregated_field(
                agg["aggregatedFieldId"],
                source_field,
                AggregationMethod(agg["aggregationMethod"]),
            )
            aggregated_ids.add(agg["aggregatedFieldId"])

    # ``data`` fields are copied from the source table (aggregated ids are already created by the
    # loop above); ``calculated`` fields are genuine calculated fields defined on the derived table
    # itself, so they decode directly (preserving their formula) rather than being looked up in the
    # source. Combo/data fields only exist on data tables, so anything not ``calculated`` here is a
    # source copy. Source-field copies are added as one batch (``add_source_fields`` validates and
    # copies together); calculated fields are decoded individually.
    source_fields = []
    for field_id, field_data in optional_map(data, "fieldDefinitions").items():
        if field_id in aggregated_ids:
            continue
        if field_data.get("@type") == "calculated":
            table._add_field(decode_into(Field, field_data, ctx))  # noqa: SLF001
            continue
        source_fields.append(table._source_table.get_field(field_id))  # noqa: SLF001
    if source_fields:
        table.add_source_fields(source_fields)

    for sort_key in optional_seq(data, "sortKeys"):
        field = (
            table.get_field(sort_key["field"])
            if sort_key["field"] in [f.id for f in table.get_fields()]
            else table._source_table.get_field(sort_key["field"])
        )  # noqa: SLF001
        table.add_sort_key(field, SortDirection(sort_key["direction"]))


def _populate_joined_fields(table: JoinedTable, data: dict[str, Any], ctx: LoadContext) -> None:
    # A joined table's reference fields are produced by referencing each source table; the field's
    # dataType carries the source table id, which is fully built and registered in ``ctx`` by the
    # time this runs (dependency order), so resolve it directly. A ``calculated`` field is defined
    # on the joined table itself and decodes directly (preserving its formula).
    for field_data in optional_map(data, "fieldDefinitions").values():
        if field_data.get("@type") == "calculated":
            table._add_field(decode_into(Field, field_data, ctx))  # noqa: SLF001
            continue
        table.add_table_reference(_joined_source_table(field_data, ctx))


def _joined_source_table(field_data: dict[str, Any], ctx: LoadContext) -> Table:
    """Resolve the source table a joined-table reference field points at."""
    data_type = field_data.get("dataType")
    # Key on the value, not mere presence: a model generated elsewhere may emit ``tableId`` as an
    # explicit ``null``, which ``in`` would accept and then fail to resolve.
    if isinstance(data_type, dict) and data_type.get("tableId") is not None:
        return _source_table(ctx, data_type["tableId"])
    raise LoadError(f"Cannot resolve joined-table reference field {field_data.get('id')!r}")


#: Union field-build keys (camelCase) the populator consumes. A key outside this set (and outside
#: the shared :data:`_IGNORED_FIELD_KEYS` of platform-only metadata) is unmapped and rejected.
_UNION_FIELD_KEYS = frozenset(
    {
        "@type",
        "id",
        "tableId",
        "dataType",
        "orderIndex",
        "description",
        "unique",
        "nullable",
        "defaultValue",
        "importFormat",
    }
)


def _populate_union_fields(table: UnionTable, data: dict[str, Any], ctx: LoadContext) -> None:
    for field_data in optional_map(data, "fieldDefinitions").values():
        # A ``calculated`` field is defined on the union table itself and decodes directly
        # (preserving its formula); the remaining fields are the union's own stacked data fields.
        if field_data.get("@type") == "calculated":
            table._add_field(decode_into(Field, field_data, ctx))  # noqa: SLF001
            continue
        extra = set(field_data) - _UNION_FIELD_KEYS - _IGNORED_FIELD_KEYS
        if extra:
            raise LoadError(
                f"Union field {field_data.get('id')!r}: unmapped key(s) {sorted(extra)!r}"
            )
        data_type = decode_data_type(field_data["dataType"], ctx)
        table.add_field(
            field_data["id"],
            data_type,
            order_index=field_data.get("orderIndex"),
            description=field_data.get("description"),
        )

    for mapping_key, mapping in optional_map(data, "fieldMappings").items():
        union_source = _union_source_for(table, mapping_key)
        for union_field_name, source_field_id in mapping.items():
            source_field = union_source.source_table.get_field(source_field_id)
            table.add_field_mapping(union_source, union_field_name, source_field)

    if data.get("filterField") is not None:
        table.set_filter_field(table.get_field(data["filterField"]))


def _union_source_for(table: UnionTable, mapping_key: str) -> UnionSource:
    for source in table.source_tables:
        if source.mapping_key == mapping_key:
            return source
    raise LoadError(f"Union table {table.id!r} has no source with mapping key {mapping_key!r}")


def register() -> None:
    """Register the structural table decoder for every concrete table type.

    Tables are normally decoded as part of a whole model via :func:`build_table` in
    :func:`dependency_order`. The :class:`Table`-level decoder registered here supports
    decoding a *standalone* table dict (used in tests) by spinning up a throwaway model and
    resolving any source tables from the provided context.
    """

    def decode(data: dict[str, Any], ctx: LoadContext) -> Table:
        from daitum_model.model import ModelBuilder  # noqa: PLC0415

        model = ModelBuilder()
        return build_table(_standalone_table_id(data), data, model, ctx)

    register_decoder(Table, decode)
    register_decoder(DataTable, decode)
    register_decoder(DerivedTable, decode)
    register_decoder(JoinedTable, decode)
    register_decoder(UnionTable, decode)


def _standalone_table_id(data: dict[str, Any]) -> str:
    """Recover a standalone table's id from its fields' ``tableId`` (all fields share it)."""
    for field_data in optional_map(data, "fieldDefinitions").values():
        table_id = field_data.get("tableId")
        if table_id is not None:
            return str(table_id)
    raise LoadError(
        "Cannot decode a standalone table with no fields; decode it as part of a model instead"
    )
