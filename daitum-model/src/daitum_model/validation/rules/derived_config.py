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

"""Rule: a derived table's group-by/filter/sort/aggregation fields must exist on its source."""

from __future__ import annotations

from daitum_model.derived_table import DerivedTable
from daitum_model.validation.engine import rule
from daitum_model.validation.errors import MissingSourceFieldError, TableReferenceError
from daitum_model.validation.graph import ModelGraph
from daitum_model.validation.report import ValidationReport


@rule
class DerivedTableFieldsExist:
    """Every field a :class:`DerivedTable` configures must exist on its source table.

    Covers the group-by fields, the filter field, each sort key, and each aggregated
    field's source field. These are exactly the references the platform rejects when they
    name a field that is not on the source table.
    """

    id = "derived-table-fields-exist"

    def check(self, graph: ModelGraph, report: ValidationReport) -> None:
        for table in graph.tables.values():
            if isinstance(table, DerivedTable):
                self._check_derived(table, graph, report)

    def _check_derived(
        self, table: DerivedTable, graph: ModelGraph, report: ValidationReport
    ) -> None:
        source_id = table.source_table_id
        if source_id not in graph.tables:
            report.add(
                TableReferenceError(
                    rule_id=self.id,
                    location=f"derived table '{table.id}'",
                    message=f"source table '{source_id}' is not in the model",
                )
            )
            return

        location = f"derived table '{table.id}'"

        def require(field_id: str, kind: str) -> None:
            if not graph.has_field(source_id, field_id):
                available = ", ".join(graph.available_fields(source_id)) or "<none>"
                report.add(
                    MissingSourceFieldError(
                        rule_id=self.id,
                        location=location,
                        message=(
                            f"{kind} '{field_id}' does not exist on source table '{source_id}' "
                            f"(available fields: {available})"
                        ),
                    )
                )

        if table.filter_field is not None:
            require(table.filter_field, "filter field")

        for sort_key in table.sort_keys:
            require(sort_key.field, "sort field")

        grouping = table.grouping_configuration
        if grouping is not None:
            for field_id in grouping.group_by_fields:
                require(field_id, "group-by field")
            for aggregated in grouping.aggregated_fields:
                require(aggregated.source_field_id, "aggregated source field")
