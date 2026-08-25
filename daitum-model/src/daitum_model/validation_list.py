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
Validation list table builder for aggregating model validation errors.

This module collects validation errors across all model tables into a single
``ValidationList`` table. It inspects each table for fields following the
``__invalid__`` and ``__message__`` naming conventions, derives filtered tables
containing only invalid rows, and unions them into a sorted validation table.

This is a model-only helper: it builds tables and nothing else. Presentation --
views, filters, navigation and click-through behaviour -- is built on top of the
resulting table by ``daitum_components``, which uses ``SOURCE_TABLE_FIELD`` to
derive whatever per-source columns it needs.
"""

from collections.abc import Mapping

from typeguard import typechecked

from daitum_model import (
    DataType,
    Field,
    Formula,
    MapDataType,
    ModelBuilder,
    ObjectDataType,
    Severity,
    SortDirection,
    Table,
    UnionSource,
)
from daitum_model.fields import CalculatedField, ValidationFieldsContainer
from daitum_model.formula import CONST
from daitum_model.formulas import ARRAY, IF, INDEX, ISBLANK, ROW, ROWS, TEXT, TEXTJOIN, VALUES
from daitum_model.validator import SEVERITY_RANK

# Table ids produced by this module
VALIDATION_LIST_TABLE = "ValidationList"
VALIDATION_LIST_SORTED_TABLE = "ValidationListSorted"

# Field ids shared between the validation list table and anything built on top of it
GROUP_FIELD = "__Group__"
SUBGROUP_FIELD = "__Subgroup__"
SOURCE_TABLE_FIELD = "__Source Table__"
TYPE_FIELD = "__Type__"
ROW_FIELD = "__Row__"
VALUE_FIELD = "__Value__"
FIELD_NAME_FIELD = "__Field__"
MESSAGE_FIELD = "__Message__"
SUMMARY_MESSAGE_FIELD = "__Summary Message__"
SEVERITY_RANK_FIELD = "__Severity Rank__"
SUBGROUP_ORDER_FIELD = "__Subgroup Order__"
FILTER_FIELD = "__Filter__"

# Maximum number of array elements rendered into the value column before eliding
MAX_VALUE_ROWS = 3

# Subgroups sort equal until a presentation layer calls set_subgroup_order
DEFAULT_SUBGROUP_ORDER = 0


@typechecked
def get_validation_list_table(model: ModelBuilder) -> Table | None:
    """Build the model's validation list table, or return the one already built.

    Scans every table registered with *model* for fields following the
    ``<base_id>__invalid__<severity>`` / ``<base_id>__message__<severity>`` naming
    convention. For each matching pair a union source is created that filters to
    invalid rows only, all sources are unioned into a ``ValidationList`` table, and
    a ``ValidationListSorted`` derived table is returned, ordered by subgroup, row,
    severity rank and field.

    Subgroups themselves sort equal, so they fall back to sorting by name. Call
    :func:`set_subgroup_order` afterwards to impose an order the model does not know
    about, such as the one the navigation bar uses.

    Safe to call more than once. The second call returns the table built by the
    first, so a single model can carry both a model transform's log table and a
    validation list view without building the table twice.

    Every table with a validated field must carry a validation group, set via
    :meth:`~daitum_model.Table.set_validation_group`.

    Args:
        model: The model builder whose tables are scanned, and onto which the
            validation list tables and their supporting calculated fields are added.

    Returns:
        The sorted validation list table, or ``None`` when the model has no
        validated fields.

    Raises:
        ValueError: If a table with a validated field has no validation group.
    """

    for table in model.get_tables():
        if table.id == VALIDATION_LIST_SORTED_TABLE:
            return table
    return _ValidationListBuilder(model).build()


@typechecked
def get_validated_table_ids(model: ModelBuilder) -> list[str]:
    """Return the ids of tables with at least one validated field, in registration order.

    These are the tables that contribute rows to the validation list, and the values
    that appear in ``SOURCE_TABLE_FIELD``. A pure query -- it does not modify the model.
    """

    return [table.id for table in model.get_tables() if _validated_fields(table)]


@typechecked
def set_subgroup_order(model: ModelBuilder, subgroup_order: Mapping[str, int]) -> None:
    """Override the subgroup sort position of source tables on a built validation list.

    The validation list leaves every subgroup sorting equal, so they fall back to sorting
    by name -- fine for a model transform's log table, which has no navigation to follow.
    A presentation layer that wants a particular order -- matching the navigation bar,
    say -- calls this once the table has been built.

    Only the sort position changes: the column, the union mappings and the sort keys are
    all untouched, so any table derived from the validation list picks the new order up.
    Call it before the model is built, and after
    :func:`get_validation_list_table`.

    Args:
        model: The model builder carrying the validation list.
        subgroup_order: Source table id to sort position. Ids that contributed no rows to
            the validation list are ignored, so a caller may pass positions for every
            table it knows about.

    Raises:
        ValueError: If the validation list has not been built yet.
    """

    source_table_ids = get_validated_table_ids(model)
    if not source_table_ids:
        raise ValueError(
            "Cannot set the subgroup order: the model has no validated fields, so no "
            "validation list table was produced."
        )

    for table_id in source_table_ids:
        if table_id not in subgroup_order:
            continue
        _subgroup_order_field(model.get_table(table_id)).formula = CONST(subgroup_order[table_id])


def _subgroup_order_field(table: Table) -> CalculatedField:
    """Return the table's subgroup order column, added when the validation list is built."""

    for field in table.get_fields():
        if field.id == SUBGROUP_ORDER_FIELD and isinstance(field, CalculatedField):
            return field
    raise ValueError(
        f"Cannot set the subgroup order for {table.id}: the validation list has not been "
        f"built. Call get_validation_list_table() first."
    )


def _validated_fields(table: Table) -> list[tuple[Field, ValidationFieldsContainer]]:
    """Return each (field, validation container) pair the table contributes."""

    pairs: list[tuple[Field, ValidationFieldsContainer]] = []
    for field in table.get_fields():
        containers = field.get_validation_fields()
        if not containers or not isinstance(containers, list):
            continue
        pairs.extend((field, container) for container in containers)
    return pairs


@typechecked
class _ValidationListBuilder:
    """Builds the validation list tables for one model. Single use, via ``build()``."""

    def __init__(self, model: ModelBuilder):
        self.model = model
        self._source_tables: set[str] = set()

    def build(self) -> Table | None:
        union_sources: list[Table | UnionSource] = []
        source_field_mappings: list[list[tuple[str, Field]]] = []

        for table_id in get_validated_table_ids(self.model):
            table = self.model.get_table(table_id)
            for field, container in _validated_fields(table):
                source, field_mappings = self._build_union_source(table, field, container)
                union_sources.append(source)
                source_field_mappings.append(field_mappings)

        if not union_sources:
            return None
        return self._build_sorted_union_table(union_sources, source_field_mappings)

    def _resolve_group(self, table: Table) -> str:
        if not table.validation_group:
            raise ValueError(
                f"Table {table.id} must have a validation group; "
                f"call set_validation_group() on it."
            )
        return table.validation_group

    def _get_row_field(self, table: Table) -> Field:
        if ROW_FIELD in [f.id for f in table.get_fields()]:
            return table.get_field(ROW_FIELD)
        return table.add_calculated_field(ROW_FIELD, ROW())

    def _add_shared_fields(self, table: Table) -> None:
        """Add the columns every row of a source table shares, once per table."""

        if table.id in self._source_tables:
            return
        self._source_tables.add(table.id)

        table.add_calculated_field(GROUP_FIELD, self._resolve_group(table))
        table.add_calculated_field(SUBGROUP_FIELD, table.display_name)
        # The model makes no claim about subgroup order; a presentation layer that wants
        # one calls set_subgroup_order. Left equal, subgroups fall back to the next sort
        # key, the subgroup name.
        table.add_calculated_field(SUBGROUP_ORDER_FIELD, DEFAULT_SUBGROUP_ORDER)
        table.add_calculated_field(SOURCE_TABLE_FIELD, table.id)

    def _display_text(self, field: Field) -> Formula:
        """Render *field* as the string shown in ``VALUE_FIELD``."""

        text_field: Field | Formula = field
        data_type = text_field.to_data_type()

        if isinstance(data_type, ObjectDataType):
            source_table = self.model.get_table(data_type._source_table.id)
            display_column = source_table.key_column or source_table.id_field
            if display_column is None:
                raise ValueError(
                    f"Either key_column or id_field must be set for the "
                    f"table {data_type._source_table.id}."
                )
            text_field = field[display_column]

        if isinstance(data_type, MapDataType):
            text_field = VALUES(field)

        if not text_field.to_data_type().is_array():
            return TEXT(text_field)

        string_array = TEXT(text_field)
        sub_array_values = INDEX(string_array, ARRAY(True, 1, 2, 3))
        final_string_array = IF(
            ROWS(string_array) > MAX_VALUE_ROWS,
            ARRAY(True, sub_array_values, "..."),
            string_array,
        )
        return TEXTJOIN(", ", True, final_string_array)

    def _build_union_source(
        self, table: Table, field: Field, container: ValidationFieldsContainer
    ) -> tuple[UnionSource, list[tuple[str, Field]]]:
        severity = container.severity.value

        bridge_field = table.add_calculated_field(
            f"{field.id}__msg__{severity}", container.message_field
        )
        row_field = self._get_row_field(table)
        self._add_shared_fields(table)

        # Per-(field, severity) columns need a unique prefix on the source table
        unique_prefix = f"{field.id}__{severity}"
        type_field = table.add_calculated_field(f"{unique_prefix}__type", severity)
        value_field = table.add_calculated_field(
            f"{unique_prefix}__value", IF(ISBLANK(field), "", self._display_text(field))
        )
        field_name_field = table.add_calculated_field(f"{unique_prefix}__field_id", field.id)
        summary_field = table.add_calculated_field(
            f"{unique_prefix}__summary_msg", container.summary_message
        )

        union_source = UnionSource(table, f"{table.id}__{unique_prefix}")
        field_mappings: list[tuple[str, Field]] = [
            (FILTER_FIELD, container.invalid_field),
            (GROUP_FIELD, table.get_field(GROUP_FIELD)),
            (SUBGROUP_FIELD, table.get_field(SUBGROUP_FIELD)),
            (SUBGROUP_ORDER_FIELD, table.get_field(SUBGROUP_ORDER_FIELD)),
            (SOURCE_TABLE_FIELD, table.get_field(SOURCE_TABLE_FIELD)),
            (ROW_FIELD, row_field),
            (TYPE_FIELD, type_field),
            (VALUE_FIELD, value_field),
            (FIELD_NAME_FIELD, field_name_field),
            (MESSAGE_FIELD, bridge_field),
            (SUMMARY_MESSAGE_FIELD, summary_field),
        ]
        return union_source, field_mappings

    def _build_sorted_union_table(
        self,
        union_sources: list[Table | UnionSource],
        source_field_mappings: list[list[tuple[str, Field]]],
    ) -> Table:
        union_table = self.model.add_union_table(VALIDATION_LIST_TABLE, union_sources)

        filter_field = union_table.add_field(FILTER_FIELD, DataType.BOOLEAN, None)
        union_table.filter_field = filter_field.id

        union_table.add_field(GROUP_FIELD, DataType.STRING, None)
        union_table.add_field(SUBGROUP_FIELD, DataType.STRING, None)
        union_table.add_field(SUBGROUP_ORDER_FIELD, DataType.INTEGER, None)
        union_table.add_field(SOURCE_TABLE_FIELD, DataType.STRING, None)
        union_table.add_field(TYPE_FIELD, DataType.STRING, None)
        union_table.add_field(ROW_FIELD, DataType.INTEGER, None)
        union_table.add_field(VALUE_FIELD, DataType.STRING, None)
        union_table.add_field(FIELD_NAME_FIELD, DataType.STRING, None)
        union_table.add_field(MESSAGE_FIELD, DataType.STRING, None)
        union_table.add_field(SUMMARY_MESSAGE_FIELD, DataType.STRING, None)

        for union_source, field_mappings in zip(union_sources, source_field_mappings, strict=True):
            for union_field_name, source_field in field_mappings:
                union_table.add_field_mapping(union_source, union_field_name, source_field)

        type_field = union_table.get_field(TYPE_FIELD)
        set_error_warning_info_rank = IF(
            type_field.equal_to("Error"),
            SEVERITY_RANK[Severity.ERROR],
            IF(
                type_field.equal_to("Warning"),
                SEVERITY_RANK[Severity.WARNING],
                SEVERITY_RANK[Severity.INFO],
            ),
        )
        union_table.add_calculated_field(
            SEVERITY_RANK_FIELD,
            IF(
                type_field.equal_to("Critical"),
                SEVERITY_RANK[Severity.CRITICAL],
                set_error_warning_info_rank,
            ),
        )

        sorted_table = self.model.add_derived_table(VALIDATION_LIST_SORTED_TABLE, union_table)
        sorted_table.add_source_fields()
        sorted_table.add_sort_key(
            sorted_table.get_field(SUBGROUP_ORDER_FIELD), SortDirection.ASCENDING
        )
        sorted_table.add_sort_key(sorted_table.get_field(SUBGROUP_FIELD), SortDirection.ASCENDING)
        sorted_table.add_sort_key(sorted_table.get_field(ROW_FIELD), SortDirection.ASCENDING)
        sorted_table.add_sort_key(
            sorted_table.get_field(SEVERITY_RANK_FIELD), SortDirection.DESCENDING
        )
        sorted_table.add_sort_key(sorted_table.get_field(FIELD_NAME_FIELD), SortDirection.ASCENDING)

        return sorted_table
