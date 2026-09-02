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

"""Rule: a joined table's match fields must exist on the tables being joined."""

from __future__ import annotations

from daitum_model.joined_table import JoinedTable
from daitum_model.validation.engine import rule
from daitum_model.validation.errors import MissingSourceFieldError, TableReferenceError
from daitum_model.validation.graph import ModelGraph
from daitum_model.validation.report import ValidationReport


@rule
class JoinConditionFieldsExist:
    """Each join condition's left/right match field must exist on the respective table.

    CROSS joins carry no match fields, so their ``None`` fields are skipped. Tables named by
    a condition must also be in the model.
    """

    id = "join-condition-fields-exist"

    def check(self, graph: ModelGraph, report: ValidationReport) -> None:
        for table in graph.tables.values():
            if isinstance(table, JoinedTable):
                self._check_joined(table, graph, report)

    def _check_joined(
        self, table: JoinedTable, graph: ModelGraph, report: ValidationReport
    ) -> None:
        for index, condition in enumerate(table.join_conditions):
            location = f"joined table '{table.id}'.condition[{index}]"
            self._check_side(
                condition.left_table_id, condition.left_table_field, location, graph, report
            )
            self._check_side(
                condition.right_table_id, condition.right_table_field, location, graph, report
            )

    def _check_side(
        self,
        table_id: str,
        field_id: str | None,
        location: str,
        graph: ModelGraph,
        report: ValidationReport,
    ) -> None:
        if table_id not in graph.tables:
            report.add(
                TableReferenceError(
                    rule_id=self.id,
                    location=location,
                    message=f"join table '{table_id}' is not in the model",
                )
            )
            return
        if field_id is not None and not graph.has_field(table_id, field_id):
            available = ", ".join(graph.available_fields(table_id)) or "<none>"
            report.add(
                MissingSourceFieldError(
                    rule_id=self.id,
                    location=location,
                    message=(
                        f"match field '{field_id}' does not exist on table '{table_id}' "
                        f"(available fields: {available})"
                    ),
                )
            )
