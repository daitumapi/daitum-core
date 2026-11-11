Charts
======

.. automodule:: daitum_ui.charts
    :no-index:
    :members:
    :show-inheritance:

Examples
--------

Creating a stacked area chart:

.. code-block:: python

    from daitum_ui.charts import ChartViewStacking

    # Stacked area chart showing composition over time
    stacked_area = CombinationChartComponent(
        chart_type=ChartType.AREA,
        stacking=ChartViewStacking.NORMAL,
        orientation=ChartViewOrientation.VERTICAL
    )

    # Add multiple series that will stack
    stacked_area.add_data_series(
        source_field=sales_table.product_a_field,
        name="Product A",
        color="#4caf50"
    )
    stacked_area.add_data_series(
        source_field=sales_table.product_b_field,
        name="Product B",
        color="#ff9800"
    )
    stacked_area.add_data_series(
        source_field=sales_table.product_c_field,
        name="Product C",
        color="#f44336"
    )

Creating a scatter plot with custom markers:

.. code-block:: python

    from daitum_ui.charts import DataPointMarker, DataPointMarkerSymbol

    # Scatter plot with custom markers
    scatter_chart = CombinationChartComponent(
        chart_type=ChartType.SCATTER
    )

    # Custom marker configuration
    custom_marker = DataPointMarker(
        symbol=DataPointMarkerSymbol.DIAMOND,
        radius=6,
        fill_color="#9c27b0",
        line_color="#ffffff",
        line_width=2
    )

    scatter_chart.add_data_series(
        source_field=analysis_table.correlation_field,
        name="Correlation Data",
        marker=custom_marker
    )

Creating a percentage stacked bar chart:

.. code-block:: python

    # Percentage stacked bar chart
    percent_stack = CombinationChartComponent(
        chart_type=ChartType.BAR,
        stacking=ChartViewStacking.PERCENT,
        orientation=ChartViewOrientation.VERTICAL
    )

    percent_stack.add_data_series(
        source_field=survey_table.option_a_field,
        name="Strongly Agree"
    )
    percent_stack.add_data_series(
        source_field=survey_table.option_b_field,
        name="Agree"
    )
    percent_stack.add_data_series(
        source_field=survey_table.option_c_field,
        name="Neutral"
    )

Creating a combination chart with different series types:

.. code-block:: python

    # Combination chart with multiple series
    combo_chart = CombinationChartComponent(
        chart_type=ChartType.BAR,
        orientation=ChartViewOrientation.VERTICAL
    )

    # Bar series for sales volume
    combo_chart.add_data_series(
        source_field=sales_table.volume_field,
        name="Sales Volume",
        color="#2196f3"
    )

    # Line series for target (different visual style)
    combo_chart.add_data_series(
        source_field=sales_table.target_field,
        name="Target",
        color="#ff5722"
    )

Using tooltips and point labels:

.. code-block:: python

    # Chart with custom tooltips
    detailed_chart = CombinationChartComponent(
        chart_type=ChartType.SPLINE,
        tooltip="${series.name}: ${point.y}",
        point_label="${point.y}"
    )

    detailed_chart.add_data_series(
        source_field=metrics_table.value_field,
        name="Performance Metric",
        display_field=metrics_table.formatted_value_field
    )

Creating a horizontal bar chart:

.. code-block:: python

    # Horizontal bar chart (useful for rankings)
    horizontal_bars = CombinationChartComponent(
        chart_type=ChartType.BAR,
        orientation=ChartViewOrientation.HORIZONTAL
    )

    horizontal_bars.add_data_series(
        source_field=products_table.sales_rank_field,
        name="Product Rankings",
        color="#00bcd4"
    )

Box plot for statistical analysis:

.. code-block:: python

    # Box plot showing distribution
    box_plot = CombinationChartComponent(
        chart_type=ChartType.BOX_PLOT,
        orientation=ChartViewOrientation.VERTICAL
    )

    box_plot.add_data_series(
        source_field=experiments_table.results_field,
        name="Experiment Results"
    )

Setting series colours at chart level:

.. code-block:: python

    # Define colour palette for entire chart
    chart = CombinationChartComponent(
        chart_type=ChartType.BAR
    )

    # Add series
    chart.add_data_series(source_field=data.series1, name="Series 1")
    chart.add_data_series(source_field=data.series2, name="Series 2")
    chart.add_data_series(source_field=data.series3, name="Series 3")

    # Apply colour palette
    chart.add_series_color("#e3f2fd")
    chart.add_series_color("#90caf9")
    chart.add_series_color("#1976d2")

Area range chart for min-max visualisation:

.. code-block:: python

    # Area range showing value boundaries
    range_chart = CombinationChartComponent(
        chart_type=ChartType.AREA_RANGE,
        orientation=ChartViewOrientation.VERTICAL
    )

    range_chart.add_data_series(
        source_field=temperature_table.range_field,
        name="Temperature Range",
        color="#ff9800"
    )

Multiple series with individual markers:

.. code-block:: python

    # Chart with different markers per series
    multi_marker_chart = CombinationChartComponent(
        chart_type=ChartType.LINE
    )

    # Series 1 with circle markers
    multi_marker_chart.add_data_series(
        source_field=data.metric1,
        name="Metric 1",
        color="#4caf50",
        marker=DataPointMarker(
            symbol=DataPointMarkerSymbol.CIRCLE,
            radius=4
        )
    )

    # Series 2 with square markers
    multi_marker_chart.add_data_series(
        source_field=data.metric2,
        name="Metric 2",
        color="#2196f3",
        marker=DataPointMarker(
            symbol=DataPointMarkerSymbol.SQUARE,
            radius=4
        )
    )
