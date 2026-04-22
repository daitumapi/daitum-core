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

from typeguard import typechecked

from daitum_ui._buildable import Buildable
from daitum_ui._composite_view import CompositeView, ScrollSync, ViewConfig
from daitum_ui.base_view import BaseView


class FlexDirection(Enum):
    """
    Defines the direction in which flex items are laid out in a flex container.

    Attributes:
        COLUMN: Items are laid out vertically from top to bottom.
        ROW: Items are laid out horizontally from left to right.
        COLUMN_REVERSE: Items are laid out vertically from bottom to top.
        ROW_REVERSE: Items are laid out horizontally from right to left.
    """

    COLUMN = "column"
    ROW = "row"
    COLUMN_REVERSE = "column-reverse"
    ROW_REVERSE = "row-reverse"


class FlexWrap(Enum):
    """
    Controls whether flex items wrap onto multiple lines. If wrapping is enabled, the children must
    have a cross-axis dimension set (e.g., height for row direction, width for column direction).

    Attributes:
        NOWRAP: All items are kept on a single line (default).
        WRAP: Items wrap onto multiple lines from top to bottom.
        WRAP_REVERSE: Items wrap onto multiple lines from bottom to top.
    """

    NOWRAP = "nowrap"
    WRAP = "wrap"
    WRAP_REVERSE = "wrap-reverse"


class FlexAlignment(Enum):
    """
    Defines how flex items are aligned within the container.

    Attributes:
        FLEX_START: Lines are packed to the start of the axis.
        FLEX_END: Lines are packed to the end of the axis.
        CENTER: Lines are centered along the axis.
        SPACE_BETWEEN: Even spacing between lines with no space at the edges.
        SPACE_AROUND: Even spacing around each line.
        SPACE_EVENLY: Equal spacing between all lines and edges.
        STRETCH: Lines stretch to fill the container. (Only applies to cross-axis alignment
            when wrapped)
    """

    FLEX_START = "flex-start"
    FLEX_END = "flex-end"
    CENTER = "center"
    SPACE_BETWEEN = "space-between"
    SPACE_AROUND = "space-around"
    SPACE_EVENLY = "space-evenly"
    STRETCH = "stretch"


class FlexAlignSelf(Enum):
    """
    Controls the cross-axis alignment of an individual flex item.

    Attributes:
        AUTO: Inherits the parent's align-items setting (default).
        FLEX_START: Aligns the item to the start of the cross axis.
        FLEX_END: Aligns the item to the end of the cross axis.
        CENTER: Centers the item along the cross axis.
        BASELINE: Aligns the item with the baseline of the parent.
        STRETCH: Stretches the item to fill the cross axis (if no height is set).
    """

    AUTO = "auto"
    FLEX_START = "flex-start"
    FLEX_END = "flex-end"
    CENTER = "center"
    BASELINE = "baseline"
    STRETCH = "stretch"


class GridAlignment(Enum):
    """
    Defines the default alignment of items inside a grid container.

    Attributes:
        START: Items are aligned to the start of the cell.
        END: Items are aligned to the end of the cell.
        CENTER: Items are centered within the cell.
        STRETCH: Items stretch to fill the entire space of the cell.
    """

    START = "start"
    END = "end"
    CENTER = "center"
    STRETCH = "stretch"


@typechecked
@dataclass
class FlexChild(Buildable):
    """
    Configuration options for a flex item (i.e., a child of a flex container).

    Attributes:
        flex_grow (Optional[float]):
            Determines how much the item should grow relative to others
            when there is extra space in the container.
            A value of 0 (default) means the item will not grow.
            A value of 1 or higher means the item can grow to fill remaining space,
            with higher values getting proportionally more.

            Example:
                If one item has flex_grow=2 and another has flex_grow=1,
                the first will get twice as much of the remaining space as the second.

        flex_shrink (Optional[float]):
            Determines how much the item should shrink relative to others
            when the container is too small to fit all items.
            A value of 1 (default) allows proportional shrinking.
            A value of 0 prevents shrinking at all.

            Example:
                If one item has flex_shrink=2 and another has flex_shrink=1,
                the first will shrink twice as much when space is constrained.

        flex_basis (Optional[str | int]):
            The initial size of the item before it is adjusted by grow or shrink.
            Can be an explicit size like "100px", a percentage, or "auto".
            Default is "auto".

        align_self (Optional[FlexAlignSelf]):
            Overrides the container’s `align-items` value for this individual item.
            Useful for one-off alignment behavior. Default is None.

        padding (Optional[str | int]):
            The padding inside the flex item. Can be any valid CSS padding value
            such as "10px", "1em", or "unset". Default is "unset".

        margin (Optional[str | int]):
            The margin around the flex item. Can be any valid CSS margin value
            such as "0", "8px", or "auto". Default is None.

        border (Optional[str]):
            CSS border definition for the item, e.g., "1px solid #ccc".
            Default is None.

        border_radius (Optional[str | int]):
            Rounding of corners. Accepts values like "4px" or "50%".
            Default is None.

        box_shadow (Optional[str]):
            Shadow styling for the item, e.g., "0 4px 6px rgba(0,0,0,0.1)".
            Default is None.

        background_color (Optional[str]):
            Background color of the flex item. Can be any valid CSS color value,
            e.g., "#f0f0f0", "rgba(255,255,255,0.8)", or "transparent".
            Default is None.
    """

    flex_grow: float | None = 0
    flex_shrink: float | None = 0
    flex_basis: str | int | None = "auto"
    align_self: FlexAlignSelf | None = None
    padding: str | int | None = "unset"
    margin: str | int | None = None
    border: str | None = "none"
    border_radius: str | int | None = None
    box_shadow: str | None = "none"
    background_color: str | None = None
    border_color: str | None = None
    width: str | None = None
    height: str | None = None


@typechecked
class FlexView(CompositeView):
    """
    A composite view that arranges its child views using CSS Flexbox layout.

    This view manages its children in a flexible container, allowing control
    over direction, alignment, wrapping, and spacing using standard Flexbox properties.

    Args:
        display_name (Optional[str], optional):
            A human-readable name for this view. Defaults to None.
        hidden (bool, optional):
            Whether the view is initially hidden. Defaults to False.
        scroll_sync_enabled (bool, optional):
            If True, enables synchronized scrolling with sibling views.
            Defaults to False.
        flex_direction (FlexDirection, optional):
            The main axis direction of the flex container.
            Defaults to `FlexDirection.COLUMN`.
        justify_content (FlexAlignment, optional):
            How children are distributed along the main axis.
            Defaults to `FlexAlignment.FLEX_START`.
        flex_wrap (FlexWrap, optional):
            Whether children wrap onto multiple lines.
            Defaults to `FlexWrap.NOWRAP`.
        align_content (FlexAlignment, optional):
            How multiple lines are aligned along the cross axis when wrapping.
            Defaults to `FlexAlignment.FLEX_START`.
        gap (str, optional):
            The gap between flex items, e.g., "5px", "1rem".
            Defaults to "5px".
    """

    def __init__(
        self,
        display_name: str | None = None,
        hidden: bool = False,
    ):
        parent_styles: dict = {
            "display": "flex",
            "flexDirection": FlexDirection.COLUMN.value,
            "justifyContent": FlexAlignment.FLEX_START.value,
            "flexWrap": FlexWrap.NOWRAP.value,
            "alignContent": FlexAlignment.FLEX_START.value,
            "gap": "5px",
        }
        super().__init__(display_name, hidden, parent_styles, False)

    def set_flex_direction(self, flex_direction: FlexDirection) -> "FlexView":
        """Sets the main axis direction of the flex container."""
        self.parent_styles["flexDirection"] = flex_direction.value
        return self

    def set_justify_content(self, justify_content: FlexAlignment) -> "FlexView":
        """Sets how children are distributed along the main axis."""
        self.parent_styles["justifyContent"] = justify_content.value
        return self

    def set_flex_wrap(self, flex_wrap: FlexWrap) -> "FlexView":
        """Sets whether children wrap onto multiple lines."""
        self.parent_styles["flexWrap"] = flex_wrap.value
        return self

    def set_align_content(self, align_content: FlexAlignment) -> "FlexView":
        """Sets how multiple lines are aligned along the cross axis when wrapping."""
        self.parent_styles["alignContent"] = align_content.value
        return self

    def set_gap(self, gap: str) -> "FlexView":
        """Sets the gap between flex items."""
        self.parent_styles["gap"] = gap
        return self

    def set_background_colour(self, colour: str) -> "FlexView":
        """Sets the background colour of the flex view."""
        self.parent_styles["backgroundColor"] = colour
        return self

    def set_padding(self, padding: str) -> "FlexView":
        """Sets the padding of the flex view."""
        self.parent_styles["padding"] = padding
        return self

    def set_scroll_sync_enabled(self, enabled: bool) -> "FlexView":
        """Sets whether synchronized scrolling with sibling views is enabled."""
        self.scroll_sync = ScrollSync(enabled)
        return self

    def add_child(self, view: BaseView, exclude_default_styling: bool = False, **kwargs):
        """
        Adds a child view to this composite layout with flexible styling options.

        Args:
            view (BaseView):
                The view to be added as a child within this composite layout.
            exclude_default_styling (bool, optional):
                If True, default system styling for the child view will be skipped.
                Defaults to False.
            **kwargs:
                Keyword arguments that define style configuration for this child view.
                All keys must correspond to attributes of the :class:`FlexChild` class, including
                layout behavior (e.g., `flex_grow`, `flex_shrink`, `align_self`) and visual styling
                (e.g., `padding`, `margin`, `border`, `box_shadow`, `background_color`).

                If a keyword does not match any attribute of :class:`FlexChild`, an `AttributeError`
                is raised.

        Raises:
            AttributeError:
                If any key in `**kwargs` does not match a valid `FlexChild` attribute.

        Example:
            >>> add_child(
            ...     view=some_view,
            ...     flex_grow=1,
            ...     padding="1rem",
            ...     background_color="#f0f0f0"
            ... )
        """
        child = FlexChild()

        for key, value in kwargs.items():
            if hasattr(child, key):
                setattr(child, key, value)
            else:
                raise AttributeError(f"{type(child).__name__} has no attribute '{key}'")

        view_config = ViewConfig(
            view_id=view.id,
            element_styles=child.build(),
            exclude_default_styling=exclude_default_styling,
        )
        self.children.append(view_config)
        return view_config


@typechecked
@dataclass
class GridChild(Buildable):
    """
    Configuration options for a grid item inside a grid container.

    Attributes:
        grid_column_start (Optional[str | int]):
            The starting grid column line where this item should be placed.
            Accepts an integer (e.g., 1), a string value (e.g., "auto" or "span 2").
            Example: `grid_column_start=2` places the item starting at the second vertical line.

        grid_column_end (Optional[str | int]):
            The ending grid column line. Defines how many columns the item spans.
            Example: `grid_column_end="span 3"` causes the item to span three columns.

        grid_row_start (Optional[str | int]):
            The starting grid row line where this item should be placed.
            Accepts a number or string like "auto" or "span 2".
            Example: `grid_row_start=1` places the item at the top of the grid.

        grid_row_end (Optional[str | int]):
            The ending grid row line. Defines how many rows the item spans.
            Example: `grid_row_end="span 2"` causes the item to span two rows.

        grid_area (Optional[str]):
            A named grid area that this item should occupy, defined in the
            parent container’s `grid-template-areas`.

        justify_self (Optional[JustifySelf]):
            Horizontal alignment of the item within its own grid cell.
            Overrides the container’s `justify-items` setting.
            Options: `start`, `end`, `center`, `stretch`.

        align_self (Optional[GridAlignment]):
            Vertical alignment of the item within its own grid cell.
            Overrides the container’s `align-items` setting.
            Options: `start`, `end`, `center`, `stretch`.

        padding (Optional[str | int]):
            Space between the item's content and its border.
            Can be specified in CSS units (e.g., `"1rem"`, `"10px"`).

        margin (Optional[str | int]):
            Space outside the item, separating it from other elements.
            Can be specified in CSS units.

        border (Optional[str]):
            Defines the item’s border. Accepts any valid CSS border definition.
            Example: `"1px solid #ccc"`.

        border_radius (Optional[str | int]):
            Rounds the corners of the item’s border.
            Example: `"4px"` or `"0.5rem"`.

        box_shadow (Optional[str]):
            Applies a shadow effect around the item.
            Example: `"0 1px 3px rgba(0,0,0,0.2)"`.

        background_color (Optional[str]):
            Sets the background color of the item.
            Can be any valid CSS color (hex, rgb, named, etc.).
            Example: `"#ffffff"` or `"rgba(0,0,0,0.1)"`.
    """

    grid_column_start: str | int | None = None
    grid_column_end: str | int | None = None
    grid_row_start: str | int | None = None
    grid_row_end: str | int | None = None
    grid_area: str | None = None
    justify_self: GridAlignment | None = None
    align_self: GridAlignment | None = None
    padding: str | int | None = "unset"
    margin: str | int | None = None
    border: str | None = "none"
    border_radius: str | int | None = None
    box_shadow: str | None = "none"
    background_color: str | None = None
    border_color: str | None = None
    width: str = "100%"
    height: str = "100%"


@typechecked
@dataclass
class GridLayout:
    """
    Defines CSS Grid layout.

    Attributes:
        columns (List[str]): Track sizing for columns, e.g., ["1fr", "2fr"].
        rows (List[str]): Track sizing for rows, e.g., ["auto", "1fr"].
        areas (Optional[List[List[str]]]): 2D list of area names; must match row and column
            dimensions.
    """

    columns: list[str]
    rows: list[str]
    areas: list[list[str]] | None = None

    def __post_init__(self):
        self._validate_area_dimensions()

    def build(self) -> dict:
        styles = {
            "gridTemplateColumns": " ".join(self.columns),
            "gridTemplateRows": " ".join(self.rows),
            "gridTemplateAreas": self._format_areas(),
        }

        if self.areas is not None:
            self._validate_area_dimensions()
            styles["gridTemplateAreas"] = self._format_areas()

        return styles

    def _validate_area_dimensions(self):
        assert self.areas is not None
        if len(self.areas) != len(self.rows):
            raise ValueError(
                f"Grid area rows ({len(self.areas)}) must match row tracks ({len(self.rows)})"
            )
        for row in self.areas:
            if len(row) != len(self.columns):
                raise ValueError(f"Each area row must match column count ({len(self.columns)})")

    def _format_areas(self) -> str:
        assert self.areas is not None
        return "\n".join(f'"{" ".join(row)}"' for row in self.areas)


@typechecked
class GridView(CompositeView):
    """
    A composite view that arranges child views using CSS Grid layout.

    This view uses a `GridLayout` object to define grid template properties,
    providing a powerful and flexible way to position children within rows and columns.

    Args:
        layout (GridLayout):
            The grid layout configuration that defines columns, rows, and areas.
        display_name (Optional[str], optional):
            A human-readable name for this view. Defaults to None.
        hidden (bool, optional):
            Whether the view is initially hidden. Defaults to False.
        scroll_sync_enabled (bool, optional):
            If True, enables synchronized scrolling with sibling views.
            Defaults to False.
        justify_items (GridAlignment, optional):
            Alignment of items along the inline (row) axis.
            Defaults to `GridAlignment.START`.
        align_items (GridAlignment, optional):
            Alignment of items along the block (column) axis.
            Defaults to `GridAlignment.START`.
        gap (str, optional):
            The gap between grid items (both rows and columns).
            Defaults to "5px".
        row_gap (Optional[str], optional):
            Overrides the gap between rows if specified.
        column_gap (Optional[str], optional):
            Overrides the gap between columns if specified.
    """

    def __init__(
        self,
        layout: GridLayout,
        display_name: str | None = None,
        hidden: bool = False,
    ):
        parent_styles: dict = {
            "display": "grid",
            "justifyItems": GridAlignment.START.value,
            "alignItems": GridAlignment.START.value,
            "gap": "5px",
            **layout.build(),
        }
        super().__init__(display_name, hidden, parent_styles, False)

    def set_scroll_sync_enabled(self, enabled: bool) -> "GridView":
        """Sets whether synchronized scrolling with sibling views is enabled."""
        self.scroll_sync = ScrollSync(enabled)
        return self

    def set_justify_items(self, justify_items: GridAlignment) -> "GridView":
        """Sets the alignment of items along the inline (row) axis."""
        self.parent_styles["justifyItems"] = justify_items.value
        return self

    def set_align_items(self, align_items: GridAlignment) -> "GridView":
        """Sets the alignment of items along the block (column) axis."""
        self.parent_styles["alignItems"] = align_items.value
        return self

    def set_gap(self, gap: str) -> "GridView":
        """Sets the gap between grid items."""
        self.parent_styles["gap"] = gap
        return self

    def set_row_gap(self, row_gap: str) -> "GridView":
        """Sets the gap between rows."""
        self.parent_styles["rowGap"] = row_gap
        return self

    def set_column_gap(self, column_gap: str) -> "GridView":
        """Sets the gap between columns."""
        self.parent_styles["columnGap"] = column_gap
        return self

    def set_background_colour(self, colour: str) -> "GridView":
        """Sets the background colour of the grid view."""
        self.parent_styles["backgroundColor"] = colour
        return self

    def set_padding(self, padding: str) -> "GridView":
        """Sets the padding of the grid view."""
        self.parent_styles["padding"] = padding
        return self

    def add_child(self, view: BaseView, exclude_default_styling: bool = False, **kwargs):
        """
        Adds a child view to this composite layout with flexible styling options.

        Args:
            view (BaseView):
                The view to be added as a child within this composite layout.
            exclude_default_styling (bool, optional):
                If True, default system styling for the child view will be skipped.
                Defaults to False.
            **kwargs:
                Keyword arguments that define style configuration for this child view.
                All keys must correspond to attributes of the :class:`GridChild` class.

                If a keyword does not match any attribute of :class:`GridChild`, an `AttributeError`
                is raised.

        Raises:
            AttributeError:
                If any key in `**kwargs` does not match a valid `GridChild` attribute.

        Example:
            >>> add_child(
            ...     view=some_view,
            ...     grid_area="header",
            ...     padding="1rem",
            ...     background_color="#f0f0f0"
            ... )
        """
        child = GridChild()

        for key, value in kwargs.items():
            if hasattr(child, key):
                setattr(child, key, value)
            else:
                raise AttributeError(f"{type(child).__name__} has no attribute '{key}'")

        view_config = ViewConfig(
            view_id=view.id,
            element_styles=child.build(),
            exclude_default_styling=exclude_default_styling,
        )
        self.children.append(view_config)
        return view_config
