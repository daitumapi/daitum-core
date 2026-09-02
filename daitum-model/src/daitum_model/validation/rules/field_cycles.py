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

"""Rule: fields within a table must not depend on each other in a cycle.

Cross-table field cycles are not checked here — a field referencing another table's field
creates a *table* dependency, which the table-cycle rule already forbids (table cycles are
never allowed, even through combo fields). This rule covers only cycles internal to a single
table.

The one exception: a cycle is allowed when it contains a :class:`ComboField` pair with
opposite ``calculate_in_optimiser`` values (one ``True``, one ``False``). Only one side of
such a pair is ever calculated at a time — the other acts as stored data — so the loop never
resolves. Two combos with the *same* flag, or a combo paired with a plain calculated field,
do not break the cycle.
"""

from __future__ import annotations

from daitum_model.fields import ComboField, Field
from daitum_model.validation.engine import rule
from daitum_model.validation.errors import CircularDependencyError
from daitum_model.validation.graph import ModelGraph, detect_cycles, find_cycle_path
from daitum_model.validation.report import ValidationReport


@rule
class NoCircularFieldDependencies:
    """Detect cyclic dependencies among the fields of a single table."""

    id = "no-circular-field-dependencies"

    def check(self, graph: ModelGraph, report: ValidationReport) -> None:
        for table_id in graph.tables:
            edges = graph.intra_table_field_edges(table_id)
            for group in detect_cycles(edges):
                if self._broken_by_combo_pair(group, table_id, graph):
                    continue
                path = find_cycle_path(edges, group)
                report.add(
                    CircularDependencyError(
                        rule_id=self.id,
                        location=f"table '{table_id}' fields {' -> '.join(path)}",
                        message=(
                            "circular dependency between fields; "
                            "break the cycle, or make the pair combo fields with opposite "
                            "calculate_in_optimiser values"
                        ),
                    )
                )

    @staticmethod
    def _broken_by_combo_pair(group: list[str], table_id: str, graph: ModelGraph) -> bool:
        """Whether the cycle contains a combo field with each ``calculate_in_optimiser`` value.

        Such a pair always leaves one side acting as data, so the cycle never resolves.
        """
        fields = graph.fields_by_table.get(table_id, {})
        has_calc_in_optimiser = False
        has_data_in_optimiser = False
        for field_id in group:
            field: Field | None = fields.get(field_id)
            if isinstance(field, ComboField):
                if field.calculate_in_optimiser:
                    has_calc_in_optimiser = True
                else:
                    has_data_in_optimiser = True
        return has_calc_in_optimiser and has_data_in_optimiser
