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
Navigation item system for organizing and structuring UI views.

This module provides classes for creating navigation menus and organizing views
into hierarchical structures. Navigation items can link to individual views or
group multiple views together with customizable appearance and behavior.

Main Components
---------------

**Base Class:**
    - NavItem: Abstract base class for all navigation items with color styling

**Navigation Item Types:**
    - SingleViewNavItem: Links directly to a single view
    - GroupViewNavItem: Collapsible group containing multiple views

Navigation Item Types
---------------------

**SingleViewNavItem:**
    Links directly to one view. When clicked, navigates to that view.

    - Simple one-to-one view mapping
    - Customizable colors for active/inactive states
    - Ideal for standalone views or frequently accessed pages

**GroupViewNavItem:**
    Organizes multiple views into a collapsible group.

    - Contains multiple child views
    - Can auto-collapse when navigating away
    - Supports conditional visibility
    - Enforces unique group names across the application
    - Useful for organizing related views (e.g., "Reports", "Settings")

Color Customization
-------------------
All navigation items support three color properties:

- **background_color**: Default background color when inactive
- **active_color**: Background color when selected/active
- **font_color**: Text color for the navigation item label

All colors accept CSS-compatible strings (hex codes, color names, rgb/rgba).

Conditional Visibility
----------------------
GroupViewNavItem supports conditional visibility through:

- **hidden**: Static boolean to hide the entire group
- **hidden_conditions**: List of Condition objects that dynamically control visibility

When any hidden condition evaluates to True, the group is hidden from navigation.

Auto-Collapse Behavior
----------------------
Groups can automatically collapse when navigating away:

- **auto_collapse=True** (default): Group collapses when user navigates elsewhere
- **auto_collapse=False**: Group remains expanded until manually collapsed

This helps maintain a clean navigation structure in UIs with many views.

Examples
--------
Creating a single view navigation item::

    from daitum_ui import UiBuilder
    from daitum_model import Table

    # Create builder and view
    builder = UiBuilder()
    sales_table = Table("sales")
    sales_view = builder.add_table_view(
        table=sales_table,
        display_name="Sales Report"
    )

    # Create navigation item for the view
    sales_nav = builder.add_navigation_item(
        view=sales_view,
        background_color="#ffffff",
        active_color="#1976d2",
        font_color="#333333"
    )

Creating a navigation group::

    # Create views
    sales_view = builder.add_table_view(...)
    inventory_view = builder.add_table_view(...)
    analytics_view = builder.add_chart_view(...)

    # Create a collapsible group
    reports_group = builder.add_navigation_group(
        name="Reports",
        auto_collapse=True,
        background_color="#f5f5f5",
        active_color="#2196f3",
        font_color="#212121"
    )

    # Add views to the group
    reports_group.add_view(sales_view)
    reports_group.add_view(inventory_view)
    reports_group.add_view(analytics_view)

Conditional visibility for groups::

    from daitum_ui.data import Condition

    # Create views
    user_management_view = builder.add_table_view(...)
    system_settings_view = builder.add_form_view(...)

    # Create admin-only navigation group
    admin_group = builder.add_navigation_group(
        name="Administration",
        auto_collapse=True
    )

    # Add views
    admin_group.add_view(user_management_view)
    admin_group.add_view(system_settings_view)

    # Add condition to hide from non-admins
    is_not_admin = Condition(...)  # Define your condition
    admin_group.add_hidden_condition(is_not_admin)

Building a complete navigation structure::

    # Create builder
    builder = UiBuilder()

    # Create views
    dashboard_view = builder.add_named_value_view(display_name="Dashboard")
    customers_view = builder.add_table_view(...)
    products_view = builder.add_table_view(...)
    orders_view = builder.add_table_view(...)
    sales_report_view = builder.add_chart_view(...)
    inventory_report_view = builder.add_chart_view(...)
    user_settings_view = builder.add_form_view(...)
    app_settings_view = builder.add_form_view(...)

    # Top-level view
    dashboard_nav = builder.add_navigation_item(
        view=dashboard_view,
        active_color="#4caf50"
    )

    # Grouped views
    data_group = builder.add_navigation_group(name="Data Management")
    data_group.add_view(customers_view)
    data_group.add_view(products_view)
    data_group.add_view(orders_view)

    reports_group = builder.add_navigation_group(name="Reports")
    reports_group.add_view(sales_report_view)
    reports_group.add_view(inventory_report_view)

    settings_group = builder.add_navigation_group(
        name="Settings",
        auto_collapse=False
    )
    settings_group.add_view(user_settings_view)
    settings_group.add_view(app_settings_view)

Creating a hidden group::

    # Create views
    debug_console_view = builder.add_form_view(...)
    api_explorer_view = builder.add_table_view(...)

    # Group that's hidden by default (e.g., for development)
    debug_group = builder.add_navigation_group(
        name="Debug Tools",
        hidden=True  # Statically hidden
    )
    debug_group.add_view(debug_console_view)
    debug_group.add_view(api_explorer_view)

Styling navigation with custom colors::

    # Create views
    advanced_analytics_view = builder.add_chart_view(...)
    export_tools_view = builder.add_form_view(...)

    # Create a visually distinct navigation group
    premium_group = builder.add_navigation_group(
        name="Premium Features",
        background_color="#ffd700",  # Gold background
        active_color="#ff6f00",      # Orange when active
        font_color="#000000"         # Black text
    )
    premium_group.add_view(advanced_analytics_view)
    premium_group.add_view(export_tools_view)

Mixed navigation structure::

    # Create views
    home_view = builder.add_form_view(display_name="Home")
    notifications_view = builder.add_table_view(...)
    operations_view1 = builder.add_table_view(...)
    operations_view2 = builder.add_table_view(...)
    analytics_view1 = builder.add_chart_view(...)
    analytics_view2 = builder.add_chart_view(...)

    # Combination of single items and groups
    # Top-level standalone view
    builder.add_navigation_item(view=home_view, active_color="#2196f3")

    # Group for related views
    operations_group = builder.add_navigation_group(name="Operations")
    operations_group.add_view(operations_view1)
    operations_group.add_view(operations_view2)

    # Another standalone view
    builder.add_navigation_item(view=notifications_view, active_color="#ff9800")

    # Another group
    analytics_group = builder.add_navigation_group(name="Analytics")
    analytics_group.add_view(analytics_view1)
    analytics_group.add_view(analytics_view2)

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
