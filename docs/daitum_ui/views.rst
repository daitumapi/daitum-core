Views
=====

Views are the fundamental display components that define how data and content are presented
to users in the Daitum UI framework. Each view type serves a specific purpose, from
displaying tabular data and hierarchical structures to visualising charts, maps, and forms.

Views are created through the ``UiBuilder`` class using factory methods (e.g., ``add_table_view()``,
``add_chart_view()``), and can be organised into navigation structures to create complete
application interfaces. They work with data tables, support filtering and context variables,
and can be configured with various styling and interaction options to meet specific requirements.

**Examples**:

Table views display data in a traditional row-and-column format:

.. code-block:: python

    from daitum_ui.ui_builder import UiBuilder
    from daitum_model import Table, Field, DataType

    builder = UiBuilder()

    # Create data source
    products_table = Table("products")

    # Add table view
    products_view = builder.add_table_view(
        table=products_table,
        display_name="Product Catalog"
    )

    # Configure columns
    products_view.add_field(Field("name", DataType.STRING))
    products_view.add_field(Field("price", DataType.DECIMAL))
    products_view.add_field(Field("stock", DataType.INTEGER))

Chart views visualize data with various chart types:

.. code-block:: python

    from daitum_ui.charts import ChartSeries, ChartType

    # Define chart data series
    sales_table = Table("sales")

    primary_series = ChartSeries(
        x_axis_field=Field("month", DataType.STRING),
        y_axis_field=Field("revenue", DataType.DECIMAL)
    )

    secondary_series = ChartSeries(
        x_axis_field=Field("month", DataType.STRING),
        y_axis_field=Field("units_sold", DataType.INTEGER)
    )

    # Create chart view
    sales_chart = builder.add_chart_view(
        chart_title="Monthly Sales Performance",
        primary_series=primary_series,
        secondary_series=secondary_series,
        chart_type=ChartType.BAR,
        table=sales_table,
        display_name="Sales Dashboard"
    )

Flex and Grid views organize content with flexible layouts:

.. code-block:: python

    from daitum_ui.layout import FlexDirection, FlexAlignment, GridLayout, GridAlignment

    # Flex layout for vertical stacking
    sidebar = builder.add_flex_view(
        display_name="Sidebar",
        flex_direction=FlexDirection.COLUMN,
        justify_content=FlexAlignment.FLEX_START,
        gap="15px"
    )

    # Grid layout for structured positioning
    grid_layout = GridLayout(
        template_columns="1fr 2fr 1fr",
        template_rows="auto 1fr"
    )

    dashboard = builder.add_grid_view(
        layout=grid_layout,
        display_name="Dashboard",
        gap="10px",
        align_items=GridAlignment.CENTER
    )


View Types
----------

.. toctree::
    :maxdepth: 2

    base_view
    tabular
    layout
    card_view
    roster_view
    chart_view
    gantt_view
    map_view
    tabbed_view
    form_view
    fixed_value_view
    named_value_view

Supporting Components
---------------------

.. toctree::
    :maxdepth: 2

    data
    elements
    styles
    navigation_items
    modal
    charts
    icons
    model_event
    context_variable
    filter_component
