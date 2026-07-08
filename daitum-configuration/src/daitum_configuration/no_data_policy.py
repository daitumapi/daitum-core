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

""":class:`NoDataPolicy` — controls whether a zero-row import fails the data source."""

from enum import Enum


class NoDataPolicy(Enum):
    """
    Whether an import that loads no rows should be treated as a failure.
    """

    ALLOW = "ALLOW"
    """No data loaded is acceptable; never a failure."""

    FAIL_IF_ALL_EMPTY = "FAIL_IF_ALL_EMPTY"
    """Fail only when every target sheet loaded zero rows."""

    FAIL_IF_ANY_SHEET_EMPTY = "FAIL_IF_ANY_SHEET_EMPTY"
    """Fail when any single target sheet loaded zero rows."""
