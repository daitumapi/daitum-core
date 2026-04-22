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
CMA-ES (Covariance Matrix Adaptation Evolution Strategy) Algorithm Configuration.

This module implements the configuration for the CMA-ES optimisation algorithm.

The CMAESAlgorithm class extends the base Algorithm class with CMA-ES specific parameters including:

- Population size and evolution strategy parameters
- Covariance matrix adaptation parameters
- Step-size control parameters
- Diagonalising parameters

Key Features:

- Configurable population size (can be expressed relative to problem dimension)
- Adaptive covariance matrix and step-size control
- Configurable diagonalising phase
- Comprehensive parameter validation
- Support for both numeric values and NumericExpressions for dynamic parameter calculation

The configuration includes default values based on established CMA-ES heuristics, particularly
for parameters that typically scale with the problem dimension (NUM_VARIABLES).

Examples:

.. code-block:: python

    ca1 = CMAESAlgorithm(population_size=1000, min_improvement=1.2, sigma=0.1)
    ca2 = CMAESAlgorithm(ccov=10.0 / NumericExpression("NUM_VARIABLES"))

Note:
    - The default values for many parameters are expressed as NumericExpressions involving
      NUM_VARIABLES, which will be evaluated at runtime based on the actual problem dimension.
"""

from dataclasses import dataclass
from typing import Any

from daitum_configuration.algorithm_configuration.algorithm import Algorithm, NamedValue
from daitum_configuration.algorithm_configuration.numeric_expression import NumericExpression


# pylint: disable=too-many-arguments,too-many-positional-arguments,too-many-instance-attributes
# pylint: disable=too-many-branches, duplicate-code
@dataclass
class CMAESAlgorithm(Algorithm):
    """
    CMA-ES (Covariance Matrix Adaptation Evolution Strategy) algorithm configuration.

    This is a discrete variant of the CMA-ES algorithm, adapted for combinatorial
    optimisation problems. CMA-ES iteratively updates a probability distribution
    over the solution space based on previous samples, learning correlations
    between variables to guide the search. It is particularly suited for complex,
    high-dimensional, and noisy discrete optimisation problems where gradients
    are unavailable or unreliable.
    """

    population_size: int | NamedValue = NumericExpression("NUM_VARIABLES")
    """
    Number of individuals in the population. Determines the size of the search pool. Note, as the
    fitness function for each element of the population is computed parallel, it makes most sense to
    set the population size to a multiple of the number of threads. For example, if running on 16
    cpus, the population should be set to a multiple of 16. In general, higher dimension problems
    work best with larger populations. However, if the fitness function is particularly expensive to
    compute, smaller populations will be required.
    """

    consistency_check: bool = False
    """
    Flag to enable or disable consistency checks on the algorithm's results during optimisation.
    If set to True, the algorithm ensures that the population is consistent in terms of fitness.
    """

    cc: float | NamedValue = 4 / NumericExpression("NUM_VARIABLES")
    """
    Learning rate for the covariance matrix adaptation. Controls the influence of the
    previous population on the covariance update, affecting how quickly the algorithm adapts.
    """

    cs: float | NamedValue = 2 / NumericExpression("NUM_VARIABLES")
    """
    Step-size parameter for the distribution's mean update. Governs the size of the step
    taken towards the new mean based on the current population.
    """

    damps: float | NamedValue = 1 + 2 / NumericExpression("NUM_VARIABLES")
    """
    Damping factor that controls the adaptation of the learning rate. It is used to scale
    the standard deviation during updates and prevents overly large steps in solution space.
    """

    ccov: float | NamedValue = 1 / NumericExpression("NUM_VARIABLES")
    """
    Learning rate for covariance matrix updates. Controls how much the covariance matrix
    should adapt in each generation based on the current population and the objective function.
    """

    ccovsep: float | NamedValue = 1 / (
        NumericExpression("NUM_VARIABLES") * NumericExpression("NUM_VARIABLES")
    )
    """
    Learning rate for covariance matrix updates when using separate covariance matrices for each
    dimension of the solution space. Allows for more flexible adaptation of the covariance matrix.
    """

    sigma: float | NamedValue = 0.5
    """
    Initial standard deviation, which controls the step size for the mutation. It determines how
    much variability is introduced into the population during mutation.
    """

    diagonal_iterations: int | NamedValue = NumericExpression("NUM_VARIABLES")
    """
    Number of iterations for diagonalising the covariance matrix. The higher the value,
    the more time is spent on fine-tuning the covariance matrix, potentially leading to
    better performance in high-dimensional problems.
    """

    def __post_init__(self):

        self.key = "daitum-cmaes"

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
            "Population size": Algorithm._create_quantitative(self.population_size),
            "Consistency check": Algorithm._create_quantitative(self.consistency_check),
            "CC": Algorithm._create_quantitative(self.cc),
            "CS": Algorithm._create_quantitative(self.cs),
            "Damps": Algorithm._create_quantitative(self.damps),
            "CCOV": Algorithm._create_quantitative(self.ccov),
            "CCOVSEP": Algorithm._create_quantitative(self.ccovsep),
            "Sigma": Algorithm._create_quantitative(self.sigma),
            "Diagonal iterations": Algorithm._create_quantitative(self.diagonal_iterations),
        }

        super().__post_init__()

        self._validate_cmaes()

    def to_dict(self) -> dict[str, Any]:
        return {"algorithmKey": self.key, "parameters": self.config}

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
