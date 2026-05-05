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

from typing import Any

from typeguard import typechecked

from daitum_configuration._buildable import Buildable
from daitum_configuration.algorithm_configuration.algorithm import Algorithm
from daitum_configuration.schedule_configuration.step_configuration import StepConfiguration


# pylint: disable=too-few-public-methods
@typechecked
class ScheduleConfiguration(Buildable):
    """
    Multi-step optimisation schedule.

    Pairs a map of named :class:`~daitum_configuration.algorithm_configuration.algorithm.Algorithm`
    instances with a :class:`StepConfiguration` tree that references them by key.

    Args:
        algorithm_configurations: Map from algorithm key (referenced by
            :class:`StepConfiguration`) to :class:`Algorithm`.
        schedule_root: Root step of the execution tree.
    """

    def __init__(
        self,
        algorithm_configurations: dict[str, Algorithm] | None = None,
        schedule_root: StepConfiguration | None = None,
    ):
        self.global_parameters: dict[str, str] | None = None

        self.algorithm_configurations: dict[str, Algorithm] | None = algorithm_configurations
        self.schedule_root = schedule_root

    def set_algorithm_configurations(
        self, algorithm_configurations: dict[str, Algorithm]
    ) -> "ScheduleConfiguration":
        """Set the key → :class:`Algorithm` map used by step references."""
        self.algorithm_configurations = algorithm_configurations
        return self

    def set_schedule_root(self, schedule_root: StepConfiguration) -> "ScheduleConfiguration":
        """Set the root :class:`StepConfiguration` of the execution tree."""
        self.schedule_root = schedule_root
        return self

    def build(self) -> dict[str, Any]:
        """Serialise to a JSON-compatible dict."""
        return super().build()
