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

from daitum_model.expression import ColumnAccess, MemberAccess
from daitum_model.fields import CalculatedField, ComboField, Field
from daitum_model.formula import Formula, Operand
from daitum_model.named_values import Calculation, Parameter
from daitum_model.tables import Table
from daitum_model.validation.engine import rule
from daitum_model.validation.errors import FieldReferenceError, TableReferenceError
from daitum_model.validation.graph import ModelGraph
from daitum_model.validation.report import ValidationReport


def _local_field_references(formula: Formula) -> set[Operand]:
    """The bare (unqualified ``[id]``) reference leaves a formula uses directly.

    These are leaves reached **without** passing through a column access (``table[col]``) or
    member access (``obj.field``) — i.e. the operands that render as a bare ``[id]`` and that the
    platform resolves against the formula's own table. A ``ColumnAccess``/``MemberAccess`` is an
    explicit cross-table read, so its accessed field is excluded; any bare references in a member
    access's base still count.
    """
    found: set[Operand] = set()
    if isinstance(formula, ColumnAccess):
        return found
    if isinstance(formula, MemberAccess):
        # ``obj.field``: the accessed field is foreign, but any bare references in the base
        # (``obj``) are still local. ``children()`` is exactly ``(base,)``.
        for base in formula.children():
            if isinstance(base, Formula):
                found |= _local_field_references(base)
            else:
                found.add(base)
        return found
    for child in formula.children():
        if isinstance(child, Formula):
            found |= _local_field_references(child)
        else:
            found.add(child)
    return found


@rule
class AllFieldReferencesExist:
    """Every reference leaf used by a formula must resolve in the assembled model.

    Walks the formula dependencies of every calculated field, combo field, and calculation.

    A **bare field reference** (an unqualified ``[id]`` — a ``Field`` object used directly in a
    formula, as opposed to a ``table[col]`` / ``obj.field`` access) must resolve in the formula's
    local scope:

    - On a **calculated/combo field**, a bare field reference must name a field that exists on
      the field's *own* table. It is not enough for the field to exist on the source/parent
      table — the platform resolves ``[id]`` against the hosting table only, so the field must be
      present there (copied in via ``add_source_fields``, produced by a join, or added as an
      aggregated/pivot column). This catches the common mistake of a derived table's calculated
      field referencing a group-by/source field that was never copied onto it.
    - A **calculation** has no table context, so a bare field reference in it is never valid —
      every field it reads must go through an explicit table context (``table[col]`` /
      ``obj.field``).

    Cross-table reads via ``table[col]`` (``ColumnAccess``) or ``obj.field`` (``MemberAccess``)
    are legitimate; the accessed field is still checked for existence on its owning table. A
    referenced ``Calculation`` / ``Parameter`` / ``Table`` must be registered in the model. The
    platform would otherwise reject the model only on upload.
    """

    id = "all-field-references-exist"

    def check(self, graph: ModelGraph, report: ValidationReport) -> None:
        for table in graph.tables.values():
            for field in table.field_definitions.values():
                if isinstance(field, (CalculatedField, ComboField)):
                    self._check_object(
                        field,
                        f"table '{table.id}'.field '{field.id}'",
                        table.id,
                        graph,
                        report,
                    )

        for named_value in graph.named_values.values():
            if isinstance(named_value, Calculation):
                self._check_object(
                    named_value, f"calculation '{named_value.id}'", None, graph, report
                )

    def _check_object(
        self,
        obj: CalculatedField | ComboField | Calculation,
        location: str,
        host_table_id: str | None,
        graph: ModelGraph,
        report: ValidationReport,
    ) -> None:
        # Bare field references (unqualified ``[id]``) are scoped to the formula's local context.
        local_field_ids: set[str] = set()
        for leaf in _local_field_references(obj.formula):
            if isinstance(leaf, Field):
                local_field_ids.add(leaf.id)
                self._check_local_field(leaf, location, host_table_id, graph, report)

        # Every other reference leaf must resolve where it is defined / registered. A bare field
        # already checked above is skipped so it is not reported twice.
        for leaf in graph.formula_dependencies(obj):
            if isinstance(leaf, Field) and leaf.id in local_field_ids:
                continue
            self._check_leaf(leaf, location, graph, report)

    def _check_local_field(
        self,
        leaf: Field,
        location: str,
        host_table_id: str | None,
        graph: ModelGraph,
        report: ValidationReport,
    ) -> None:
        if host_table_id is None:
            # A calculation has no table, so a bare field reference is never valid.
            report.add(
                FieldReferenceError(
                    rule_id=self.id,
                    location=location,
                    message=(
                        f"references field '{leaf.id}' directly, but a calculation has no table "
                        "context. Reference a field through a table (e.g. Table[Field])"
                    ),
                )
            )
        elif not graph.has_field(host_table_id, leaf.id):
            available = ", ".join(graph.available_fields(host_table_id)) or "<none>"
            report.add(
                FieldReferenceError(
                    rule_id=self.id,
                    location=location,
                    message=(
                        f"references field '{leaf.id}', which does not exist in table "
                        f"'{host_table_id}' (available fields: {available}). A formula may only "
                        "reference fields defined on its own table"
                    ),
                )
            )

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
