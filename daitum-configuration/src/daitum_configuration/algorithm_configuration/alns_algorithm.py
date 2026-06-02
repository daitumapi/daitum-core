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

""":class:`AdaptiveLargeNeighbourhoodSearch` configuration."""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from daitum_configuration.algorithm_configuration.algorithm import Algorithm, NamedValue
from daitum_configuration.algorithm_configuration.numeric_expression import NumericExpression


class AcceptanceCriterionType(Enum):
    """Strategy used to decide whether a candidate solution replaces the current one."""

    SIMULATED_ANNEALING = "Simulated Annealing"
    GREEDY = "Greedy"


# pylint: disable=too-few-public-methods
@dataclass
class AcceptanceCriterion:
    """An ALNS acceptance criterion: a :class:`AcceptanceCriterionType` plus its parameters.

    Simulated Annealing accepts improving moves and probabilistically accepts worsening
    moves based on a temperature schedule. Greedy only accepts improving (or equal) moves.
    """

    name: AcceptanceCriterionType
    parameters: dict[str, Any]

    @classmethod
    def simulated_annealing(
        cls,
        initial_temperature: float | NumericExpression | None = None,
        cooling_rate: float | NumericExpression | None = None,
    ) -> "AcceptanceCriterion":
        """Construct a Simulated Annealing acceptance criterion.

        Args:
            initial_temperature: Starting temperature for the SA schedule. Must be
                positive. Defaults to ``100.0``.
            cooling_rate: Geometric cooling factor applied each iteration. Must be in
                ``(0, 1)``. Defaults to ``0.9998``.
        """
        if initial_temperature is not None:
            if not isinstance(initial_temperature, float | NumericExpression):
                raise TypeError("initial_temperature must be float or NumericExpression")
            if isinstance(initial_temperature, float) and initial_temperature <= 0:
                raise ValueError("initial_temperature must be positive")
        if cooling_rate is not None:
            if not isinstance(cooling_rate, float | NumericExpression):
                raise TypeError("cooling_rate must be float or NumericExpression")
            if isinstance(cooling_rate, float) and not 0.0 < cooling_rate < 1.0:
                raise ValueError("cooling_rate must be in the open interval (0, 1)")
        return cls(
            name=AcceptanceCriterionType.SIMULATED_ANNEALING,
            parameters={
                "Initial temperature": (
                    initial_temperature if initial_temperature is not None else 100.0
                ),
                "Cooling rate": cooling_rate if cooling_rate is not None else 0.9998,
            },
        )

    @classmethod
    def greedy(cls) -> "AcceptanceCriterion":
        """Construct a Greedy acceptance criterion (only improving moves are accepted)."""
        return cls(name=AcceptanceCriterionType.GREEDY, parameters={})


# pylint: disable=too-many-instance-attributes
@dataclass
class AdaptiveLargeNeighbourhoodSearch(Algorithm):
    r"""
    Adaptive Large Neighbourhood Search (Ropke & Pisinger, 2006).

    ALNS maintains a single incumbent solution and, each iteration, generates one or
    more candidate solutions by applying a ``destroy`` operator followed by a
    ``repair`` operator. Operators are drawn from user-supplied pools by weighted
    random selection; their weights are updated online based on the outcome of each
    iteration so that operators that recently produced good moves are picked more
    often.

    Each iteration:

    1. Select ``k`` destroy operators by weighted random sampling.
    2. Select ``k`` repair operators by weighted random sampling.
    3. Generate ``k`` candidate solutions by applying each destroy/repair pair to a
       copy of the incumbent.
    4. Evaluate the ``k`` candidates (in parallel when ``k > 1``).
    5. Decide whether to accept the best candidate via the configured
       :class:`AcceptanceCriterion`.
    6. Reward the operator pairs that produced this iteration's candidates.
    7. Every :attr:`segment_length` iterations, decay all operator weights by
       :attr:`decay_factor`.

    The operator-reward schedule has three tiers:

    - :attr:`new_best_reward` (:math:`\sigma_1`) — the candidate became a new
      global best.
    - :attr:`improving_reward` (:math:`\sigma_2`) — the candidate improved on the
      current incumbent but is not a new global best.
    - :attr:`accepted_reward` (:math:`\sigma_3`) — the candidate did not improve
      but was accepted by the acceptance criterion (e.g. by SA).

    Operator weights are then decayed each segment via:

    .. math::

        w_{t+1} = \rho \cdot w_t

    where :math:`\rho` is :attr:`decay_factor`.

    The destroy and repair operator pools, plus the solution representation, are
    defined inside the user's external model implementation (see the platform
    ``ALNSExternalModel`` interface); only the algorithm-level controls are
    configured here.
    """

    #: Number of candidate solutions generated per iteration. ``k=1`` runs
    #: sequentially; ``k>1`` evaluates candidates in parallel.
    candidates_per_iteration: int | NamedValue = 1
    #: Iterations between operator weight decay steps.
    segment_length: int | NamedValue = 100
    #: :math:`\rho`: weight multiplier applied per segment. Must be in ``(0, 1)``.
    decay_factor: float | NamedValue = 0.80
    #: :math:`\sigma_1`: reward applied to operators that produced a new global best.
    new_best_reward: float | NamedValue = 33.0
    #: :math:`\sigma_2`: reward applied to operators that produced a candidate
    #: improving on the current incumbent (but not a new global best).
    improving_reward: float | NamedValue = 9.0
    #: :math:`\sigma_3`: reward applied to operators that produced an accepted but
    #: non-improving candidate.
    accepted_reward: float | NamedValue = 3.0
    #: Number of consecutive iterations without a new global best before triggering a
    #: soft restart. Set to ``0`` to disable. Requires ``perturb()`` to be implemented
    #: in the external model.
    stagnation_limit: int | NamedValue = 0
    #: Acceptance criterion governing whether candidates replace the incumbent.
    acceptance_criterion: AcceptanceCriterion = field(
        default_factory=AcceptanceCriterion.simulated_annealing
    )

    def __post_init__(self):
        super().__post_init__()
        self._validate_alns()

    @property
    def key(self) -> str:
        return "daitum-alns-single-objective"

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
            "Candidates per iteration": Algorithm._quant(self.candidates_per_iteration),
            "Segment length": Algorithm._quant(self.segment_length),
            "Decay factor": Algorithm._quant(self.decay_factor),
            "New best reward": Algorithm._quant(self.new_best_reward),
            "Improving reward": Algorithm._quant(self.improving_reward),
            "Accepted reward": Algorithm._quant(self.accepted_reward),
            "Stagnation limit": Algorithm._quant(self.stagnation_limit),
            "Acceptance criterion": Algorithm._qual(
                self.acceptance_criterion.name.value,
                {k: Algorithm._quant(v) for k, v in self.acceptance_criterion.parameters.items()},
            ),
        }

    def _validate_alns(self) -> None:
        self._validate_int("candidates_per_iteration", self.candidates_per_iteration, min_value=1)
        self._validate_int("segment_length", self.segment_length, min_value=1)
        self._validate_float("decay_factor", self.decay_factor, min_value=0.0, max_value=1.0)
        self._validate_float("new_best_reward", self.new_best_reward, min_value=0.0)
        self._validate_float("improving_reward", self.improving_reward, min_value=0.0)
        self._validate_float("accepted_reward", self.accepted_reward, min_value=0.0)
        self._validate_int("stagnation_limit", self.stagnation_limit, min_value=0)

        if not isinstance(self.acceptance_criterion, AcceptanceCriterion):
            raise TypeError("acceptance_criterion must be an instance of AcceptanceCriterion")

    @staticmethod
    def _validate_int(name: str, value: int | NamedValue, *, min_value: int) -> None:
        if not isinstance(value, int | NamedValue):
            raise TypeError(f"{name} must be int or NamedValue")
        if isinstance(value, int) and value < min_value:
            raise ValueError(f"{name} must not be less than {min_value}")

    @staticmethod
    def _validate_float(
        name: str,
        value: float | NamedValue,
        *,
        min_value: float | None = None,
        max_value: float | None = None,
    ) -> None:
        if not isinstance(value, float | NamedValue):
            raise TypeError(f"{name} must be float or NamedValue")
        if isinstance(value, float):
            if min_value is not None and value < min_value:
                raise ValueError(f"{name} must not be less than {min_value}")
            if max_value is not None and value > max_value:
                raise ValueError(f"{name} must not be greater than {max_value}")
