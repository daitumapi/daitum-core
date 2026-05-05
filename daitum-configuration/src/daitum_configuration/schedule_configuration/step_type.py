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

""":class:`StepType` enum used by :class:`StepConfiguration`."""

from enum import Enum


class StepType(Enum):
    """Kind of node in a :class:`ScheduleConfiguration` execution tree.

    Values:
        PARALLEL: Run child steps concurrently.
        SEQUENCE: Run child steps one after another.
        SINGLE: Run a single algorithm referenced by key.
    """

    PARALLEL = "PARALLEL"
    SEQUENCE = "SEQUENCE"
    SINGLE = "SINGLE"
