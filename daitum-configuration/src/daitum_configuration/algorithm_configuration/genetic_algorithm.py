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
:class:`GeneticAlgorithm` configuration plus its mutation, selection, and recombination
operator types.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from daitum_configuration.algorithm_configuration.algorithm import Algorithm, NamedValue
from daitum_configuration.algorithm_configuration.numeric_expression import NumericExpression


class RecombinatorType(Enum):
    """Crossover strategies for combining parent solutions."""

    UNIFORM_CROSSOVER = "Uniform crossover"
    N_POINT_CROSSOVER = "N-point crossover"


class ComparatorType(Enum):
    """Solution-comparison strategy for multi-objective optimisation."""

    LEXICOGRAPHIC_COMPARATOR = "Lexicographic comparator"
    WEIGHTED_OBJECTIVE_COMPARATOR = "Weighted objective lexicographic comparator"
    SAMPLE_WEIGHTED_OBJECTIVE_COMPARATOR = "Weighted objective online lexicographic comparator"
    USER_WEIGHTED_OBJECTIVE_COMPARATOR = "User weighted objective comparator"
    LEXICOGRAPHIC_ONLINE_WEIGHTED_OBJECTIVE_COMPARATOR = (
        "Lexicographic online weighted objective comparator"
    )


class MutationType(Enum):
    """Mutation strategy used to perturb individual solutions."""

    GAUSSIAN_MUTATION = "Gaussian mutation"
    UNIFORM_MUTATION = "Uniform mutation"


class SelectionType(Enum):
    """Strategy for selecting individuals from the population."""

    TOURNAMENT_SELECTION = "Tournament selection"
    FAST_TOURNAMENT_SELECTION = "Fast tournament selection"
    RANDOM_SELECTION = "Random selection"


_MIN_SELECTION_POOL_SIZE = 2


class DistanceMetricType(Enum):
    """Distance metric used for diversity-aware operators."""

    EUCLIDEAN_DISTANCE = "Euclidean distance"
    HAMMING_DISTANCE = "Manhattan distance"


class SamplingMethodType(Enum):
    """Method used to generate the initial population."""

    UNIFORM_RANDOM = "Uniform random"
    LATIN_HYPERCUBE = "Latin Hypercube"


# pylint: disable=too-few-public-methods
@dataclass
class Mutation:
    """A mutation operator: a :class:`MutationType` plus its operator-specific parameters."""

    name: MutationType
    parameters: dict[str, Any]

    @classmethod
    def mutation(
        cls,
        name: MutationType | None = None,
        variation_range: float | NumericExpression | None = None,
    ) -> "Mutation":
        """Construct a :class:`Mutation` with default operator parameters.

        Args:
            name: Mutation strategy. Defaults to ``UNIFORM_MUTATION``.
            variation_range: Variation magnitude for uniform mutation. Must be
                non-negative.
        """
        if variation_range:
            if not isinstance(variation_range, float | NumericExpression):
                raise TypeError("variation_range must be float or NumericExpression")
            if isinstance(variation_range, float) and variation_range < 0:
                raise ValueError("variation_range must be non-negative")

        return cls(
            name=name or MutationType.UNIFORM_MUTATION,
            parameters={"Uniform mutation variation range": variation_range or 0.0},
        )


# pylint: disable=too-few-public-methods
@dataclass
class Selection:
    """A selection operator: a :class:`SelectionType` plus its operator-specific parameters."""

    name: SelectionType
    parameters: dict[str, Any]

    @classmethod
    def selection(
        cls,
        name: SelectionType | None = None,
        pool_size: int | NumericExpression | None = None,
    ) -> "Selection":
        """Construct a :class:`Selection` with default operator parameters.

        Args:
            name: Selection strategy. Defaults to ``FAST_TOURNAMENT_SELECTION``.
            pool_size: Tournament pool size. Must be at least 2.
        """
        if pool_size:
            if not isinstance(pool_size, int | NumericExpression):
                raise TypeError("pool_size must be int or NumericExpression")
            if isinstance(pool_size, int) and pool_size < _MIN_SELECTION_POOL_SIZE:
                raise ValueError("pool_size must not be less than 2")
        return cls(
            name=name or SelectionType.FAST_TOURNAMENT_SELECTION,
            parameters={"Selection pool size": pool_size or 2},
        )


# pylint: disable=too-many-arguments,too-many-positional-arguments,too-many-instance-attributes
# pylint: disable=too-many-branches, duplicate-code
@dataclass
class GeneticAlgorithm(Algorithm):
    """Population-based evolutionary algorithm."""

    #: Probability of mutating an offspring (0–1).
    mutation_rate: float | NamedValue = 1 / NumericExpression("NUM_VARIABLES")
    #: Probability of applying crossover (0–1).
    recombinator_rate: float | NamedValue = 0.8
    #: Number of individuals in the population.
    population_size: int | NamedValue = NumericExpression("NUM_VARIABLES")
    #: Number of top individuals copied unchanged into the next generation.
    elitism: int | NamedValue = 1
    #: Mutation operator.
    mutation: Mutation = field(default_factory=Mutation.mutation)
    #: Crossover strategy.
    recombinator: RecombinatorType = RecombinatorType.UNIFORM_CROSSOVER
    #: Number of crossover points; auto-set for N-point crossover.
    n_point_cuts: int | NamedValue | None = None
    #: Selection operator.
    selection: Selection = field(default_factory=Selection.selection)
    #: Optional solution comparator for multi-objective runs.
    comparator: ComparatorType | None = None
    #: Apply a diversity-aware tiebreaker on equal objective values.
    tiebreaker: bool = False
    #: Distance metric for diversity-aware operators.
    distance_metric: DistanceMetricType = DistanceMetricType.EUCLIDEAN_DISTANCE
    #: Initial-sample count for sampling-based seeding.
    sample_count: int | NamedValue = 0
    #: Initial-population sampling method.
    sampling_method: SamplingMethodType = SamplingMethodType.UNIFORM_RANDOM

    def __post_init__(self):
        if self.recombinator == RecombinatorType.N_POINT_CROSSOVER:
            self.n_point_cuts = 2
        else:
            self.n_point_cuts = None

        super().__post_init__()
        self._validate_genetic()

    @property
    def key(self) -> str:
        return "daitum-gga-single-objective"

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
            "Mutation rate": Algorithm._quant(self.mutation_rate),
            "Recombinator rate": Algorithm._quant(self.recombinator_rate),
            "Population size": Algorithm._quant(self.population_size),
            "Elitism": Algorithm._quant(self.elitism),
            "Mutation": Algorithm._qual(
                self.mutation.name.value,
                {k: Algorithm._quant(v) for k, v in self.mutation.parameters.items()},
            ),
            "Recombinator": Algorithm._qual(self.recombinator.value),
            "N-point cuts": Algorithm._quant(self.n_point_cuts),
            "Selection": Algorithm._qual(
                self.selection.name.value,
                {k: Algorithm._quant(v) for k, v in self.selection.parameters.items()},
            ),
            "Comparator": Algorithm._qual(
                self.comparator.value if self.comparator is not None else None
            ),
            "Tiebreaker": Algorithm._quant(self.tiebreaker),
            "Distance Metric": Algorithm._qual(self.distance_metric.value),
            "Sample Count": Algorithm._quant(self.sample_count),
            "Sampling Method": Algorithm._qual(self.sampling_method.value),
        }

    def _validate_genetic(self):
        self._validate_ga_rates()
        self._validate_ga_operators()
        self._validate_ga_diversity()

    def _validate_ga_rates(self):
        if not isinstance(self.mutation_rate, float | NamedValue):
            raise TypeError("mutation_rate must be float or NamedValue")
        if isinstance(self.mutation_rate, float) and (
            self.mutation_rate < 0 or self.mutation_rate > 1
        ):
            raise ValueError("mutation_rate must be in range 0-1")

        if not isinstance(self.recombinator_rate, float | NamedValue):
            raise TypeError("recombinator_rate must be float or NamedValue")
        if isinstance(self.recombinator_rate, float) and (
            self.recombinator_rate < 0 or self.recombinator_rate > 1
        ):
            raise ValueError("recombinator_rate must be in range 0-1")

        if not isinstance(self.population_size, int | NamedValue):
            raise TypeError("population_size must be int or NamedValue")
        if isinstance(self.population_size, int) and self.population_size < 0:
            raise ValueError("population_size must be non-negative")

        if not isinstance(self.elitism, int | NamedValue):
            raise TypeError("elitism must be int or NamedValue")
        if isinstance(self.elitism, int) and self.elitism < 0:
            raise ValueError("elitism must be non-negative")

    def _validate_ga_operators(self):
        if not isinstance(self.mutation, Mutation):
            raise TypeError("mutation must be an instance of Mutation")

        if not isinstance(self.recombinator, RecombinatorType):
            raise TypeError("recombinator must be an instance of RecombinatorType")

        if self.n_point_cuts:
            if not isinstance(self.n_point_cuts, int | NamedValue):
                raise TypeError("n_point_cuts must be int or NamedValue")
            if isinstance(self.n_point_cuts, int) and self.n_point_cuts < 1:
                raise ValueError("n_point_cuts must not be less than 1")

        if not isinstance(self.selection, Selection):
            raise TypeError("selection must be an instance of Selection")

        if self.comparator:
            if not isinstance(self.comparator, ComparatorType):
                raise TypeError("comparator must be None or an instance of ComparatorType")

    def _validate_ga_diversity(self):
        if not isinstance(self.tiebreaker, bool):
            raise TypeError("tiebreaker must be bool")

        if not isinstance(self.distance_metric, DistanceMetricType):
            raise TypeError("distance_metric must be an instance of DistanceMetricType")

        if not isinstance(self.sample_count, int | NamedValue):
            raise TypeError("sample_count must be int or NamedValue")
        if isinstance(self.sample_count, int) and self.sample_count < 0:
            raise ValueError("sample_count must be non-negative")

        if not isinstance(self.sampling_method, SamplingMethodType):
            raise TypeError("sampling_method must be an instance of SamplingMethodType")
