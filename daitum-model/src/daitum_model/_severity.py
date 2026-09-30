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
Validation severity levels and their ranking.

A leaf module: it imports nothing from the package, so anything may depend on it. That is
the point -- :class:`Severity` is needed by modules on both sides of
:mod:`daitum_model.model` in the import graph, and keeping it here lets
:mod:`daitum_model.validator` depend on ``model`` at runtime rather than through a
forward reference.

:class:`Severity` is public API, re-exported from :mod:`daitum_model` and from
:mod:`daitum_model.validator`; import it from either rather than from here.
"""

from enum import Enum


class Severity(Enum):
    """Enumeration of validation severity levels."""

    INFO = "Info"
    WARNING = "Warning"
    ERROR = "Error"
    CRITICAL = "Critical"


#: Ascending order of seriousness, so the highest rank among a model's failing validators is
#: the one that describes its overall state.
SEVERITY_RANK = {
    Severity.INFO: 1,
    Severity.WARNING: 2,
    Severity.ERROR: 3,
    Severity.CRITICAL: 4,
}
