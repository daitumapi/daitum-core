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
Navigation item system for organising and structuring UI views.

Navigation items link to individual views or group multiple views together into
collapsible sections, with customisable colours and conditional visibility.
``SingleViewNavItem`` targets one view; ``GroupViewNavItem`` holds several and
can auto-collapse or be hidden by static flag or condition.

Example:
    >>> from daitum_ui import UiBuilder
    >>> from daitum_model import Table
    >>> builder = UiBuilder()
    >>> sales_view = builder.add_table_view(
    ...     table=Table("sales"), display_name="Sales Report"
    ... )
    >>> sales_nav = builder.add_navigation_item(
    ...     view=sales_view, active_color="#1976d2"
    ... )
"""

from abc import ABC
from dataclasses import dataclass
from typing import ClassVar

from typeguard import typechecked

from daitum_ui._buildable import Buildable, json_type_info
from daitum_ui.base_view import BaseView
from daitum_ui.data import Condition


@dataclass
@typechecked
class NavItem(ABC, Buildable):
    """
    Base class representing a navigation item within the user interface.

    Attributes:
        background_color:
            The CSS-compatible background colour to use for the navigation item
            in its default (inactive) state.
        active_color:
            The CSS-compatible colour to display when the navigation item is in
            an active or selected state.
        font_color:
            The CSS-compatible font colour used to render the text of the
            navigation item.
    """

    background_color: str | None = None
    active_color: str | None = None
    font_color: str | None = None


@typechecked
@json_type_info("view")
class SingleViewNavItem(NavItem):
    """
    A navigation item that links directly to a single view.

    Attributes:
        view:
            The view instance that this navigation item should activate or
            display when selected.
    """

    def __init__(
        self,
        view: BaseView,
    ):
        super().__init__()
        self.view = view.id

    def set_background_colour(self, colour: str) -> "SingleViewNavItem":
        """Sets the background colour for this navigation item."""
        self.background_color = colour
        return self

    def set_active_colour(self, colour: str) -> "SingleViewNavItem":
        """Sets the active state colour for this navigation item."""
        self.active_color = colour
        return self

    def set_font_colour(self, colour: str) -> "SingleViewNavItem":
        """Sets the font colour for this navigation item."""
        self.font_color = colour
        return self


@typechecked
@json_type_info("group")
class GroupViewNavItem(NavItem):
    """
    A navigation item representing a collapsible group of views.

    Attributes:
        name:
            A unique display name for the group.
        auto_collapse:
            If True, the group will automatically collapse when the user
            navigates to a different view or group.
        views:
            A list of view names to include in this group, in display order.
        hidden:
            Whether the entire group should be hidden in the UI.
        hidden_conditions:
            A list of conditions under which the group should be hidden.

    Raises:
        ValueError: if name given is not unique
    """

    _registry: ClassVar[set[str]] = set()

    def __init__(
        self,
        name: str,
        auto_collapse: bool = True,
        hidden: bool = False,
    ):
        super().__init__()

        if name in GroupViewNavItem._registry:
            raise ValueError(f"Duplicate group name: '{name}'")

        GroupViewNavItem._registry.add(name)

        self.name = name
        self.auto_collapse = auto_collapse
        self.hidden = hidden

        self.views: list[str] = []
        self.hidden_conditions: list[Condition] | None = None

    def set_background_colour(self, colour: str) -> "GroupViewNavItem":
        """Sets the background colour for this navigation group."""
        self.background_color = colour
        return self

    def set_active_colour(self, colour: str) -> "GroupViewNavItem":
        """Sets the active state colour for this navigation group."""
        self.active_color = colour
        return self

    def set_font_colour(self, colour: str) -> "GroupViewNavItem":
        """Sets the font colour for this navigation group."""
        self.font_color = colour
        return self

    def add_view(self, view: BaseView):
        """
        Adds a view into this navigation group.

        Parameters:
            view:
                The `BaseView` instance to include in this group.
        """
        view._navigation_group = self.name
        self.views.append(view.id)

    def add_hidden_condition(self, condition: Condition):
        """
        Registers a visibility condition that determines when this navigation
        group should be hidden.

        Parameters:
            condition:
                A `Condition` instance defining the logical rule that triggers
                the group to be hidden. The condition is appended to the
                `hidden_conditions` list.
        """
        if self.hidden_conditions is None:
            self.hidden_conditions = []
        self.hidden_conditions.append(condition)
