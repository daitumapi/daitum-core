Navigation Items
================

.. automodule:: daitum_ui.navigation_items
    :no-index:
    :members:
    :show-inheritance:

Examples
--------

Creating a navigation group:

.. code-block:: python

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

Conditional visibility for groups:

.. code-block:: python

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

Building a complete navigation structure:

.. code-block:: python

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

Creating a hidden group:

.. code-block:: python

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

Styling navigation with custom colours:

.. code-block:: python

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

Mixed navigation structure:

.. code-block:: python

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
