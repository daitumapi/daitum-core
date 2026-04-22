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
This module defines the BatchDataSourceType enumeration, which is used to represent
different stages of parallel batch data processing in a data pipeline. These stages
help control and identify how data batches are handled across parallel tasks.
"""

from enum import Enum


class BatchDataSourceType(Enum):
    """
    Enumeration for the type of data source in a batch processing pipeline,
    particularly in scenarios involving parallel processing.

    Attributes:
        START_PARALLEL: Marks the beginning of a parallel batch process.
        NEXT_PARALLEL: Represents subsequent steps in the parallel batch process.
        END_PARALLEL: Marks the end of a parallel batch process.
        NONE_PARALLEL: Indicates no parallel processing is applied.
    """

    START_PARALLEL = "START_PARALLEL"
    NEXT_PARALLEL = "NEXT_PARALLEL"
    END_PARALLEL = "END_PARALLEL"
    NONE_PARALLEL = "NONE_PARALLEL"
