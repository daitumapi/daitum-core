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

""":class:`BatchDataSourceType` enum used to mark a step's parallelism stage."""

from enum import Enum


class BatchDataSourceType(Enum):
    """Position of a batched-data-source step in a parallel block."""

    START_PARALLEL = "START_PARALLEL"
    """First step of a parallel block."""

    NEXT_PARALLEL = "NEXT_PARALLEL"
    """Subsequent step inside a parallel block."""

    END_PARALLEL = "END_PARALLEL"
    """Final step of a parallel block."""

    NONE_PARALLEL = "NONE_PARALLEL"
    """Sequential step (no parallel block)."""
