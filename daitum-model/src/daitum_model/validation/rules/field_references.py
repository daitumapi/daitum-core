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

"""Rule: every field/named-value/table referenced by a formula must exist in the model."""

from __future__ import annotations

from daitum_model.fields import CalculatedField, ComboField, Field
from daitum_model.named_values import Calculation, Parameter
from daitum_model.tables import Table
from daitum_model.validation.engine import rule
from daitum_model.validation.errors import FieldReferenceError, TableReferenceError
from daitum_model.validation.graph import ModelGraph
from daitum_model.validation.report import ValidationReport


@rule
class AllFieldReferencesExist:
    """Every reference leaf used by a formula must resolve in the assembled model.

    Walks the formula dependencies of every calculated field, combo field, and calculation.
    A referenced ``Field`` must still exist on its owning table; a referenced
    ``Calculation`` / ``Parameter`` / ``Table`` must still be registered. This catches
    formulas that referenced something later removed or never added — the platform would
    otherwise reject the model only on upload.
    """

    id = "all-field-references-exist"

    def check(self, graph: ModelGraph, report: ValidationReport) -> None:
        for table in graph.tables.values():
            for field in table.field_definitions.values():
                if isinstance(field, (CalculatedField, ComboField)):
                    self._check_object(
                        field, f"table '{table.id}'.field '{field.id}'", graph, report
                    )

        for named_value in graph.named_values.values():
            if isinstance(named_value, Calculation):
                self._check_object(named_value, f"calculation '{named_value.id}'", graph, report)

    def _check_object(
        self,
        obj: CalculatedField | ComboField | Calculation,
        location: str,
        graph: ModelGraph,
        report: ValidationReport,
    ) -> None:
        for leaf in graph.formula_dependencies(obj):
            self._check_leaf(leaf, location, graph, report)

    def _check_leaf(
        self, leaf: object, location: str, graph: ModelGraph, report: ValidationReport
    ) -> None:
        if isinstance(leaf, Field):
            owning_table = leaf.table.id
            if owning_table not in graph.tables:
                report.add(
                    TableReferenceError(
                        rule_id=self.id,
                        location=location,
                        message=(
                            f"references field '{leaf.id}' on table '{owning_table}', "
                            "which is not in the model"
                        ),
                    )
                )
            elif not graph.has_field(owning_table, leaf.id):
                available = ", ".join(graph.available_fields(owning_table)) or "<none>"
                report.add(
                    FieldReferenceError(
                        rule_id=self.id,
                        location=location,
                        message=(
                            f"references field '{leaf.id}', which does not exist in table "
                            f"'{owning_table}' (available fields: {available})"
                        ),
                    )
                )
        elif isinstance(leaf, (Calculation, Parameter)):
            if leaf.id not in graph.named_values:
                report.add(
                    FieldReferenceError(
                        rule_id=self.id,
                        location=location,
                        message=(f"references named value '{leaf.id}', which is not in the model"),
                    )
                )
        elif isinstance(leaf, Table):
            if leaf.id not in graph.tables:
                report.add(
                    TableReferenceError(
                        rule_id=self.id,
                        location=location,
                        message=f"references table '{leaf.id}', which is not in the model",
                    )
                )
