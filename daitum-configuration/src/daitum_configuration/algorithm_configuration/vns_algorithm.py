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
Variable Neighbourhood Search (VNS) Configuration Framework.

This module provides a configuration system for Variable Neighbourhood Search (VNS)
algorithms. It defines all key parameters, validation logic, and operator structures
required to configure and execute a VNS-based optimisation process.

Variable Neighbourhood Search is a metaheuristic that systematically changes the
neighbourhood structures during the search to escape local optima. It alternates
between diversification (exploration) and intensification (exploitation) phases,
making it suitable for both combinatorial and continuous optimisation problems.

Key Components:
    1. Parameter Definitions:
        - Mutation rate controls adaptive diversification strength.
        - Offspring size controls the number of candidate solutions per iteration.
        - Mutation operator defines how new solutions are perturbed.

    2. Mutation Adaptation:
        - The mutation rate can dynamically increase or decrease depending on
          the recent success of the search process.
        - Scaling factors (`mutation_rate_up_scale`, `mutation_rate_down_scale`)
          determine the adaptation rate.

    3. Validation and Configuration:
        - Automatic validation ensures all parameters are within logical bounds.
        - Configurations are represented in a consistent dictionary format for
          integration with other components.

Example:

.. code-block:: python

    vns = VariableNeighbourhoodSearch(
        initial_mutation_rate=0.2,
        offspring_size=32,
        mutation_rate_up_scale=1.3,
        mutation_rate_down_scale=0.85
    )
"""

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
    Variable Neighbourhood Search (VNS) configuration.

    This class extends the base :class:`Algorithm` to include VNS-specific
    parameters such as adaptive mutation rate scaling, offspring size,
    and mutation operator configuration.
    """

    initial_mutation_rate: float | NamedValue = 0.1
    """
    The initial probability of mutating a single gene in a solution.
    Acts as the baseline for adaptive mutation adjustments.
    """

    minimum_mutation_rate: float | NamedValue = 1 / NumericExpression("NUM_VARIABLES")
    """
    The minimum allowable mutation rate. When reached, mutation adaptation
    will not decrease further.
    """

    maximum_mutation_rate: float | NamedValue = 1.0
    """
    The maximum allowable mutation rate. When reached, mutation adaptation
    will not increase further.
    """

    mutation_rate_up_scale: float | NamedValue = 1.5
    """
    The multiplicative factor applied to the mutation rate when a search
    iteration is considered successful.

    A successful iteration is defined as one in which the number of improved or
    stagnant solutions exceeds the square root of the offspring size. This
    increases mutation strength to encourage broader exploration.
    """

    mutation_rate_down_scale: float | NamedValue = 0.9
    """
    The multiplicative factor applied to the mutation rate when a search
    iteration is considered unsuccessful.

    An unsuccessful iteration occurs when the number of improved or stagnant
    solutions falls below the square root of the offspring size. This decreases
    mutation strength to favour local exploitation.
    """

    offspring_size: int | NamedValue = 64
    """
    The number of candidate solutions generated per iteration. For parallel
    implementations, this is typically set to the number of available threads.
    """

    mutation: Mutation = field(default_factory=Mutation.mutation)
    """
    The mutation operator defining how candidate solutions are perturbed
    during neighbourhood exploration.
    """

    def __post_init__(self):
        self.key = "daitum-vns-single-objective"
        self.config = {
            "Log info": Algorithm._create_quantitative(self.log_info),
            "Evaluations": Algorithm._create_quantitative(self.evaluations),
            "Maximum evaluations without improvement": Algorithm._create_quantitative(
                self.max_evaluations_without_improvement
            ),
            "Maximum time without improvement": Algorithm._create_quantitative(
                self.max_time_without_improvement
            ),
            "Minimum improvement": Algorithm._create_quantitative(self.min_improvement),
            "Maximum restart count": Algorithm._create_quantitative(self.max_restart_count),
            "PRNG seed": Algorithm._create_quantitative(self.prng_seed),
            "Time limit": Algorithm._create_quantitative(self.time_limit),
            "Initial mutation rate": Algorithm._create_quantitative(self.initial_mutation_rate),
            "Maximum mutation rate": Algorithm._create_quantitative(self.maximum_mutation_rate),
            "Minimum mutation rate": Algorithm._create_quantitative(self.minimum_mutation_rate),
            "Mutation rate up scale": Algorithm._create_quantitative(self.mutation_rate_up_scale),
            "Mutation rate down scale": Algorithm._create_quantitative(
                self.mutation_rate_down_scale
            ),
            "Offspring size": Algorithm._create_quantitative(self.offspring_size),
            "Mutation": Algorithm._create_qualitative(
                self.mutation.name.value,
                {k: Algorithm._create_quantitative(v) for k, v in self.mutation.parameters.items()},
            ),
        }

        super().__post_init__()
        self._validate_config()

    def to_dict(self) -> dict[str, Any]:
        return {"algorithmKey": self.key, "parameters": self.config}

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
