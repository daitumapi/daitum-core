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
This module defines the ModelConfiguration class used to encapsulate
an optimization model's configuration. It supports adding and retrieving
decision variables, objectives, and constraints.

Classes:
    ModelConfiguration: A class that stores the configuration of an optimization model,
    including its decision variables, objectives, constraints, and other model parameters.
"""

from typing import Any

from daitum_model import Calculation, Parameter
from daitum_model.fields import DataField, Field
from daitum_model.tables import DataTable, Table
from typeguard import typechecked

from daitum_configuration.model_configuration.constraint import Constraint
from daitum_configuration.model_configuration.decision_variable import DecisionVariable, DVType
from daitum_configuration.model_configuration.external_configuration import (
    ExternalModelConfiguration,
)
from daitum_configuration.model_configuration.objective import Objective
from daitum_configuration.model_configuration.priority import Priority
from daitum_configuration.model_configuration.scenario_output import ScenarioOutput
from daitum_configuration.model_configuration.stochastic_configuration import (
    StochasticConfiguration,
)


# pylint: disable=too-many-arguments,too-many-positional-arguments,too-many-instance-attributes
# pylint: disable=too-many-branches,too-few-public-methods
@typechecked
class ModelConfiguration:
    """
    Represents the configuration of an optimization model, containing
    decision variables, objectives, constraints, and various model settings.

    The following attributes may be added in the future:

        - usingCustomEvaluator: Flag for custom evaluation functions
        - usingCustomEvaluatorValidation: Flag for custom validation
        - customEvaluatorVersion: Version identifier for evaluator
        - customEvaluatorKey: Authentication key for evaluator
        - externalConfiguration: External config reference
    """

    def __init__(self):
        """Initialises a ModelConfiguration."""
        self._decision_variables: list[DecisionVariable] = []
        self._objectives: list[dict[str, Any]] = []
        self._constraints: list[Constraint] = []
        self._scenario_outputs: list[dict[str, Any]] = []

        self._using_custom_evaluator: bool | None = None
        self._custom_evaluator_version: str | None = None
        self._custom_evaluator_key: str | None = None
        self._external_configuration: ExternalModelConfiguration | None = None

        self._disable_seed_solution: bool = False
        self._calculated_seed: bool = False
        self._validation_enabled: bool = True
        self._profiling: bool = False
        self._hide_objective_when_infeasible: bool = False
        self._stochastic_configuration: StochasticConfiguration | None = None

    def set_disable_seed_solution(self, disable_seed_solution: bool) -> "ModelConfiguration":
        """Sets whether the seed solution is disabled."""
        self._disable_seed_solution = disable_seed_solution
        return self

    def set_calculated_seed(self, calculated_seed: bool) -> "ModelConfiguration":
        """Sets whether seed calculation is enabled."""
        self._calculated_seed = calculated_seed
        return self

    def set_validation_enabled(self, validation_enabled: bool) -> "ModelConfiguration":
        """Sets whether model validation is enabled."""
        self._validation_enabled = validation_enabled
        return self

    def set_profiling(self, profiling: bool) -> "ModelConfiguration":
        """Sets whether performance profiling is enabled."""
        self._profiling = profiling
        return self

    def set_hide_objective_when_infeasible(
        self, hide_objective_when_infeasible: bool
    ) -> "ModelConfiguration":
        """Sets whether objectives are hidden when the solution is infeasible."""
        self._hide_objective_when_infeasible = hide_objective_when_infeasible
        return self

    def set_stochastic_configuration(
        self, stochastic_configuration: StochasticConfiguration
    ) -> "ModelConfiguration":
        """Sets the stochastic configuration."""
        self._stochastic_configuration = stochastic_configuration
        return self

    def set_external_configuration(
        self,
        custom_evaluator_version: str,
        custom_evaluator_key: str,
        external_configuration: ExternalModelConfiguration,
    ):
        """
        Configure the model’s external evaluation settings and mappings.

        Args:
            custom_evaluator_version (str): Version identifier of the custom evaluator.
            custom_evaluator_key (str): Unique key associated with the evaluator instance.
            external_configuration (ExternalModelConfiguration): External model configuration
                defining data, parameter, and output mappings.
        """
        self._using_custom_evaluator = True
        self._custom_evaluator_version = custom_evaluator_version
        self._custom_evaluator_key = custom_evaluator_key
        self._external_configuration = external_configuration

    def add_decision_variable(
        self,
        dv: Parameter | Field,
        dv_table: Table | None = None,
        dv_type: DVType = DVType.RANGE,
    ) -> DecisionVariable:
        """
        Adds a decision variable to the model configuration.

        Args:
            dv (Parameter | Field): Primary value or reference.
            dv_table (Optional[Table]): Associated table, if field-based.
            dv_type (DVType): Type of the decision variable (range, list, real).

        Returns:
            DecisionVariable: The created decision variable for further configuration
                via its builder methods (e.g. ``set_min``, ``set_max``, ``set_scale``).

        Notes:
            - Only ``Parameter`` and ``DataField`` are allowed for ``dv``.
            - Only ``DataTable`` is allowed for ``dv_table``.
        """

        if not isinstance(dv, Parameter | DataField):
            raise ValueError(f"{dv} is not a Parameter or DataField")

        if not isinstance(dv_table, DataTable) and dv_table is not None:
            raise ValueError(f"{dv_table} is not a DataTable or None")

        dv_instance = DecisionVariable(dv, dv_table, dv_type)
        self._decision_variables.append(dv_instance)
        return dv_instance

    def add_objective(
        self,
        objective: Calculation | Parameter,
        maximise: bool = False,
        priority: Priority = Priority.HIGH,
        weight: float = 1.0,
        name: str | None = None,
    ):
        """
        Adds an objective to the model configuration.

        Args:
            objective (Calculation): A `Calculation` object representing the optimization target.
            maximise (bool): Whether the objective should be maximised. Defaults to False.
            priority (Priority): The priority level of the objective. Defaults to Priority.HIGH.
            weight (float): The relative importance (weight) of the objective. Defaults to 1.0.
            name (Optional[str]): An human-readable name for the objective. Defaults to None.

        Notes:
            - Only `Calculation` is allowed for `objective`. This is hardcoded due to pipeline
              test constraints.
        """

        if not isinstance(objective, Calculation):
            raise ValueError("Objective must be an instance of Calculation.")

        objective_instance = Objective(objective, maximise, priority, weight, name)
        self._objectives.append(objective_instance.to_dict())

    def add_constraint(self, constraint: Calculation | Parameter) -> Constraint:
        """
        Adds a constraint to the model configuration.

        Args:
            constraint (Calculation): A ``Calculation`` representing the constraint target.

        Returns:
            Constraint: The created constraint for further configuration via its builder
                methods (e.g. ``set_type``, ``set_lower_bound``, ``set_upper_bound``).

        Notes:
            - Only ``Calculation`` is allowed for ``constraint``.
        """

        if not isinstance(constraint, Calculation):
            raise ValueError("Constraint must be an instance of Calculation.")

        constraint_instance = Constraint(constraint)
        self._constraints.append(constraint_instance)
        return constraint_instance

    def add_scenario_output(
        self,
        name: str,
        scenario_output_value: Calculation | Parameter | Field,
        scenario_output_table: Table | None = None,
    ):
        """
        Sets the scenario output for the model.

        Args:
            name str: A human-readable name for the output reference.
            scenario_output_value (Calculation | Parameter | Field): The value
                defining the scenario output.
            scenario_output_table (Optional[Table]): The table the output is
                associated with, if applicable.

        Raises:
            ValueError: If a scenario output with the same name or value ID already exists.
        """

        scenario_output = ScenarioOutput(
            name,
            scenario_output_value,
            scenario_output_table,
        )

        serialised = scenario_output.to_dict()
        cell_reference = serialised["cellReference"]

        # Check for duplicates before adding
        for existing in self._scenario_outputs:
            if existing["name"] == name:
                raise ValueError(f"Scenario output with name '{name}' already exists.")
            if existing["cellReference"] == cell_reference:
                raise ValueError(
                    f"Scenario output with cell reference '{cell_reference}' already exists."
                )

        self._scenario_outputs.append(serialised)

    def to_dict(self) -> dict[str, Any]:
        """
        Returns the full configuration of the model.

        Returns:
            dict: A dictionary containing the model configuration with:

                - decisionVariables: List of decision variables
                - objectives: List of objectives
                - constraints: List of constraints
                - scenarioOutputs: List of scenario outputs
                - disableSeedSolution: Seed solution disabled flag
                - calculatedSeed: Seed calculation enabled flag
                - validationEnabled: Validation enabled flag
                - profiling: Profiling enabled flag
                - stochasticConfiguration: List of stochastic configurations
                - hideObjectiveWhenInfeasible: Hide objective when infeasible flag
        """
        return {
            "decisionVariables": [dv.to_dict() for dv in self._decision_variables],
            "objectives": self._objectives,
            "constraints": [c.to_dict() for c in self._constraints],
            "scenarioOutputs": self._scenario_outputs,
            "disableSeedSolution": self._disable_seed_solution,
            "calculatedSeed": self._calculated_seed,
            "validationEnabled": self._validation_enabled,
            "profiling": self._profiling,
            "stochasticConfiguration": (
                self._stochastic_configuration.to_dict() if self._stochastic_configuration else None
            ),
            "hideObjectiveWhenInfeasible": self._hide_objective_when_infeasible,
            "externalConfiguration": (
                self._external_configuration.build() if self._external_configuration else None
            ),
            "usingCustomEvaluator": self._using_custom_evaluator,
            "customEvaluatorVersion": self._custom_evaluator_version,
            "customEvaluatorKey": self._custom_evaluator_key,
        }
