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

""":class:`CMAESAlgorithm` configuration for Covariance Matrix Adaptation Evolution Strategy."""

from dataclasses import dataclass
from typing import Any

from daitum_configuration.algorithm_configuration.algorithm import Algorithm, NamedValue
from daitum_configuration.algorithm_configuration.numeric_expression import NumericExpression


# pylint: disable=too-many-arguments,too-many-positional-arguments,too-many-instance-attributes
# pylint: disable=too-many-branches, duplicate-code
@dataclass
class CMAESAlgorithm(Algorithm):
    """Covariance Matrix Adaptation Evolution Strategy."""

    #: Number of candidate solutions per generation.
    population_size: int | NamedValue = NumericExpression("NUM_VARIABLES")
    #: Enable internal consistency assertions.
    consistency_check: bool = False
    #: Covariance-matrix cumulation constant.
    cc: float | NamedValue = 4 / NumericExpression("NUM_VARIABLES")
    #: Step-size cumulation constant.
    cs: float | NamedValue = 2 / NumericExpression("NUM_VARIABLES")
    #: Damping factor for step-size control.
    damps: float | NamedValue = 1 + 2 / NumericExpression("NUM_VARIABLES")
    #: Learning rate for the covariance-matrix update.
    ccov: float | NamedValue = 1 / NumericExpression("NUM_VARIABLES")
    #: Learning rate for the separable update.
    ccovsep: float | NamedValue = 1 / (
        NumericExpression("NUM_VARIABLES") * NumericExpression("NUM_VARIABLES")
    )
    #: Initial step size.
    sigma: float | NamedValue = 0.5
    #: Iterations using the diagonal-only update before the full update.
    diagonal_iterations: int | NamedValue = NumericExpression("NUM_VARIABLES")

    def __post_init__(self):
        super().__post_init__()
        self._validate_cmaes()

    @property
    def key(self) -> str:
        return "daitum-cmaes"

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
            "Population size": Algorithm._quant(self.population_size),
            "Consistency check": Algorithm._quant(self.consistency_check),
            "CC": Algorithm._quant(self.cc),
            "CS": Algorithm._quant(self.cs),
            "Damps": Algorithm._quant(self.damps),
            "CCOV": Algorithm._quant(self.ccov),
            "CCOVSEP": Algorithm._quant(self.ccovsep),
            "Sigma": Algorithm._quant(self.sigma),
            "Diagonal iterations": Algorithm._quant(self.diagonal_iterations),
        }

    def _validate_cmaes(self):
        self._validate_cmaes_population()
        self._validate_cmaes_step_params()
        self._validate_cmaes_cov_params()

    def _validate_cmaes_population(self):
        if not isinstance(self.population_size, int | NamedValue):
            raise TypeError("population_size must be int or NamedValue")
        if isinstance(self.population_size, int) and self.population_size < 0:
            raise ValueError("population_size must be non-negative")

        if not isinstance(self.consistency_check, bool):
            raise TypeError("consistency_check must be bool")

    def _validate_cmaes_step_params(self):
        if not isinstance(self.cc, float | NamedValue):
            raise TypeError("cc must be float or NamedValue")
        if isinstance(self.cc, float) and self.cc < 0:
            raise ValueError("cc must be non-negative")

        if not isinstance(self.cs, float | NamedValue):
            raise TypeError("cs must be float or NamedValue")
        if isinstance(self.cs, float) and self.cs < 0:
            raise ValueError("cs must be non-negative")

        if not isinstance(self.damps, float | NamedValue):
            raise TypeError("damps must be float or NamedValue")
        if isinstance(self.damps, float) and self.damps < 0:
            raise ValueError("damps must be non-negative")

    def _validate_cmaes_cov_params(self):
        if not isinstance(self.ccov, float | NamedValue):
            raise TypeError("ccov must be float or NamedValue")
        if isinstance(self.ccov, float) and self.ccov < 0:
            raise ValueError("ccov must be non-negative")

        if not isinstance(self.ccovsep, float | NamedValue):
            raise TypeError("ccovsep must be float or NamedValue")
        if isinstance(self.ccovsep, float) and self.ccovsep < 0:
            raise ValueError("ccovsep must be non-negative")

        if not isinstance(self.sigma, float | NamedValue):
            raise TypeError("sigma must be float or NamedValue")
        if isinstance(self.sigma, float) and self.sigma < 0:
            raise ValueError("sigma must be non-negative")

        if not isinstance(self.diagonal_iterations, int | NamedValue):
            raise TypeError("diagonal_iterations must be int or NamedValue")
        if isinstance(self.diagonal_iterations, int) and self.diagonal_iterations < 0:
            raise ValueError("diagonal_iterations must be non-negative")
