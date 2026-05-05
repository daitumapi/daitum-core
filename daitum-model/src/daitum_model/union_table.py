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
``UnionTable`` and its supporting ``UnionSource`` value object.

A union table stacks rows from multiple source tables. Field mappings declare which source-table
fields populate each union-table field, since the source schemas may differ.
"""

from __future__ import annotations

from typing import Any

from typeguard import typechecked

from ._buildable import Buildable
from .data_types import BaseDataType
from .fields import DataField, Field
from .tables import Table


@typechecked
class UnionSource(Buildable):
    """
    A source table in a union. Multiple ``UnionSource`` instances in a ``UnionTable`` may
    reference the same underlying table, distinguished by ``mapping_key``.
    """

    def __init__(self, source_table: Table, mapping_key: str):
        self._source_table = source_table
        self.source_table_id = source_table.id
        self.mapping_key = mapping_key

    @property
    def source_table(self) -> Table:
        return self._source_table


@typechecked
class UnionTable(Table):
    """
    Represents a table that is derived by performing a union operation on multiple source tables.

    A union operation combines rows from multiple tables into a single table. Unlike joins,
     a union does not merge columns based on key relationships but instead stacks rows from
     different tables on top of each other.

    Attributes:
        source_tables: The list of tables being combined into the `UnionTable`.
        filter_field: An optional field ID that acts as a filter for selecting specific rows
                      across the source tables.
    """

    def __init__(
        self,
        id: str,
        source_tables: list[Table | UnionSource],
    ):
        super().__init__(id)
        self.filter_field: str | None = None
        self.source_tables = [
            (s if isinstance(s, UnionSource) else UnionSource(s, s.id)) for s in source_tables
        ]

        self.field_mappings: dict[str, UnionTable.FieldMapping] = {}

    def set_filter_field(self, field: Field) -> UnionTable:
        """Sets the filter field for this union table. Returns self."""
        self.filter_field = field.id
        return self

    def add_field(
        self,
        id: str,
        data_type: BaseDataType,
        order_index: int | None = None,
        description: str | None = None,
    ) -> DataField:
        """
        Adds a new field to the `UnionTable`.

        Args:
            id: A unique identifier for the field.
            data_type: The data type of the field.
            order_index: (Optional) The order in which the field appears.

        Returns:
            DataField: The newly created `DataField` instance.
        """
        # tracking??
        data_field = DataField(id, self, data_type)
        if order_index is not None:
            data_field.set_order_index(order_index)
        if description is not None:
            data_field.set_description(description)
        self._add_field(data_field)
        return data_field

    def _resolve_union_source(self, source_table: Table | UnionSource) -> UnionSource:
        """
        Find the `UnionSource` registered on this `UnionTable` that matches *source_table*.

        ``UnionSource`` does not implement ``__eq__``, so a fresh instance constructed at the call
        site is never equal (under default identity semantics) to one already stored in
        ``self.source_tables``. Resolve by matching on the underlying table (and ``mapping_key``
        when a ``UnionSource`` is supplied) instead of relying on object identity.
        """
        if isinstance(source_table, UnionSource):
            for registered in self.source_tables:
                if (
                    registered.source_table is source_table.source_table
                    and registered.mapping_key == source_table.mapping_key
                ):
                    return registered
            raise ValueError("The provided source table does not appear in the UnionTable")

        matches = [s for s in self.source_tables if s.source_table is source_table]
        if not matches:
            raise ValueError("The provided source table does not appear in the UnionTable")
        if len(matches) > 1:
            raise ValueError(
                f"Source table '{source_table.id}' is registered multiple times in the UnionTable; "
                "pass a UnionSource with the desired mapping_key to disambiguate"
            )
        return matches[0]

    def add_field_mapping(
        self, source_table: Table | UnionSource, field_name: str, source_field: Field
    ):
        """
        Maps a field from a source table to a field in the `UnionTable`.

        Field mappings allow fields with different names in different tables to be treated as
        equivalent in the `UnionTable`.

        Args:
            source_table: The source table containing the field, or a UnionSource describing the
                source table and the key to identify it if the same source is reused.
            field_name: The name of the field in the `UnionTable`.
            source_field: The corresponding field in the source table.

        Raises:
            ValueError: If the source table is not part of the `UnionTable`.
        """
        union_source = self._resolve_union_source(source_table)

        if field_name not in self.field_definitions:
            raise ValueError(f"The field '{field_name}' does not exist in the UnionTable")
        union_field = self.field_definitions[field_name]
        if union_field.data_type != source_field.data_type:
            raise ValueError(
                f"Data type mismatch for field mapping '{field_name}': UnionTable field has type "
                f"{union_field.data_type}, but source field '{source_field.id}' has type "
                f"{source_field.data_type}"
            )

        if union_source.mapping_key not in self.field_mappings:
            self.field_mappings[union_source.mapping_key] = UnionTable.FieldMapping(union_source)
        self.field_mappings[union_source.mapping_key].add_map(field_name, source_field)

    def direct_field_mapping(self, source_tables: list[Table | UnionSource] | None = None):
        """
        Automatically maps fields from the source tables that have matching field IDs.

        If `source_tables` is not provided, it defaults to all source tables in the `UnionTable`.

        Args:
            source_tables: (Optional) A list of source tables to perform direct field mapping on.

        Raises:
            ValueError: If a provided source table is not part of the `UnionTable`.
        """
        tables = (
            [self._resolve_union_source(s) for s in source_tables]
            if source_tables
            else self.source_tables
        )

        for table in tables:
            for field in self.field_definitions.values():
                if (
                    isinstance(field, DataField)
                    and field.id in table.source_table.field_definitions
                ):
                    source_field = table.source_table.field_definitions[field.id]
                    self.add_field_mapping(table, field.id, source_field)

    class FieldMapping(Buildable):
        def __init__(self, union_source: UnionSource):
            self.union_source = union_source
            self.mapping: dict[str, str] = {}

        @property
        def source_table(self) -> Table:
            """
            Returns: the source table for this field mapping.
            """
            return self.union_source.source_table

        @property
        def mapping_key(self) -> str:
            """
            Returns: mapping_key for this field mapping.
            """
            return self.union_source.mapping_key

        # pylint: disable=missing-function-docstring
        def add_map(self, field_name: str, source_field: Field):
            if source_field.id not in (field.id for field in self.source_table.get_fields()):
                raise ValueError(
                    f"The provided source field with id {source_field.id} does not appear in"
                    f" the source table"
                )

            self.mapping[field_name] = source_field.id

        def build(self) -> dict[str, Any]:
            return self.mapping
