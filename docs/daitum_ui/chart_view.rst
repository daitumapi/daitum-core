Chart View
==========

.. automodule:: daitum_ui.chart_view
    :no-index:
    :members:
    :show-inheritance:

Examples
--------

Build and configure a bar chart with a secondary series and an additional
comparison series:

.. code-block:: python

    # Define the data source
    sales_table = Table("monthly_sales")

    # Create chart series
    primary_series = ChartSeries(
        source_field=Field("month", DataType.STRING),
        name="Month"
    )
    secondary_series = ChartSeries(
        source_field=Field("revenue", DataType.DECIMAL),
        name="Revenue"
    )

    # Create and register a bar chart
    builder = UiBuilder()
    chart_view = builder.add_chart_view(
        primary_series=primary_series,
        chart_type=ChartType.BAR,
        table=sales_table,
        display_name="Sales Dashboard"
    )

    # Configure chart properties
    chart_view.set_chart_title("Monthly Revenue")
    chart_view.set_secondary_series(secondary_series)
    chart_view.xaxis_label = "Month"
    chart_view.yaxis_label = "Revenue ($)"
    chart_view.orientation = ChartViewOrientation.VERTICAL

    # Add additional data series for comparison
    chart_view.add_data_series(
        source_field=Field("target_revenue", DataType.DECIMAL),
    )
