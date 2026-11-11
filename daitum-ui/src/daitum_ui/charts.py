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
Chart and data visualisation components for the UI Generator.

Defines the chart types, orientation and stacking modes, data-point markers,
chart series, and the ``CombinationChartComponent`` container that holds one or
more series (optionally of mixed chart types) in a single visualisation.

Example:
    Create a line chart with a single data series::

        from daitum_ui.charts import (
            CombinationChartComponent,
            ChartType,
            ChartViewOrientation,
        )

        line_chart = CombinationChartComponent(
            chart_type=ChartType.LINE,
            orientation=ChartViewOrientation.VERTICAL,
        )
        line_chart.add_data_series(
            source_field=sales_table.revenue_field,
            name="Monthly Revenue",
            color="#2196f3",
        )

See the published documentation for further worked examples.
"""

from dataclasses import dataclass
from enum import Enum

from daitum_model import Field
from typeguard import typechecked

from daitum_ui._buildable import Buildable


class DataPointMarkerSymbol(Enum):
    """
    Enumeration of supported marker shapes for data points in charts.

    CIRCLE
        A circular marker shape.
    SQUARE
        A square marker shape.
    TRIANGLE
        An upward-pointing triangular marker.
    DIAMOND
        A diamond-shaped marker.
    TRIANGLE_DOWN
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
        """
        Args:
            source_field: The field whose values are plotted by this series.
            name: Optional display name shown in the legend and tooltips.
            color: Optional colour override (hex code or colour name).
            display_field: Optional alternate field ID used for label or tooltip text.
            marker: Optional visual configuration for individual data-point markers.
        """
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
            Optional colour overrides applied to each series in rendering order.
    """

    def __init__(
        self,
        orientation: ChartViewOrientation | None = None,
        chart_type: ChartType | None = None,
        stacking: ChartViewStacking | None = None,
        point_label: str | None = None,
        tooltip: str | None = None,
    ):
        """
        Args:
            orientation: Chart orientation (vertical or horizontal).
            chart_type: The chart type for this component (e.g. ``LINE``, ``BAR``).
            stacking: How multiple series are stacked (``NORMAL`` or ``PERCENT``).
            point_label: Optional label template displayed on each data point.
            tooltip: Optional tooltip template for hover interactions.
        """
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
                Optional colour override for the series.
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
        Appends a colour value to the list of series-level colour overrides.

        Parameters:
            color (str):
                A colour code or name used to override chart series colours
                in rendering order.
        """
        self.series_colors.append(color)
