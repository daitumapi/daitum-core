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

""":class:`StepConfiguration` — one node in a :class:`ScheduleConfiguration` tree."""

from __future__ import annotations

from typeguard import typechecked

from daitum_configuration._buildable import Buildable
from daitum_configuration.schedule_configuration.step_type import StepType


# pylint: disable=too-few-public-methods
@typechecked
class StepConfiguration(Buildable):
    """
    One node in a :class:`ScheduleConfiguration` execution tree.

    A node is either a leaf (:attr:`StepType.SINGLE` referencing an algorithm
    by key) or a container (:attr:`StepType.PARALLEL` or
    :attr:`StepType.SEQUENCE`) holding child steps.

    Args:
        step_type: :class:`StepType` of this node.
        steps: Child steps. Required for container types, forbidden for SINGLE.
        algorithm_config_key: Key into the schedule's algorithm map. Required
            for SINGLE, forbidden for container types.

    Raises:
        ValueError: If ``steps`` and ``algorithm_config_key`` do not match
            ``step_type``.
    """

    def __init__(
        self,
        step_type: StepType,
        steps: list[StepConfiguration] | None = None,
        algorithm_config_key: str | None = None,
    ):
        if step_type == StepType.SINGLE:
            if algorithm_config_key is None or steps is not None:
                raise ValueError("Inputs are incompatible with the StepType.SINGLE.")
        elif algorithm_config_key is not None or steps is None:
            raise ValueError(
                "Inputs are incompatible with the StepType.PARALLEL or StepType.SEQUENCE."
            )

        self.step_performance_ratios: list[float] | None = None
        self.parameter_overrides: dict[str, str] | None = None

        self.type = step_type
        self.steps: list[StepConfiguration] | None = None
        self.algorithm_config_key = algorithm_config_key

    def add_step(self, step_configuration: StepConfiguration) -> StepConfiguration:
        """Append a child step to this container.

        Raises:
            ValueError: If this node is :attr:`StepType.SINGLE`.
        """
        if self.type == StepType.SINGLE:
            raise ValueError("Adding step is incompatible with the StepType.SINGLE.")
        if self.steps is None:
            self.steps = []
        self.steps.append(step_configuration)
        return self
