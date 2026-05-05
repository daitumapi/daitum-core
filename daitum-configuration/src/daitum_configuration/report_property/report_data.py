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

""":class:`ReportData` — sheet/feature prerequisites for a :class:`ReportProperty`."""

from typing import Any

from typeguard import typechecked

from daitum_configuration._buildable import Buildable


# pylint: disable=too-few-public-methods
@typechecked
class ReportData(Buildable):
    """
    Sheet and feature prerequisites for one report.

    Args:
        required_sheets: Sheet names that must be present for the report to run.
        requires_monte_carlo: Whether the report depends on Monte Carlo output.
        requires_scenario_comparison: Whether the report depends on scenario
            comparison output.
    """

    def __init__(
        self,
        required_sheets: set[str] | None = None,
        requires_monte_carlo: bool = False,
        requires_scenario_comparison: bool = False,
    ):
        self._required_sheets = required_sheets if required_sheets is not None else set()
        self.requires_monte_carlo = requires_monte_carlo
        self.requires_scenario_comparison = requires_scenario_comparison

    def build(self) -> dict[str, Any]:
        """Serialise to a JSON-compatible dict (the required-sheets set becomes a list)."""
        result = {"requiredSheets": list(self._required_sheets)}
        result.update(super().build())
        return result
