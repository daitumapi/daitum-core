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
Module for managing a data model consisting of calculations, parameters, and tables.

This module defines the `ModelBuilder` class, which provides methods to create and manage various
 types of tables, including data tables, derived tables, joined tables, and union tables. The model
  also supports adding calculations and parameters that can be referenced across the tables.

Key Classes:
    - `ModelBuilder`: A class responsible for building and managing the data model, including adding
        tables, calculations, and parameters.
    - `Calculation`: Represents a calculation with an associated formula.
    - `Parameter`: Represents a parameter with a specified data type and value.
    - `Table` and its subclasses (`DataTable`, `DerivedTable`, `JoinedTable`, `UnionTable`):
        Represent various types of tables in the model.
    - `Field`: Represents a column of values in a table
        data aggregation.
    - `Formula`: Represents a formula used in a calculation.

This module also includes utility methods for serialising the model to JSON and writing it to a
 file for persistence.

Usage Example:
    model = ModelBuilder()
    data_table = model.add_data_table("my_table", id_field="id", key_column="key")
    data_table.add_data_field("id", DataType.INTEGER)
    data_table.add_data_field("key", DataType.STRING)
    model.add_calculation("calc1", CONST(0))
    model.write_to_file("model.json", "named_values.json")
"""

import json
import os
from typing import Any, cast

from typeguard import typechecked

from ._helpers import replace_field, replace_named_value
from .data_types import MapDataType, ObjectDataType
from .enums import SEVERITY_RANK, DataType
from .fields import CalculatedField, Field
from .formula import CONST, Formula, Operand
from .named_values import Calculation, Parameter
from .tables import (
    DataTable,
    DerivedTable,
    JoinCondition,
    JoinedTable,
    Table,
    UnionSource,
    UnionTable,
)


@typechecked
class ModelBuilder:
    """
    Represents a model that contains a collection of calculations, parameters, and tables.

    The ModelBuilder class provides methods to add calculations, parameters, and various types of
    tables to a model, as well as to serialise the model to JSON. It manages the relationships
    between these entities and ensures that there are no duplicates in the model.
    """

    def __init__(self):
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
        Adds a calculation to the model.

        Args:
            id (str): The unique identifier for the calculation.
            formula (Formula): The formula to be used for the calculation.
            model_level (bool): A flag indicating whether the calculation is at the model level.

        Returns:
            Calculation: The newly added calculation.

        Raises:
            ValueError: If a calculation or parameter with the same id already exists.
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
        data_type: DataType | ObjectDataType | MapDataType,
        value: Any,
        model_level: bool = False,
        tracking_group: str | None = None,
    ) -> Parameter:
        """
        Adds a parameter to the model.

        Args:
            id (str): The unique identifier for the parameter.
            data_type (DataType | ObjectDataType | MapDataType): The data type of the parameter.
            value (Any): The value of the parameter.
            model_level (bool): A flag indicating whether the parameter is at the model level.

        Returns:
            Parameter: The newly added parameter.
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
        Adds a Data Table to the model.

        Args:
            id (str): The unique identifier for the data table.

        Returns:
            DataTable: The newly added data table.
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
        Adds a Derived Table to the model based on an existing source table.

        Args:
            id (str): The unique identifier for the derived table.
            source_table (Table): The source table from which the derived table is created.
            group_by (list[Field], optional): Fields to group by.
            filter_field (Field, optional): A BOOLEAN field to filter rows by.

        Returns:
            DerivedTable: The newly added derived table.
        """
        table = source_table.create_derived_table(id, group_by=group_by, filter_field=filter_field)
        self._add_table(table)
        return table

    def add_joined_table(self, id: str, join_conditions: list[JoinCondition]) -> JoinedTable:
        """
        Adds a Joined Table to the model.

        Args:
            id (str): The unique identifier for the joined table.
            join_conditions (list[JoinCondition]): The conditions for joining tables.

        Returns:
            JoinedTable: The newly added joined table.
        """
        table = JoinedTable(id, join_conditions)
        self._add_table(table)
        return table

    def add_union_table(self, id: str, source_tables: list[Table | UnionSource]) -> UnionTable:
        """
        Adds a Union Table to the model.

        Args:
            id (str): The unique identifier for the union table.
            source_tables (list[Table]): The source tables to be included in the union.

        Returns:
            UnionTable: The newly added union table.
        """
        table = UnionTable(id, source_tables)
        self._add_table(table)
        return table

    def set_partial_evaluation_allowed(self, partial_evaluation_allowed: bool = True):
        """
        Specifies whether partial evaluation of the model is allowed. When set to True, can speed
        up UI rendering by only evaluating necessary changes.
        """
        self._partial_evaluation_allowed = partial_evaluation_allowed

    def set_data_validation_rule(self, named_value: Parameter | Calculation):
        """
        Sets a data validation rule that determines whether optimisation can proceed.

        The rule is defined by a named value (either a Parameter or Calculation).
        If the value evaluates to True, optimisation is allowed to run. If False,
        optimisation is blocked. In cases where optimisation is blocked and a validation
        screen has been specified in the UI definition, the user will automatically
        be redirected to the validation screen when attempting to start optimisation.

        Args:
            named_value (Parameter | Calculation): The named value used for validation.

        Raises:
            ValueError: If the provided named value is not of boolean data type.
        """
        if named_value.to_data_type() != DataType.BOOLEAN:
            raise ValueError(f"Invalid data validation rule with type {named_value.to_data_type()}")
        self._validation_named_val = named_value

    def get_tables(self) -> list[Table]:
        """
        Retrieves all tables in the model.

        Returns:
            list[Table]: A list of all tables in the model.
        """
        return self._tables

    def get_table(self, id: str) -> Table:
        """
        Retrieves a specific table by its table ID.

        Args:
            id (str): The unique identifier for the table.

        Returns:
            Table: The table with the specified ID.

        Raises:
            ValueError: If the table does not exist in the model.
        """
        if not any(table.id == id for table in self._tables):
            raise ValueError(f"The table {id} does not exist in the model")
        return next(table for table in self._tables if table.id == id)

    def get_named_value(self, id: str) -> Parameter | Calculation:
        """
        Retrieves a named value (either a parameter or calculation) by its ID.

        Args:
            id (str): The unique identifier for the named value.

        Returns:
            Parameter | Calculation: The named value with the specified ID.

        Raises:
            ValueError: If the named value does not exist in the model.
        """
        if any(parameter.id == id for parameter in self._parameters):
            return next(parameter for parameter in self._parameters if parameter.id == id)
        if any(calculation.id == id for calculation in self._calculations):
            return next(calculation for calculation in self._calculations if calculation.id == id)
        raise ValueError(f"The named value {id} does not exist in the model")

    def get_validation_state(self) -> Calculation | Parameter:
        """
        Build a formula-based calculation representing the maximum severity rank
        among all currently-invalid fields, parameters, and calculations.

        For each entity with validators, the corresponding ``__invalid__`` formula
        is inspected at runtime: only entities whose ``__invalid__`` formula evaluates
        to ``True`` contribute to the result.  The returned calculation evaluates to
        the highest ``SEVERITY_RANK`` value among those failing entities, or ``0``
        when nothing is invalid.

        The result is registered in the model as a calculation named
        ``__validation_state__``.  Subsequent calls return the already-registered
        calculation without rebuilding it.

        Returns:
            Calculation: A model-level calculation whose integer value is the
            highest severity rank of any currently-invalid entity.
        """
        from daitum_model import formulas  # pylint: disable=import-outside-toplevel

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
        Adds a table to the model.

        Args:
            table (Table): The table to be added.

        Raises:
            ValueError: If a table with the same id already exists in the model.
        """
        if any(_table.id == table.id for _table in self._tables):
            raise ValueError(f"A table with id {table.id} already exists in the model")
        self._tables.append(table)

    def write_to_file(
        self, file_name: str, scenario_named_value_path: str, model_named_value_path: str
    ):
        """
        Serialises the model and writes it to two separate JSON files.

        Args:
            file_name (str): The path to the file where the model will be saved.
            named_value_path (str): The path to the file where named values will be saved.
        """
        directory = os.path.dirname(file_name)
        if directory and not os.path.exists(directory):
            os.makedirs(directory)
        with open(file_name, "w", encoding="utf-8") as fp:
            json.dump(self.build(), fp, indent=2, sort_keys=True)
        directory = os.path.dirname(scenario_named_value_path)
        if directory and not os.path.exists(directory):
            os.makedirs(directory)
        with open(scenario_named_value_path, "w", encoding="utf-8") as fp:
            json.dump(self.to_named_value_dict(False), fp, indent=2, sort_keys=True)
        directory = os.path.dirname(model_named_value_path)
        if directory and not os.path.exists(directory):
            os.makedirs(directory)
        with open(model_named_value_path, "w", encoding="utf-8") as fp:
            json.dump(self.to_named_value_dict(True), fp, indent=2, sort_keys=True)

    def build(self) -> dict[str, Any]:
        """
        Converts the `Model` object to a dictionary representation for JSON serialisation.

        Returns:
            dict[str, Any]: A dictionary representation of the model.
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
        Converts the `Model` object to a dictionary representation for named values.

        Returns:
            dict[str, Any]: A dictionary representation of the model.
        """
        return {
            "values": {
                param.id: param.to_named_value_dict()
                for param in self._parameters
                if (param.model_level == model_level)
            }
        }
