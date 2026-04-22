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

from dataclasses import dataclass
from enum import Enum

from daitum_model import Calculation, DataType, Field, Parameter, Table
from typeguard import typechecked

from daitum_ui._buildable import Buildable, json_type_info
from daitum_ui.base_view import BaseView
from daitum_ui.filter_component import FilterableView, FilterComponent
from daitum_ui.model_event import ModelEvent


class XAxisHeader(Enum):
    """
    Defines the available header interval types for the Gantt chart x-axis.

    Attributes:
        QUARTER_HOUR:
            Displays x-axis headers at 15-minute intervals.
        HOUR:
            Displays x-axis headers at hourly intervals.
        HOUR_24:
            Displays x-axis headers at hourly intervals, with 24hr time.
        DAY:
            Displays x-axis headers daily.
        WEEK:
            Displays x-axis headers weekly, displaying start day of week.
        WEEK_LARGE:
            Displays x-axis headers weekly, displaying start day of week in extended format.
            Useful for top header row
        CALENDAR_WEEK:
            Displays x-axis headers weekly, based on calendar week.
        MONTH:
            Displays x-axis headers monthly.
        YEAR:
            Displays x-axis headers yearly.
        STANDARD_SCALING:
            Standard dynamic scaling, with AM/PM times.
        STANDARD_SCALING_24:
            Standard dynamic scaling, with 24hr times.
        CALENDAR_WEEK_SCALING:
            Calendar week dynamic scaling, with AM/PM times.
        CALENDAR_WEEK_SCALING_24:
            Calendar week dynamic scaling, with 24hr times.
        STANDARD_TOP_ROW:
            Top row (year-month-week-day) dynamic scaling.
        CALENDAR_WEEK_TOP_ROW:
            Top row (year-month-week-day) dynamic scaling with calendar weeks.
    """

    QUARTER_HOUR = "QUARTER_HOUR"
    HOUR = "HOUR"
    HOUR_24 = "HOUR_24"
    DAY = "DAY"
    WEEK = "WEEK"
    WEEK_LARGE = "WEEK_LARGE"
    CALENDAR_WEEK = "CALENDAR_WEEK"
    MONTH = "MONTH"
    YEAR = "YEAR"
    STANDARD_SCALING = "STANDARD_SCALING"
    STANDARD_SCALING_24 = "STANDARD_SCALING_24"
    CALENDAR_WEEK_SCALING = "CALENDAR_WEEK_SCALING"
    CALENDAR_WEEK_SCALING_24 = "CALENDAR_WEEK_SCALING_24"
    STANDARD_TOP_ROW = "STANDARD_TOP_ROW"
    CALENDAR_WEEK_TOP_ROW = "CALENDAR_WEEK_TOP_ROW"


class DragDropSnapInterval(Enum):
    """
    Determines the snapping behaviour when a user drags a task along
    the Gantt chart x-axis.

    Attributes:
        MINUTE:
            Snap dragged positions to 1-minute increments.
        FIVE_MINUTES:
            Snap positions to 5-minute increments.
        QUARTER_HOUR:
            Snap positions to 15-minute increments.
        HOUR:
            Snap positions to hourly increments.
        DAY:
            Snap positions to full-day increments.
    """

    MINUTE = "MINUTE"
    FIVE_MINUTES = "FIVE_MINUTES"
    QUARTER_HOUR = "QUARTER_HOUR"
    HOUR = "HOUR"
    DAY = "DAY"


class DragDropHandleBehaviour(Enum):
    """
    Specifies how drag-and-drop handles behave for Gantt chart tasks.

    Attributes:
        START_AND_END:
            Both the start and end of a task can be adjusted by dragging.
        START_ONLY:
            Only the start time of the task can be dragged.
        END_ONLY:
            Only the end time of the task can be dragged.
        NONE:
            Drag handles are disabled; tasks cannot be resized.
    """

    START_AND_END = "START_AND_END"
    START_ONLY = "START_ONLY"
    END_ONLY = "END_ONLY"
    NONE = "NONE"


class TooltipPropertyType(Enum):
    """
    Defines the types of tooltip properties that can be shown for a
    Gantt chart task.

    Attributes:
        START_DATE:
            Display the task's start date in the tooltip.
        END_DATE:
            Display the task's end date in the tooltip.
        CUSTOM:
            Display a custom field value based on the configuration.
    """

    START_DATE = "START_DATE"
    END_DATE = "END_DATE"
    CUSTOM = "CUSTOM"


class TooltipBoundary(Enum):
    """
    Determines the positional constraint applied when displaying
    tooltips within the Gantt chart.

    Attributes:
        WITHIN_CHART:
            The tooltip must remain within chart boundaries.
        NO_BOUNDARY:
            The tooltip may render outside chart boundaries if needed.
    """

    WITHIN_CHART = "WITHIN_CHART"
    NO_BOUNDARY = "NO_BOUNDARY"


class RangeSelectorButtonType(Enum):
    """
    Defines the time unit types available for range selector buttons.

    Attributes:
        HOUR:
            Selects a range measured in hours.
        DAY:
            Selects a range measured in days.
        WEEK:
            Selects a range measured in weeks.
        MONTH:
            Selects a range measured in months.
        YEAR:
            Selects a range measured in years.
        YTD:
            Selects a year-to-date range (from start of year to current date).
        ALL:
            Selects the entire available date range.
    """

    HOUR = "HOUR"
    DAY = "DAY"
    WEEK = "WEEK"
    MONTH = "MONTH"
    YEAR = "YEAR"
    YTD = "YTD"
    ALL = "ALL"


@typechecked
def _validate_field(field_obj: Field, *datatype: DataType):
    """
    Validate that a field matches one of the specified data types.

    Args:
        field_obj: The Field object to validate.
        *datatype: One or more DataType values that are acceptable for this field.

    Raises:
        ValueError: If the field's data type is not in the list of allowed types.
    """
    if field_obj.to_data_type() not in datatype:
        allowed_types = ", ".join([dt.value for dt in datatype])
        raise ValueError(f"Field '{field_obj.id}' must be of type: {allowed_types}.")


@typechecked
class TooltipProperty(Buildable):
    """
    Defines a single property to display in a Gantt chart task tooltip.

    Configures what information appears when hovering over or interacting
    with a task, including predefined properties (start/end dates) or
    custom field values.

    Attributes:
        type: The type of tooltip property (START_DATE, END_DATE, or CUSTOM).
        property_name: The display name for this property in the tooltip.
        value_source_field: The field ID containing the value to display.
    """

    def __init__(
        self,
        property_type: TooltipPropertyType,
        property_name: str,
        value_source_field: Field,
    ):
        """
        Initialize a TooltipProperty instance.

        Args:
            property_type: The type of property to display in the tooltip.
            property_name: The label to show for this property.
            value_source_field: The field containing the value to display.
        """
        self.type = property_type
        self.property_name = property_name
        self.value_source_field = value_source_field.id


@typechecked
class FontProperties(Buildable):
    """
    Configures font styling properties for Gantt chart tasks.

    Allows customization of text appearance by mapping font attributes
    to source fields in the underlying data.

    Args:
        font_color_source_field:
            Field containing the color value for task text.
        font_weight_source_field:
            Field containing the font weight.
        font_style_source_field:
            Field containing the font style.
    """

    def __init__(
        self,
        font_color_source_field: Field | None = None,
        font_weight_source_field: Field | None = None,
        font_style_source_field: Field | None = None,
    ):
        self.font_color_source_field = (
            font_color_source_field.id if font_color_source_field else None
        )
        self.font_weight_source_field = (
            font_weight_source_field.id if font_weight_source_field else None
        )
        self.font_style_source_field = (
            font_style_source_field.id if font_style_source_field else None
        )


@typechecked
class IconProperties(Buildable):
    """
    Configures icon properties for Gantt chart tasks.

    Allows customization of task icons by mapping icon attributes
    to source fields in the underlying data.

    Args:
        icon_source_source_field:
            Field containing the icon identifier or source.
        icon_color_source_field:
            Field containing the color value for the icon.
    """

    def __init__(
        self,
        icon_source_source_field: Field | None = None,
        icon_color_source_field: Field | None = None,
    ):
        self.icon_source_source_field = (
            icon_source_source_field.id if icon_source_source_field else None
        )
        self.icon_color_source_field = (
            icon_color_source_field.id if icon_color_source_field else None
        )


@typechecked
class Dependencies(Buildable):
    """
    Configures task dependencies for Gantt chart visualization.

    Defines relationships between tasks by mapping dependency information
    to a source field containing an array of related task IDs.

    Args:
        point_ids_source_field:
            Field containing an array of valid task IDs that this task depends on.
    """

    def __init__(
        self,
        point_ids_source_field: Field,
    ):
        _validate_field(point_ids_source_field, DataType.STRING_ARRAY)
        self.point_ids_source_field = point_ids_source_field.id


@dataclass
@typechecked
class RangeSelectorButton(Buildable):
    """
    Represents a button used in the Gantt or chart range selector.

    Attributes:
        type (RangeSelectorButtonType):
            The type of range selector option (e.g., DAY, WEEK, MONTH).
        count (int):
            A numeric value associated with the range (e.g., 7 days, 3 months).
        text (str):
            Optional display text shown on the button.
    """

    type: RangeSelectorButtonType
    count: int
    text: str


@typechecked
class GanttTaskDefinition(Buildable):
    """
    Defines the field mappings and configuration for Gantt chart tasks.

    Maps source data fields to task properties such as ID, dates, display names,
    colors, drag behavior, and visual styling. This class serves as the central
    configuration for how task data is interpreted and displayed in the Gantt chart.

    Attributes:
        id_field: Field ID for the unique task identifier.
        name_field: Field ID for the category name (tree-grid only).
        start_date_source_field: Field ID for the task start date.
        end_date_source_field: Field ID for the task end date.
        break_start_date_source_field: Field ID for break period start.
        break_end_date_source_field: Field ID for break period end.
        display_name_field: Field ID for the task display name.
        parent_field: Field ID for the parent task ID (tree-grid only).
        color_source_field: Field ID for the task color.
        border_color_source_field: Field ID for the task border color.
        drag_drop_x_source_field: Field ID for drag-drop enabled flag.
        on_click_source_field: Field ID for click event handler key.
        opacity_source_field: Field ID for task opacity.
        pattern_source_field: Field ID for visual pattern name.
        font_properties: Font styling configuration for task text.
        icon_properties: Icon configuration for task visualization.
        dependencies: Task dependency configuration.
        drag_drop_handle_behaviour_source_field: Field ID for drag handle behavior.
        tooltip_properties_source_field: Field for tooltip property definition key.
    """

    def __init__(
        self,
        id_field: Field,
        display_name_field: Field | None = None,
        drag_drop_x_source_field: Field | None = None,
        on_click_source_field: Field | None = None,
    ):
        """
        Initialize a GanttTaskDefinition instance.

        Args:
            id_field: Field containing unique task identifiers.
            display_name_field: Field containing the task display name.
            drag_drop_x_source_field: Field containing boolean flag for drag-drop
                (must be BOOLEAN type).
            on_click_source_field: Field containing click event handler key.

        Raises:
            ValueError: If validated fields are not of the required data type.
        """

        self.id_field = id_field.id

        self.name_field: str | None = None
        self.parent_field: str | None = None

        self.start_date_source_field: str | None = None
        self.end_date_source_field: str | None = None
        self.break_start_date_source_field: str | None = None
        self.break_end_date_source_field: str | None = None

        self.display_name_field = display_name_field.id if display_name_field else None

        self.color_source_field: str | None = None
        self.border_color_source_field: str | None = None

        if drag_drop_x_source_field:
            _validate_field(drag_drop_x_source_field, DataType.BOOLEAN)
            self.drag_drop_x_source_field: str | None = drag_drop_x_source_field.id
        else:
            self.drag_drop_x_source_field = None

        if on_click_source_field:
            _validate_field(on_click_source_field, DataType.DECIMAL)
            self.on_click_source_field: str | None = on_click_source_field.id
        else:
            self.on_click_source_field = None

        self.opacity_source_field: str | None = None
        self.pattern_source_field: str | None = None

        self.font_properties: FontProperties | None = None
        self.icon_properties: IconProperties | None = None
        self.dependencies: Dependencies | None = None

        self.drag_drop_handle_behaviour_source_field: str | None = None
        self.tooltip_properties_source_field: str | None = None

    def set_opacity_source_field(self, field: Field) -> "GanttTaskDefinition":
        """Sets the field providing opacity values for tasks."""
        self.opacity_source_field = field.id
        return self

    def set_pattern_source_field(self, field: Field) -> "GanttTaskDefinition":
        """Sets the field providing visual pattern identifiers for tasks."""
        self.pattern_source_field = field.id
        return self

    def set_drag_drop_handle_behaviour_source_field(self, field: Field) -> "GanttTaskDefinition":
        """Sets the field providing drag handle behaviour (must be STRING type)."""
        _validate_field(field, DataType.STRING)
        self.drag_drop_handle_behaviour_source_field = field.id
        return self

    def set_tooltip_properties_source_field(self, field: Field) -> "GanttTaskDefinition":
        """Sets the field identifying which tooltip definition to use."""
        self.tooltip_properties_source_field = field.id
        return self

    def set_date_source_fields(
        self, start: Field | None, end: Field | None
    ) -> "GanttTaskDefinition":
        """
        Configure the start and end date fields for tasks.

        Validates that provided fields are of DATE and DATETIME type before setting them
        as the source fields for task time ranges.

        Args:
            start: Field containing the task start date.
            end: Field containing the task end date.

        Raises:
            ValueError: If either field is not DATE or DATETIME type.
        """
        if start:
            _validate_field(start, DataType.DATE, DataType.DATETIME)
            self.start_date_source_field = start.id

        if end:
            _validate_field(end, DataType.DATE, DataType.DATETIME)
            self.end_date_source_field = end.id
        return self

    def set_break_date_source_fields(
        self, start: Field | None, end: Field | None
    ) -> "GanttTaskDefinition":
        """
        Configure the break period date fields for tasks.

        Defines fields that specify a break or pause period within a task's
        timeline. Validates that provided fields are of DATE or DATETIME type.

        Args:
            start: Field containing the break period start date.
            end: Field containing the break period end date.

        Raises:
            ValueError: If either field is not DATE or DATETIME type.
        """
        if start:
            _validate_field(start, DataType.DATE, DataType.DATETIME)
            self.break_start_date_source_field = start.id

        if end:
            _validate_field(end, DataType.DATE, DataType.DATETIME)
            self.break_end_date_source_field = end.id
        return self

    def set_colour_source_field(
        self, colour: Field | None, border_colour: Field | None
    ) -> "GanttTaskDefinition":
        """
        Configure the colour fields for task visual styling.

        Sets the fields that determine the fill colour and border colour
        for task bars in the Gantt chart.

        Args:
            colour: Field containing the task fill colour value.
            border_colour: Field containing the task border colour value.
        """
        self.color_source_field = colour.id if colour else None
        self.border_color_source_field = border_colour.id if border_colour else None
        return self

    def set_font_properties(
        self,
        font_color_source_field: Field | None = None,
        font_weight_source_field: Field | None = None,
        font_style_source_field: Field | None = None,
    ) -> FontProperties:
        """
        Configure font styling properties for task text.

        Creates and assigns a FontProperties object that maps fields to
        font styling attributes.

        Args:
            font_color_source_field: Field containing the text color.
            font_weight_source_field: Field containing the font weight.
            font_style_source_field: Field containing the font style.

        Returns:
            The created FontProperties instance.
        """
        font_properties = FontProperties(
            font_color_source_field, font_weight_source_field, font_style_source_field
        )
        self.font_properties = font_properties
        return font_properties

    def set_icon_properties(
        self,
        icon_source_source_field: Field | None = None,
        icon_color_source_field: Field | None = None,
    ) -> IconProperties:
        """
        Configure icon properties for task visualization.

        Creates and assigns an IconProperties object that maps fields to
        icon attributes for displaying icons on tasks.

        Args:
            icon_source_source_field: Field containing the icon identifier.
            icon_color_source_field: Field containing the icon color.

        Returns:
            The created IconProperties instance.
        """
        icon_properties = IconProperties(icon_source_source_field, icon_color_source_field)
        self.icon_properties = icon_properties
        return icon_properties

    def set_dependencies(self, point_ids_source_field: Field) -> Dependencies:
        """
        Configure task dependency relationships.

        Creates and assigns a Dependencies object that maps a field to
        an array of task IDs representing dependency relationships.

        Args:
            point_ids_source_field: Field containing an array of dependent task IDs
                (must be STRING_ARRAY type).

        Returns:
            The created Dependencies instance.

        Raises:
            ValueError: If the field is not of STRING_ARRAY type.
        """
        dependencies = Dependencies(point_ids_source_field)
        self.dependencies = dependencies
        return dependencies


@typechecked
class TreeGridGanttTaskDefinition(GanttTaskDefinition):
    """
    Specialized task definition for tree-grid Gantt views with hierarchical support.

    Extends GanttTaskDefinition to provide tree-grid specific functionality,
    including parent-child task relationships and category grouping. This
    allows tasks to be organized in a hierarchical tree structure.

    Inherits all attributes from GanttTaskDefinition.
    """

    def __init__(
        self,
        id_field: Field,
        display_name_field: Field | None = None,
        drag_drop_x_source_field: Field | None = None,
        on_click_source_field: Field | None = None,
    ):
        super().__init__(
            id_field,
            display_name_field,
            drag_drop_x_source_field,
            on_click_source_field,
        )

    def set_name_field(self, field: Field) -> "TreeGridGanttTaskDefinition":
        """
        Set the category name field for tree-grid Gantt views.

        This field is used to group multiple tasks on the same row when they
        share the same category and parent ID value. Only applicable to
        tree-grid type Gantt charts.

        Args:
            field: The field containing the category name.
        """
        self.name_field = field.id
        return self

    def set_parent_field(self, field: Field) -> "TreeGridGanttTaskDefinition":
        """
        Set the parent task ID field for hierarchical task relationships.

        Defines the field containing the parent task identifier, enabling
        tree-like task hierarchies. Only applicable to tree-grid type
        Gantt charts.

        Args:
            field: The field containing the parent task ID.
        """
        self.parent_field = field.id
        return self


@typechecked
class CategoryGanttTaskDefinition(GanttTaskDefinition):
    """
    Defines a category-based Gantt task configuration.

    This class extends class `GanttTaskDefinition` to describe how tasks
    should be interpreted and rendered in a category-style Gantt view.
    It primarily maps table fields to task-level behaviours and visual
    properties such as drag-and-drop behaviour, click handling, opacity,
    and tooltip configuration.

    Note:
        This definition is intended for category-based Gantt views and
        does not introduce additional task hierarchy fields beyond those defined in the base
        class `GanttTaskDefinition`.
    """

    def __init__(
        self,
        id_field: Field,
        display_name_field: Field | None = None,
        drag_drop_x_source_field: Field | None = None,
        on_click_source_field: Field | None = None,
    ):
        super().__init__(
            id_field,
            display_name_field,
            drag_drop_x_source_field,
            on_click_source_field,
        )


@typechecked
class GanttView(BaseView, FilterableView):
    """
    Base class for Gantt chart views that visualize time-based task data.

    Provides core functionality for configuring Gantt chart behavior including
    x-axis settings, drag-and-drop interactions, tooltips, navigation, and
    event handling. This class serves as the foundation for specific Gantt
    view implementations.

    Attributes:
        table: The data table containing task information.
        gantt_task_definition: Configuration mapping fields to task properties.
        chart_title: Optional title displayed on the chart.
        on_click_handler_mapping: Maps task keys to click event handlers.
        x_axis_min_field: Field ID for the minimum x-axis value.
        x_axis_max_field: Field ID for the maximum x-axis value.
        with_drag_drop_x: Whether drag-and-drop is enabled on the x-axis.
        with_x_axis_header: Whether x-axis headers are displayed.
        drag_drop_handle_behaviour: Configuration for drag handle behavior.
        snap_x_axis_drag: Snapping interval for drag operations.
        x_axis_headers: List of x-axis header configurations.
        range_selector_buttons: List of range selector button configurations.
        tooltip_properties_mapping: Maps task keys to tooltip property lists.
        with_navigator: Whether the navigator is enabled.
        tooltip_disabled: Whether tooltips are disabled.
        tooltip_boundary: Boundary constraint for tooltip positioning.
    """

    def __init__(
        self,
        table: Table,
        gantt_task_definition: GanttTaskDefinition,
        display_name: str | None = None,
        hidden: bool = False,
    ):
        """
        Initialize a GanttView instance.

        Args:
            table: The data table containing task records.
            gantt_task_definition: Configuration defining how fields map to task properties.
            display_name: Optional name displayed for this view in the UI.
            hidden: Whether the view should be hidden by default.
        """
        # Initialise BaseView
        BaseView.__init__(self, hidden)
        if display_name is not None:
            self._display_name = display_name
        FilterableView.__init__(self, None)

        self.table = table.id
        self.gantt_task_definition = gantt_task_definition
        self.chart_title: str | None = None
        self.on_click_handler_mapping: dict[str, ModelEvent] = {}

        self.x_axis_min_field: str | None = None
        self.x_axis_max_field: str | None = None
        self.with_drag_drop_x: bool = False
        self.with_x_axis_header: bool = True
        self.drag_drop_handle_behaviour: DragDropHandleBehaviour | None = None
        self.snap_x_axis_drag: DragDropSnapInterval | None = None

        self.x_axis_headers: list[XAxisHeader] = [
            XAxisHeader.STANDARD_SCALING,
            XAxisHeader.STANDARD_TOP_ROW,
        ]
        self.range_selector_buttons: list[RangeSelectorButton] = []
        self.tooltip_properties_mapping: dict[str, list[TooltipProperty]] = {}

        self.with_navigator: bool = False
        self.tooltip_disabled: bool = False
        self.tooltip_boundary: TooltipBoundary | None = None

    def set_use_filter(self, use_filter: FilterComponent) -> "GanttView":
        """Attaches a filter component to this Gantt view."""
        FilterableView.__init__(self, use_filter)
        return self

    def set_x_axis_behaviour(
        self,
        min_field: Parameter | Calculation | None,
        max_field: Parameter | Calculation | None,
    ) -> "GanttView":
        """
        Configure the x-axis range boundaries using field values.

        Validates that the provided fields have supported data types
        before assigning them as the minimum and maximum x-axis limits.

        Args:
            min_field (Optional[Parameter | Calculation]):
                Field representing the minimum x-axis value (start of range).

            max_field (Optional[Parameter | Calculation]):
                Field representing the maximum x-axis value (end of range).

        Raises:
            ValueError:
                If a provided field has an unsupported data type.
        """
        if min_field:
            if min_field.to_data_type() not in [DataType.DATE, DataType.DATETIME]:
                raise ValueError(f"Invalid datatype: {min_field.to_data_type()}")
            self.x_axis_min_field = min_field.to_string()
        if max_field:
            if max_field.to_data_type() not in [DataType.DATE, DataType.DATETIME]:
                raise ValueError(f"Invalid datatype: {max_field.to_data_type()}")
            self.x_axis_max_field = max_field.to_string()
        return self

    def set_drag_drop_behaviour(
        self,
        drag_drop_snap_interval: DragDropSnapInterval | None,
        drag_drop_handle_behaviour: DragDropHandleBehaviour | None,
    ) -> "GanttView":
        """
        Configure drag-and-drop behavior for Gantt chart tasks.

        Sets the snapping interval and handle behavior for dragging tasks.
        Automatically enables drag-and-drop functionality if either parameter
        is provided.

        Args:
            drag_drop_snap_interval: The interval to which dragged positions snap
                (e.g., MINUTE, HOUR, DAY).
            drag_drop_handle_behaviour: Defines which handles are available for
                dragging (e.g., START_AND_END, START_ONLY, END_ONLY, NONE).
        """
        self.drag_drop_handle_behaviour = (
            drag_drop_handle_behaviour if drag_drop_handle_behaviour else None
        )
        self.snap_x_axis_drag = drag_drop_snap_interval if drag_drop_snap_interval else None
        return self

    def add_on_click_handler_mapping(self, key: str, event: ModelEvent):
        """
        Register a click event handler for a specific task key.

        Args:
            key: The unique identifier for the task.
            event: The ModelEvent to trigger when the task is clicked.
        """
        self.on_click_handler_mapping[key] = event

    def add_x_axis_header(self, x_axis_header: XAxisHeader) -> None:
        """
        Adds a unique x-axis header and set with_x_axis_header to True. Duplicate headers are
        ignored.
        """
        if x_axis_header not in self.x_axis_headers:
            self.x_axis_headers.append(x_axis_header)
            self.with_x_axis_header = True

    def set_standard_x_axis_header(self) -> None:
        """
        Sets the X-axis header to the standard set.
        """
        self.x_axis_headers = [
            XAxisHeader.STANDARD_SCALING,
            XAxisHeader.STANDARD_TOP_ROW,
        ]

    def set_standard_24_x_axis_header(self) -> None:
        """
        Sets the X-axis header to the standard 24hr time set.
        """
        self.x_axis_headers = [
            XAxisHeader.STANDARD_SCALING_24,
            XAxisHeader.STANDARD_TOP_ROW,
        ]

    def set_calendar_week_x_axis_header(self) -> None:
        """
        Sets the X-axis header to the calendar week set.
        """
        self.x_axis_headers = [
            XAxisHeader.CALENDAR_WEEK_SCALING,
            XAxisHeader.CALENDAR_WEEK_TOP_ROW,
        ]

    def set_calendar_week_24_x_axis_header(self) -> None:
        """
        Sets the X-axis header to the calendar week set with 24hr time.
        """
        self.x_axis_headers = [
            XAxisHeader.CALENDAR_WEEK_SCALING_24,
            XAxisHeader.CALENDAR_WEEK_TOP_ROW,
        ]

    def add_range_selector_buttons(
        self, button_type: RangeSelectorButtonType, count: int, text: str
    ):
        """
        Add a range selector button to the Gantt chart controls.

        Range selector buttons allow users to quickly change the visible time range
        (e.g., "Last 7 Days", "This Month", "Next Quarter").

        Args:
            button_type: The type of time range for the button (e.g., DAY, WEEK, MONTH).
            count: The number of time units to include in the range.
            text: A custom label text for the button.
        """
        range_selector_button = RangeSelectorButton(button_type, count, text)
        self.range_selector_buttons.append(range_selector_button)

    def add_tooltip_properties_mapping(self, key: str, property_list: list[TooltipProperty]):
        """
        Configure tooltip properties for a specific task key.

        Defines which properties should be displayed in the tooltip when
        hovering over or interacting with a task.

        Args:
            key: The unique identifier for the task.
            property_list: List of TooltipProperty objects defining what information
                to display in the tooltip (e.g., start date, end date, custom fields).
        """
        self.tooltip_properties_mapping[key] = property_list


@typechecked
@json_type_info("tree grid gantt")
class TreeGridGanttView(GanttView):
    """
    A specialized Gantt view that combines a tree grid with Gantt chart visualization.

    Extends the base GanttView to provide a hierarchical tree structure alongside
    the timeline visualization, allowing users to see task relationships and
    dependencies in a tree format while viewing their schedules.
    """

    def __init__(
        self,
        table: Table,
        gantt_task_definition: TreeGridGanttTaskDefinition,
        display_name: str | None = None,
        hidden: bool = False,
        use_filter: FilterComponent | None = None,
    ):
        """
        Initialize a TreeGridGanttView instance.

        Args:
            table: The data table containing task records.
            gantt_task_definition: TreeGridGanttTaskDefinition with tree-grid specific
                configuration.
            display_name: Optional name displayed for this view in the UI.
            hidden: Whether the view should be hidden by default.
            use_filter: The identifier (filter name) of a ViewFilterDef
                to apply when querying data for this view.
        """
        GanttView.__init__(self, table, gantt_task_definition, display_name, hidden)
        if use_filter is not None:
            FilterableView.__init__(self, use_filter)


@typechecked
@json_type_info("category gantt")
class CategoryGanttView(GanttView):
    """
    A Gantt view that organizes tasks into categories along the y-axis.

    Extends the base GanttView to support categorical organization of tasks,
    where the y-axis represents different categories (e.g., resources, teams,
    or departments) rather than a hierarchical tree structure. Tasks can be
    grouped and displayed in rows corresponding to their category.

    Attributes:
        y_axis_source: Table ID containing the category definitions.
        y_axis_display_field: Field ID for the category display name.
        y_axis_reference_field: Field ID linking tasks to their category.
        with_drag_drop_y: Whether tasks can be dragged between categories.
    """

    def __init__(
        self,
        table: Table,
        gantt_task_definition: CategoryGanttTaskDefinition,
        display_name: str | None = None,
        hidden: bool = False,
    ):
        """
        Initialize a CategoryGanttView instance.

        Args:
            table: The data table containing task records.
            gantt_task_definition: Configuration defining how fields map to task properties.
            display_name: Optional name displayed for this view in the UI.
            hidden: Whether the view should be hidden by default.
        """
        GanttView.__init__(self, table, gantt_task_definition, display_name, hidden)

        self.y_axis_source: str | None = None
        self.y_axis_display_field: str | None = None
        self.y_axis_reference_field: str | None = None
        self.with_drag_drop_y: bool | None = None

    def set_use_filter(self, use_filter: FilterComponent) -> "CategoryGanttView":
        """Attaches a filter component to this Gantt view."""
        self.use_filter = use_filter.filter_name
        self.show_filter = use_filter.filter_name
        return self

    def set_y_axis(
        self,
        y_axis_source: Table,
        y_axis_display_field: Field | None = None,
        y_axis_reference_field: Field | None = None,
    ) -> "CategoryGanttView":
        """
        Configures the y-axis category source and display fields.

        Args:
            y_axis_source: The table containing category definitions for the y-axis.
            y_axis_display_field: The field in y_axis_source to display as category labels.
            y_axis_reference_field: The field linking tasks to their category in y_axis_source.

        Raises:
            ValueError: If y_axis_display_field is not a field in the y_axis_source table.
        """
        if y_axis_display_field and y_axis_display_field not in y_axis_source.get_fields():
            raise ValueError(f"{y_axis_display_field} is not in the table {y_axis_source}.")

        self.y_axis_source = y_axis_source.id
        self.y_axis_display_field = y_axis_display_field.id if y_axis_display_field else None
        self.y_axis_reference_field = y_axis_reference_field.id if y_axis_reference_field else None
        return self

    def set_with_drag_drop_y(self, with_drag_drop_y: bool) -> "CategoryGanttView":
        """Sets whether tasks can be dragged between categories on the y-axis."""
        self.with_drag_drop_y = with_drag_drop_y if with_drag_drop_y else None
        return self
