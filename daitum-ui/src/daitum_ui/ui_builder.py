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
UI Builder module for constructing complete user interface definitions.

This module provides the UiBuilder class, which serves as the central orchestrator
for creating and managing all aspects of a user interface. It offers a fluent,
builder-pattern API for constructing complex UIs through factory methods that
create and register various components.

The builder pattern allows for declarative UI construction where components are
added incrementally and then compiled into a final model definition via the
build() method.

Classes:
    - UiBuilder: Central builder class for UI construction

Example:
    >>> # Initialize builder
    >>> builder = UiBuilder()
    >>>
    >>> # Add views
    >>> products_table = Table("products")
    >>> products_view = builder.add_table_view(
    ...     table=products_table,
    ...     display_name="Product Catalog"
    ... )
    >>>
    >>> sales_view = builder.add_chart_view(
    ...     chart_title="Sales Dashboard",
    ...     primary_series=sales_series,
    ...     secondary_series=region_series,
    ...     chart_type=ChartType.BAR,
    ...     table=sales_table
    ... )
    >>>
    >>> # Configure navigation
    >>> builder.add_navigation_item(products_view)
    >>> builder.add_navigation_item(sales_view)
    >>>
    >>> # Set default and build
    >>> builder.set_default_view(products_view)
    >>> ui_definition = builder.build()
"""

import json
import os
import pathlib
import random
import string

from daitum_model import Calculation, Field, Parameter, Table

from ._buildable import Buildable
from .base_view import BaseView
from .card_view import Card, CardView
from .chart_view import ChartView, CombinationChartView
from .charts import ChartSeries, ChartType
from .context_variable import ContextVariable, CVType
from .data import MatchRowFilterMode
from .elements import FontWeight, LayoutStyle, Slider, Text
from .filter_component import FilterComponent
from .fixed_value_view import FixedValueView
from .form_view import FormView
from .gantt_view import (
    CategoryGanttTaskDefinition,
    CategoryGanttView,
    TreeGridGanttTaskDefinition,
    TreeGridGanttView,
)
from .layout import (
    FlexView,
    GridLayout,
    GridView,
)
from .map_view import MapType, MapView
from .menu_configurations import MenuConfigurations
from .modal import Modal
from .named_value_view import NamedValueView, Orientation
from .navigation_items import GroupViewNavItem, SingleViewNavItem
from .roster_view import RosterView
from .tabbed_view import TabbedView
from .tabular import TableView, TreeView


class UiBuilder(Buildable):
    """
    Central builder class for constructing complete user interface definitions.

    UiBuilder serves as the main orchestrator for creating UI configurations. It provides
    an API for building complex user interfaces through a series of factory
    methods that create and register various UI components.

    Once all components are configured, calling ``build()`` produces the final
    ui definition that can be used to render the complete UI.
    """

    def __init__(self):
        self._views = list()
        self.navigation = list()
        self.modals = list()
        self.variables = list()
        self.menu_configurations: MenuConfigurations = MenuConfigurations()
        self.filters = list()
        self.optimisation_validation_view_id = None

        self._true_context = self.add_context_variable(
            "TRUE", type=CVType.BOOLEAN, is_array=False, default_value=True
        )
        self._false_context = self.add_context_variable(
            "FALSE", type=CVType.BOOLEAN, is_array=False, default_value=False
        )

        self._default_view: BaseView | None = None

    def set_validation_view(self, view: BaseView):
        """
        Sets the view to be redirected to if optimisation is blocked.

        Args:
            view (BaseView): The view to use for data validation.
        """
        self.optimisation_validation_view_id = view.id

    def add_context_variable(
        self,
        id: str,
        type: CVType,
        default_value: bool | int | float | str | Parameter | Calculation | None = None,
        is_array: bool = False,
    ) -> ContextVariable:
        """
        Register a context variable that can be referenced within the view.

        Parameters:
            id:
                Unique identifier of the context variable.
            type:
                Declared data type of the variable (e.g., INTEGER, DECIMAL, STRING, BOOLEAN).
            default_value:
                Optional default value used when no explicit value is provided.
            is_array:
                Whether the variable represents a list of values instead of a single scalar.

        Raises:
            ValueError when id already exists.

        Example:
            >>> builder = UiBuilder()
            >>>
            >>> # Add a simple integer context variable
            >>> page_size_var = builder.add_context_variable(
            ...     id="page_size",
            ...     type=CVType.INTEGER,
            ...     default_value=25
            ... )
            >>>
            >>> # Add a boolean flag
            >>> debug_mode = builder.add_context_variable(
            ...     id="debug_mode",
            ...     type=CVType.BOOLEAN,
            ...     default_value=False
            ... )
            >>>
            >>> # Add an array variable
            >>> selected_ids = builder.add_context_variable(
            ...     id="selected_items",
            ...     type=CVType.INTEGER,
            ...     is_array=True
            ... )
        """
        if id in [cv.id for cv in self.variables]:
            raise ValueError(f"Context variable '{id}' already exists.")

        variable = ContextVariable(id, type, default_value, is_array)
        self.variables.append(variable)
        return variable

    def get_context_variable(self, variable_id: str):
        """
        Retrieve a context variable by ID.

        Raises:
            KeyError: If no context variable with the given ID exists.

        Returns:
            ContextVariable

        Example:
            >>> builder = UiBuilder()
            >>> page_size = builder.add_context_variable(
            ...     "page_size",
            ...     CVType.INTEGER,
            ...     default_value=25
            ... )
            >>>
            >>> # Retrieve the context variable later
            >>> retrieved_var = builder.get_context_variable("page_size")
            >>> print(retrieved_var.id)  # Output: page_size
            >>>
            >>> # Use pre-configured variables
            >>> true_var = builder.get_context_variable("TRUE")
            >>> false_var = builder.get_context_variable("FALSE")
        """
        for context_variable in self.variables:
            if context_variable.id == variable_id:
                return context_variable
        raise KeyError(f"Context variable '{variable_id}' not found.")

    def add_location_view(
        self,
        table: Table,
        latitude: Field,
        longitude: Field,
    ) -> MapView:
        """
        Create and register a location-based map view.

        A location view displays individual point locations on a map using
        latitude and longitude coordinates from the data table. Each row
        in the table represents a single location marker on the map.

        Args:
            table (Table):
                The data table containing location information.
            latitude (Field):
                Field in the table containing latitude coordinates (numeric).
            longitude (Field):
                Field in the table containing longitude coordinates (numeric).

        Returns:
            MapView:
                The created location map view builder instance, allowing
                further configuration such as markers, popups, and styling.

        Example:
            >>> map_view = builder.add_location_view(
            ...     table=locations_table,
            ...     latitude=lat_field,
            ...     longitude=lng_field,
            ... )
        """
        builder = MapView(table, MapType.LOCATION, latitude, longitude)
        self._views.append(builder)
        return builder

    def add_route_view(
        self,
        table: Table,
        latitude: Field,
        longitude: Field,
    ) -> MapView:
        """
        Create and register a route-based map view.

        A route view displays connected paths or routes on a map by connecting
        sequential points from the data table. The rows are ordered and connected
        to form a continuous path, useful for visualising delivery routes, travel
        paths, or sequential journeys.

        Args:
            table (Table):
                The data table containing route waypoint information.
            latitude (Field):
                Field in the table containing latitude coordinates for waypoints.
            longitude (Field):
                Field in the table containing longitude coordinates for waypoints.

        Returns:
            MapView:
                The created route map view builder instance, allowing further
                configuration such as route styling, markers, and waypoint display.

        Example:
            >>> route_view = builder.add_route_view(
            ...     table=delivery_table,
            ...     latitude=lat_field,
            ...     longitude=lng_field,
            ... )
        """
        builder = MapView(table, MapType.ROUTE, latitude, longitude)
        self._views.append(builder)
        return builder

    def add_grid_view(
        self,
        layout: GridLayout,
        display_name: str | None = None,
        hidden: bool = False,
    ) -> GridView:
        """
        Create and register a CSS grid-based layout view.

        A grid view uses CSS Grid Layout to arrange child components in a
        two-dimensional grid structure with precise control over rows, columns,
        and alignment. This is ideal for creating structured, responsive layouts.

        Args:
            layout (GridLayout):
                The grid layout configuration defining the grid structure,
                including template columns, rows, and cell assignments.
            display_name (str | None):
                Optional display label for the view. Default is None.
            hidden (bool):
                Whether the view should initially be hidden. Default is False.

        Returns:
            GridView:
                The created grid view builder instance for further configuration.

        Example:
            >>> from daitum_ui.layout import GridLayout
            >>>
            >>> grid_layout = GridLayout(
            ...     columns=["1fr", "2fr", "1fr"],
            ...     rows=["auto", "1fr"],
            ...     areas=[["header", "header", "header"], ["nav", "main", "aside"]]
            ... )
            >>>
            >>> grid_view = builder.add_grid_view(
            ...     layout=grid_layout,
            ...     display_name="Dashboard Layout"
            ... )
        """
        builder = GridView(layout, display_name, hidden)
        self._views.append(builder)
        return builder

    def add_flex_view(
        self,
        display_name: str | None = None,
        hidden: bool = False,
    ) -> FlexView:
        """
        Create and register a CSS flexbox-based layout view.

        A flex view uses CSS Flexbox Layout to arrange child components in a
        one-dimensional flow (either horizontal or vertical) with flexible sizing
        and alignment. This is ideal for creating responsive, flowing layouts.

        Args:
            display_name (str | None):
                Optional display label for the view. Default is None.
            hidden (bool):
                Whether the view should initially be hidden. Default is False.

        Returns:
            FlexView:
                The created flex view builder instance for further configuration.

        Example:
            >>> toolbar_view = builder.add_flex_view(display_name="Toolbar")
            >>> toolbar_view.set_flex_direction(FlexDirection.ROW).set_gap("10px")
        """
        builder = FlexView(display_name, hidden)
        self._views.append(builder)
        return builder

    def add_table_view(
        self,
        table: Table,
        display_name: str | None = None,
        hidden: bool = False,
    ) -> TableView:
        """
        Create and register a tabular data view.

        A table view displays data in a traditional row-and-column spreadsheet-like
        format with support for sorting, filtering, and interactive controls. This
        is one of the most common view types for displaying structured data.

        Args:
            table (Table):
                The data table to display.
            display_name (str | None):
                Optional display label for the view in navigation. Default is None.
            hidden (bool):
                Whether the view should initially be hidden. Default is False.

        Returns:
            TableView:
                The created table view builder instance for further configuration,
                such as adding columns, configuring actions, and styling.

        Example:
            >>> products_table = Table("products")
            >>> products_view = builder.add_table_view(
            ...     table=products_table,
            ...     display_name="Product Catalog"
            ... )
        """
        builder = TableView(table, display_name, hidden)
        self._views.append(builder)
        return builder

    def add_tree_view(
        self,
        table: Table,
        display_name: str | None = None,
        hidden: bool = False,
    ) -> TreeView:
        """
        Create and register a hierarchical tree table view.

        A tree view displays data in a hierarchical structure with expandable/
        collapsible nodes, similar to a file system browser. Each row can have
        child rows, creating a parent-child relationship that can be nested
        multiple levels deep.

        Args:
            table (Table):
                The data table containing hierarchical data. The table should
                have a parent reference field to define relationships.
            display_name (str | None):
                Optional display label for the view in navigation. Default is None.
            hidden (bool):
                Whether the view should initially be hidden. Default is False.

        Returns:
            TreeView:
                The created tree view builder instance for further configuration,
                including setting the parent field and configuring columns.

        Example:
            >>> tasks_table = Table("tasks")
            >>>
            >>> tree_view = builder.add_tree_view(
            ...     table=tasks_table,
            ...     display_name="Task Hierarchy"
            ... )
        """
        builder = TreeView(table, display_name, hidden)
        self._views.append(builder)
        return builder

    def add_fixed_value_view(
        self,
        display_name: str | None = None,
        hidden: bool = False,
    ) -> FixedValueView:
        """
        Creates and registers a FixedValueView configuration for this element.

        Args:
            display_name (str): The name displayed in the UI.
            hidden (bool): Whether the element should be initially hidden.

        Returns:
            FixedValueView: The created view builder instance.

        Example:
            >>> constants_view = builder.add_fixed_value_view(
            ...     display_name="System Constants"
            ... )
        """
        builder = FixedValueView(display_name, hidden)
        self._views.append(builder)
        return builder

    def add_named_value_view(
        self,
        display_name: str | None = None,
        hidden: bool = False,
        orientation: Orientation = Orientation.HORIZONTAL,
    ) -> NamedValueView:
        """
        Create and register a named value display view.

        A named value view displays a collection of label-value pairs in a
        structured format. This is useful for showing key metrics, summary
        statistics, or configuration values in a clean, organized way.

        Args:
            display_name (str | None):
                Optional display label for the view in navigation. Default is None.
            hidden (bool):
                Whether the view should initially be hidden. Default is False.
            orientation (Orientation):
                Layout orientation for the name-value pairs. HORIZONTAL arranges
                labels and values side-by-side, while VERTICAL stacks them.
                Default is Orientation.HORIZONTAL.

        Returns:
            NamedValueView:
                The created named value view builder instance for adding
                name-value pairs and configuring styling.

        Example:
            >>> # Create a horizontal stats display
            >>> stats_view = builder.add_named_value_view(
            ...     display_name="Summary Statistics",
            ...     orientation=Orientation.HORIZONTAL
            ... )
        """
        builder = NamedValueView(display_name, hidden, orientation)
        self._views.append(builder)
        return builder

    def add_chart_view(
        self,
        primary_series: ChartSeries,
        chart_type: ChartType,
        table: Table,
        display_name: str | None = None,
    ) -> ChartView:
        """
        Create and register a standard ChartView.

        Args:
            primary_series: Primary data series definition.
            chart_type: Type of chart to render (e.g., BAR, LINE).
            table: Table from which the chart draws its data.
            display_name: Optional display label for the view.

        Returns:
            ChartView: The created chart view builder instance.

        Example:
            >>> chart_view = builder.add_chart_view(
            ...     primary_series=primary,
            ...     chart_type=ChartType.BAR,
            ...     table=sales_table,
            ...     display_name="Sales Chart"
            ... )
        """
        builder = ChartView(primary_series, chart_type, table, display_name)
        self._views.append(builder)
        return builder

    def add_combination_chart_view(
        self,
        primary_series: ChartSeries,
        chart_type: ChartType,
        table: Table,
        display_name: str | None = None,
    ) -> CombinationChartView:
        """
        Create and register a CombinationChartView.

        Args:
            primary_series: Primary data series definition.
            chart_type: Base chart type applied to the view.
            table: Table providing the data for the chart.
            display_name: Optional display label for the view.

        Returns:
            CombinationChartView: The created combination chart view builder instance.

        Example:
            >>> combo_chart = builder.add_combination_chart_view(
            ...     primary_series=revenue_series,
            ...     chart_type=ChartType.BAR,
            ...     table=metrics_table,
            ...     display_name="Performance Dashboard"
            ... )
        """
        builder = CombinationChartView(primary_series, chart_type, table, display_name)
        self._views.append(builder)
        return builder

    def add_roster_view(
        self,
        source_table: Table,
        display_name: str | None = None,
        hidden: bool = False,
    ) -> RosterView:
        """
        Create and register a `RosterView` for this view builder.

        Parameters:
            source_table:
                The data table that supplies row and shift information for the roster.
            display_name:
                An optional human-readable name for the roster view.
            hidden:
                Whether the roster view should be initially hidden in the UI.

        Returns:
            RosterView
                The constructed roster view builder instance, allowing additional
                configuration to be chained fluently.

        Example:
            >>> roster_view = builder.add_roster_view(
            ...     source_table=shifts_table,
            ...     display_name="Employee Schedule"
            ... )
        """
        builder = RosterView(source_table, display_name, hidden)
        self._views.append(builder)
        return builder

    def add_card_view(
        self,
        card_template: Card,
        table: Table | None = None,
        display_name: str | None = None,
    ) -> CardView:
        """
        Creates and adds a CardView definition to this view builder.

        Args:
            card_template:
                The card layout template applied to each rendered row.
            table:
                Optional data table that provides rows for the card view.
            display_name:
                Optional display name for the card view.

        Returns:
            CardView: The newly created card view definition.

        Example:
            >>> card_view = builder.add_card_view(
            ...     card_template=product_card,
            ...     table=products_table,
            ...     display_name="Product Gallery"
            ... )
        """
        builder = CardView(card_template, display_name)
        if table is not None:
            builder.set_table(table)
        self._views.append(builder)
        return builder

    def add_tree_grid_gantt_view(
        self,
        table: Table,
        gantt_task_definition: TreeGridGanttTaskDefinition,
        display_name: str | None = None,
        hidden: bool = False,
        use_filter: FilterComponent | None = None,
    ) -> TreeGridGanttView:
        """
        Create and register a TreeGridGanttView with hierarchical task organization.

        A tree-grid Gantt view combines a hierarchical tree structure with a Gantt
        chart timeline, allowing tasks to be organized with parent-child relationships
        and displayed alongside their schedule visualization.

        Args:
            table: The data table containing task records.
            gantt_task_definition: TreeGridGanttTaskDefinition with tree-grid specific
                configuration including parent field and name field mappings.
            display_name: Optional display label for the view in the navigation.
            hidden: Whether the view should initially be hidden in the UI.
            use_filter: The identifier (filter name) of a ViewFilterDef
                to apply when querying data for this view.

        Returns:
            TreeGridGanttView: The created tree-grid Gantt view builder instance,
                allowing further configuration such as x-axis behavior, drag-drop
                settings, and tooltip properties.

        Example:
            >>> # Create a hierarchical project Gantt chart
            >>> project_tasks = Table("project_tasks")
            >>> task_def = TreeGridGanttTaskDefinition(
            ...     name_field=Field("task_name", DataType.STRING),
            ...     start_field=Field("start_date", DataType.DATE),
            ...     end_field=Field("end_date", DataType.DATE),
            ...     parent_field=Field("parent_task_id", DataType.INTEGER)
            ... )
            >>>
            >>> gantt_view = builder.add_tree_grid_gantt_view(
            ...     table=project_tasks,
            ...     gantt_task_definition=task_def,
            ...     display_name="Project Timeline"
            ... )
        """
        builder = TreeGridGanttView(table, gantt_task_definition, display_name, hidden, use_filter)
        self._views.append(builder)
        return builder

    def add_category_gantt_view(
        self,
        table: Table,
        gantt_task_definition: CategoryGanttTaskDefinition,
        display_name: str | None = None,
    ) -> CategoryGanttView:
        """
        Create and register a CategoryGanttView with categorical task organization.

        A category Gantt view organizes tasks into categories along the y-axis
        rather than using a hierarchical tree structure. Each category row can contain
        multiple tasks displayed on the timeline.

        Args:
            table: The data table containing task records.
            gantt_task_definition: GanttTaskDefinition defining how fields map to
                task properties.
            display_name: Optional display label for the view in the navigation.

        Returns:
            CategoryGanttView: The created category Gantt view builder instance,
                allowing further configuration such as x-axis behavior, drag-drop
                settings, and tooltip properties.

        Example:
            >>> gantt_view = builder.add_category_gantt_view(
            ...     table=assignments_table,
            ...     gantt_task_definition=task_def,
            ...     display_name="Resource Allocation"
            ... )
        """
        builder = CategoryGanttView(table, gantt_task_definition, display_name)
        self._views.append(builder)
        return builder

    def add_form_view(
        self,
        display_name: str | None = None,
        hidden: bool = False,
        total_rows: int | None = None,
        table: Table | None = None,
        match_row: MatchRowFilterMode | None = None,
    ) -> FormView:
        """
        Creates and adds a FormView definition to this view builder.

        Args:
            display_name:
                Optional display name for the view.
            hidden:
                Whether the form view should initially be hidden.
            total_rows:
                Optional fixed number of rows for the form layout.
            table:
                Optional data table backing the form.
            match_row:
                Determines how row-matching is applied when binding data.

        Returns:
            FormView: The newly created form view definition.

        Example:
            >>> # Create a data entry form
            >>> customer_table = Table("customers")
            >>> form_view = builder.add_form_view(
            ...     display_name="Customer Information",
            ...     total_rows=4,
            ...     table=customer_table,
            ...     match_row=MatchRowFilterMode.FIRST_ROW
            ... )
            >>>
            >>> # Add form fields
            >>> form_view.add_column("100px")
        """
        builder = FormView(display_name, hidden, total_rows, table, match_row)
        self._views.append(builder)
        return builder

    def add_tabbed_view(
        self,
        display_name: str | None = None,
        hidden: bool = False,
        use_full_width_tabs: bool = False,
        headless_context_variable: ContextVariable | None = None,
        tab_padding: str | None = None,
    ) -> TabbedView:
        """
        Creates and adds a TabbedView definition to this view builder.

        Args:
            display_name:
                Optional display name for the tabbed view.
            hidden:
                Whether the tabbed view should initially be hidden.
            use_full_width_tabs:
                If True, tabs stretch across the full width of the container.
            headless_context_variable:
                Context variable controlling which tab is active when
                headless mode is enabled.
            tab_padding:
                Optional padding applied around the tab headers.

        Returns:
            TabbedView: The newly created tabbed view definition.

        Example:
            >>> # Create a tabbed view with multiple tabs
            >>> tabbed_view = builder.add_tabbed_view(
            ...     display_name="Dashboard Tabs",
            ...     use_full_width_tabs=True,
            ...     tab_padding="10px"
            ... )
            >>>
            >>> # Add tabs (child views)
            >>> overview_table = builder.add_table_view(...)
            >>> details_chart = builder.add_chart_view(...)
            >>> tabbed_view.add_tab("Overview", overview_table)
            >>> tabbed_view.add_tab("Details", details_chart)
        """
        builder = TabbedView(
            display_name,
            hidden,
            use_full_width_tabs,
            headless_context_variable,
            tab_padding,
        )
        self._views.append(builder)
        return builder

    def add_navigation_item(
        self,
        view: BaseView,
        background_color: str | None = None,
        active_color: str | None = None,
        font_color: str | None = None,
    ) -> SingleViewNavItem:
        """
        Create and register a single-view navigation item.

        Parameters:
            view:
                The view that this navigation item should open directly.
            background_color:
                Optional hex RGB string for the item's default background colour.
            active_color:
                Optional hex RGB string for the highlight colour when the item is active.
            font_color:
                Optional hex RGB string specifying the text colour of the navigation label.

        Returns:
            SingleViewNavItem
                A builder allowing further configuration, such as attaching hidden
                conditions or adjusting colours.

        Example:
            >>> # Create views and add to navigation
            >>> products_view = builder.add_table_view(
            ...     table=products_table,
            ...     display_name="Products"
            ... )
            >>> orders_view = builder.add_table_view(
            ...     table=orders_table,
            ...     display_name="Orders"
            ... )
            >>>
            >>> # Add navigation items with custom colors
            >>> builder.add_navigation_item(
            ...     view=products_view,
            ...     background_color="#F0F0F0",
            ...     active_color="#007BFF",
            ...     font_color="#333333"
            ... )
            >>> builder.add_navigation_item(view=orders_view)
        """
        builder = SingleViewNavItem(view)
        if background_color is not None:
            builder.set_background_colour(background_color)
        if active_color is not None:
            builder.set_active_colour(active_color)
        if font_color is not None:
            builder.set_font_colour(font_color)

        view._navigation_item = True

        self.navigation.append(builder)
        return builder

    def add_navigation_group(
        self,
        name: str,
        auto_collapse: bool = True,
        hidden: bool = False,
    ) -> GroupViewNavItem:
        """
        Create and register a navigation group - an expandable tab containing
        multiple related views.

        Parameters:
            name:
                The label displayed for the group in the navigation panel.
                Must be unique across all navigation items.
            auto_collapse:
                If True (default), the group collapses automatically when the user
                navigates away to a different group or view.
            hidden:
                Whether the entire group should initially be hidden in the UI.

        Returns:
            GroupViewNavItem
                A navigation group builder that can be used to add multiple views
                and configure visibility conditions.

        Example:
            >>> reports_group = builder.add_navigation_group(name="Reports")
            >>> reports_group.add_view(sales_report)
        """
        builder = GroupViewNavItem(name, auto_collapse, hidden)
        self.navigation.append(builder)
        return builder

    def get_views(self):
        """
        Retrieve the list of all registered view builders.

        This method returns a list of all view builder instances that have been
        added to this UiBuilder through the various add_*_view() factory methods.
        The views are returned in the order they were added, except that the
        default view (if set) will be first after build() is called.

        Returns:
            list[BaseView]:
                A list of all view builder instances registered with this UiBuilder.
                This includes table views, chart views, form views, and all other
                view types that have been added.

        Example:
            >>> builder = UiBuilder()
            >>> table_view = builder.add_table_view(products_table)
            >>> chart_view = builder.add_chart_view(...)
            >>>
            >>> # Get all views
            >>> all_views = builder.get_views()
            >>> print(f"Total views: {len(all_views)}")  # Output: Total views: 2
            >>>
            >>> # Iterate through views
            >>> for view in builder.get_views():
            ...     print(view.display_name)
        """
        return self._views

    def add_modal(
        self,
        view: BaseView,
        height: str = "auto",
        width: str = "auto",
        title: str | ContextVariable | None = None,
    ) -> Modal:
        """
        Creates and registers a new modal dialog associated with the given view.

        Args:
            view:
                The ``BaseView`` to be displayed inside the modal.
            height:
                A CSS height value for the modal. Defaults to `"auto"`.
            width:
                A CSS width value for the modal. Defaults to `"auto"`.
            title:
                Optional static title text for the modal dialog.

        Returns:
            Modal: The configured modal builder instance.

        Example:
            >>> # Create a form view to display in a modal
            >>> edit_form = builder.add_form_view(
            ...     display_name="Edit Customer",
            ...     table=customers_table
            ... )
            >>>
            >>> # Create modal with custom size
            >>> modal = builder.add_modal(
            ...     view=edit_form,
            ...     height="600px",
            ...     width="800px",
            ...     title="Customer Details"
            ... )
            >>>
            >>> # Use context variable for dynamic title
            >>> title_var = builder.add_context_variable("modal_title", CVType.STRING)
            >>> modal2 = builder.add_modal(
            ...     view=another_view,
            ...     title=title_var
            ... )
        """
        builder = Modal(view, height, width, title)
        self.modals.append(builder)
        return builder

    def set_menu_configurations(
        self,
        hide_optimisation: bool = False,
        hide_import: bool = False,
        hide_bulk_import: bool = False,
        hide_import_into_sheets: bool = False,
    ) -> MenuConfigurations:
        """
        Configure the visibility of menu actions available within the view.

        Parameters:
            hide_optimisation:
                If `True`, hides the optimisation-related actions from the menu.
                Defaults to ``False`` so optimisation features are available unless
                explicitly disabled.
            hide_import:
                If `True`, hides the standard data import menu options.
                Defaults to `False`.
            hide_bulk_import:
                If `True`, hides bulk-import functionality in the menu.
                Defaults to `False`.
            hide_import_into_sheets:
                If `True`, hides the option to import data directly into sheets.
                Defaults to `False`.

        Returns:
            MenuConfigurations
                The configuration object created. This allows callers to chain further
                customisation on the returned configuration instance if required.

        Example:
            >>> # Hide all import-related menu options
            >>> builder.set_menu_configurations(
            ...     hide_import=True,
            ...     hide_bulk_import=True,
            ...     hide_import_into_sheets=True
            ... )
            >>>
            >>> # Hide only optimisation features
            >>> builder.set_menu_configurations(
            ...     hide_optimisation=True
            ... )
        """

        self.menu_configurations.hide_optimisation = hide_optimisation
        self.menu_configurations.hide_import = hide_import
        self.menu_configurations.hide_bulk_import = hide_bulk_import
        self.menu_configurations.hide_import_into_sheets = hide_import_into_sheets
        return self.menu_configurations

    def add_filter(
        self,
        filter_name: str,
        source_table: Table,
    ) -> FilterComponent:
        """
        Creates and registers a filter view for this model.

        Args:
           filter_name (str):
               The unique identifier for the filter.
           source_table (Table):
               The table from which the filter values are sourced.

        Returns:
           FilterComponent:
               The newly created filter view builder.

        Example:
            >>> # Create a filter for a products table
            >>> products_table = Table("products")
            >>> product_filter = builder.add_filter(
            ...     filter_name="product_filter",
            ...     source_table=products_table
            ... )
            >>>
            >>> # Add filter options
            >>> product_filter.add_filter_option(
            ...     field=Field("category", DataType.STRING),
            ...     display_name="Category"
            ... )
            >>> product_filter.add_filter_option(
            ...     field=Field("price", DataType.DECIMAL),
            ...     display_name="Price"
            ... )
            >>>
            >>> # Use the filter in a table view
            >>> table_view = builder.add_table_view(
            ...     table=products_table,
            ...     use_filter=product_filter
            ... )
        """
        builder = FilterComponent(filter_name, source_table)
        self.filters.append(builder)
        return builder

    def add_toggle_view(
        self,
        display_name: str,
        first_view: BaseView,
        second_view: BaseView,
        toggle_label: str,
    ) -> GridView:
        """
        Create a grid view that toggles between two child views via a slider.

        A boolean context variable drives visibility: the first view is shown when
        the variable is ``False`` and the second when it is ``True``. A labelled
        slider is rendered in the top-right corner to let the user switch between
        them.

        Args:
            display_name:
                Display label for the outer grid view.
            first_view:
                The view rendered when the toggle is off (default state).
            second_view:
                The view rendered when the toggle is on.
            toggle_label:
                Bold text label displayed next to the toggle slider.

        Returns:
            GridView: The outer grid view containing both child views and the
            toggle control.

        Example:
            >>> table_view = builder.add_table_view(table=my_table, display_name="Table")
            >>> chart_view = builder.add_chart_view(
            ...     chart_title="Chart",
            ...     primary_series=series,
            ...     chart_type=ChartType.BAR,
            ...     table=my_table,
            ... )
            >>> toggle_view = builder.add_toggle_view(
            ...     display_name="Results",
            ...     first_view=table_view,
            ...     second_view=chart_view,
            ...     toggle_label="Chart View",
            ... )
        """
        context_id: str = "".join(random.choices(string.ascii_letters, k=16))
        hidden_variable = self.add_context_variable(context_id, CVType.BOOLEAN, default_value=False)

        grid = [["-", "toggle"], ["main", "main"]]
        layout = GridLayout(columns=["auto", "auto"], rows=["20px", "auto"], areas=grid)

        grid_view = self.add_grid_view(layout=layout, display_name=display_name)

        first_child = grid_view.add_child(first_view, grid_area="main")
        first_child.add_variable_hidden_condition(hidden_variable, negate=False)

        second_child = grid_view.add_child(second_view, grid_area="main")
        second_child.add_variable_hidden_condition(hidden_variable, negate=True)

        toggle_text = Text(value=toggle_label, font_weight=FontWeight.BOLD)
        toggle_element = Slider(data_source=hidden_variable)

        toggle_card = Card(
            row_count=1,
            layout_style=LayoutStyle.GRID,
            border_color="#00000000",
            padding="0px",
        )
        toggle_card.add_element(toggle_text)
        toggle_card.add_element(toggle_element)

        card_view = self.add_card_view(toggle_card)
        grid_view.add_child(card_view, grid_area="toggle")

        return grid_view

    def set_default_view(self, view: BaseView):
        """
        Sets the default view for this model.

        The default view is prioritised during the build process and will
        be ordered first among all views when the model definition is built.

        Args:
            view (BaseView):
                The view instance to be marked as the default view.

        Example:
            >>> # Create multiple views
            >>> products_view = builder.add_table_view(
            ...     table=products_table,
            ...     display_name="Products"
            ... )
            >>> orders_view = builder.add_table_view(
            ...     table=orders_table,
            ...     display_name="Orders"
            ... )
            >>>
            >>> # Set the products view as default
            >>> builder.set_default_view(products_view)
            >>>
            >>> # When the UI loads, products_view will be displayed first
        """
        self._default_view = view

    def _sort_views(self) -> None:
        if not self._default_view:
            return

        default_id = self._default_view.id

        self._views.sort(key=lambda b: b.id != default_id)

    def build(self):
        """
        Builds the final ui definition.

        This method ensures views are correctly ordered (with the default
        view first) before delegating to the base ``build`` implementation.

        Returns:
            dict:
                The fully built ui definition.

        Example:
            >>> # Build a complete UI definition
            >>> builder = UiBuilder()
            >>>
            >>> # Add views
            >>> products_view = builder.add_table_view(
            ...     table=products_table,
            ...     display_name="Products"
            ... )
            >>> sales_chart = builder.add_chart_view(
            ...     chart_title="Sales",
            ...     primary_series=series,
            ...     secondary_series=series2,
            ...     chart_type=ChartType.BAR,
            ...     table=sales_table
            ... )
            >>>
            >>> # Configure navigation
            >>> builder.add_navigation_item(products_view)
            >>> builder.add_navigation_item(sales_chart)
            >>>
            >>> # Set default view
            >>> builder.set_default_view(products_view)
            >>>
            >>> # Build and get the final UI definition
            >>> ui_definition = builder.build()
            >>> # ui_definition is a dict that can be serialized and used to render the UI
        """
        self._sort_views()
        built = super().build()
        built["views"] = [view.build() for view in self._views]
        return built

    def write_to_file(self, model_directory: str | os.PathLike[str]) -> None:
        """
        Serialises the UI definition into ``ui-definition.json`` under the given directory.

        Args:
            model_directory: Directory to write the UI definition into. Created if missing.
        """
        path = pathlib.Path(model_directory) / "ui-definition.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", encoding="utf-8") as fp:
            json.dump(self.build(), fp, indent=4, sort_keys=False)
