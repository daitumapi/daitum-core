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
Base view components for the UI Generator framework.

This module provides the foundational classes for building user interface views.
It defines the abstract base class that all specific view types (tables, charts,
forms, etc.) inherit from, as well as common UI components like action bars.

The BaseView class establishes the common interface and functionality shared across
all views, including:
    - View identification and display properties
    - Title configuration with styling and positioning
    - Visibility control with conditional hiding
    - Action bars for interactive elements
    - Filter integration

All concrete view implementations (TableView, ChartView, FormView, etc.) extend
BaseView to inherit this common functionality while adding their specific features.

Classes:
    - ActionBar: A horizontal container for interactive UI elements.
    - BaseView: Abstract base class for all view definitions.
"""

import random
import string
from abc import ABC
from dataclasses import dataclass, field

from daitum_model import Calculation, Field, Parameter
from typeguard import typechecked

from ._buildable import Buildable
from ._data import ModelPermissionsCondition, ModelVariableCondition
from .context_variable import ContextVariable
from .data import Condition
from .elements import Element, get_model_variable
from .styles import BaseStyle, Position, Title


@dataclass
@typechecked
class ActionBar(Buildable):
    """
    A UI container that displays a horizontal bar of interactive elements
    such as buttons, sliders, or text components. The action bar is typically
    used for presenting user controls related to a specific view, section,
    or workflow.

    Attributes:
        items:
            The list of UI elements to display within the action bar,
            rendered in order. Each element may represent an action,
            control, or informational display.
    """

    items: list[Element] = field(default_factory=list)


@typechecked
class BaseView(ABC, Buildable):
    """
    Abstract base class for all view definitions. Handles common elements such as title.

    Args:
        display_name (Optional[str]): Optional name for display.
            Defaults to the ID of the underlying table.
        hidden (bool): If True, the view is not visible in the UI. Defaults to False
        navigation_group (Optional[str]): Stores the navigation group to which the
            TableView is added, if any.
        navigation_item (bool): Check if the TableView is added to a navigation item.

    Attributes:
        title (Optional[Title]): The title to be displayed for the view, including
            optional styling and position (above or below content). Set via
            ``set_title()``.
        action_bar_definition (Optional[ActionBar]): The action bar containing
            interactive UI elements for this view. Lazily instantiated when the
            first element is added via ``add_action_element()``.
        show_filter (Optional[str]): The name of the filter definition to display
            alongside this view. Set via ``set_show_filter()``.
        nav_view_id (Optional[str]): The ID of the associated navigation view, if
            this view is linked to a navigation item.
    """

    def __init__(
        self,
        hidden: bool = False,
        navigation_item: bool = False,
    ):
        self._id: str = "".join(random.choices(string.ascii_letters, k=16))
        self._display_name: str = ""
        self._hidden = hidden
        self._hidden_conditions: list[Condition] | None = None

        self._navigation_group: str | None = None
        self._navigation_item = navigation_item

        self._nav_view_id: str | None = None

        self.title: Title | None = None
        self.action_bar_definition: ActionBar | None = None
        self.show_filter: str | None = None

    def set_display_name(self, name: str) -> "BaseView":
        """Sets the display name for this view."""
        self._display_name = name
        return self

    def set_navigation_group(self, group: str) -> "BaseView":
        """Sets the navigation group this view belongs to."""
        self._navigation_group = group
        return self

    def set_title(
        self,
        value: str,
        style: BaseStyle | None = None,
        position: Position = Position.ABOVE_CONTENT,
    ):
        """
        Sets the view title with optional style and position.

        Args:
            value (str): The text value of the title.
            style (Optional[BaseStyle]): Optional styling to apply to the title.
            position (Position): Where to place the title (above or below content).
        """
        self.title = Title(value, style=style, position=position)

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

    def add_action_element(self, element: Element):
        """
        Adds a UI element to the action bar for this view or component.

        If the action bar has not yet been created, this method will
        instantiate it before adding the element.

        Args:
            element (Element):
                The UI element to add to the action bar.
        """
        if self.action_bar_definition is None:
            self.action_bar_definition = ActionBar()

        self.action_bar_definition.items.append(element)

    def set_show_filter(self, filter_name: str):
        """
        Sets the filter to be shown for this view.

        Args:
            filter_name (str):
                The filter definition to show. Its `filter_name` is used
                as the reference ID.
        """
        self.show_filter = filter_name

    @property
    def id(self):
        return self._id

    @property
    def display_name(self):
        return self._display_name

    @property
    def hidden(self):
        return self._hidden

    @property
    def hidden_conditions(self):
        return (
            [condition.build() for condition in self._hidden_conditions]
            if self._hidden_conditions is not None
            else None
        )

    def build(self):
        view_definition = super().build()
        return {
            "id": self.id,
            "displayName": self.display_name,
            "hidden": self.hidden,
            "hiddenConditions": self.hidden_conditions,
            "viewDefinition": view_definition,
        }
