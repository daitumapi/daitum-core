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

    A :class:`StepConfiguration`'s type determines whether it executes an
    algorithm (leaf) or composes child steps (container).

    SINGLE
        Leaf node — runs the algorithm registered under ``algorithm_config_key``
        against the current best solution. Carries no children.
    SEQUENCE
        Container — runs child steps one after another, each seeded with the
        previous step's best solution.
    PARALLEL
        Container — runs child steps concurrently from the same seed and merges
        their results.
    """

    PARALLEL = "PARALLEL"
    SEQUENCE = "SEQUENCE"
    SINGLE = "SINGLE"
