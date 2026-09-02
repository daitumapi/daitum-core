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

"""Rule: a union table's sources, mappings, and filter field must resolve."""

from __future__ import annotations

from daitum_model.union_table import UnionTable
from daitum_model.validation.engine import rule
from daitum_model.validation.errors import MissingSourceFieldError, TableReferenceError
from daitum_model.validation.graph import ModelGraph
from daitum_model.validation.report import ValidationReport


@rule
class UnionSourceAndMappingFieldsExist:
    """A union table's source tables must be in the model, each mapped source field must
    exist on its source table, and any filter field must exist on the union table."""

    id = "union-source-and-mapping-fields-exist"

    def check(self, graph: ModelGraph, report: ValidationReport) -> None:
        for table in graph.tables.values():
            if isinstance(table, UnionTable):
                self._check_union(table, graph, report)

    def _check_union(self, table: UnionTable, graph: ModelGraph, report: ValidationReport) -> None:
        location = f"union table '{table.id}'"

        for source in table.source_tables:
            if source.source_table_id not in graph.tables:
                report.add(
                    TableReferenceError(
                        rule_id=self.id,
                        location=location,
                        message=f"source table '{source.source_table_id}' is not in the model",
                    )
                )

        for mapping in table.field_mappings.values():
            source_id = mapping.source_table.id
            for union_field, source_field_id in mapping.mapping.items():
                if not graph.has_field(source_id, source_field_id):
                    available = ", ".join(graph.available_fields(source_id)) or "<none>"
                    report.add(
                        MissingSourceFieldError(
                            rule_id=self.id,
                            location=f"{location}.field '{union_field}'",
                            message=(
                                f"mapped source field '{source_field_id}' does not exist on "
                                f"source table '{source_id}' (available fields: {available})"
                            ),
                        )
                    )

        if table.filter_field is not None and not graph.has_field(table.id, table.filter_field):
            available = ", ".join(graph.available_fields(table.id)) or "<none>"
            report.add(
                MissingSourceFieldError(
                    rule_id=self.id,
                    location=location,
                    message=(
                        f"filter field '{table.filter_field}' does not exist on the union table "
                        f"(available fields: {available})"
                    ),
                )
            )
