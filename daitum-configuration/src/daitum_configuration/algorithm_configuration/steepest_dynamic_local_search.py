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

""":class:`SteepestDynamicLocalSearch` configuration for steepest-descent local search."""

from dataclasses import dataclass
from typing import Any

from daitum_configuration.algorithm_configuration.algorithm import Algorithm, NamedValue


# pylint: disable=too-many-instance-attributes, duplicate-code
@dataclass
class SteepestDynamicLocalSearch(Algorithm):
    """
    Steepest Descent local search with a dynamic step-size schedule.

    Each iteration perturbs every decision variable by ±``step_size`` and
    accepts the best neighbour. :attr:`integer_step_size` applies to
    integer-typed variables; :attr:`decimal_step_size` applies to real-typed
    variables. When an iteration finds no improvement the step shrinks
    toward ``..._lowest_step`` by ``..._step_change``; once at the lowest
    step with no further improvement the search terminates (subject to the
    base stopping criteria inherited from :class:`Algorithm`).

    :attr:`allow_neutral_walks` permits accepting equal-objective neighbours,
    letting the search drift across plateaus.
    """

    #: Accept neighbours with equal objective value (plateau drift).
    allow_neutral_walks: bool = False
    #: Initial perturbation magnitude for integer-typed variables.
    integer_step_size: int | NamedValue = 10
    #: Initial perturbation magnitude for real-typed variables.
    decimal_step_size: float | NamedValue = 0.1
    #: Amount by which the integer step is reduced after a non-improving iteration.
    integer_step_change: int | NamedValue = 1
    #: Floor below which the integer step will not shrink.
    integer_lowest_step: int | NamedValue = 1
    #: Amount by which the decimal step is reduced after a non-improving iteration.
    decimal_step_change: float | NamedValue = 0.001
    #: Floor below which the decimal step will not shrink.
    decimal_lowest_step: float | NamedValue = 0.001

    def __post_init__(self):
        super().__post_init__()
        self._validate_sdls()

    @property
    def key(self) -> str:
        return "daitum-steepest-dynamic-localsearch-single-objective"

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
            "Allow neutral walks": Algorithm._quant(self.allow_neutral_walks),
            "Integer step size": Algorithm._quant(self.integer_step_size),
            "Decimal step size": Algorithm._quant(self.decimal_step_size),
            "Integer step change": Algorithm._quant(self.integer_step_change),
            "Integer lowest step": Algorithm._quant(self.integer_lowest_step),
            "Decimal step change": Algorithm._quant(self.decimal_step_change),
            "Decimal lowest step": Algorithm._quant(self.decimal_lowest_step),
        }

    def _validate_sdls(self):
        if not isinstance(self.allow_neutral_walks, bool):
            raise TypeError("allow_neutral_walks must be bool")

        self._validate_int_param("integer_step_size", self.integer_step_size)
        self._validate_int_param("integer_step_change", self.integer_step_change)
        self._validate_int_param("integer_lowest_step", self.integer_lowest_step)

        self._validate_float_param("decimal_step_size", self.decimal_step_size)
        self._validate_float_param("decimal_step_change", self.decimal_step_change)
        self._validate_float_param("decimal_lowest_step", self.decimal_lowest_step)

    @staticmethod
    def _validate_int_param(name: str, value: int | NamedValue) -> None:
        if not isinstance(value, int | NamedValue):
            raise TypeError(f"{name} must be int or NamedValue")
        if isinstance(value, int) and value < 0:
            raise ValueError(f"{name} must be non-negative")

    @staticmethod
    def _validate_float_param(name: str, value: float | NamedValue) -> None:
        if not isinstance(value, float | NamedValue):
            raise TypeError(f"{name} must be float or NamedValue")
        if isinstance(value, float) and value < 0:
            raise ValueError(f"{name} must be non-negative")
