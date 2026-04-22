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
This module defines the StepType enumeration for algorithm scheduling configurations.

The StepType enum specifies the different types of steps that can be used when building
an execution schedule for algorithms. These step types form the building blocks for
creating complex execution workflows that can include parallel processing, sequential
execution, or single algorithm runs.

The available step types are:
    - PARALLEL: For executing multiple steps concurrently
    - SEQUENCE: For executing multiple steps in a defined order
    - SINGLE: For executing a single algorithm

This enum is typically used in conjunction with the StepConfiguration class to create
complete schedule definitions.
"""

from enum import Enum


class StepType(Enum):
    """
    Enumeration of different possible elements in an algorithm schedule.

    This defines the types of steps that can be used to build an execution schedule.

    Values:
        - PARALLEL: Step contains a number of other steps to be run alongside each other
          in parallel.
        - SEQUENCE: Step contains a number of other steps to be run in sequence.
        - SINGLE: Step is a single algorithm execution.
    """

    PARALLEL = "PARALLEL"
    SEQUENCE = "SEQUENCE"
    SINGLE = "SINGLE"
