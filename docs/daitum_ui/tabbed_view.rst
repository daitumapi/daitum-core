Tabbed View
===========

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

.. autoclass:: daitum_ui.tabbed_view.TabbedView
    :no-index:
    :members:
    :show-inheritance:

.. autoclass:: daitum_ui.tabbed_view.TabDefinition
    :no-index:
    :members:
    :show-inheritance:
