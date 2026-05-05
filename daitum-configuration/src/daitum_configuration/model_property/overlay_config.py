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

""":class:`OverlayConfig` — toggles for spreadsheet result overlays."""

from typeguard import typechecked

from daitum_configuration._buildable import Buildable


# pylint: disable=too-few-public-methods,too-many-positional-arguments
@typechecked
class OverlayConfig(Buildable):
    """
    Toggles for spreadsheet overlays that surface solver state in the UI.

    Args:
        show_decision_overlay: Highlight cells driven by decision variables.
        show_lock_overlay: Highlight cells locked at their seed value.
        show_objective_overlay: Highlight cells contributing to objectives.
        show_constraint_overlay: Highlight cells contributing to constraints.
    """

    def __init__(
        self,
        show_decision_overlay: bool = False,
        show_lock_overlay: bool = False,
        show_objective_overlay: bool = False,
        show_constraint_overlay: bool = False,
    ):
        self.show_decision_overlay = show_decision_overlay
        self.show_lock_overlay = show_lock_overlay
        self.show_objective_overlay = show_objective_overlay
        self.show_constraint_overlay = show_constraint_overlay
