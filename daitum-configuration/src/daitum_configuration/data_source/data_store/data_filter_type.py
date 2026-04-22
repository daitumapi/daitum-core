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
This module defines the DataFilterType enumeration, which represents the types of
data filtering operations that can be applied to a dataset. These types include
equality, inequality, set membership, wildcard patterns, and regular expressions.
"""

from enum import Enum


class DataFilterType(Enum):
    """
    Enumeration of supported data filter types.

    Attributes:
        EQUALITY: Filters data by exact match.
        INEQUALITY: Filters data by non-equality.
        SET: Filters data based on membership in a set of values.
        WILDCARD: Filters data using wildcard patterns (e.g., '*' or '?').
        REGEX: Filters data using regular expressions.
    """

    EQUALITY = "equality"
    INEQUALITY = "inequality"
    SET = "set"
    WILDCARD = "wildcard"
    REGEX = "regex"
