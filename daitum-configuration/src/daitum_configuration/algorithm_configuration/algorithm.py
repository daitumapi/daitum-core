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
Abstract :class:`Algorithm` base class for optimisation solver configurations.

Subclasses define their own ``key`` and parameter dict; common stopping criteria
(evaluation budget, time limits, restart count, PRNG seed) live on the base.
Numeric parameters accept a plain number, a
:class:`~daitum_configuration.NumericExpression`, or a model
:class:`~daitum_model.Parameter`/:class:`~daitum_model.Calculation`.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any

from daitum_model import Calculation, Parameter

from daitum_configuration._buildable import Buildable
from daitum_configuration.algorithm_configuration.numeric_expression import NumericExpression

# A numeric algorithm parameter that may be a plain expression or a model named value.
NamedValue = NumericExpression | Parameter | Calculation


# pylint: disable=too-many-arguments,too-many-positional-arguments,too-many-instance-attributes
# pylint: disable=too-many-branches
@dataclass
class Algorithm(Buildable, ABC):
    """Abstract base for optimisation algorithm configurations."""

    #: Whether the solver emits per-iteration progress logs.
    log_info: bool = False
    #: Maximum total evaluations before the run terminates.
    evaluations: int | NamedValue = 100000 * NumericExpression("NUM_VARIABLES")
    #: Stop after this many consecutive evaluations with no improvement.
    max_evaluations_without_improvement: int | NamedValue = 10000 * NumericExpression(
        "NUM_VARIABLES"
    )
    #: Stop after this many seconds with no improvement.
    max_time_without_improvement: int | NamedValue = 300
    #: Smallest objective change counted as an improvement.
    min_improvement: float | NamedValue = 0.000001
    #: Maximum number of restarts after stagnation.
    max_restart_count: int | NamedValue = 0
    #: Optional fixed seed for deterministic runs.
    prng_seed: int | None = None
    #: Hard wall-clock limit in seconds.
    time_limit: int | NamedValue = 60

    def __post_init__(self):
        self._validate()

    def _validate(self):
        self._validate_eval_params()
        self._validate_time_params()

    def _validate_eval_params(self):
        if not isinstance(self.log_info, bool):
            raise TypeError("log_info must be bool")

        if not isinstance(self.evaluations, int | NamedValue):
            raise TypeError("evaluations must be int or NamedValue")
        if isinstance(self.evaluations, int) and self.evaluations < 1:
            raise ValueError("evaluations must not be less than 1")

        if not isinstance(self.max_evaluations_without_improvement, int | NamedValue):
            raise TypeError("max_evaluations_without_improvement must be int or NamedValue")
        if (
            isinstance(self.max_evaluations_without_improvement, int)
            and self.max_evaluations_without_improvement < 1
        ):
            raise ValueError("max_evaluations_without_improvement must not be less than 1")

        if not isinstance(self.min_improvement, float | NamedValue):
            raise TypeError("min_improvement must be float or NamedValue")
        if isinstance(self.min_improvement, float) and self.min_improvement < 0:
            raise ValueError("min_improvement must be non-negative")

        if not isinstance(self.max_restart_count, int | NamedValue):
            raise TypeError("max_restart_count must be int or NamedValue")
        if isinstance(self.max_restart_count, int) and self.max_restart_count < 0:
            raise ValueError("max_restart_count must be non-negative")

        if self.prng_seed:
            if not isinstance(self.prng_seed, int | NamedValue):
                raise TypeError("prng_seed must be int or NamedValue")

    def _validate_time_params(self):
        if not isinstance(self.max_time_without_improvement, int | NamedValue):
            raise TypeError("max_time_without_improvement must be int or NamedValue")
        if (
            isinstance(self.max_time_without_improvement, int)
            and self.max_time_without_improvement < 1
        ):
            raise ValueError("max_time_without_improvement must not be less than 1")

        if not isinstance(self.time_limit, int | NamedValue):
            raise TypeError("time_limit must be int or NamedValue")
        if isinstance(self.time_limit, int) and self.time_limit < 0:
            raise ValueError("time_limit must be non-negative")

    @property
    @abstractmethod
    def key(self) -> str:
        """The algorithm key emitted as ``algorithmKey`` in the serialised output."""

    @abstractmethod
    def _build_parameters(self) -> dict[str, Any]:
        """Return the display-name-keyed parameter dict for serialisation."""

    def build(self) -> dict[str, Any]:
        """Serialise to the ``{algorithmKey, parameters}`` shape."""
        return {"algorithmKey": self.key, "parameters": self._build_parameters()}

    @staticmethod
    def _quant(value: Any | None) -> dict[str, Any]:
        if isinstance(value, bool):
            return {"@type": "quantitative", "value": value}
        if isinstance(value, Parameter | Calculation):
            return {"@type": "quantitative", "value": f"!!!{value.id}"}
        return {"@type": "quantitative", "value": str(value) if value is not None else None}

    @staticmethod
    def _qual(value: Any | None, parameters: dict[str, Any] | None = None) -> dict[str, Any]:
        if isinstance(value, bool):
            return {
                "@type": "qualitative",
                "value": value,
                "parameters": parameters or {},
            }
        if isinstance(value, Parameter | Calculation):
            return {
                "@type": "quantitative",
                "value": f"!!!{value.id}",
                "parameters": parameters or {},
            }
        return {
            "@type": "qualitative",
            "value": str(value) if value is not None else None,
            "parameters": parameters or {},
        }
