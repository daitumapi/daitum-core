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

""":class:`ScheduleConfiguration` — multi-step optimisation schedule."""

from typeguard import typechecked

from daitum_configuration._buildable import Buildable
from daitum_configuration.algorithm_configuration.algorithm import Algorithm
from daitum_configuration.schedule_configuration.step_configuration import StepConfiguration


@typechecked
class ScheduleConfiguration(Buildable):
    """
    Multi-step optimisation schedule.

    Pairs a named map of
    :class:`~daitum_configuration.algorithm_configuration.algorithm.Algorithm`
    instances with a :class:`StepConfiguration` tree that references them by
    key. The tree is the execution plan; the map supplies the algorithms each
    :attr:`StepType.SINGLE` leaf invokes.

    Algorithms are registered via :meth:`add_algorithm`. The ``key`` argument
    is the same string that a SINGLE :class:`StepConfiguration` passes as its
    ``algorithm_config_key``. Schedule-wide parameter overrides are registered
    via :meth:`add_global_parameter`; step-scoped overrides on individual
    steps take precedence (see
    :meth:`StepConfiguration.add_override_parameter`).

    Attach a built schedule to a
    :class:`~daitum_configuration.ConfigurationBuilder` with
    :meth:`~daitum_configuration.ConfigurationBuilder.set_schedule_configuration`
    — mutually exclusive with
    :meth:`~daitum_configuration.ConfigurationBuilder.set_algorithm`.

    Example::

        from daitum_configuration import (
            GeneticAlgorithm,
            ScheduleConfiguration,
            StepConfiguration,
            StepType,
        )

        root = StepConfiguration(StepType.SINGLE, algorithm_config_key="ga")
        schedule = (
            ScheduleConfiguration(root)
            .add_algorithm("ga", GeneticAlgorithm())
            .add_global_parameter("seed", "42")
        )

    Args:
        schedule_root: Root step of the execution tree. Required.
    """

    def __init__(self, schedule_root: StepConfiguration):
        self.global_parameters: dict[str, str] | None = None

        self.algorithm_configurations: dict[str, Algorithm] | None = None
        self.schedule_root = schedule_root

    def add_algorithm(self, key: str, algorithm: Algorithm) -> "ScheduleConfiguration":
        """Register an :class:`Algorithm` under ``key``.

        ``key`` is the same string a SINGLE :class:`StepConfiguration` passes
        as its ``algorithm_config_key`` to invoke this algorithm. Every
        ``algorithm_config_key`` referenced anywhere in the schedule tree must
        resolve to a key registered here. Adding the same ``key`` twice
        replaces the previous algorithm.
        """
        if self.algorithm_configurations is None:
            self.algorithm_configurations = {}
        self.algorithm_configurations[key] = algorithm
        return self

    def add_global_parameter(self, key: str, value: str) -> "ScheduleConfiguration":
        """Add a parameter override applied across every step in the schedule.

        ``key`` is a parameter name and ``value`` is a serialised model value.
        Adding the same ``key`` twice replaces the previous value. Step-scoped
        overrides set via
        :meth:`StepConfiguration.add_override_parameter` take precedence over
        these globals for the steps on which they're set.
        """
        if self.global_parameters is None:
            self.global_parameters = {}
        self.global_parameters[key] = value
        return self
