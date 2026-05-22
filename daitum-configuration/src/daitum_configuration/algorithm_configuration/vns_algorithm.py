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
from daitum_configuration.algorithm_configuration.genetic_algorithm import Mutation, Selection
from daitum_configuration.algorithm_configuration.numeric_expression import NumericExpression


# pylint: disable=too-many-instance-attributes
@dataclass
class VariableNeighbourhoodSearch(Algorithm):
    """
    Variable Neighbourhood Search — a (μ+λ) evolutionary algorithm with a
    self-adapting mutation rate.

    Each individual carries its own mutation rate as part of its genome.
    When producing offspring, the rate is perturbed by a lognormal step:

    .. math::

        \\text{childRate} = \\text{parentRate} \\times \\exp(\\tau \\cdot
        \\mathcal{N}(0, 1))

    where :math:`\\tau` is :attr:`mutation_rate_tau`. The result is clamped to
    ``[minimum_mutation_rate, maximum_mutation_rate]``, and the offspring
    inherits the new rate alongside the mutated genome. Larger :math:`\\tau` widens the
    per-generation step in log-space.

    The population is (μ+λ): :attr:`population_size` is **λ** (total
    offspring per generation) and the number of parents **μ** is
    ``population_size / offspring_size``. :attr:`selection` picks the μ
    parents each generation.
    """

    #: Mutation rate used to seed each individual at the start of the run (0–1).
    initial_mutation_rate: float | NamedValue = 1 / NumericExpression("NUM_VARIABLES")
    #: Lower clamp on per-individual mutation rate (0–1).
    minimum_mutation_rate: float | NamedValue = 1 / NumericExpression("NUM_VARIABLES")
    #: Upper clamp on per-individual mutation rate (0–1).
    maximum_mutation_rate: float | NamedValue = 1.0
    #: Log-normal learning rate τ controlling the magnitude of per-offspring
    #: mutation-rate steps: ``childRate = parentRate × exp(τ × N(0, 1))``.
    #: Must be non-negative; larger values widen the step distribution.
    mutation_rate_tau: float | NamedValue = 0.5
    #: Offspring produced per parent each generation. Combined with
    #: :attr:`population_size` this fixes μ = ``population_size / offspring_size``.
    offspring_size: int | NamedValue = 64
    #: Total offspring per generation — **λ** in (μ+λ) notation.
    population_size: int | NamedValue = NumericExpression("NUM_VARIABLES")
    #: Mutation operator applied to offspring genomes.
    mutation: Mutation = field(default_factory=Mutation.mutation)
    #: Parent-selection operator.
    selection: Selection = field(default_factory=Selection.selection)

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
            "Mutation rate tau": Algorithm._quant(self.mutation_rate_tau),
            "Offspring size": Algorithm._quant(self.offspring_size),
            "Population size": Algorithm._quant(self.population_size),
            "Mutation": Algorithm._qual(
                self.mutation.name.value,
                {k: Algorithm._quant(v) for k, v in self.mutation.parameters.items()},
            ),
            "Selection": Algorithm._qual(
                self.selection.name.value,
                {k: Algorithm._quant(v) for k, v in self.selection.parameters.items()},
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
        self._validate_in_bounds("Mutation rate tau", self.mutation_rate_tau, 0.0, None)

        if not isinstance(self.population_size, int | NamedValue):
            raise TypeError("population_size must be int or NamedValue")
        if isinstance(self.population_size, int) and self.population_size < 0:
            raise ValueError("population_size must be non-negative")

        if not isinstance(self.mutation, Mutation):
            raise TypeError("mutation must be an instance of Mutation")
        if not isinstance(self.selection, Selection):
            raise TypeError("selection must be an instance of Selection")
