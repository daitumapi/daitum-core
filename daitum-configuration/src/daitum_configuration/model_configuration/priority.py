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
This module defines an enumeration for priority levels using Python's Enum class.
It is intended to standardize the use of priority labels across the application,
such as LOW, MEDIUM, and HIGH.

Classes:
    - Priority: An enumeration representing three levels of task or item priority.
"""

from enum import Enum


class Priority(Enum):
    """
    Enum representing the priority levels.
    """

    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
