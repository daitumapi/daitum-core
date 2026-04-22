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
Genetic Algorithm Configuration Framework.

This module provides a comprehensive configuration system for genetic algorithms (GAs), including:

- Core GA parameters (mutation rate, recombination rate, population size)
- Genetic operators (selection, mutation, recombination)
- Comparison and diversity maintenance mechanisms
- Initialisation/sampling methods

Key Components:

1. Enum Types:
    - RecombinatorType: Crossover operations (uniform, n-point)
    - ComparatorType: Solution comparison strategies (lexicographic, weighted objectives)
    - MutationType: Mutation operations (Gaussian, uniform)
    - SelectionType: Parent selection mechanisms (tournament, random)
    - DistanceMetricType: Diversity metrics (Euclidean, Manhattan)
    - SamplingMethodType: Initialisation methods (uniform random, Latin Hypercube)

2. Operator Classes:
    - Mutation: Configures mutation operations with parameters
    - Selection: Configures selection mechanisms with parameters

3. Main GA Configuration:
     - GeneticAlgorithm: Complete GA configuration with all parameters
     - Supports both fixed values and dynamic NumericExpressions
     - Comprehensive validation of all parameters
     - Default values based on GA best practices

Features:
    - Flexible configuration with both fixed values and problem-dependent expressions
    - Type-safe enumeration of all algorithm choices
    - Built-in parameter validation
    - Support for both single-objective and multi-objective variants
    - Configurable diversity maintenance mechanisms

Examples:

.. code-block:: python

    ga1 = GeneticAlgorithm()
    ga2 = GeneticAlgorithm(population_size=1000, log_info=True, mutation_rate=0.9)

    # Define a custom mutation
    custom_mutation = Mutation.mutation(MutationType.GAUSSIAN_MUTATION)
    ga3 = GeneticAlgorithm(mutation=custom_mutation)

Note:
    - The default values for many parameters are expressed as NumericExpressions involving
      NUM_VARIABLES, which will be evaluated at runtime based on the actual problem dimension.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from daitum_configuration.algorithm_configuration.algorithm import Algorithm, NamedValue
from daitum_configuration.algorithm_configuration.numeric_expression import NumericExpression


class RecombinatorType(Enum):
    """
    Enum for different recombination (crossover) strategies in a genetic algorithm.

    Recombination combines two parent solutions to produce new offspring by mixing their
    genetic information. Different strategies control how the genes are exchanged between
    parents.

    Members:
        UNIFORM_CROSSOVER:
            Each gene is chosen randomly from one of the parents with equal probability.
            This creates high variability between offspring.

        N_POINT_CROSSOVER:
            The parents' genes are split at N random points, and segments are alternated
            between parents to create offspring. Controls the amount of mixing based on the
            number of crossover points.
    """

    UNIFORM_CROSSOVER = "Uniform crossover"
    N_POINT_CROSSOVER = "N-point crossover"


class ComparatorType(Enum):
    """
    Enum for different comparator strategies used to evaluate and rank solutions
    in multi-objective optimisation.

    A comparator defines how solutions are compared based on multiple objectives,
    which directly affects selection pressure and convergence in an evolutionary
    algorithm.

    Members:
        LEXICOGRAPHIC_COMPARATOR:
            Solutions are compared based on objective priorities, in order.
            The first objective is compared; if equal, the second is compared, and so on.

        WEIGHTED_OBJECTIVE_COMPARATOR:
            Objectives are combined using predefined weights to form a single score,
            which is then used for comparison.

        SAMPLE_WEIGHTED_OBJECTIVE_COMPARATOR:
            Similar to the weighted objective comparator, but weights are sampled
            dynamically during the optimisation process to introduce variability.

        USER_WEIGHTED_OBJECTIVE_COMPARATOR:
            Like the weighted objective comparator, but the weights are explicitly
            provided by the user, offering full control over objective importance.

        LEXICOGRAPHIC_ONLINE_WEIGHTED_OBJECTIVE_COMPARATOR:
            A hybrid approach that combines lexicographic ordering with online-sampled
            weights, allowing dynamic prioritisation of objectives during optimisation.
    """

    LEXICOGRAPHIC_COMPARATOR = "Lexicographic comparator"
    WEIGHTED_OBJECTIVE_COMPARATOR = "Weighted objective lexicographic comparator"
    SAMPLE_WEIGHTED_OBJECTIVE_COMPARATOR = "Weighted objective online lexicographic comparator"
    USER_WEIGHTED_OBJECTIVE_COMPARATOR = "User weighted objective comparator"
    LEXICOGRAPHIC_ONLINE_WEIGHTED_OBJECTIVE_COMPARATOR = (
        "Lexicographic online weighted objective comparator"
    )


class MutationType(Enum):
    """
    Enum for different mutation strategies used in evolutionary algorithms.

    Mutation introduces random changes to candidate solutions, promoting
    diversity and helping the algorithm escape local optima.

    Members:
        GAUSSIAN_MUTATION:
            Applies random changes to variables by adding noise sampled from
            a Gaussian (normal) distribution.

        UNIFORM_MUTATION:
            Mutates variables by assigning a new random value drawn uniformly
            from the allowed range.
    """

    GAUSSIAN_MUTATION = "Gaussian mutation"
    UNIFORM_MUTATION = "Uniform mutation"


class SelectionType(Enum):
    """
    Enum for different selection strategies used in evolutionary algorithms.

    Selection determines how individuals are chosen to produce the next
    generation, balancing exploration and exploitation.

    Members:
        TOURNAMENT_SELECTION:
            Randomly selects a group (tournament) of individuals and picks the
            best among them for reproduction. Balances exploration and pressure.

        FAST_TOURNAMENT_SELECTION:
            A more computationally efficient version of tournament selection,
            optimised for large populations.

        RANDOM_SELECTION:
            Selects individuals completely at random, ignoring fitness values.
            Useful for introducing high randomness or restarting diversity.
    """

    TOURNAMENT_SELECTION = "Tournament selection"
    FAST_TOURNAMENT_SELECTION = "Fast tournament selection"
    RANDOM_SELECTION = "Random selection"


_MIN_SELECTION_POOL_SIZE = 2


class DistanceMetricType(Enum):
    """
    Enum for different distance metrics used in optimisation algorithms.

    Distance metrics quantify how far apart two solutions are, which is
    important in tasks like clustering, diversity maintenance, or selection.

    Members:
        EUCLIDEAN_DISTANCE:
            Standard straight-line distance between two points in Euclidean
            space. Suitable for continuous variables.

        HAMMING_DISTANCE:
            Measures the number of positions at which the corresponding
            elements differ. Commonly used for discrete or binary variables.
    """

    EUCLIDEAN_DISTANCE = "Euclidean distance"
    HAMMING_DISTANCE = "Manhattan distance"


class SamplingMethodType(Enum):
    """
    Enum for different sampling methods used to generate initial solutions.

    Sampling methods are used to create diverse starting populations for
    optimisation algorithms.

    Members:
        UNIFORM_RANDOM:
            Samples points completely randomly with uniform probability
            across the search space.

        LATIN_HYPERCUBE:
            Samples points to better cover the space by stratifying each
            dimension, ensuring more even distribution than random sampling.
    """

    UNIFORM_RANDOM = "Uniform random"
    LATIN_HYPERCUBE = "Latin Hypercube"


# pylint: disable=too-few-public-methods
@dataclass
class Mutation:
    """
    A class representing a mutation operation in a genetic algorithm.

    Attributes:
        name: The type of mutation to be performed.
        parameters: A dictionary containing the parameters for the mutation operation.
    """

    name: MutationType
    parameters: dict[str, Any]

    @classmethod
    def mutation(
        cls,
        name: MutationType | None = None,
        variation_range: float | None | NumericExpression | None = None,
    ) -> "Mutation":
        """
        Creates a uniform mutation configuration.

        Args:
            name: The type of mutation. Defaults to UNIFORM_MUTATION if not specified.
            variation_range: The range for uniform mutation. Can be either:
                - A float value representing the absolute variation range
                - A NumericExpression for dynamic variation range
                    If not provided, defaults to 0.0.

        Returns:
            Mutation: A configured Mutation instance with uniform mutation parameters.

        Raises:
            TypeError: If variation_range is not a float or NumericExpression.
            ValueError: If variation_range is a negative float.
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
    """
    A class representing a selection operation in a genetic algorithm.

    Attributes:
        name: The type of selection to be performed.
        parameters: A dictionary containing the parameters for the selection operation.
    """

    name: SelectionType
    parameters: dict[str, Any]

    @classmethod
    def selection(
        cls,
        name: SelectionType | None = None,
        pool_size: int | None | NumericExpression | None = None,
    ) -> "Selection":
        """
        Creates a tournament selection configuration.

        Args:
            name: The type of selection. Defaults to FAST_TOURNAMENT_SELECTION if not specified.
            pool_size: The size of the tournament pool. Can be either:
                - An integer representing the fixed pool size
                - A NumericExpression for dynamic pool size
                If not provided, defaults to 2.

        Returns:
            Selection: A configured Selection instance with tournament selection parameters.

        Raises:
            TypeError: If pool_size is not an integer or NumericExpression.
            ValueError: If pool_size is an integer less than 2.
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
    """
    Genetic Algorithm configuration.

    A Genetic Algorithm (GA) is a population-based optimisation method inspired
    by natural selection. It evolves a set of candidate solutions over multiple
    generations by selecting, recombining, and mutating individuals based on
    their fitness. Over time, the population adapts towards better solutions.

    This class inherits from the base Algorithm and adds GA-specific parameters
    such as selection, mutation, recombination, and population size.
    """

    mutation_rate: float | NamedValue = 1 / NumericExpression("NUM_VARIABLES")
    """
    The probability of mutating a single gene in a child solution.
    """

    recombinator_rate: float | NamedValue = 0.8
    """
    The probability of applying recombination (crossover) between two parent solutions.
    """

    population_size: int | NamedValue = NumericExpression("NUM_VARIABLES")
    """
    Number of individuals in the population for each generation. Note, as the fitness function for
    each element of the population is computed parallel, it makes most sense to set the population
    size to a multiple of the number of threads. For example, if running on 16 cpus, the population
    should be set to a multiple of 16. In general, higher dimension problems work best with larger
    populations. However, if the fitness function is particularly expensive to compute, smaller
    populations will be required.
    """

    elitism: int | NamedValue = 1
    """
    Number of top-performing individuals carried over unchanged to the next generation.
    """

    mutation: Mutation = field(default_factory=Mutation.mutation)
    """
    The mutation operator used to modify individuals during evolution.
    """

    recombinator: RecombinatorType = RecombinatorType.UNIFORM_CROSSOVER
    """
    The recombination (crossover) strategy applied to parent solutions.
    """

    n_point_cuts: int | NamedValue | None = None
    """
    Number of crossover points used if n-point crossover is selected.
    """

    selection: Selection = field(default_factory=Selection.selection)
    """
    The selection strategy used to choose individuals for reproduction.
    """

    comparator: ComparatorType | None = None
    """
    Comparator used to rank individuals based on objective values.
    """

    tiebreaker: bool = False
    """
    If enabled, breaks ties between individuals randomly during selection.
    """

    distance_metric: DistanceMetricType = DistanceMetricType.EUCLIDEAN_DISTANCE
    """
    Distance metric used when calculating similarity between individuals.
    """

    sample_count: int | NamedValue = 0
    """
    Number of samples to generate when using sample-based methods.
    """

    sampling_method: SamplingMethodType = SamplingMethodType.UNIFORM_RANDOM
    """
    Method used to generate initial samples or resampling points.
    """

    def __post_init__(self):

        if self.recombinator == RecombinatorType.N_POINT_CROSSOVER:
            self.n_point_cuts = 2
        else:
            self.n_point_cuts = None

        self.key = "daitum-gga-single-objective"
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
            "Mutation rate": Algorithm._create_quantitative(self.mutation_rate),
            "Recombinator rate": Algorithm._create_quantitative(self.recombinator_rate),
            "Population size": Algorithm._create_quantitative(self.population_size),
            "Elitism": Algorithm._create_quantitative(self.elitism),
            "Mutation": Algorithm._create_qualitative(
                self.mutation.name.value,
                {k: Algorithm._create_quantitative(v) for k, v in self.mutation.parameters.items()},
            ),
            "Recombinator": Algorithm._create_qualitative(self.recombinator.value),
            "N-point cuts": Algorithm._create_quantitative(self.n_point_cuts),
            "Selection": Algorithm._create_qualitative(
                self.selection.name.value,
                {
                    k: Algorithm._create_quantitative(v)
                    for k, v in self.selection.parameters.items()
                },
            ),
            "Comparator": Algorithm._create_qualitative(
                self.comparator.value if self.comparator is not None else None
            ),
            "Tiebreaker": Algorithm._create_quantitative(self.tiebreaker),
            "Distance Metric": Algorithm._create_qualitative(self.distance_metric.value),
            "Sample Count": Algorithm._create_quantitative(self.sample_count),
            "Sampling Method": Algorithm._create_qualitative(self.sampling_method.value),
        }

        super().__post_init__()
        self._validate_genetic()

    def to_dict(self) -> dict[str, Any]:
        return {"algorithmKey": self.key, "parameters": self.config}

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
