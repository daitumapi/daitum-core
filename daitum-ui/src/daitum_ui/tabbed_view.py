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
Tabbed view components for the UI Generator framework.

This module provides the TabbedView class, which enables organizing multiple views
into a tabbed interface. Tabbed views are container components that allow users to
switch between different content sections using tab navigation, improving usability
and screen space efficiency.

Tabbed views create organized, multi-section interfaces where each tab contains a
complete view (table, chart, form, etc.). Only one tab's content is visible at a
time, with users clicking tab headers to switch between sections.

Key features:
    Standard mode:
        - Visible tab headers for manual navigation
        - Click-based tab switching
        - Visual indication of active tab

    Headless mode:
        - Tab headers hidden
        - Programmatic control via context variable
        - Ideal for wizard-style flows or external navigation

Classes:
    - TabDefinition: Configuration for a single tab within a tabbed view
    - TabbedView: Container view organizing multiple views as tabs

Example:
    >>> # Create child views for tabs
    >>> builder = UiBuilder()
    >>> overview_table = builder.add_table_view(
    ...     table=Table("overview_data"),
    ...     display_name="Overview"
    ... )
    >>> details_chart = builder.add_chart_view(
    ...     chart_title="Details",
    ...     primary_series=series1,
    ...     secondary_series=series2,
    ...     chart_type=ChartType.BAR,
    ...     table=Table("details_data")
    ... )
    >>> history_table = builder.add_table_view(
    ...     table=Table("history_data"),
    ...     display_name="History"
    ... )
    >>>
    >>> # Create tabbed view
    >>> tabbed_view = builder.add_tabbed_view(
    ...     display_name="Customer Information",
    ...     use_full_width_tabs=True,
    ...     tab_padding="10px"
    ... )
    >>>
    >>> # Add tabs
    >>> tabbed_view.add_tab(overview_table, tab_name="Overview")
    >>> tabbed_view.add_tab(details_chart, tab_name="Analytics")
    >>> tabbed_view.add_tab(history_table, tab_name="History")
    >>>
    >>> # Example: Headless mode with programmatic control
    >>> active_tab_var = builder.add_context_variable(
    ...     id="active_tab",
    ...     type=CVType.INTEGER,
    ...     default_value=0
    ... )
    >>> wizard_view = builder.add_tabbed_view(
    ...     display_name="Setup Wizard",
    ...     headless_context_variable=active_tab_var
    ... )
    >>> wizard_view.add_tab(step1_form, tab_name="Step 1")
    >>> wizard_view.add_tab(step2_form, tab_name="Step 2")
    >>> wizard_view.add_tab(step3_form, tab_name="Step 3")
"""

from dataclasses import dataclass

from typeguard import typechecked

from daitum_ui._buildable import Buildable, json_type_info
from daitum_ui.base_view import BaseView
from daitum_ui.context_variable import ContextVariable


@dataclass
@typechecked
class TabDefinition(Buildable):
    """
    Represents a single tab within a TabbedView.

    Attributes:
        view_id:
            Identifier of the view to render when this tab is selected.
        display_name:
            Optional text label to show on the tab header.
    """

    view_id: str
    display_name: str | None = None


@typechecked
@json_type_info("tabbed")
class TabbedView(BaseView):
    """
    A container view that organises views into multiple tabs.

    Attributes:
        use_full_width_tabs:
            If True, tabs stretch across the full width of the container.
        headless_mode:
            If True, suppresses the tab headers and renders only the active
            tab content. Intended for views that are controlled externally.
        headless_context_variable_id:
            Name of the context variable used to determine which tab is active
            when headless mode is enabled.
        tab_padding:
            Controls the padding around individual tab headers. This does not
            affect the content within each tab.
    """

    def __init__(
        self,
        display_name: str | None = None,
        hidden: bool = False,
        use_full_width_tabs: bool = False,
        headless_context_variable: ContextVariable | None = None,
        tab_padding: str | None = None,
    ):
        # Initialise BaseView fields
        super().__init__(hidden)
        if display_name is not None:
            self._display_name = display_name
        self.use_full_width_tabs = use_full_width_tabs

        self.headless_mode = headless_context_variable is not None
        self.headless_context_variable_id = None
        if self.headless_mode and headless_context_variable:
            self.headless_context_variable_id = headless_context_variable.id

        self.tab_padding = tab_padding

        self.tabs: list[TabDefinition] = []

    def add_tab(self, view: BaseView, tab_name: str | None = None):
        """
        Adds a new tab to the TabbedView.

        Args:
            view:
                Identifier of the child view rendered when this tab is selected.
            tab_name:
                Optional label displayed on the tab header.
        """
        tab = TabDefinition(view.id, tab_name)
        self.tabs.append(tab)
