Quickstart
==========

This guide will help you get started with the Daitum UI API.

Installation
------------

.. code-block:: bash

    pip install daitum-ui

For version pinning and the bundled ``daitum-core`` meta-package, see
:doc:`/getting_started/installation`.

Basic Usage
-----------

The primary workflow uses the ``UiBuilder`` class to construct complete UI definitions:

.. code-block:: python

    # Initialize the builder
    builder = UiBuilder()

    # Create data source
    products_table = Table("products")

    # Add a table view
    products_view = builder.add_table_view(
        table=products_table,
        display_name="Product Catalog"
    )

    # Add a chart view
    sales_chart = builder.add_chart_view(
        chart_title="Sales Dashboard",
        primary_series=ChartSeries(
            x_axis_field=Field("month", DataType.STRING),
            y_axis_field=Field("revenue", DataType.DECIMAL)
        ),
        secondary_series=ChartSeries(
            x_axis_field=Field("month", DataType.STRING),
            y_axis_field=Field("units", DataType.INTEGER)
        ),
        chart_type=ChartType.BAR,
        table=products_table
    )

    # Configure navigation
    builder.add_navigation_item(products_view)
    builder.add_navigation_item(sales_chart)

    # Set default view and build
    builder.set_default_view(products_view)
    ui_definition = builder.build()