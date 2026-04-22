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
This module defines the ScheduleConfiguration class which represents a configuration
for scheduling algorithms and steps in a computational workflow.

The ScheduleConfiguration class serves as a container for algorithm configurations
and a root step configuration that defines the execution schedule. It provides methods
to convert the configuration to a dictionary format.
"""

from typing import Any

from typeguard import typechecked

from daitum_configuration.algorithm_configuration.algorithm import Algorithm
from daitum_configuration.schedule_configuration.step_configuration import StepConfiguration


# pylint: disable=too-few-public-methods
@typechecked
class ScheduleConfiguration:
    """
    Represents a configuration for scheduling algorithms and execution steps.

    This class holds algorithm configurations and a root step configuration that
    defines the execution schedule hierarchy. It can be converted to a dictionary
    representation for serialization.

    Notes:
        - _global_parameters: Not sure how does this work: can not be overwritten for now

    """

    def __init__(
        self,
        algorithm_configurations: dict[str, Algorithm] | None = None,
        schedule_root: StepConfiguration | None = None,
    ):
        """
        Initializes a ScheduleConfiguration instance.

        Args:
            algorithm_configurations: Optional dictionary of algorithm configurations.
                Keys are algorithm keys and values are Algorithm instances.
                Defaults to an empty dictionary.
            schedule_root: Optional root step configuration that defines the
                execution schedule hierarchy. Defaults to None.
        """
        # Not sure how does this work: can not be overwritten for now
        self._global_parameters: dict[str, str] | None = None

        self._algorithm_configurations = algorithm_configurations
        self._schedule_root = schedule_root

        self._algorithm_configurations_string: dict[str, dict[str, Any]] | None = None
        if algorithm_configurations is not None:
            self._algorithm_configurations_string = {}
            for key, algorithm in algorithm_configurations.items():
                self._algorithm_configurations_string[key] = algorithm.to_dict()

    def to_dict(self) -> dict[str, Any]:
        """
        Converts the schedule configuration to a dictionary representation.

        The resulting dictionary can be used for serialization.

        Returns:

        - "algorithmConfigurations": The algorithm configurations dictionary
        - "globalParameters": The global parameters (currently always None)
        - "scheduleRoot": Dictionary representation of the root step configuration,
          or None if no root step is configured
        """
        return {
            "algorithmConfigurations": self._algorithm_configurations_string,
            "globalParameters": self._global_parameters,
            "scheduleRoot": self._schedule_root.to_dict() if self._schedule_root else None,
        }
