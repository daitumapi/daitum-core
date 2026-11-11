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

Provides style classes, alignment options, editor configurations, and conditional
formatting rules for controlling the appearance and interactive behaviour of UI
elements. Styles follow an inheritance hierarchy (BaseStyle -> CellStyle ->
ColumnStyle), each level adding more specialised attributes.

Example:
    >>> from daitum_ui.styles import BaseStyle, HorizontalAlignment
    >>> header_style = BaseStyle(
    ...     font_family="Arial",
    ...     font_size=16,
    ...     font_weight="bold",
    ...     font_color="#333333",
    ...     background_color="#f0f0f0",
    ...     horizontal_alignment=HorizontalAlignment.CENTER,
    ... )
"""

from __future__ import annotations

from abc import ABC
from dataclasses import dataclass, field
from enum import Enum
from typing import TYPE_CHECKING, ClassVar

from daitum_model import Calculation, Field, Parameter

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
            Centres the element horizontally.
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
        MIDDLE: Centres content vertically.
        BOTTOM: Aligns content to the bottom edge.
    """

    TOP = "TOP"
    MIDDLE = "MIDDLE"
    BOTTOM = "BOTTOM"


@dataclass
class BaseStyle(Buildable):
    """
    Defines base-level styling attributes for UI components such as cells, headers, or columns.

    Includes options for font appearance, text alignment, colours, dimensions, and borders.

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
            Colour of the text, usually a hex code or CSS colour string.

        background_color (Optional[str]):
            Background colour of the element, also typically a hex or CSS colour.

        horizontal_alignment (Optional[HorizontalAlignment]):
            Horizontal alignment of the content (e.g., left, center, right).

        vertical_alignment (Optional[VerticalAlignment]):
            Vertical alignment of the content (e.g., top, middle, bottom).

        border_top (Optional[str]):
            Style or colour for the top border (e.g., "1px solid #000").

        border_right (Optional[str]):
            Style or colour for the right border.

        border_bottom (Optional[str]):
            Style or colour for the bottom border.

        border_left (Optional[str]):
            Style or colour for the left border.
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
    Defines styling and behavioural options for a single cell in a table, extending `BaseStyle`.

    In addition to basic font, alignment, and colour settings from `BaseStyle`, `CellStyle` includes
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
            Optional colour override for the icon, specified as a string (e.g., hex code or
            colour name).
    """

    source: Icon
    color: str | None = None


class EditorType(Enum):
    """
    Enumeration of supported editor types for UI fields.

    Attributes:
        PERCENTAGE: Editor specialised for percentage input.
        MONTH: Editor specialised for month selection.
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
    Defines styling and behaviour specific to table columns, extending the generic cell styling
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


@dataclass
class AxisLabelStyle(Buildable):
    """
    Styling for a chart axis' labels.

    Values are CSS values, exactly as they are for a task's colour and font fields. Properties set
    directly here are the default for every label. `property_field_mapping` overrides them per row:
    the key is one of the supported properties, the value a reference to a field, a named value, or
    a literal. Conditional styling comes from the model, by pointing a property at a calculated
    field.

    `property_field_mapping` is populated only via `add_property_field_mapping`, which validates
    the key against `SUPPORTED_PROPERTIES`; it is not a constructor argument.

    Attributes:
        color: Default CSS text colour for every label.
        background_color: Default CSS background colour for every label.
        font_weight: Default CSS font weight.
        font_style: Default CSS font style.
        font_size: Default CSS font size.
        text_decoration: Default CSS text decoration.
        padding: Default CSS padding.
        border_radius: Default CSS border radius.
        border_left: Default CSS left border.
        width: Default CSS width.
        property_field_mapping: Maps a supported property to the field, named value or literal
            supplying its value per row.
    """

    SUPPORTED_PROPERTIES: ClassVar[frozenset[str]] = frozenset(
        {
            "color",
            "backgroundColor",
            "fontWeight",
            "fontStyle",
            "fontSize",
            "textDecoration",
            "padding",
            "borderRadius",
            "borderLeft",
            "width",
        }
    )

    color: str | None = None
    background_color: str | None = None
    font_weight: str | None = None
    font_style: str | None = None
    font_size: str | None = None
    text_decoration: str | None = None
    padding: str | None = None
    border_radius: str | None = None
    border_left: str | None = None
    width: str | None = None
    property_field_mapping: dict[str, str] = field(init=False, default_factory=dict)

    def add_property_field_mapping(
        self, property_name: str, value: Field | Parameter | Calculation | str
    ) -> AxisLabelStyle:
        """
        Override a label property per row, from a field, named value or literal.

        Args:
            property_name: One of the supported CSS properties (camelCase, e.g. "backgroundColor").
            value: A Field (of the axis' own table), a Parameter/Calculation named value, or a
                literal string supplying the property's value for each row.

        Raises:
            ValueError: If property_name is not a supported property.
        """
        if property_name not in self.SUPPORTED_PROPERTIES:
            supported = ", ".join(sorted(self.SUPPORTED_PROPERTIES))
            raise ValueError(
                f"Unsupported axis label property '{property_name}'. "
                f"Supported properties are: {supported}."
            )
        reference = value if isinstance(value, str) else value.to_string()
        self.property_field_mapping[property_name] = reference
        return self
