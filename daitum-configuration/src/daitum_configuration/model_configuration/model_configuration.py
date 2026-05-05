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
:class:`ModelConfiguration` — the decision variables, objectives, and constraints
of an optimisation problem, plus per-model solver flags.
"""

from typing import Any

from daitum_model import Calculation, Parameter
from daitum_model.fields import DataField, Field
from daitum_model.tables import DataTable, Table
from typeguard import typechecked

from daitum_configuration._buildable import Buildable
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
class ModelConfiguration(Buildable):
    """
    Decision variables, objectives, constraints, and solver-level flags for one model.
    """

    def __init__(self):
        self.decision_variables: list[DecisionVariable] = []
        self.objectives: list[Objective] = []
        self.constraints: list[Constraint] = []
        self.scenario_outputs: list[ScenarioOutput] = []

        self.disable_seed_solution: bool = False
        self.calculated_seed: bool = False
        self.validation_enabled: bool = True
        self.profiling: bool = False
        self.stochastic_configuration: StochasticConfiguration | None = None
        self.hide_objective_when_infeasible: bool = False
        self.external_configuration: ExternalModelConfiguration | None = None
        self.using_custom_evaluator: bool | None = None
        self.custom_evaluator_version: str | None = None
        self.custom_evaluator_key: str | None = None

    def set_disable_seed_solution(self, disable_seed_solution: bool) -> "ModelConfiguration":
        """Disable the seed solution loaded from input data."""
        self.disable_seed_solution = disable_seed_solution
        return self

    def set_calculated_seed(self, calculated_seed: bool) -> "ModelConfiguration":
        """Enable computing the seed solution from formulas instead of input data."""
        self.calculated_seed = calculated_seed
        return self

    def set_validation_enabled(self, validation_enabled: bool) -> "ModelConfiguration":
        """Enable or disable validators on the input data."""
        self.validation_enabled = validation_enabled
        return self

    def set_profiling(self, profiling: bool) -> "ModelConfiguration":
        """Enable solver-side performance profiling."""
        self.profiling = profiling
        return self

    def set_hide_objective_when_infeasible(
        self, hide_objective_when_infeasible: bool
    ) -> "ModelConfiguration":
        """Hide objective values from the UI when the solution is infeasible."""
        self.hide_objective_when_infeasible = hide_objective_when_infeasible
        return self

    def set_stochastic_configuration(
        self, stochastic_configuration: StochasticConfiguration
    ) -> "ModelConfiguration":
        """Attach a :class:`StochasticConfiguration` for multi-trial evaluation."""
        self.stochastic_configuration = stochastic_configuration
        return self

    def set_external_configuration(
        self,
        custom_evaluator_version: str,
        custom_evaluator_key: str,
        external_configuration: ExternalModelConfiguration,
    ) -> "ModelConfiguration":
        """Route evaluation through an external evaluator with the given version, key,
        and :class:`ExternalModelConfiguration` mappings."""
        self.using_custom_evaluator = True
        self.custom_evaluator_version = custom_evaluator_version
        self.custom_evaluator_key = custom_evaluator_key
        self.external_configuration = external_configuration
        return self

    def add_decision_variable(
        self,
        dv: Parameter | Field,
        dv_table: Table | None = None,
        dv_type: DVType = DVType.RANGE,
    ) -> DecisionVariable:
        """Register a decision variable.

        Args:
            dv: A model :class:`~daitum_model.Parameter` (model-level DV) or a
                :class:`~daitum_model.fields.DataField` (per-row DV).
            dv_table: The :class:`~daitum_model.tables.DataTable` for a per-row
                DV. ``None`` for a model-level DV.
            dv_type: :class:`DVType` controlling the variable's domain.

        Returns:
            The new :class:`DecisionVariable`; chain ``.set_min(...)`` and
            ``.set_max(...)`` to bound it.
        """
        if not isinstance(dv, Parameter | DataField):
            raise ValueError(f"{dv} is not a Parameter or DataField")

        if not isinstance(dv_table, DataTable) and dv_table is not None:
            raise ValueError(f"{dv_table} is not a DataTable or None")

        dv_instance = DecisionVariable(dv, dv_table, dv_type)
        self.decision_variables.append(dv_instance)
        return dv_instance

    def add_objective(
        self,
        objective: Calculation | Parameter,
        maximise: bool = False,
        priority: Priority = Priority.HIGH,
        weight: float = 1.0,
        name: str | None = None,
    ) -> Objective:
        """Register an :class:`Objective`.

        Args:
            objective: Numeric :class:`~daitum_model.Calculation` to optimise.
            maximise: Direction of optimisation. Defaults to minimise.
            priority: Lexicographic :class:`Priority` for multi-objective runs.
            weight: Objective weight when combining via a weighted comparator.
            name: Optional display name.
        """
        if not isinstance(objective, Calculation):
            raise ValueError("Objective must be an instance of Calculation.")

        objective_instance = Objective(objective, maximise, priority, weight, name)
        self.objectives.append(objective_instance)
        return objective_instance

    def add_constraint(self, constraint: Calculation | Parameter) -> Constraint:
        """Register a :class:`Constraint` over a numeric calculation.

        Returns the new :class:`Constraint`; chain ``.set_type(...)`` and
        ``.set_lower_bound(...)``/``.set_upper_bound(...)`` to configure it.
        """
        if not isinstance(constraint, Calculation):
            raise ValueError("Constraint must be an instance of Calculation.")

        constraint_instance = Constraint(constraint)
        self.constraints.append(constraint_instance)
        return constraint_instance

    def add_scenario_output(
        self,
        name: str,
        scenario_output_value: Calculation | Parameter | Field,
        scenario_output_table: Table | None = None,
    ) -> ScenarioOutput:
        """Register a :class:`ScenarioOutput` exposed in scenario comparison.

        Raises:
            ValueError: If ``name`` or the resolved cell reference duplicates an
                existing scenario output.
        """
        scenario_output = ScenarioOutput(
            name,
            scenario_output_value,
            scenario_output_table,
        )

        for existing in self.scenario_outputs:
            if existing.name == name:
                raise ValueError(f"Scenario output with name '{name}' already exists.")
            if existing.cell_reference == scenario_output.cell_reference:
                raise ValueError(
                    f"Scenario output with cell reference '{scenario_output.cell_reference}' "
                    f"already exists."
                )

        self.scenario_outputs.append(scenario_output)
        return scenario_output

    def build(self) -> dict[str, Any]:
        """Serialise this model configuration to a JSON-compatible dict."""
        return super().build()
