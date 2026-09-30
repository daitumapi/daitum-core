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
Construction of the model's validation list tables.

Internal to :mod:`daitum_model`: the public API that builds and orders the table lives on
:class:`~daitum_model.ModelBuilder`, whose
:meth:`~daitum_model.ModelBuilder.set_validation_table` is this module's only caller.
Only the table construction lives here, to keep it out of the builder's own module.

The table and field ids below are the contract between the built table and anything
presented on top of it, so they are re-exported from :mod:`daitum_model`; import them from
there rather than from this module. They sit in this module, not on
:mod:`daitum_model.model`, because ``model`` is imported while the package is still
initialising -- a module it depends on must not reach back into the package.
"""

from typing import TYPE_CHECKING

from typeguard import typechecked

from daitum_model.formulas import ARRAY, IF, INDEX, ISBLANK, ROW, ROWS, TEXT, TEXTJOIN, VALUES

from ._severity import SEVERITY_RANK, Severity
from .data_types import DataType, MapDataType, ObjectDataType
from .derived_table import SortDirection
from .fields import Field, ValidationFieldsContainer
from .formula import Formula
from .tables import Table
from .union_table import UnionSource

if TYPE_CHECKING:
    from .model import ModelBuilder


#: Table ids produced by :meth:`~daitum_model.ModelBuilder.set_validation_table`.
VALIDATION_LIST_TABLE = "ValidationList"
VALIDATION_LIST_SORTED_TABLE = "ValidationListSorted"

#: Field ids shared between the validation list table and anything built on top of it.
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

#: Maximum number of array elements rendered into the value column before eliding.
MAX_VALUE_ROWS = 3

#: Subgroups sort equal until a presentation layer calls :meth:`ModelBuilder.set_subgroup_order`.
DEFAULT_SUBGROUP_ORDER = 0


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

    # ``model`` can only be a forward reference here, since ``model`` imports this module,
    # so typeguard does not check it. The sole caller is
    # ``ModelBuilder.set_validation_table``, which passes itself.
    def __init__(self, model: "ModelBuilder"):
        self.model = model
        self._source_tables: set[str] = set()

    def build(self) -> Table | None:
        union_sources: list[Table | UnionSource] = []
        source_field_mappings: list[list[tuple[str, Field]]] = []

        for table_id in self.model.get_validated_table_ids():
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
