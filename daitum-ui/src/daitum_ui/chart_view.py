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
Chart view components for the UI Generator framework.

Provides chart visualisation through the ``ChartView`` and ``CombinationChartView``
classes, covering bar, line, pie and scatter charts with multiple data series,
axis configuration and styling. ``CombinationChartView`` adds mixed chart types
(e.g. line + bar) within a single view via chart components.

Example:
    >>> builder = UiBuilder()
    >>> chart_view = builder.add_chart_view(
    ...     primary_series=primary_series,
    ...     chart_type=ChartType.BAR,
    ...     table=sales_table,
    ...     display_name="Sales Dashboard"
    ... )
    >>> chart_view.set_chart_title("Monthly Revenue")
"""

from daitum_model import Field, Table
from typeguard import typechecked

from daitum_ui._buildable import json_type_info
from daitum_ui.base_view import BaseView
from daitum_ui.charts import (
    ChartSeries,
    ChartType,
    ChartViewOrientation,
    ChartViewStacking,
    CombinationChartComponent,
)
from daitum_ui.filter_component import FilterableView, FilterComponent


@typechecked
@json_type_info("chart")
class ChartView(BaseView, FilterableView):
    """
    Represents a chart view configuration within the UI model. This class defines
    chart metadata, axes configuration, series data, and rendering behaviour.

    Attributes:
        table (str):
            The table providing the source data for this chart.
        chart_title (ChartSeries):
            Title text displayed above the chart.
        primary_series (ChartSeries):
            The primary chart series used to position or group data points.
        secondary_series (ChartSeries):
            Additional series used for secondary grouping or comparative displays.
        orientation (ChartViewOrientation):
            Orientation of the chart (vertical or horizontal).
        type (ChartType):
            Type of chart to render (line, bar, pie, scatter, etc.).
        stacking (ChartViewStacking):
            Stacking behaviour for multi-series charts (normal or percent).
        xaxis_label (str | None):
            Label text displayed along the X-axis.
        yaxis_label (str | None):
            Label text displayed along the Y-axis.
        xaxis_type (str | None):
            Defines how x-axis values are interpreted (e.g., numeric, category, datetime).
        ignore_empty_series (bool):
            Whether to hide or skip rendering for data series with no values.
        point_label (str | None):
            Custom label displayed on individual data points (if supported).
        tooltip (str | None):
            Tooltip text or template for hover interactions.
        data_series (list[ChartSeries]):
            A list of additional chart data series beyond the primary and secondary series.
        series_colors (list[str] | None):
            Optional colour overrides applied to series in rendering order.
    """

    def __init__(
        self,
        primary_series: ChartSeries,
        chart_type: ChartType,
        table: Table,
        display_name: str | None = None,
        hidden: bool = False,
    ):
        """
        Args:
            primary_series: The primary data series for the chart.
            chart_type: The chart type to render.
            table: The source data table.
            display_name: Optional display name for this view.
            hidden: If ``True``, the view is not visible in the UI.

        Raises:
            ValueError: If any series references a field not present in *table*.
        """
        BaseView.__init__(self, hidden)
        if display_name is not None:
            self._display_name = display_name
        FilterableView.__init__(self, None)
        self._table = table
        self.table = table.id
        self.chart_title: str | None = None
        self.primary_series = primary_series
        self.secondary_series: ChartSeries | None = None

        self.orientation: ChartViewOrientation = ChartViewOrientation.HORIZONTAL
        self.type = chart_type
        self.stacking: ChartViewStacking | None = None
        self.xaxis_label: str | None = None
        self.yaxis_label: str | None = None
        self.xaxis_type: str | None = None
        self.ignore_empty_series: bool = False
        self.point_label: str | None = None
        self.tooltip: str | None = "{<b>{point.name}</b>}"

        self.data_series: list[ChartSeries] = []
        self.series_colors: list[str] | None = None

        self._validate_chart_series()

    def set_chart_title(self, chart_title: str) -> "ChartView":
        """Sets the title displayed above the chart."""
        self.chart_title = chart_title
        return self

    def set_secondary_series(self, secondary_series: ChartSeries) -> "ChartView":
        """Sets the secondary data series for comparative display."""
        self.secondary_series = secondary_series
        self._validate_chart_series()
        return self

    def set_use_filter(self, use_filter: FilterComponent) -> "ChartView":
        """Attaches a filter component to this chart view."""
        FilterableView.__init__(self, use_filter)
        return self

    def _validate_chart_series(self):
        """
        Check if chart series are in the table.

        Raises:
            Raises ValueError if a ChartSeries references a field that does not exist
            in the associated table.

        """
        all_series = [self.primary_series]
        if self.secondary_series is not None:
            all_series.append(self.secondary_series)
        for series in all_series:
            if series._source_field not in self._table.get_fields():
                raise ValueError(
                    f"Field '{series.source_field}' not found in table '{self.table}'."
                )

    def add_data_series(
        self,
        source_field: Field,
    ) -> ChartSeries:
        """
        Adds a new data series to the chart.

        Parameters:
            source_field (Field):
                Name of the field supplying values for this series.

        Returns:
            ChartSeries: The constructed series for further configuration via setters.

        Raises:
            ValueError: If the field does not exist in the associated table.
        """
        if source_field not in self._table.get_fields():
            raise ValueError(f"Field '{source_field}' not found in table '{self.table}'.")

        data = ChartSeries(source_field)
        self.data_series.append(data)
        return data

    def add_series_color(self, color: str):
        """
        Appends a colour value to the list of series-level colour overrides.

        Parameters:
            color (str):
                A colour code or name used to override chart series colours
                in rendering order.
        """
        if self.series_colors is None:
            self.series_colors = []
        self.series_colors.append(color)


@typechecked
@json_type_info("combination chart")
class CombinationChartView(ChartView):
    """
    A view definition used for rendering combination charts.

    This class extends :class:`ChartView` by allowing multiple
    :class:`CombinationChartComponent` objects to be attached to the chart.
    A combination chart typically includes multiple dataset types or multiple
    chart styles (e.g., line + bar), which are represented as individual
    components.

    Parameters:
        display_name:
            Display name of the chart view.
        hidden:
            Whether the chart view should be initially hidden.
        table:
            Optional data source table from which the chart values are derived.
        chart_title:
            Title displayed above the chart.
        primary_series:
            Primary data series associated with the chart.
        secondary_series:
            Secondary data series (if applicable).
    """

    def __init__(
        self,
        primary_series: ChartSeries,
        chart_type: ChartType,
        table: Table,
        display_name: str | None = None,
        hidden: bool = False,
    ):
        """
        Args:
            primary_series: The primary data series for the chart.
            chart_type: The default chart type for new components.
            table: The source data table.
            display_name: Optional display name for this view.
            hidden: If ``True``, the view is not visible in the UI.
        """
        super().__init__(primary_series, chart_type, table, display_name, hidden)
        self.chart_components: list[CombinationChartComponent] = []

    def add_combination_chart_component(self, chart_component: CombinationChartComponent):
        """
        Add a CombinationChartComponent to the view with field validation.

        This method validates all data series defined within the given
        CombinationChartComponent to ensure that their `source_field` and optional
        `display_field` exist in the associated table. If any referenced field
        does not exist, a ValueError is raised.

        Args:
            chart_component: The combination chart component containing one or
                more ChartSeries definitions to attach to this view.

        Raises:
            ValueError: If any series references a `source_field` or `display_field`
                that does not exist in the underlying table.

        """
        data_series = chart_component.data_series
        if data_series:
            for series in data_series:
                if series.source_field not in self._table.get_fields():
                    raise ValueError(
                        f"Field '{series.source_field}' not found in table '{self.table}'."
                    )

                if series.display_field is not None:
                    if series.display_field not in self._table.get_fields():
                        raise ValueError(
                            f"Field '{series.source_field}' not found in table '{self.table}'."
                        )
        self.chart_components.append(chart_component)
