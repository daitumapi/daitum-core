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

from dataclasses import dataclass

from daitum_model import Calculation, Field, Parameter
from typeguard import typechecked

from daitum_ui._buildable import Buildable, json_type_info
from daitum_ui._data import ModelPermissionsCondition, ModelVariableCondition
from daitum_ui.base_view import BaseView
from daitum_ui.context_variable import ContextVariable
from daitum_ui.data import Condition
from daitum_ui.elements import get_model_variable


@dataclass
@typechecked
class ScrollSync(Buildable):
    """Controls whether child views within a ``CompositeView`` scroll in sync."""

    enabled: bool


@dataclass
@typechecked
class ViewConfig(Buildable):
    """
    Configuration for a child view within a ``CompositeView``.

    Wraps a view reference with element-level style overrides and optional
    hidden conditions.

    Attributes:
        element_styles: CSS-style overrides keyed by element identifier.
        view_id: The ID of the child view this config applies to.
        exclude_default_styling: If ``True``, the platform's default styles are suppressed.
    """

    element_styles: dict[str, str]
    view_id: str
    exclude_default_styling: bool = False

    def __post_init__(self):
        self._hidden_conditions: list[Condition] | None = None

    def add_permission_hidden_condition(self, hide_from_base_user: bool):
        """
        Adds a ModelPermissionsCondition to hide the view based on user permissions.

        Args:
            hide_from_base_user (bool): If True, the view is hidden from base users and
                displayed to advanced users. If False, the opposite is true.
        """
        if self._hidden_conditions is None:
            self._hidden_conditions = []

        condition = ModelPermissionsCondition(is_advanced_user=not hide_from_base_user)
        self._hidden_conditions.append(condition)

    def add_variable_hidden_condition(
        self,
        condition_variable: Field | Parameter | Calculation | ContextVariable,
        negate: bool = False,
    ):
        """
        Adds a conditional visibility rule that hides the view when the given
        variable evaluates to True (or False, when negated).

        Args:
            condition_variable (Field | Parameter | Calculation | ContextVariable):
                The input representing the boolean condition that determines whether
                the view should be hidden.
            negate (bool):
                If True, the logical result of the condition is inverted.
                For example, a condition that normally hides when True will instead
                hide when False.
        """
        if self._hidden_conditions is None:
            self._hidden_conditions = []

        model_variable = get_model_variable(condition_variable)

        condition = ModelVariableCondition(model_variable=model_variable, negate=negate)
        self._hidden_conditions.append(condition)

    @property
    def hidden_conditions(self):
        """The serialised hidden conditions list, or ``None`` if none have been added."""
        return (
            [condition.build() for condition in self._hidden_conditions]
            if self._hidden_conditions is not None
            else None
        )

    def build(self):
        """Serialise this config, injecting the ``hiddenConditions`` key."""
        view_definition = super().build()
        view_definition["hiddenConditions"] = self.hidden_conditions
        return view_definition


@json_type_info("composite")
@typechecked
class CompositeView(BaseView):
    """
    A view that contains multiple child views arranged side-by-side or in a configurable layout.

    Each child is represented by a ``ViewConfig`` that pairs a view reference with its
    element-level styles and hidden conditions.
    """

    def __init__(
        self,
        display_name: str | None = None,
        hidden: bool = False,
        parent_styles: dict[str, str] | None = None,
        scroll_sync_enabled: bool = False,
    ):
        """
        Args:
            display_name: Optional display name for the composite view.
            hidden: If ``True``, the view is not visible in the UI.
            parent_styles: CSS-style overrides for the composite container element.
            scroll_sync_enabled: If ``True``, child views scroll together.
        """
        super().__init__(hidden)
        if display_name is not None:
            self._display_name = display_name
        self.scroll_sync = ScrollSync(scroll_sync_enabled)
        self.parent_styles: dict[str, str] = parent_styles if parent_styles else {}
        self.children: list[ViewConfig] = []
