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
Chart and data visualization components for the UI Generator.

This module provides a comprehensive charting system for creating interactive
data visualizations. It supports multiple chart types, customizable data series,
marker configurations, and combination charts that can display multiple series
with different visualization styles.

Main Components
---------------

**Chart Types:**
    ChartType enum defines available visualization types:

    Line-based:
        - LINE: Standard line chart with straight segments
        - SPLINE: Smoothed line chart using spline curves
        - AREA: Line chart with filled area underneath
        - AREA_SPLINE: Smoothed area chart

    Bar-based:
        - BAR: Vertical bar chart for categorical data
        - BAR_RANGE: Bar chart showing value ranges

    Statistical:
        - BOX_PLOT: Distribution visualization with quartiles and outliers
        - SCATTER: Individual data points on x-y axis

    Range-based:
        - AREA_RANGE: Area chart showing min-max ranges

    Proportional:
        - PIE: Circular chart showing proportional values

**Configuration Enums:**
    - ChartViewOrientation: VERTICAL, HORIZONTAL (chart layout direction)
    - ChartViewStacking: NORMAL, PERCENT (how series stack)
    - DataPointMarkerSymbol: CIRCLE, SQUARE, TRIANGLE, DIAMOND, TRIANGLE_DOWN

**Core Classes:**
    - DataPointMarker: Visual configuration for individual data points
    - ChartSeries: Single data series with styling and source field
    - CombinationChartComponent: Main chart container supporting multiple series

Stacking Modes
--------------

**NORMAL Stacking:**
    Series values are added on top of each other to show cumulative totals.
    Each segment shows its absolute value contribution to the total.

**PERCENT Stacking:**
    Series values are converted to percentages of the total for each category.
    The chart always reaches 100%, showing relative proportions rather than
    absolute values.

Data Point Markers
------------------

Markers can be customized with:

- **symbol**: Shape (circle, square, triangle, diamond, triangle down)
- **radius**: Size in pixels
- **fill_color**: Interior color
- **line_color**: Border/outline color
- **line_width**: Border width in pixels

Markers help identify individual data points and can differentiate series.

Combination Charts
------------------

CombinationChartComponent allows multiple data series with potentially
different chart types in the same visualization. This enables:

- Comparing different metrics on the same axis
- Overlaying trend lines on bar charts
- Mixing line and area series
- Creating complex multi-metric dashboards

Examples
--------
Creating a simple line chart::

    from daitum_ui.charts import (
        CombinationChartComponent,
        ChartType,
        ChartViewOrientation
    )

    # Create line chart component
    line_chart = CombinationChartComponent(
        chart_type=ChartType.LINE,
        orientation=ChartViewOrientation.VERTICAL
    )

    # Add data series
    line_chart.add_data_series(
        source_field=sales_table.revenue_field,
        name="Monthly Revenue",
        color="#2196f3"
    )

Creating a stacked area chart::

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

Creating a scatter plot with custom markers::

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

Creating a percentage stacked bar chart::

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

Creating a combination chart with different series types::

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

Using tooltips and point labels::

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

Creating a horizontal bar chart::

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

Box plot for statistical analysis::

    # Box plot showing distribution
    box_plot = CombinationChartComponent(
        chart_type=ChartType.BOX_PLOT,
        orientation=ChartViewOrientation.VERTICAL
    )

    box_plot.add_data_series(
        source_field=experiments_table.results_field,
        name="Experiment Results"
    )

Setting series colors at chart level::

    # Define color palette for entire chart
    chart = CombinationChartComponent(
        chart_type=ChartType.BAR
    )

    # Add series
    chart.add_data_series(source_field=data.series1, name="Series 1")
    chart.add_data_series(source_field=data.series2, name="Series 2")
    chart.add_data_series(source_field=data.series3, name="Series 3")

    # Apply color palette
    chart.add_series_color("#e3f2fd")
    chart.add_series_color("#90caf9")
    chart.add_series_color("#1976d2")

Area range chart for min-max visualization::

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

Multiple series with individual markers::

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
"""

from dataclasses import dataclass
from enum import Enum

from daitum_model import Field
from typeguard import typechecked

from daitum_ui._buildable import Buildable


class DataPointMarkerSymbol(Enum):
    """
    Enumeration of supported marker shapes for data points in charts.

    Values:
        CIRCLE:
            A circular marker shape.

        SQUARE:
            A square marker shape.

        TRIANGLE:
            An upward-pointing triangular marker.

        DIAMOND:
            A diamond-shaped marker.

        TRIANGLE_DOWN:
            A downward-pointing triangular marker.
    """

    CIRCLE = "CIRCLE"
    SQUARE = "SQUARE"
    TRIANGLE = "TRIANGLE"
    DIAMOND = "DIAMOND"
    TRIANGLE_DOWN = "TRIANGLE_DOWN"


class ChartViewOrientation(Enum):
    """
    Defines the orientation of the chart layout.

    Attributes:
        VERTICAL:
            The chart is rendered with a vertical orientation.

        HORIZONTAL:
            The chart is rendered with a horizontal orientation.
    """

    VERTICAL = "VERTICAL"
    HORIZONTAL = "HORIZONTAL"


class ChartType(Enum):
    """
    Specifies the type of chart to be rendered.

    Attributes:
        LINE:
            A standard line chart where data points are connected by straight lines.

        BAR:
            A vertical bar chart where values are represented as rectangular bars.

        PIE:
            A circular chart divided into sectors to illustrate proportional values.

        SCATTER:
            A scatter plot where individual data points are placed on an x-y axis.

        AREA:
            An area chart similar to a line chart, but the area under the line is filled.

        SPLINE:
            A smoothed line chart using spline curves instead of straight segments.

        AREA_SPLINE:
            A spline-based area chart where the area under a smooth curve is filled.

        AREA_RANGE:
            An area chart representing a range (e.g., min and max values) between two boundaries.

        BAR_RANGE:
            A bar chart that displays ranges instead of single numeric values.

        BOX_PLOT:
            A statistical chart showing distribution through quartiles, median, and outliers.
    """

    LINE = "LINE"
    BAR = "BAR"
    PIE = "PIE"
    SCATTER = "SCATTER"
    AREA = "AREA"
    SPLINE = "SPLINE"
    AREA_SPLINE = "AREA_SPLINE"
    AREA_RANGE = "AREA_RANGE"
    BAR_RANGE = "BAR_RANGE"
    BOX_PLOT = "BOX_PLOT"


class ChartViewStacking(Enum):
    """
    Defines how multiple data series should be stacked in the chart.

    Attributes:
        NORMAL:
            Standard stacking mode. Series values are added on top of each other,
            producing a cumulative effect (e.g., stacked bar or stacked area chart).

        PERCENT:
            Percentage stacking mode. Each series value is converted into a
            percentage of the total for that category, so stacked segments
            represent relative proportions rather than absolute values.
    """

    NORMAL = "NORMAL"
    PERCENT = "PERCENT"


@dataclass
@typechecked
class DataPointMarker(Buildable):
    """
    Represents the visual marker used to display individual data points on a chart.

    Attributes:
        symbol (Optional[DataPointMarkerSymbol]):
            The marker shape for data points (e.g., circle, square, triangle).
            If None, the chart may use a default marker or render without markers.

        radius (Optional[int]):
            The radius (in pixels) of the marker. Applies to circular markers and
            is used as a size reference for other shapes. If None, the chart's
            default marker size is used.

        fill_color (Optional[str]):
            The fill colour of the marker, expressed as a hex code or colour name.
            If None, the marker may inherit the series colour.

        line_color (Optional[str]):
            The colour of the marker's border/outline. If None, no border may be drawn.

        line_width (Optional[int]):
            The width (in pixels) of the marker outline. If None, the default width applies.
    """

    symbol: DataPointMarkerSymbol | None = None
    radius: int | None = None
    fill_color: str | None = None
    line_color: str | None = None
    line_width: int | None = None


@typechecked
class ChartSeries(Buildable):
    """
    Represents a single series in a chart, including its data source,
    styling preferences, and optional data point marker configuration.

    Attributes:
       source_field (str):
           The underlying data field used as the source values for this series.

       name (Optional[str]):
           The display name for the series, shown in the legend or tooltips.

       color (Optional[str]):
           A custom colour for the series line or bars (hex code or colour name).

       display_field (Optional[str]):
           A field used for formatting or displaying values (e.g., tooltip text).

       marker (Optional[DataPointMarker]):
           Optional configuration defining the appearance of data point markers.
    """

    def __init__(
        self,
        source_field: Field,
        name: str | None = None,
        color: str | None = None,
        display_field: str | None = None,
        marker: DataPointMarker | None = None,
    ):
        self._source_field = source_field
        self.source_field = source_field.id

        self.name = name
        self.color = color
        self.marker = marker
        self.display_field = display_field

    def set_name(self, name: str) -> "ChartSeries":
        """Sets the display name for this series."""
        self.name = name
        return self

    def set_color(self, color: str) -> "ChartSeries":
        """Sets the colour override for this series."""
        self.color = color
        return self

    def set_display_field(self, field: str) -> "ChartSeries":
        """Sets the alternate display field for tooltips or labels."""
        self.display_field = field
        return self

    def set_marker(self, marker: DataPointMarker) -> "ChartSeries":
        """Sets the marker configuration for individual data points."""
        self.marker = marker
        return self


@typechecked
class CombinationChartComponent(Buildable):
    """
    Represents a chart component capable of rendering multiple data series,
    potentially using different chart types within the same chart area.
    This component defines general chart configuration (such as orientation,
    stacking mode, and tooltip formatting) and holds all series that form
    the combination chart.

    Attributes:
        orientation (Optional[ChartViewOrientation]):
            Orientation of the chart.
        type (Optional[ChartType]):
            Chart type associated with this component.
        stacking (Optional[ChartViewStacking]):
            Stacking behaviour for all included series.
        point_label (Optional[str]):
            Label displayed for each data point.
        tooltip (Optional[str]):
            Hover text or formatting for data point tooltips.
        data_series (List[ChartSeries]):
            A collection of chart series included in the combination chart.
        series_colors (List[str]):
            Optional color overrides applied to each series in rendering order.
    """

    def __init__(
        self,
        orientation: ChartViewOrientation | None = None,
        chart_type: ChartType | None = None,
        stacking: ChartViewStacking | None = None,
        point_label: str | None = None,
        tooltip: str | None = None,
    ):
        self.orientation = orientation
        self.type = chart_type
        self.stacking = stacking
        self.point_label = point_label
        self.tooltip = tooltip
        self.data_series: list[ChartSeries] = []
        self.series_colors: list[str] = []

    def add_data_series(
        self,
        source_field: Field,
        name: str | None = None,
        color: str | None = None,
        display_field: str | None = None,
        marker: DataPointMarker | None = None,
    ):
        """
        Adds a new data series to the chart.

        Parameters:
            source_field (Field):
                Name of the field supplying values for this series.
            name (Optional[str]):
                Display name for the series.
            color (Optional[str]):
                Optional color override for the series.
            display_field (Optional[Field]):
                Optional alternate display field for tooltips or labels.
            marker (Optional[DataPointMarker]):
                Marker configuration for individual data points.

        Notes:
            This method constructs a new `ChartSeries` object and appends it
            to `self.data_series`.
        """
        data = ChartSeries(source_field, name, color, display_field, marker)
        self.data_series.append(data)

    def add_series_color(self, color: str):
        """
        Appends a color value to the list of series-level color overrides.

        Parameters:
            color (str):
                A color code or name used to override chart series colors
                in rendering order.
        """
        self.series_colors.append(color)
