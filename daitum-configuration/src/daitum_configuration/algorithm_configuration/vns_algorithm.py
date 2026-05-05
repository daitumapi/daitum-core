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

""":class:`VariableNeighbourhoodSearch` configuration."""

from dataclasses import dataclass, field
from typing import Any

from typeguard import typechecked

from daitum_configuration.algorithm_configuration.algorithm import Algorithm, NamedValue
from daitum_configuration.algorithm_configuration.genetic_algorithm import Mutation
from daitum_configuration.algorithm_configuration.numeric_expression import NumericExpression


# pylint: disable=too-many-instance-attributes
@dataclass
class VariableNeighbourhoodSearch(Algorithm):
    """
    Variable Neighbourhood Search metaheuristic.

    Adapts mutation rate dynamically: scales up after stagnation, down after
    improvement, within the configured bounds.
    """

    #: Mutation rate used at the start of the run (0–1).
    initial_mutation_rate: float | NamedValue = 0.1
    #: Lower bound on the mutation rate (0–1).
    minimum_mutation_rate: float | NamedValue = 1 / NumericExpression("NUM_VARIABLES")
    #: Upper bound on the mutation rate (0–1).
    maximum_mutation_rate: float | NamedValue = 1.0
    #: Factor applied to the mutation rate after stagnation (must be ≥ 1).
    mutation_rate_up_scale: float | NamedValue = 1.5
    #: Factor applied to the mutation rate after improvement (0–1).
    mutation_rate_down_scale: float | NamedValue = 0.9
    #: Number of offspring generated per iteration.
    offspring_size: int | NamedValue = 64
    #: Mutation operator.
    mutation: Mutation = field(default_factory=Mutation.mutation)

    def __post_init__(self):
        super().__post_init__()
        self._validate_config()

    @property
    def key(self) -> str:
        return "daitum-vns-single-objective"

    def _build_parameters(self) -> dict[str, Any]:
        return {
            "Log info": Algorithm._quant(self.log_info),
            "Evaluations": Algorithm._quant(self.evaluations),
            "Maximum evaluations without improvement": Algorithm._quant(
                self.max_evaluations_without_improvement
            ),
            "Maximum time without improvement": Algorithm._quant(self.max_time_without_improvement),
            "Minimum improvement": Algorithm._quant(self.min_improvement),
            "Maximum restart count": Algorithm._quant(self.max_restart_count),
            "PRNG seed": Algorithm._quant(self.prng_seed),
            "Time limit": Algorithm._quant(self.time_limit),
            "Initial mutation rate": Algorithm._quant(self.initial_mutation_rate),
            "Maximum mutation rate": Algorithm._quant(self.maximum_mutation_rate),
            "Minimum mutation rate": Algorithm._quant(self.minimum_mutation_rate),
            "Mutation rate up scale": Algorithm._quant(self.mutation_rate_up_scale),
            "Mutation rate down scale": Algorithm._quant(self.mutation_rate_down_scale),
            "Offspring size": Algorithm._quant(self.offspring_size),
            "Mutation": Algorithm._qual(
                self.mutation.name.value,
                {k: Algorithm._quant(v) for k, v in self.mutation.parameters.items()},
            ),
        }

    @typechecked
    def _validate_in_bounds(
        self,
        param_name: str,
        param: int | float | NamedValue,
        min_value: float | None,
        max_value: float | None,
    ) -> None:
        if isinstance(param, (int, float)):
            if (min_value is not None and param < min_value) or (
                max_value is not None and param > max_value
            ):
                raise ValueError(
                    f"{param_name} must be within range {min_value or '-∞'} to {max_value or '∞'}"
                )

    def _validate_config(self):
        self._validate_in_bounds("Initial mutation rate", self.initial_mutation_rate, 0.0, 1.0)
        self._validate_in_bounds("Minimum mutation rate", self.minimum_mutation_rate, 0.0, 1.0)
        self._validate_in_bounds("Maximum mutation rate", self.maximum_mutation_rate, 0.0, 1.0)
        self._validate_in_bounds("Mutation rate up scale", self.mutation_rate_up_scale, 1.0, None)
        self._validate_in_bounds(
            "Mutation rate down scale", self.mutation_rate_down_scale, 0.0, 1.0
        )
