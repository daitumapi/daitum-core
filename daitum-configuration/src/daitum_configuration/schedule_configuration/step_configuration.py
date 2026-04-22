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
This module defines the StepConfiguration class which represent the building blocks of
algorithm execution schedules.

The StepConfiguration class represents a single node in a schedule hierarchy, which can be
either a single algorithm execution or a container for other steps (parallel or sequential).
"""

from __future__ import annotations

from typing import Any

from typeguard import typechecked

from daitum_configuration.schedule_configuration.step_type import StepType


# pylint: disable=too-few-public-methods
@typechecked
class StepConfiguration:
    """
    Represents a configuration node in an algorithm execution schedule.

    Each StepConfiguration can be either:
        - A single algorithm execution (SINGLE type)
        - A container for parallel execution of steps (PARALLEL type)
        - A container for sequential execution of steps (SEQUENCE type)

    The class includes validation to ensure proper configuration based on the step type.

    Raises:
        ValueError: If the configuration is invalid for the specified step type.

    Notes:
        - _parameter_overrides: Not sure how does this work: can not be overwritten for now.
        - _step_performance_ratios: Not sure how does this work: can not be overwritten for now.
    """

    def __init__(
        self,
        step_type: StepType,
        steps: list[StepConfiguration] | None = None,
        algorithm_config_key: str | None = None,
    ):
        """
        Initializes a StepConfiguration with the given parameters.

        Args:
            step_type: The type of step to create (SINGLE, PARALLEL, or SEQUENCE).
            steps: Required for PARALLEL/SEQUENCE steps - the list of child steps.
                Must be None for SINGLE steps.
            algorithm_config_key: Required for SINGLE steps - the algorithm config key.
                Must be None for PARALLEL/SEQUENCE steps.

        Raises:
            ValueError: If the inputs are incompatible with the specified step type or
                if steps and step_performance_ratios have mismatched lengths.
        """

        if step_type == StepType.SINGLE:
            if algorithm_config_key is None or steps is not None:
                raise ValueError("Inputs are incompatible with the StepType.SINGLE.")
        elif algorithm_config_key is not None or steps is None:
            raise ValueError(
                "Inputs are incompatible with the StepType.PARALLEL or StepType.SEQUENCE."
            )

        # Not sure how does this work: can not be overwritten for now
        self._parameter_overrides: dict[str, str] | None = None
        self._step_performance_ratios: list[float] | None = None

        self._step_type = step_type
        self._steps: list[StepConfiguration] | None = None
        self._algorithm_config_key = algorithm_config_key

    def add_step(self, step_configuration: StepConfiguration) -> None:
        """
        Adds a step configuration to the current list of steps.

        This method appends the given `step_configuration` to the internal list of steps
        if the step type is not `StepType.SINGLE`. If the step type is `StepType.SINGLE`,
        adding additional steps is not allowed, and a `ValueError` will be raised.

        Args:
            step_configuration (StepConfiguration): The step configuration to add.

        Raises:
            ValueError: If the current step type is `StepType.SINGLE`.
        """
        if self._step_type == StepType.SINGLE:
            raise ValueError("Adding step is incompatible with the StepType.SINGLE.")
        if self._steps is None:
            self._steps = []
        self._steps.append(step_configuration)

    def to_dict(self) -> dict[str, Any]:
        """
        Converts the step configuration to a dictionary representation.

        Returns:

        - "type": The step type as a string value
        - "steps": List of child steps (None for SINGLE steps)
        - "stepPerformanceRatios": Performance ratios if provided
        - "parameterOverrides": Parameter overrides if provided
        - "algorithmConfigKey": Algorithm config key for SINGLE steps
        """
        return {
            "type": self._step_type.value,
            "steps": [step.to_dict() for step in self._steps] if self._steps else None,
            "stepPerformanceRatios": self._step_performance_ratios,
            "parameterOverrides": self._parameter_overrides,
            "algorithmConfigKey": self._algorithm_config_key,
        }
