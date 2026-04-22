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
This module defines the ReportData class, representing metadata required
for exporting reports, including sheet requirements and calculation flags.
"""

from typeguard import typechecked


# pylint: disable=too-few-public-methods
@typechecked
class ReportData:
    """
    Data model representing report-related metadata.
    """

    def __init__(
        self,
        required_sheets: set[str] | None = None,
        requires_monte_carlo: bool = False,
        requires_scenario_comparison: bool = False,
    ):
        """
        Initialize ReportData instance.

        Args:
            required_sheets: A set of required sheet names. Defaults to empty set.
            requires_monte_carlo: Indicates if Monte Carlo simulation is required.
            requires_scenario_comparison: Indicates if scenario comparison is required.
        """
        self._required_sheets = required_sheets if required_sheets is not None else set()
        self._requires_monte_carlo = requires_monte_carlo
        self._requires_scenario_comparison = requires_scenario_comparison

    def to_dict(self) -> dict:
        """
        Serializes the ReportData instance to a dictionary.

        Returns:
            dict: A dictionary representation of the ReportData instance.
        """
        return {
            "requiredSheets": list(self._required_sheets),
            "requiresMonteCarlo": self._requires_monte_carlo,
            "requiresScenarioComparison": self._requires_scenario_comparison,
        }
