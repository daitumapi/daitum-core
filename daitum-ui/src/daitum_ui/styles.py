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
Styling system for UI components in the UI Generator.

This module provides a comprehensive styling framework for controlling the visual
presentation and interactive behavior of UI elements. It includes style classes,
alignment options, editor configurations, and conditional formatting rules.

Main Components
---------------

**Alignment Enums:**
    - HorizontalAlignment: LEFT, CENTER, RIGHT, START, END
    - VerticalAlignment: TOP, MIDDLE, BOTTOM

**Style Classes:**
    Hierarchical styling system for UI components:

    - BaseStyle: Foundation styling (fonts, colors, alignment, borders)
    - CellStyle: Extends BaseStyle with cell-specific features (formatting, filtering)
    - ColumnStyle: Extends CellStyle with column features (frozen, editors, header styles)

**Editor Classes:**
    Custom input editors for specialized data types:

    - Editor: Abstract base class for all editors
    - PercentageEditor: For percentage value input
    - MonthEditor: For month selection
    - IconEditor: For icon selection/display
    - IconCheckboxEditor: Toggle between two icons (checkbox behavior)

**Editor Types:**
    EditorType enum defines available editor types: PERCENTAGE, MONTH, ICON, ICON_CHECKBOX

**Conditional Formatting:**
    - ConditionalFormattingType: BOOLEAN, AFTER_TODAY, BEFORE_TODAY
    - ConditionalFormattingRule: Applies styles based on column value conditions

**Additional Components:**
    - IconConfig: Icon configuration with source and color
    - Title: Title element with styling and positioning
    - Position: Title positioning (ABOVE_CONTENT, BELOW_CONTENT)

Style Hierarchy
---------------
Styles follow an inheritance hierarchy allowing progressive refinement::

    BaseStyle
    └── CellStyle
        └── ColumnStyle

Each level adds more specialized attributes:
- BaseStyle: Universal styling (fonts, colors, alignment, borders)
- CellStyle: Cell-specific (display formatting, field mapping, filtering)
- ColumnStyle: Column-specific (frozen state, editors, header/read-only overrides)

Alignment System
----------------
Two-dimensional alignment control:

**Horizontal alignment:**

- LEFT/CENTER/RIGHT: Absolute positioning
- START/END: Layout-direction-aware (supports RTL languages)
    Note: START/END not supported in BaseStyle; use LEFT/RIGHT instead

**Vertical alignment:**

- TOP: Align to top edge
- MIDDLE: Center vertically
- BOTTOM: Align to bottom edge

Editor System
-------------
Editors control how users interact with data in cells:

- **PercentageEditor**: Specialized input for percentage values (0-100%)
- **MonthEditor**: Month picker for month-based data
- **IconEditor**: Icon selector from available icon set
- **IconCheckboxEditor**: Binary toggle using custom on/off icons

Each editor can be assigned to a column via ColumnStyle.editor.

Conditional Formatting
----------------------
Apply styles dynamically based on data conditions:

**Condition Types:**

- BOOLEAN: Apply style if condition column is True
- AFTER_TODAY: Apply if date is after current date
- BEFORE_TODAY: Apply if date is before current date

**Rule Evaluation:**

- Rules evaluated in order of definition
- stop_if_true prevents subsequent rule evaluation
- Multiple rules can apply unless stopped

Examples
--------
Creating basic styles::

    from daitum_ui.styles import BaseStyle, HorizontalAlignment

    # Basic text styling
    header_style = BaseStyle(
        font_family="Arial",
        font_size=16,
        font_weight="bold",
        font_color="#333333",
        background_color="#f0f0f0",
        horizontal_alignment=HorizontalAlignment.CENTER
    )

Creating cell styles with formatting::

    from daitum_ui.styles import CellStyle

    # Currency cell with custom formatting
    price_cell_style = CellStyle(
        display_format="${value}",
        font_color="#2e7d32",
        horizontal_alignment=HorizontalAlignment.RIGHT,
        can_filter=True
    )

    # Date cell with formatting
    date_cell_style = CellStyle(
        display_format="yyyy-MM-dd",
        horizontal_alignment=HorizontalAlignment.CENTER
    )

Creating column styles with editors::

    from daitum_ui.styles import ColumnStyle, PercentageEditor, MonthEditor

    # Percentage column with specialized editor
    completion_column = ColumnStyle(
        editor=PercentageEditor(),
        display_format="{value}%",
        frozen=False,
        can_filter=True
    )

    # Month column with month picker
    month_column = ColumnStyle(
        editor=MonthEditor(),
        frozen=True
    )

Using icon editors::

    from daitum_ui.styles import IconCheckboxEditor, IconConfig
    from daitum_ui.icons import Icon

    # Checkbox column with custom icons
    status_column = ColumnStyle(
        editor=IconCheckboxEditor(
            on_icon=IconConfig(source=Icon.CHECK_CIRCLE, color="#4caf50"),
            off_icon=IconConfig(source=Icon.CANCEL, color="#f44336")
        )
    )

Conditional formatting examples::

    from daitum_ui.styles import (
        ConditionalFormattingRule,
        ConditionalFormattingType,
        ColumnStyle
    )

    # Highlight overdue items (date before today)
    overdue_rule = ConditionalFormattingRule(
        condition_column="due_date",
        override_styles=ColumnStyle(
            background_color="#ffebee",
            font_color="#c62828"
        ),
        type=ConditionalFormattingType.BEFORE_TODAY,
        stop_if_true=True
    )

    # Highlight completed items (boolean condition)
    completed_rule = ConditionalFormattingRule(
        condition_column="is_completed",
        override_styles=ColumnStyle(
            background_color="#e8f5e9",
            strikethrough=True
        ),
        type=ConditionalFormattingType.BOOLEAN,
        stop_if_true=False
    )

Creating headers with custom styles::

    # Column with distinct header style
    column_with_header = ColumnStyle(
        font_size=12,
        font_color="#333333",
        header_style=CellStyle(
            font_size=14,
            font_weight="bold",
            background_color="#1976d2",
            font_color="#ffffff",
            horizontal_alignment=HorizontalAlignment.CENTER
        )
    )

Frozen columns::

    # Frozen ID column that stays visible during scrolling
    id_column = ColumnStyle(
        frozen=True,
        font_weight="bold",
        width=80,
        can_filter=False
    )

Read-only column styling::

    # Column with distinct read-only appearance
    calculated_column = ColumnStyle(
        font_color="#666666",
        read_only_style=CellStyle(
            background_color="#fafafa",
            italic=True
        )
    )

Title styling::

    from daitum_ui.styles import Title, Position

    # Title above content
    view_title = Title(
        value="Sales Dashboard",
        style=BaseStyle(
            font_size=24,
            font_weight="bold",
            font_color="#1a237e"
        ),
        position=Position.ABOVE_CONTENT
    )

Border styling::

    # Cell with custom borders
    bordered_cell = CellStyle(
        border_top="2px solid #e0e0e0",
        border_bottom="2px solid #e0e0e0",
        border_left="1px solid #f5f5f5",
        border_right="1px solid #f5f5f5"
    )
"""

from __future__ import annotations

from abc import ABC
from dataclasses import dataclass, field
from enum import Enum
from typing import TYPE_CHECKING

from daitum_ui._buildable import Buildable, json_type_info
from daitum_ui.icons import Icon

if TYPE_CHECKING:
    from daitum_ui.elements import ElementStates


class HorizontalAlignment(Enum):
    """
    Specifies the horizontal alignment of an element within its container.

    Options:
        LEFT:
            Aligns the element to the left side.
        CENTER:
            Centers the element horizontally.
        RIGHT:
            Aligns the element to the right side.
        START:
            Aligns the element to the start edge, depending on layout direction.
        END:
            Aligns the element to the end edge, depending on layout direction.
    """

    LEFT = "LEFT"
    CENTER = "CENTER"
    RIGHT = "RIGHT"
    START = "START"
    END = "END"


class VerticalAlignment(Enum):
    """
    Specifies vertical alignment options for text or content within a UI element.

    Attributes:
        TOP: Aligns content to the top edge.
        MIDDLE: Centers content vertically.
        BOTTOM: Aligns content to the bottom edge.
    """

    TOP = "TOP"
    MIDDLE = "MIDDLE"
    BOTTOM = "BOTTOM"


@dataclass
class BaseStyle(Buildable):
    """
    Defines base-level styling attributes for UI components such as cells, headers, or columns.

    Includes options for font appearance, text alignment, colors, dimensions, and borders.

    Attributes:
        font_family (Optional[str]):
            Name of the font family to use (e.g., "Arial", "Roboto").

        font_size (Optional[int]):
            Size of the font in points or pixels.

        font_weight (Optional[str]):
            Weight of the font, typically values like "normal", "bold", or numeric strings like
            "400".

        italic (Optional[bool]):
            Whether the text should be rendered in italics.

        underline (Optional[bool]):
            Whether the text should be underlined.

        strikethrough (Optional[bool]):
            Whether the text should have a strikethrough line.

        width (Optional[int]):
            Optional fixed width of the UI element in pixels.

        font_color (Optional[str]):
            Color of the text, usually a hex code or CSS color string.

        background_color (Optional[str]):
            Background color of the element, also typically a hex or CSS color.

        horizontal_alignment (Optional[HorizontalAlignment]):
            Horizontal alignment of the content (e.g., left, center, right).

        vertical_alignment (Optional[VerticalAlignment]):
            Vertical alignment of the content (e.g., top, middle, bottom).

        border_top (Optional[str]):
            Style or color for the top border (e.g., "1px solid #000").

        border_right (Optional[str]):
            Style or color for the right border.

        border_bottom (Optional[str]):
            Style or color for the bottom border.

        border_left (Optional[str]):
            Style or color for the left border.
    """

    # Font settings
    font_family: str | None = None
    font_size: int | None = None
    font_weight: str | None = None
    italic: bool | None = None
    underline: bool | None = None
    strikethrough: bool | None = None
    width: int | None = None

    # Colours
    font_color: str | None = None
    background_color: str | None = None

    # Alignment
    horizontal_alignment: HorizontalAlignment | None = None
    vertical_alignment: VerticalAlignment | None = None

    # Borders
    border_top: str | None = None
    border_right: str | None = None
    border_bottom: str | None = None
    border_left: str | None = None

    def __post_init__(self):
        """
        Validate the container's horizontal alignment.

        If the user attempts to set an invalid alignment (START or END),
        a TypeError will be raised to indicate incorrect configuration.
        """
        if self.horizontal_alignment in {
            HorizontalAlignment.START,
            HorizontalAlignment.END,
        }:
            raise TypeError(
                f"HorizontalAlignment '{self.horizontal_alignment.value}' "
                "is not supported for this class."
            )


@dataclass
class CellStyle(BaseStyle):
    """
    Defines styling and behavioral options for a single cell in a table, extending `BaseStyle`.

    In addition to basic font, alignment, and color settings from `BaseStyle`, `CellStyle` includes
    options specific to how data is rendered and interacted with in a tabular UI context.

    Attributes:
        display_format (Optional[str]):
            A format string used to render the display value of the cell. This is typically used for
            numeric, date, or time formatting (e.g., "0.00" for two decimal places or "yyyy-MM-dd"
            for dates).

        display_field (Optional[str]):
            For map fields or object references, specifies the field in the underlying table
            whose value should be displayed in the cell.

        map_key_reference_field (Optional[str]):
            For cells representing map-type fields, this refers to another field in the same
            row whose value is used as the key to extract from the map. Typically this
            is a reference to a field holding the key dynamically.

        can_filter (Optional[bool]):
            Whether the column is user-filterable in the UI. If `True`, a filter control will
            be enabled for this column. Defaults to `None`.

        tooltip_field (Optional[str]):
            The field ID or named value ID containing the value to display in the tooltip.

        time_interval (Optional[int]):
            If provided, sets the time interval of the time picker in
            minutes for times and date times. Not valid for date pickers. Defaults to 30 minutes
            if not provided.
    """

    display_format: str | None = None
    display_field: str | None = None
    map_key_reference_field: str | None = None
    can_filter: bool | None = None
    tooltip_field: str | None = None
    time_interval: int | None = None


@dataclass
class IconConfig(Buildable):
    """
    Configuration for an icon used in UI elements.

    Attributes:
        source (Icon):
            The identifier for the icon.
        color (Optional[str]):
            Optional color override for the icon, specified as a string (e.g., hex code or
            color name).
    """

    source: Icon
    color: str | None = None


class EditorType(Enum):
    """
    Enumeration of supported editor types for UI fields.

    Attributes:
        PERCENTAGE: Editor specialized for percentage input.
        MONTH: Editor specialized for month selection.
        ICON: Editor that allows selection or display of an icon.
        ICON_CHECKBOX: Editor that toggles between two icons, functioning like a checkbox.
    """

    PERCENTAGE = "PERCENTAGE"
    MONTH = "MONTH"
    ICON = "ICON"
    ICON_CHECKBOX = "ICON_CHECKBOX"


class Editor(ABC, Buildable):
    """
    Abstract base class for all editor types used in UI fields.

    Subclasses should represent specific editor configurations and
    must provide the corresponding editor type through the `editor_type` attribute.

    This class acts as a marker and common base to enable polymorphic
    handling of different editor types.
    """

    # Subclasses should implement a property or class attribute `editor_type`


@json_type_info("percentage")
@dataclass
class PercentageEditor(Editor):
    """
    Editor configuration for input fields that accept percentages.

    Attributes:
        editor_type (EditorType): Constant identifying this as a percentage editor.
    """

    editor_type: EditorType = EditorType.PERCENTAGE


@json_type_info("month")
@dataclass
class MonthEditor(Editor):
    """
    Editor configuration for input fields that accept month values.

    Attributes:
        editor_type (EditorType): Constant identifying this as a month editor.
    """

    editor_type: EditorType = EditorType.MONTH


@json_type_info("icon")
@dataclass
class IconEditor(Editor):
    """
    Editor configuration for input fields that allow icon selection or display.

    Attributes:
        editor_type (EditorType): Constant identifying this as an icon editor.
    """

    editor_type: EditorType = EditorType.ICON


@json_type_info("iconCheckbox")
@dataclass
class IconCheckboxEditor(Editor):
    """
    Editor configuration for a toggleable icon checkbox input.

    Attributes:
        on_icon (IconConfig):
            Configuration for the icon to display when checked/on.
        off_icon (IconConfig):
            Configuration for the icon to display when unchecked/off.
        editor_type (EditorType): Constant identifying this as an icon checkbox editor.
    """

    on_icon: IconConfig
    off_icon: IconConfig
    editor_type: EditorType = EditorType.ICON_CHECKBOX


@dataclass
class ColumnStyle(CellStyle):
    """
    Defines styling and behavior specific to table columns, extending the generic cell styling
    with additional properties related to column interactivity and presentation.

    Attributes:
        frozen (bool):
            Indicates whether the column is frozen. Frozen columns remain visible
            when horizontally scrolling through the table.
        editor (Optional[Editor]):
            Configuration for the editor used in cells of this column. Defines how
            users can interact with or edit the column's data.
        header_style (Optional[CellStyle]):
            Styling overrides specifically applied to the column header cell,
            allowing for distinct header appearance separate from regular cells.
        read_only_style (Optional[CellStyle]):
            Styling overrides applied when the column is in a read-only state,
            typically used to visually distinguish non-editable columns.
    """

    frozen: bool = False
    editor: Editor | None = None
    header_style: CellStyle | None = None
    read_only_style: CellStyle | None = None


class ConditionalFormattingType(Enum):
    """
    Enumeration of supported conditional formatting types.

    Attributes:
        BOOLEAN:
            The condition is treated as a boolean. If True, the style is applied.
        AFTER_TODAY:
            Applies the style if the date in the condition column is after today's date.
        BEFORE_TODAY:
            Applies the style if the date in the condition column is before today's date.
    """

    BOOLEAN = "BOOLEAN"
    AFTER_TODAY = "AFTER_TODAY"
    BEFORE_TODAY = "BEFORE_TODAY"


@dataclass
class ConditionalFormattingRule(Buildable):
    """
    Defines a rule for conditionally applying styles to a column based on the value in another
    column.

    Attributes:
        condition_column (str):
            The ID or name of the column used to evaluate the condition.

        override_styles (ColumnStyle):
            The styles to apply if the condition is met. These override the default column style.

        element_states (ElementStates | None):
            The element state to apply if the condition is met.

        stop_if_true (bool):
            If True, no subsequent formatting rules are evaluated once this rule is satisfied.

        type (ConditionalFormattingType):
            The type of condition logic to apply. Defaults to BOOLEAN.
    """

    condition_column: str
    override_styles: ColumnStyle
    element_states: ElementStates | None = None
    stop_if_true: bool = False
    type: ConditionalFormattingType = field(default=ConditionalFormattingType.BOOLEAN)


class Position(Enum):
    """
    Enumeration to position a Title.

    Attributes:
        ABOVE_CONTENT: Display the title above the view.
        BELOW_CONTENT: Display the title below the view.
    """

    ABOVE_CONTENT = "ABOVE_CONTENT"
    BELOW_CONTENT = "BELOW_CONTENT"


@dataclass
class Title(Buildable):
    """
    Represents a title with associated styling and positioning.

    Attributes:
        value str:
            The text content of the title.

        style (Optional[BaseStyle]):
            The style to apply to the title text.

        position (Position):
            The position of the title relative to content.
            Defaults to Position.ABOVE_CONTENT.
    """

    value: str
    style: BaseStyle | None = None
    position: Position = Position.ABOVE_CONTENT
