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
This module defines the OverlayConfig class, representing configuration options
for spreadsheet overlays including decision, lock, objective, and constraint overlays.
"""

from typeguard import typechecked


# pylint: disable=too-few-public-methods,too-many-positional-arguments
@typechecked
class OverlayConfig:
    """
    Data model representing spreadsheet overlay configuration options.
    """

    def __init__(
        self,
        show_decision_overlay: bool = False,
        show_lock_overlay: bool = False,
        show_objective_overlay: bool = False,
        show_constraint_overlay: bool = False,
    ):
        """
        Initialize OverlayConfig instance with values.
        """
        self._show_decision_overlay = show_decision_overlay
        self._show_lock_overlay = show_lock_overlay
        self._show_objective_overlay = show_objective_overlay
        self._show_constraint_overlay = show_constraint_overlay

    def to_dict(self) -> dict:
        """
        Serializes the OverlayConfig instance to a dictionary.

        Returns:
            dict: A dictionary representation of the OverlayConfig instance.
        """
        return {
            "showDecisionOverlay": self._show_decision_overlay,
            "showLockOverlay": self._show_lock_overlay,
            "showObjectiveOverlay": self._show_objective_overlay,
            "showConstraintOverlay": self._show_constraint_overlay,
        }
