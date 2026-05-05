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

""":class:`DataFilterType` discriminator enum for :class:`DataFilter`."""

from enum import Enum


class DataFilterType(Enum):
    """Identifies the kind of row filter applied by :class:`DataFilter` subclasses.

    Values:
        EQUALITY: Match rows whose value equals a source key.
        INEQUALITY: Match rows whose value falls within a numeric range.
        SET: Match rows whose value is in a set of source keys.
        WILDCARD: Match rows whose value matches a glob pattern.
        REGEX: Match rows whose value matches a regular expression.
    """

    EQUALITY = "equality"
    INEQUALITY = "inequality"
    SET = "set"
    WILDCARD = "wildcard"
    REGEX = "regex"
