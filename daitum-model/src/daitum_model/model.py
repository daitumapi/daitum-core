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
Top-level :class:`ModelBuilder` for assembling a Daitum model definition.

A model is composed of tables (data, derived, joined, union) and named values
(:class:`~daitum_model.Calculation` and :class:`~daitum_model.Parameter`).
:meth:`ModelBuilder.write_to_file` serialises the model into the canonical
JSON layout consumed by the Daitum platform.
"""

import json
import os
import pathlib
from typing import Any, cast

from typeguard import typechecked

from ._helpers import replace_field, replace_named_value
from .data_types import BaseDataType, DataType
from .derived_table import DerivedTable
from .fields import CalculatedField, Field
from .formula import CONST, Formula, Operand
from .joined_table import JoinCondition, JoinedTable
from .named_values import Calculation, Parameter
from .tables import DataTable, Table
from .union_table import UnionSource, UnionTable


@typechecked
class ModelBuilder:
    """
    Top-level entry point for building a Daitum model.

    A model holds tables and named values (calculations and parameters). Build
    one incrementally with the ``add_*`` factory methods, then call
    :meth:`write_to_file` to emit the JSON output.
    """

    def __init__(self):
        """Initialise an empty model with no tables, calculations, or parameters."""
        self._calculations: list[Calculation] = list[Calculation]()
        self._parameters: list[Parameter] = list[Parameter]()
        self._tables: list[Table] = list[Table]()

        self._validation_named_val: Parameter | Calculation | None = None
        self._partial_evaluation_allowed: bool = True

        self._have_converted_tracked_fields: bool = False

    def add_calculation(
        self,
        id: str,
        formula: Operand | float | int | bool | str,
        model_level: bool = False,
        tracking_group: str | None = None,
    ) -> Calculation:
        """
        Add a :class:`~daitum_model.Calculation` to the model.

        Args:
            id: Unique identifier for the calculation. Must not collide with any
                existing calculation or parameter id.
            formula: The expression. A :class:`~daitum_model.Formula` or any value
                accepted by :func:`~daitum_model.formula.CONST` (number, bool, or
                string), which is wrapped automatically.
            model_level: If ``True``, the calculation is evaluated once for the
                whole model. If ``False`` (the default) it is scenario-level.
            tracking_group: Optional change-tracking group. When set, a sibling
                ``*_TRACKING_*`` calculation is generated with references to
                other tracked named values and fields rewritten to their
                tracking ids.

        Returns:
            The newly added :class:`~daitum_model.Calculation`.

        Raises:
            ValueError: If a calculation or parameter with the same ``id``
                already exists in the model.
        """
        if not isinstance(formula, Formula):
            return self.add_calculation(id, CONST(formula), model_level, tracking_group)
        if any(calculation.id == id for calculation in self._calculations) or any(
            parameter.id == id for parameter in self._parameters
        ):
            raise ValueError(f"A named value with id {id} already exists in the model")
        calc = Calculation(id, formula, model_level=model_level, model=self)
        if tracking_group is not None:
            calc.set_tracking_group(tracking_group)
        self._calculations.append(calc)

        if tracking_group is not None:
            tracking_formula = calc.formula.formula_string

            tracked_named_values = [
                named_value
                for named_value in (self._parameters or []) + (self._calculations or [])
                if named_value.tracking_group is not None
                and named_value.tracking_group == tracking_group
            ]

            for named_value in tracked_named_values:
                tracking_formula = replace_named_value(
                    tracking_formula,
                    named_value.id,
                    named_value.tracking_id,
                )

            tracked_fields = [
                field
                for table in self._tables or []
                for field in table.get_fields()
                if field.tracking_group is not None and field.tracking_group == tracking_group
            ]

            for field in tracked_fields:
                tracking_formula = replace_field(
                    tracking_formula,
                    field.id,
                    field.tracking_id,
                )

            self.add_calculation(
                calc.tracking_id,
                formula=Formula(calc.formula.data_type, tracking_formula),
                model_level=calc.model_level,
            )

        return calc

    def add_parameter(
        self,
        id: str,
        data_type: BaseDataType,
        value: Any,
        model_level: bool = False,
        tracking_group: str | None = None,
    ) -> Parameter:
        """
        Add a :class:`~daitum_model.Parameter` to the model.

        Args:
            id: Unique identifier for the parameter.
            data_type: Data type of the parameter — a :class:`~daitum_model.DataType`,
                :class:`~daitum_model.ObjectDataType`, or :class:`~daitum_model.MapDataType`.
            value: Initial value. Must be compatible with ``data_type``.
            model_level: If ``True``, the parameter is shared across all
                scenarios. If ``False`` (the default) it is scenario-level.
            tracking_group: Optional change-tracking group. When set, a sibling
                ``*_TRACKING_*`` parameter is generated with the same value.

        Returns:
            The newly added :class:`~daitum_model.Parameter`.
        """
        param = Parameter(id, data_type, value, model_level)
        if tracking_group is not None:
            param.set_tracking_group(tracking_group)
        param.set_model(self)
        self._parameters.append(param)

        if tracking_group is not None:
            self.add_parameter(param.tracking_id, data_type, value, model_level)

        return param

    def add_data_table(self, id: str) -> DataTable:
        """
        Add a :class:`~daitum_model.tables.DataTable` to the model.

        A data table holds raw imported rows and is the only table type that
        supports decision variables.

        Args:
            id: Unique identifier for the table. Must not collide with any
                existing table id.

        Returns:
            The newly added :class:`~daitum_model.tables.DataTable`. Use its
            ``add_data_field`` / ``add_calculated_field`` / ``set_key_column``
            methods to populate it.

        Raises:
            ValueError: If a table with the same ``id`` already exists.
        """
        table = DataTable(id)
        self._add_table(table)
        return table

    def add_derived_table(
        self,
        id: str,
        source_table: Table,
        group_by: list[Field] | None = None,
        filter_field: Field | None = None,
    ) -> DerivedTable:
        """
        Add a :class:`~daitum_model.derived_table.DerivedTable` to the model.

        A derived table is a grouped, filtered, and/or sorted view of an
        existing source table.

        Args:
            id: Unique identifier for the derived table.
            source_table: The table whose rows the derived table draws from.
            group_by: Optional fields to group rows by. When supplied,
                non-group fields must be added with an
                :class:`~daitum_model.AggregationMethod`.
            filter_field: Optional ``BOOLEAN`` field on ``source_table``;
                only rows where it is ``True`` are kept.

        Returns:
            The newly added :class:`~daitum_model.derived_table.DerivedTable`.

        Raises:
            ValueError: If a table with the same ``id`` already exists.
        """
        table = DerivedTable(id, source_table, group_by=group_by, filter_field=filter_field)
        self._add_table(table)
        return table

    def add_joined_table(self, id: str, join_conditions: list[JoinCondition]) -> JoinedTable:
        """
        Add a :class:`~daitum_model.joined_table.JoinedTable` to the model.

        A joined table is the result of joining two or more tables on a list
        of :class:`~daitum_model.joined_table.JoinCondition` rows.

        Args:
            id: Unique identifier for the joined table.
            join_conditions: One condition per joined table pairing. The
                :class:`~daitum_model.JoinType` of each condition controls how
                unmatched rows are handled.

        Returns:
            The newly added :class:`~daitum_model.joined_table.JoinedTable`.

        Raises:
            ValueError: If a table with the same ``id`` already exists.
        """
        table = JoinedTable(id, join_conditions)
        self._add_table(table)
        return table

    def add_union_table(self, id: str, source_tables: list[Table | UnionSource]) -> UnionTable:
        """
        Add a :class:`~daitum_model.union_table.UnionTable` to the model.

        A union table stacks rows from multiple source tables. Pass a
        :class:`~daitum_model.union_table.UnionSource` instead of a bare
        :class:`~daitum_model.Table` when the source schema does not line up
        with the union table's fields.

        Args:
            id: Unique identifier for the union table.
            source_tables: The tables (or wrapped ``UnionSource`` instances)
                whose rows are stacked.

        Returns:
            The newly added :class:`~daitum_model.union_table.UnionTable`.

        Raises:
            ValueError: If a table with the same ``id`` already exists.
        """
        table = UnionTable(id, source_tables)
        self._add_table(table)
        return table

    def set_partial_evaluation_allowed(self, partial_evaluation_allowed: bool = True):
        """
        Toggle partial evaluation for this model.

        When enabled (the default), the platform re-evaluates only the
        calculations affected by a change rather than the whole model, which
        speeds up UI rendering. Disable only if a model has dependencies that
        the partial evaluator cannot track correctly.

        Args:
            partial_evaluation_allowed: ``True`` to allow partial evaluation.
        """
        self._partial_evaluation_allowed = partial_evaluation_allowed

    def set_data_validation_rule(self, named_value: Parameter | Calculation):
        """
        Gate optimisation on a boolean named value.

        Optimisation is allowed only while ``named_value`` evaluates to
        ``True``. When it is ``False`` and the UI definition specifies a
        validation screen, the user is redirected there on attempting to start
        optimisation.

        Args:
            named_value: A :class:`~daitum_model.Parameter` or
                :class:`~daitum_model.Calculation` of type
                :attr:`~daitum_model.DataType.BOOLEAN`.

        Raises:
            ValueError: If ``named_value`` is not of boolean data type.
        """
        if named_value.to_data_type() != DataType.BOOLEAN:
            raise ValueError(f"Invalid data validation rule with type {named_value.to_data_type()}")
        self._validation_named_val = named_value

    def get_tables(self) -> list[Table]:
        """
        Return every table that has been added to the model, in insertion order.
        """
        return self._tables

    def get_table(self, id: str) -> Table:
        """
        Return the table with the given id.

        Args:
            id: Identifier of the table to look up.

        Returns:
            The matching :class:`~daitum_model.Table`.

        Raises:
            ValueError: If no table with that id exists in the model.
        """
        if not any(table.id == id for table in self._tables):
            raise ValueError(f"The table {id} does not exist in the model")
        return next(table for table in self._tables if table.id == id)

    def get_named_value(self, id: str) -> Parameter | Calculation:
        """
        Return the named value (parameter or calculation) with the given id.

        Args:
            id: Identifier of the named value to look up.

        Returns:
            The matching :class:`~daitum_model.Parameter` or
            :class:`~daitum_model.Calculation`. Parameters are searched first,
            so a parameter is returned if both exist with the same id (which
            ``add_parameter`` / ``add_calculation`` would normally prevent).

        Raises:
            ValueError: If no named value with that id exists in the model.
        """
        if any(parameter.id == id for parameter in self._parameters):
            return next(parameter for parameter in self._parameters if parameter.id == id)
        if any(calculation.id == id for calculation in self._calculations):
            return next(calculation for calculation in self._calculations if calculation.id == id)
        raise ValueError(f"The named value {id} does not exist in the model")

    def get_validation_state(self) -> Calculation | Parameter:
        """
        Return (and lazily build) a calculation summarising current validity.

        The calculation evaluates to the highest
        :data:`~daitum_model.validator.SEVERITY_RANK` among every field, parameter,
        and calculation whose ``__invalid__`` formula is currently ``True``, or
        ``0`` when nothing is invalid. Useful as the gating value for
        :meth:`set_data_validation_rule`.

        The result is registered in the model under the id
        ``__validation_state__``. Subsequent calls return the already-registered
        calculation without rebuilding it, so call this only after every
        validator has been attached.

        Returns:
            A model-level :class:`~daitum_model.Calculation` whose integer
            value is the highest severity rank of any currently-invalid entity.
        """
        from daitum_model import formulas  # pylint: disable=import-outside-toplevel

        from .validator import SEVERITY_RANK  # pylint: disable=import-outside-toplevel

        if "__validation_state__" in [cal.id for cal in self._calculations]:
            return self.get_named_value("__validation_state__")

        # Collect invalid fields' severity rank
        field_severity = []
        named_values = self._parameters + self._calculations
        for named_value in named_values:
            for validator in named_value._validators:  # pylint: disable=protected-access
                invalid_value = self.get_named_value(
                    f"{named_value.id}__invalid__{validator.severity.value}"
                )
                field_severity.append(
                    formulas.IF(invalid_value, SEVERITY_RANK[validator.severity], 0)
                )

        # Use table[column] to get a BOOLEAN_ARRAY, then COUNT(array, True) > 0
        # to produce a scalar boolean indicating whether any row is invalid
        for table in self._tables:
            for field in table.get_fields():
                for validator in field._validators:  # pylint: disable=protected-access
                    invalid_field_name = f"{field.id}__invalid__{validator.severity.value}"
                    bool_formula = table[invalid_field_name]  # BOOLEAN_ARRAY
                    any_invalid = formulas.OR(bool_formula)
                    field_severity.append(
                        formulas.IF(any_invalid, SEVERITY_RANK[validator.severity], 0)
                    )

        if not field_severity:
            return self.add_calculation("__validation_state__", 0, model_level=True)

        return self.add_calculation(
            "__validation_state__", formulas.MAX(*field_severity), model_level=True
        )

    def _add_table(self, table: Table):
        """
        Append ``table`` to the model after checking its id is unique.

        Raises:
            ValueError: If a table with the same id already exists.
        """
        if any(_table.id == table.id for _table in self._tables):
            raise ValueError(f"A table with id {table.id} already exists in the model")
        self._tables.append(table)

    def write_to_file(self, model_directory: str | os.PathLike[str]) -> None:
        """
        Serialise the model into the canonical Daitum directory layout.

        Writes three files under ``model_directory``, creating it if it does
        not exist:

        - ``model-definition.json`` — the full model definition from :meth:`build`.
        - ``scenarios/Initial/named-values.json`` — scenario-level named values
          (those added with ``model_level=False``).
        - ``model-data/named-values.json`` — model-level named values
          (those added with ``model_level=True``).

        Args:
            model_directory: Destination directory. Parents are created as needed.
        """
        root = pathlib.Path(model_directory)
        targets = [
            (root / "model-definition.json", self.build()),
            (root / "scenarios/Initial/named-values.json", self.to_named_value_dict(False)),
            (root / "model-data/named-values.json", self.to_named_value_dict(True)),
        ]
        for path, payload in targets:
            path.parent.mkdir(parents=True, exist_ok=True)
            with path.open("w", encoding="utf-8") as fp:
                json.dump(payload, fp, indent=2, sort_keys=True)

    def build(self) -> dict[str, Any]:
        """
        Build the JSON-compatible dict representation of the model.

        On the first call, change-tracking metadata is resolved: tracked
        calculated fields have their formulas rewritten to reference the
        ``*_TRACKING_*`` ids of any other tracked named values and fields.
        This step is idempotent and only runs once per builder.

        Returns:
            A dict suitable for ``json.dump`` containing
            ``calculationDefinitions``, ``parameterDefinitions``,
            ``tableDefinitions``, ``optimisationCheckNamedValue``, and
            ``partialEvaluationAllowed`` keys.
        """

        if not self._have_converted_tracked_fields:
            tracked_named_values = [
                named_value
                for named_value in (self._parameters or []) + (self._calculations or [])
                if named_value.tracking_group is not None
            ]
            tracked_fields = []
            for table in self._tables:
                for field in table.get_fields():
                    if field.tracking_group is not None:
                        tracked_fields.append(field)
            if len(tracked_fields) != 0:
                for table in self._tables:
                    for field in table.get_fields():
                        if field.tracking_group is None:
                            continue
                        if not isinstance(field, CalculatedField):
                            continue

                        tracking_group = field.tracking_group
                        tracked_field = table.get_field(field.tracking_id)
                        assert isinstance(tracked_field, CalculatedField)
                        tracked_field = cast(CalculatedField, tracked_field)

                        tracking_formula = tracked_field.formula.formula_string

                        named_values_to_replace = [
                            named_value
                            for named_value in tracked_named_values
                            if named_value.tracking_group == tracking_group
                        ]

                        for named_value in named_values_to_replace:
                            tracking_formula = replace_named_value(
                                tracking_formula,
                                named_value.id,
                                named_value.tracking_id,
                            )

                        fields_to_replace = [
                            field_to_replace
                            for field_to_replace in tracked_fields
                            if field_to_replace.tracking_group == tracking_group
                        ]

                        for field_to_replace in fields_to_replace:
                            tracking_formula = replace_field(
                                tracking_formula,
                                field_to_replace.id,
                                field_to_replace.tracking_id,
                            )

                        tracked_field.formula = Formula(tracked_field.data_type, tracking_formula)

            self._have_converted_tracked_fields = True

        return {
            "calculationDefinitions": {calc.id: calc.build() for calc in self._calculations},
            "parameterDefinitions": {param.id: param.build() for param in self._parameters},
            "tableDefinitions": {table.id: table.build() for table in self._tables},
            "optimisationCheckNamedValue": (
                self._validation_named_val.id if self._validation_named_val else None
            ),
            "partialEvaluationAllowed": self._partial_evaluation_allowed,
        }

    def to_named_value_dict(self, model_level: bool) -> dict[str, Any]:
        """
        Build the JSON-compatible dict of parameter values for one scope.

        Args:
            model_level: When ``True``, include only model-level parameters
                (written to ``model-data/named-values.json``). When ``False``,
                include only scenario-level parameters (written to
                ``scenarios/Initial/named-values.json``).

        Returns:
            ``{"values": {parameter_id: value_dict, ...}}``.
        """
        return {
            "values": {
                param.id: param.to_named_value_dict()
                for param in self._parameters
                if (param.model_level == model_level)
            }
        }
