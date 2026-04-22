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
UI element definitions for the UI Generator system.

This module provides the core building blocks for constructing user interfaces,
including base classes, containers, and interactive elements. All elements support
state management, data binding, and event handling.

Main Components
---------------

**Configuration Enums:**
    Visual and behavioral configuration options for UI elements:

    - ElementSize: Predefined size options (EXTRA_SMALL to THREE_EXTRA_LARGE)
    - ActionType: Element behavior (VALUE for data updates, EVENTS for triggers)
    - TextVariant: Text presentation styles (SPAN for inline, PARAGRAPH for block)
    - FontWeight: Text thickness (REGULAR, SEMI_BOLD, BOLD)
    - BadgeVariant: Badge visual styles (DEFAULT, UPDATED)
    - ContainerType: Layout models (FLEX, GRID)
    - LayoutStyle: Card layout modes (LIST, GRID)
    - GridOrder: Grid element arrangement (ROW, COLUMN)
    - RowSpacing: Vertical spacing options (NONE, TIGHT, RELAXED)
    - AlignContent: Alignment options (CENTER, SPACE_BETWEEN)
    - LayoutDirection: List layout direction (ROW, COLUMN)

**Base Classes:**
    Foundation classes providing common functionality:

    - BaseElement: Abstract base with state management (disabled, required, hidden, etc.)
    - Element: Base for all UI elements with property mapping and sizing
    - ElementContainer: Base for elements that contain child elements

**Container Elements:**
    Layout components for grouping and organizing UI elements:

    - Container: Flexible layout container with flex/grid display modes
    - Card: Rich container with customizable layout, styling, and interaction
    - Badge: Compact label for status or metadata display
    - OverflowElement: Replacement element shown for overflowing items in a ListElement

**Interactive Elements:**
    User input and interaction components:

    - Button: Clickable button with text, icons, and event handling
    - Checkbox: Standard checkbox with check/uncheck events
    - IconCheckbox: Checkbox using custom icons for on/off states
    - Slider: Toggle slider for boolean values or event triggers
    - ReviewRating: Star rating or similar review component

**Display Elements:**
    Components for presenting information:

    - Text: Text display with styling, variants, and tooltips
    - IconElement: Icon display with click handling and tooltips
    - ListElement: Renders all rows of a table using a reusable element template

**Helper Functions:**
    - get_boolean_variable(): Converts Field/Parameter/Calculation/bool to ModelVariable
    - get_model_variable(): Converts model objects to ModelVariable descriptors

Element Hierarchy
-----------------
All UI elements inherit from BaseElement or Element::

    BaseElement (ABC)
    └── Element
        ├── ElementContainer
        │   ├── Container
        │   ├── Card
        │   ├── Badge
        │   └── OverflowElement
        ├── Button
        ├── Checkbox
        ├── IconElement
        ├── IconCheckbox
        ├── ListElement
        ├── ReviewRating
        ├── Slider
        └── Text

State Management
----------------
Elements support dynamic state configuration through BaseElement methods:

- add_conditional_disabled(): Make element non-interactive
- add_conditional_required(): Mark as required for form validation
- add_conditional_read_only(): Prevent editing
- add_conditional_error/warning/success/info(): Visual feedback states
- add_conditional_hidden(): Hide element (optionally reserving space)

Each state can be bound to a Field, Parameter, Calculation, or boolean value.

Data Binding
------------
Elements can bind to data sources using:

- Field: Direct table field reference
- Parameter: Named parameter value
- Calculation: Computed value
- ContextVariable: Runtime context variable
- TemplateBindingKey: Template-based dynamic binding

Event Handling
--------------
Interactive elements support ModelEvent binding for user actions:

- on_click: Button and icon click events
- on_check/on_uncheck: Checkbox state changes
- toggle_on/toggle_off: Slider state changes

Elements can operate in two action modes:

- ActionType.VALUE: Updates bound data source
- ActionType.EVENTS: Triggers events without updating values

Examples
--------
Creating a text element::

    # Static text
    label = Text(value="Hello World", font_weight=FontWeight.BOLD)

    # Dynamic text bound to a field
    user_name = Text(value=user_table.name_field, color="#333333")

Creating an interactive button::

    save_button = Button(
        text_value="Save",
        background_color="#007bff",
        on_click=save_event
    )

Creating a checkbox with state management::

    agree_checkbox = Checkbox(data_source=agreement_field)
    agree_checkbox.add_conditional_required(True)
    agree_checkbox.add_conditional_disabled(is_locked_field)

Creating a card container::

    user_card = Card(
        layout_style=LayoutStyle.GRID,
        row_spacing=RowSpacing.RELAXED,
        border_radius="8px"
    )
    user_card.add_element(Text(value="Name:"))
    user_card.add_element(Text(value=user_table.name_field))

Creating elements with events::

    # Checkbox that triggers events instead of updating values
    notify_checkbox = Checkbox(data_source=notification_field)
    notify_checkbox.set_on_event(enable_notifications_event)
    notify_checkbox.set_off_event(disable_notifications_event)

Creating a list element::

    # Render every row of employees_table using a card template.
    # TemplateBindingKey declares a placeholder inside the template;
    # add_template_field_mapping connects each placeholder to a real field.
    name_key = TemplateBindingKey("name")
    role_key = TemplateBindingKey("role")

    template_card = Card(layout_style=LayoutStyle.LIST)
    template_card.add_element(Text(value=name_key, font_weight=FontWeight.BOLD))
    template_card.add_element(Text(value=role_key))

    employee_list = ListElement(
        data_source=employees_table,
        template=template_card,
        layout_direction=LayoutDirection.COLUMN,
    )
    employee_list.add_template_field_mapping(name_key, name_field)
    employee_list.add_template_field_mapping(role_key, role_field)

Creating a list element with a summarise overflow::

    overflow = OverflowElement()
    overflow.add_element(Text(value="More items..."))

    employee_list = ListElement(
        data_source=employees_table,
        template=template_card,
        overflow_strategy=OverflowStrategy.SUMMARISE,
        overflow_element=overflow,
    )
"""

from abc import ABC
from dataclasses import dataclass, field
from enum import Enum

from daitum_model import Calculation, DataType, Field, ObjectDataType, Parameter, Table
from daitum_model.named_values import NamedValue
from typeguard import typechecked

from daitum_ui._buildable import Buildable, json_type_info
from daitum_ui._data import (
    ModelPermissionsCondition,
    ModelVariable,
    ModelVariableCondition,
    ModelVariableType,
)
from daitum_ui.context_variable import ContextVariable
from daitum_ui.data import Condition
from daitum_ui.model_event import ModelEvent
from daitum_ui.styles import HorizontalAlignment, IconConfig
from daitum_ui.template_binding_key import TemplateBindingKey


class ElementSize(Enum):
    """
    Represents predefined size options for UI elements.
    """

    EXTRA_SMALL = "EXTRA_SMALL"
    SMALL = "SMALL"
    MEDIUM = "MEDIUM"
    LARGE = "LARGE"
    EXTRA_LARGE = "EXTRA_LARGE"
    TWO_EXTRA_LARGE = "TWO_EXTRA_LARGE"
    THREE_EXTRA_LARGE = "THREE_EXTRA_LARGE"


class ActionType(Enum):
    """
    Defines how an element should behave when interacted with.

    Attributes:
        VALUE:
            Element updates a value.
        EVENTS:
            Element triggers associated events instead of—or in addition to—
            updating a value.
    """

    VALUE = "VALUE"
    EVENTS = "EVENTS"


class TextVariant(Enum):
    """
    Defines how text should be semantically or visually presented.

    Attributes:
        SPAN:
            Inline text (e.g., for labels or short phrases).
        PARAGRAPH:
            Block-level text intended to occupy its own paragraph.
    """

    SPAN = "SPAN"
    PARAGRAPH = "PARAGRAPH"


class FontWeight(Enum):
    """
    Represents the thickness or boldness of the text.

    Attributes:
        REGULAR:
            Standard body-weight text.
        SEMI_BOLD:
            A slightly heavier weight, often used for emphasis.
        BOLD:
            Strong emphasis or headings.
    """

    REGULAR = "REGULAR"
    SEMI_BOLD = "SEMI_BOLD"
    BOLD = "BOLD"


class BadgeVariant(Enum):
    """
    The display variant of the badge. This is a holdover from an earlier version of the badge,
    so we'll likely remove this in the future.

    Options:
        DEFAULT:
            Standard visual appearance.
        UPDATED:
            Indicates a visually updated or emphasized state.
    """

    DEFAULT = "DEFAULT"
    UPDATED = "UPDATED"


class ContainerType(Enum):
    """
    The layout type for arranging child elements within a container.

    Options:
        FLEX:
            Uses a flexible box layout model for responsive design.
        GRID:
            Uses a grid layout model for structured arrangement.
    """

    FLEX = "flex"
    GRID = "grid"


class LayoutStyle(Enum):
    """
    Defines the layout style used when rendering elements inside the card.
    """

    LIST = "LIST"
    GRID = "GRID"


class GridOrder(Enum):
    """
    Defines how elements are arranged in GRID layout mode.

    ROW:
        Every second element is placed in the second column.
    COLUMN:
        The first column is filled up to `row_count` items before placing
        additional items in the second column.
    """

    ROW = "ROW"
    COLUMN = "COLUMN"


class RowSpacing(Enum):
    """
    Controls vertical spacing between elements within the card.
    """

    NONE = "NONE"
    TIGHT = "TIGHT"
    RELAXED = "RELAXED"


class AlignContent(Enum):
    """
    Controls how elements are aligned within the card’s container.
    """

    CENTER = "CENTER"
    SPACE_BETWEEN = "SPACE_BETWEEN"


class LayoutDirection(Enum):
    """
    Defines the direction in which items are laid out.

    ROW:
        Items are laid out horizontally.
    COLUMN:
        Items are laid out vertically.
    """

    ROW = "ROW"
    COLUMN = "COLUMN"


class OverflowStrategy(Enum):
    """
    Defines how content that exceeds its container bounds should be handled.

    Attributes:
        CLIP: Truncates (clips) the overflowing content so that only the visible
              portion within the container is shown.
        SCROLL: Enables scrolling, allowing users to access overflowing content
                via scroll interaction.
        SUMMARISE: Condenses or summarises the overflowing content into a shorter
                   representation (e.g., "..." or aggregated view).
    """

    CLIP = "CLIP"
    SCROLL = "SCROLL"
    SUMMARISE = "SUMMARISE"


@dataclass
@typechecked
class ElementStates(Buildable):
    is_disabled: list[Condition] | None = None
    is_required: list[Condition] | None = None
    is_read_only: list[Condition] | None = None
    is_error: list[Condition] | None = None
    is_warning: list[Condition] | None = None
    is_success: list[Condition] | None = None
    is_hidden: list[Condition] | None = None
    is_info: list[Condition] | None = None
    reserve_space: list[Condition] | None = None


@typechecked
def get_boolean_variable(variable: Field | Parameter | Calculation | bool):
    """
    Converts a boolean-like input into a ModelVariable representing a boolean
    value within the model.

    Parameters:
        variable (Field | Parameter | Calculation | bool):
            The source of the boolean value. Must resolve to DataType.BOOLEAN
            when a Field, Parameter, or Calculation is provided.

    Returns:
        ModelVariable:
            A model variable referencing the appropriate underlying boolean source.

    Raises:
        ValueError:
            If the provided Field, Parameter, or Calculation does not represent
            a boolean data type.
    """
    if isinstance(variable, Field):
        if variable.data_type != DataType.BOOLEAN:
            raise ValueError(
                f"Field {variable.id} is not a boolean field, cannot convert to " f"ModelVariable."
            )
        return ModelVariable(ModelVariableType.FIELD, variable.id)

    if isinstance(variable, Parameter | Calculation):
        if variable.to_data_type() != DataType.BOOLEAN:
            raise ValueError(
                f"Named value {variable.id} is not a boolean field, cannot convert to "
                f"ModelVariable."
            )
        return ModelVariable(ModelVariableType.NAMED_VALUE, variable.id)

    return ModelVariable(ModelVariableType.CONTEXT_VARIABLE, "TRUE" if variable else "FALSE")


@typechecked
class BaseElement(ABC, Buildable):
    """
    Base class for all UI elements that support state management.

    This class provides helper methods for configuring an element's
    interactive properties.

    Attributes:
        element_states (Optional[ElementStates]):
            Holds state flags for the element. Created only when a state-setting method is invoked.
    """

    def __init__(self):
        self.element_states: ElementStates | None = None

    def add_conditional_disabled(self, is_disabled: Field | Parameter | Calculation | bool):
        """
        Sets whether the element is disabled (non-interactive).
        """
        if self.element_states is None:
            self.element_states = ElementStates()
        condition = ModelVariableCondition(model_variable=get_boolean_variable(is_disabled))
        if self.element_states.is_disabled is None:
            self.element_states.is_disabled = []
        self.element_states.is_disabled.append(condition)

    def add_permission_disabled(self, is_base_user: bool):
        """
        Adds a permission-based condition controlling whether the element is disabled.

        Args:
            is_base_user (bool): If True, the element is disabled for base users
                (non-advanced users). If False, the element is disabled for advanced users only.
        """
        if self.element_states is None:
            self.element_states = ElementStates()
        condition = ModelPermissionsCondition(is_advanced_user=not is_base_user)
        if self.element_states.is_disabled is None:
            self.element_states.is_disabled = []
        self.element_states.is_disabled.append(condition)

    def add_conditional_required(self, is_required: Field | Parameter | Calculation | bool):
        """
        Sets whether the element is required for valid form submission.
        """
        if self.element_states is None:
            self.element_states = ElementStates()
        condition = ModelVariableCondition(model_variable=get_boolean_variable(is_required))
        if self.element_states.is_required is None:
            self.element_states.is_required = []
        self.element_states.is_required.append(condition)

    def add_permission_required(self, is_base_user: bool):
        """
        Adds a permission-based condition controlling whether the element is required.

        Args:
            is_base_user (bool): If True, the element is required for base users
                (non-advanced users). If False, the element is required for advanced users only.
        """
        if self.element_states is None:
            self.element_states = ElementStates()
        condition = ModelPermissionsCondition(is_advanced_user=not is_base_user)
        if self.element_states.is_required is None:
            self.element_states.is_required = []
        self.element_states.is_required.append(condition)

    def add_conditional_read_only(self, is_read_only: Field | Parameter | Calculation | bool):
        """
        Sets whether the element is read-only (not editable).
        """
        if self.element_states is None:
            self.element_states = ElementStates()
        condition = ModelVariableCondition(model_variable=get_boolean_variable(is_read_only))
        if self.element_states.is_read_only is None:
            self.element_states.is_read_only = []
        self.element_states.is_read_only.append(condition)

    def add_permission_read_only(self, is_base_user: bool):
        """
        Adds a permission-based condition controlling whether the element is read-only.

        Args:
            is_base_user (bool): If True, the element is read-only for base users
                (non-advanced users). If False, the element is read-only for advanced users only.
        """
        if self.element_states is None:
            self.element_states = ElementStates()
        condition = ModelPermissionsCondition(is_advanced_user=not is_base_user)
        if self.element_states.is_read_only is None:
            self.element_states.is_read_only = []
        self.element_states.is_read_only.append(condition)

    def add_conditional_error(self, is_error: Field | Parameter | Calculation | bool):
        """
        Sets whether the element is in an error state.
        """
        if self.element_states is None:
            self.element_states = ElementStates()
        condition = ModelVariableCondition(model_variable=get_boolean_variable(is_error))
        if self.element_states.is_error is None:
            self.element_states.is_error = []
        self.element_states.is_error.append(condition)

    def add_permission_error(self, is_base_user: bool):
        """
        Adds a permission-based condition controlling whether the element is in an error state.

        Args:
            is_base_user (bool): If True, the element shows an error state for base users
                (non-advanced users). If False, the element shows an error state for advanced
                users only.
        """
        if self.element_states is None:
            self.element_states = ElementStates()
        condition = ModelPermissionsCondition(is_advanced_user=not is_base_user)
        if self.element_states.is_error is None:
            self.element_states.is_error = []
        self.element_states.is_error.append(condition)

    def add_conditional_warning(self, is_warning: Field | Parameter | Calculation | bool):
        """
        Sets whether the element is in a warning state.
        """
        if self.element_states is None:
            self.element_states = ElementStates()
        condition = ModelVariableCondition(model_variable=get_boolean_variable(is_warning))
        if self.element_states.is_warning is None:
            self.element_states.is_warning = []
        self.element_states.is_warning.append(condition)

    def add_permission_warning(self, is_base_user: bool):
        """
        Adds a permission-based condition controlling whether the element is in a warning state.

        Args:
            is_base_user (bool): If True, the element shows a warning state for base users
                (non-advanced users). If False, the element shows a warning state for advanced
                users only.
        """
        if self.element_states is None:
            self.element_states = ElementStates()
        condition = ModelPermissionsCondition(is_advanced_user=not is_base_user)
        if self.element_states.is_warning is None:
            self.element_states.is_warning = []
        self.element_states.is_warning.append(condition)

    def add_conditional_success(self, is_success: Field | Parameter | Calculation | bool):
        """
        Sets whether the element is in a success state.
        """
        if self.element_states is None:
            self.element_states = ElementStates()
        condition = ModelVariableCondition(model_variable=get_boolean_variable(is_success))
        if self.element_states.is_success is None:
            self.element_states.is_success = []
        self.element_states.is_success.append(condition)

    def add_permission_success(self, is_base_user: bool):
        """
        Adds a permission-based condition controlling whether the element is in a success state.

        Args:
            is_base_user (bool): If True, the element shows a success state for base users
                (non-advanced users). If False, the element shows a success state for advanced
                users only.
        """
        if self.element_states is None:
            self.element_states = ElementStates()
        condition = ModelPermissionsCondition(is_advanced_user=not is_base_user)
        if self.element_states.is_success is None:
            self.element_states.is_success = []
        self.element_states.is_success.append(condition)

    def add_conditional_hidden(self, is_hidden: Field | Parameter | Calculation | bool):
        """
        Sets whether the element is hidden in the UI.
        """
        if self.element_states is None:
            self.element_states = ElementStates()
        condition = ModelVariableCondition(model_variable=get_boolean_variable(is_hidden))
        if self.element_states.is_hidden is None:
            self.element_states.is_hidden = []
        self.element_states.is_hidden.append(condition)

    def add_permission_hidden(self, is_base_user: bool):
        """
        Adds a permission-based condition controlling whether the element is hidden.

        Args:
            is_base_user (bool): If True, the element is hidden from base users
                (non-advanced users). If False, the element is hidden from advanced users only.
        """
        if self.element_states is None:
            self.element_states = ElementStates()
        condition = ModelPermissionsCondition(is_advanced_user=not is_base_user)
        if self.element_states.is_hidden is None:
            self.element_states.is_hidden = []
        self.element_states.is_hidden.append(condition)

    def add_conditional_info(self, is_info: Field | Parameter | Calculation | bool):
        """
        Sets whether the element is in an info state.
        """
        if self.element_states is None:
            self.element_states = ElementStates()
        condition = ModelVariableCondition(model_variable=get_boolean_variable(is_info))
        if self.element_states.is_info is None:
            self.element_states.is_info = []
        self.element_states.is_info.append(condition)

    def add_permission_info(self, is_base_user: bool):
        """
        Adds a permission-based condition controlling whether the element is in an info state.

        Args:
            is_base_user (bool): If True, the element shows an info state for base users
                (non-advanced users). If False, the element shows an info state for advanced
                users only.
        """
        if self.element_states is None:
            self.element_states = ElementStates()
        condition = ModelPermissionsCondition(is_advanced_user=not is_base_user)
        if self.element_states.is_info is None:
            self.element_states.is_info = []
        self.element_states.is_info.append(condition)

    def add_conditional_reserve_space(self, reserve_space: Field | Parameter | Calculation | bool):
        """
        Sets whether space is reserved in the layout when the element is hidden.
        """
        if self.element_states is None:
            self.element_states = ElementStates()
        condition = ModelVariableCondition(model_variable=get_boolean_variable(reserve_space))
        if self.element_states.reserve_space is None:
            self.element_states.reserve_space = []
        self.element_states.reserve_space.append(condition)

    def add_permission_reserve_space(self, is_base_user: bool):
        """
        Adds a permission-based condition controlling whether space is reserved when the element
        is hidden.

        Args:
            is_base_user (bool): If True, space is reserved for base users
                (non-advanced users). If False, space is reserved for advanced users only.
        """
        if self.element_states is None:
            self.element_states = ElementStates()
        condition = ModelPermissionsCondition(is_advanced_user=not is_base_user)
        if self.element_states.reserve_space is None:
            self.element_states.reserve_space = []
        self.element_states.reserve_space.append(condition)


@typechecked
class Element(BaseElement):
    """
    Base class for all UI elements.

    Attributes:
        property_field_mapping:
            Mapping between UI element properties and the underlying
            model or data field names that supply their values.
        hidden:
            Indicates whether the element should be initially hidden.
        size:
            Optional hint for how large the UI element should appear.
    """

    def __init__(self, hidden: bool | None = None, size: ElementSize | None = None):
        super().__init__()
        self.hidden = hidden
        self.size = size
        self.property_field_mapping: dict[str, str] = {}

    def add_property_field_mapping(
        self, property_name: str, value: Field | Parameter | Calculation | TemplateBindingKey
    ) -> None:
        """
        Adds a mapping from a UI property to a model field.

        Args:
            property_name (str): The UI element property key.
            value (Field | Parameter | Calculation | TemplateBindingKey): The model/data name.
        """
        self.property_field_mapping[property_name] = value.to_string()


@dataclass
@typechecked
class ElementContainer(Element):
    """
    A UI element that groups and contains one or more child UI elements.
    Containers allow hierarchical UI layouts where multiple elements are
    visually or logically grouped together.

    Attributes:
        elements:
            The list of child UI elements contained within this container.
    """

    elements: list[Element] = field(default_factory=list)

    def __post_init__(self):
        super().__init__()

    def add_element(self, element: Element) -> None:
        """
        Adds a child UI element to the container.

        Args:
            element (Element):
                The UI element to add as a child of this container.
        """
        self.elements.append(element)


@dataclass
@typechecked
@json_type_info("container")
class Container(ElementContainer):
    """
    A layout container used to group UI elements together.

    Attributes:
        display:
            CSS display property for this container, either flex or grid.
        gap:
            Spacing between child elements. Applies to both row and column gaps for flex-based
            layouts.
        horizontal_alignment:
            Determines how child elements are aligned horizontally within the container.
    """

    display: ContainerType = ContainerType.FLEX
    gap: str | None = None
    horizontal_alignment: HorizontalAlignment | None = None


@dataclass
@typechecked
@json_type_info("card")
class Card(ElementContainer):
    """
    A UI card element that displays its child elements in either a list layout
    or a grid layout. Cards may have customizable styling, spacing, and
    interaction behavior.
    """

    # Layout configuration
    layout_style: LayoutStyle | None = None
    row_count: int | None = None
    grid_ordering: GridOrder | None = None
    column_ratio: str | None = None
    row_spacing: RowSpacing | None = None
    align_content: AlignContent | None = None
    compact: bool | None = None

    # Interaction
    on_click: ModelEvent | None = None
    on_click_key: TemplateBindingKey | None = None

    # Styling
    border_color: str | None = None
    border_left: str | None = None
    border_radius: str | None = None
    background_color: str | None = None
    left_accent: str | None = None
    right_accent: str | None = None
    hover_background_color: str | None = None
    hover_border_color: str | None = None
    column_background_color: str | None = None
    padding: str | None = None

    # Footer
    footer: Element | None = None


@dataclass
@typechecked
@json_type_info("badge")
class Badge(ElementContainer):
    """
    A small visual label used to display short status or metadata.

    Attributes:
        variant:
            Determines the visual style variant of the badge.
        background_color:
            CSS-compatible string specifying the badge's background color.
        on_click:
            Action to perform when the badge is clicked.
        minimum_width:
            Minimum width for the badge, expressed in CSS-compatible units.
    """

    variant: BadgeVariant | None = None
    background_color: str | None = None
    on_click: ModelEvent | None = None
    minimum_width: str | None = None


@dataclass
@typechecked
@json_type_info("overflow")
class OverflowElement(ElementContainer):
    """
    A container element that replaces overflowing items in a :class:`ListElement`
    when its ``overflow_strategy`` is set to :attr:`OverflowStrategy.SUMMARISE`.

    Instead of clipping or scrolling, the list renders this element once in place
    of all items that did not fit within the container's bounds. Populate it with
    any child elements to create a custom overflow summary — for example, a
    :class:`Text` label such as "+5 more" or an icon paired with a count.

    Example::

        overflow = OverflowElement()
        overflow.add_element(Text(value=overflow_count_field))

        employee_list = ListElement(
            data_source=employees_table,
            template=template_card,
            overflow_strategy=OverflowStrategy.SUMMARISE,
            overflow_element=overflow,
        )
    """

    _OVERFLOW_COUNT = "${overflowCount}"

    @property
    def overflow_count(self):
        return self._OVERFLOW_COUNT


@typechecked
@json_type_info("button")
class Button(Element):
    """
    A clickable button UI element.

    Attributes:
        text_value:
            The text displayed on the button.
        text_color:
            CSS-compatible string specifying the button's text color.
        background_color:
            CSS-compatible string specifying the button's background color.
        icon_source:
            Identifier for the icon to display, in DaitumIcon format.
        icon_color:
            CSS-compatible string specifying the color of the icon.
        on_click_key:
            Optional key used for click event routing or analytics.
        on_click:
            The action to perform when the button is clicked.
    """

    def __init__(
        self,
        text_value: str | Parameter | Calculation | Field | TemplateBindingKey | None = None,
        on_click: ModelEvent | None = None,
        on_click_key: TemplateBindingKey | None = None,
        icon_source: str | None = None,
    ):
        super().__init__()

        if isinstance(text_value, str):
            self.text_value: str | None = text_value
        elif text_value:
            self.text_value = f"${{{text_value.to_string()}}}"
        else:
            self.text_value = None
        self.text_color: str | None = None
        self.background_color: str | None = None
        self.icon_source = icon_source
        self.icon_color: str | None = None
        self.on_click_key = on_click_key
        self.on_click = on_click

    def set_text_color(self, text_color: str) -> "Button":
        """Sets the CSS text colour of the button."""
        self.text_color = text_color
        return self

    def set_background_color(self, background_color: str) -> "Button":
        """Sets the CSS background colour of the button."""
        self.background_color = background_color
        return self

    def set_icon_color(self, icon_color: str) -> "Button":
        """Sets the CSS colour of the button icon."""
        self.icon_color = icon_color
        return self


@typechecked
def get_model_variable(
    variable: Field | Parameter | Calculation | ContextVariable,
) -> ModelVariable | None:
    """
    Converts a model-related object into a ModelVariable descriptor.

    Parameters:
        variable:
            A Field, Parameter, Calculation, or ContextVariable instance
            representing a model value used by UI elements.

    Returns:
        ModelVariable (Optional):
            A standardized wrapper describing the variable type
            (FIELD, NAMED_VALUE, or CONTEXT_VARIABLE) and its identifier.

    Notes:
        - Field → ModelVariableType.FIELD (uses field_id)
        - Parameter or Calculation → ModelVariableType.NAMED_VALUE (uses named_value_id)
        - ContextVariable → ModelVariableType.CONTEXT_VARIABLE (uses id)
    """
    if isinstance(variable, Field):
        return ModelVariable(ModelVariableType.FIELD, variable.id)

    if isinstance(variable, Parameter | Calculation):
        return ModelVariable(ModelVariableType.NAMED_VALUE, variable.id)

    if isinstance(variable, ContextVariable):
        return ModelVariable(ModelVariableType.CONTEXT_VARIABLE, variable.id)

    return None


@typechecked
@json_type_info("checkbox")
class Checkbox(Element):
    """
    A standard checkbox UI element.

    Attributes:
        on_check:
            Event triggered when the checkbox transitions to the checked state.
        on_uncheck:
            Event triggered when the checkbox transitions to the unchecked state.
        checkbox_data_source_id:
            Model variable that stores the current value of the checkbox.
        on_click_key:
            Optional interaction key used for analytics or routing click events.
        action_type:
            Determines the checkbox's behavior when interacted with, such as updating a value
            or emitting a custom event.
    """

    def __init__(self, data_source: Field | Parameter | Calculation | ContextVariable):
        super().__init__()

        self.checkbox_data_source_id = get_model_variable(data_source)

        self.on_check: ModelEvent | None = None
        self.on_uncheck: ModelEvent | None = None

        self.action_type = ActionType.VALUE

        self.on_click_key: TemplateBindingKey | None = None

    def set_on_event(self, event: ModelEvent) -> "Checkbox":
        """
        Assigns an event to be fired when the checkbox transitions into the "check" state.

        Parameters:
            event (ModelEvent):
                The event to trigger when the checkbox becomes checked.

        Notes:
            Setting an on-event automatically changes the action_type
            to ActionType.EVENTS, indicating the checkbox now emits events rather
            than updating a value.
        """
        self.on_check = event
        self.action_type = ActionType.EVENTS
        return self

    def set_off_event(self, event: ModelEvent) -> "Checkbox":
        """
        Assigns an event to be fired when the checkbox transitions into the "uncheck" state.

        Parameters:
            event (ModelEvent):
                The event to trigger when the checkbox becomes unchecked.

        Notes:
            Setting an off-event automatically changes the action_type
            to ActionType.EVENTS, indicating the checkbox now emits events rather
            than updating a value.
        """
        self.on_uncheck = event
        self.action_type = ActionType.EVENTS
        return self


@dataclass
@typechecked
@json_type_info("icon")
class IconElement(Element):
    """
    Represents an icon UI element.

    Attributes:
        icon_source:
            The icon to display. The string uses the DaitumIcon format, which is a string of the
            form "iconFamily.ICON".
        color:
            The CSS-compatible colour to render the icon.
        on_click:
            Event triggered when the icon is clicked.
        tooltip:
            Optional tooltip displayed when the user hovers over the icon.
    """

    def __post_init__(self):
        super().__init__()

    icon_source: str | None = None
    color: str | None = None
    on_click: ModelEvent | None = None
    tooltip: str | None = None


@typechecked
@json_type_info("iconCheckbox")
class IconCheckbox(Element):
    """
    A checkbox UI element that uses icons to represent checked and unchecked states.

    Attributes:
        on_check:
            Event triggered when the checkbox transitions to the checked state.
        on_uncheck:
            Event triggered when the checkbox transitions to the unchecked state.
        icon_checkbox_data_source_id:
            Model variable storing the current checkbox value.
        on_click_key:
            Optional key used to route click-based interactions such as analytics.
        action_type:
            Specifies how the checkbox should behave when interacted with,
            such as updating a value or emitting an event.
        off_icon:
            Icon displayed when the checkbox is unchecked.
        on_icon:
            Icon displayed when the checkbox is checked.
    """

    def __init__(
        self,
        data_source: Field | Parameter | Calculation | ContextVariable,
        off_icon: IconConfig | None = None,
        on_icon: IconConfig | None = None,
    ):
        super().__init__()

        self.icon_checkbox_data_source_id = get_model_variable(data_source)

        self.on_check: ModelEvent | None = None
        self.on_uncheck: ModelEvent | None = None

        self.action_type = ActionType.VALUE

        self.on_click_key: TemplateBindingKey | None = None

        self.off_icon = off_icon
        self.on_icon = on_icon

    def set_on_event(self, event: ModelEvent) -> "IconCheckbox":
        """
        Assigns an event to be fired when the icon checkbox transitions into the "on" state.

        Parameters:
            event (ModelEvent):
                The event to trigger when the icon checkbox turns on.

        Notes:
            Setting an on-event automatically changes the action_type
            to ActionType.EVENTS, indicating the checkbox now emits events rather
            than updating a value.
        """
        self.on_check = event
        self.action_type = ActionType.EVENTS
        return self

    def set_off_event(self, event: ModelEvent) -> "IconCheckbox":
        """
        Assigns an event to be fired when the icon checkbox transitions into the "off" state.

        Parameters:
            event (ModelEvent):
                The event to trigger when the icon checkbox turns off.

        Notes:
            Setting an off-event automatically changes the action_type
            to ActionType.EVENTS, indicating the checkbox now emits events rather
            than updating a value.
        """
        self.on_uncheck = event
        self.action_type = ActionType.EVENTS
        return self


@typechecked
@json_type_info("reviewRating")
class ReviewRating(Element):
    """
    A UI element representing a review rating component, consisting of filled and empty icons.
    It supports binding to a model variable and tracking rating state.

    Attributes:
        fill_icon:
            Icon configuration used to display the "filled" (selected) rating value.
        empty_icon:
            Icon configuration used to display the "empty" (unselected) rating value.
        review_rating_data_source_id:
            Model variable storing the current rating value (e.g., 1–5 stars).
        fill_color:
            Optional color override for the filled icons.
    """

    def __init__(
        self,
        data_source: Field | Parameter | Calculation | ContextVariable,
    ):
        super().__init__()

        self.review_rating_data_source_id = get_model_variable(data_source)
        self.fill_icon: IconConfig | None = None
        self.empty_icon: IconConfig | None = None
        self.fill_color: str | None = None

    def set_fill_icon(self, icon: IconConfig) -> "ReviewRating":
        """Sets the icon used for filled (selected) rating values."""
        self.fill_icon = icon
        return self

    def set_empty_icon(self, icon: IconConfig) -> "ReviewRating":
        """Sets the icon used for empty (unselected) rating values."""
        self.empty_icon = icon
        return self

    def set_fill_color(self, color: str) -> "ReviewRating":
        """Sets the colour override for filled rating icons."""
        self.fill_color = color
        return self


@typechecked
@json_type_info("slider")
class Slider(Element):
    """
    A slider UI element used for selecting values or triggering events.

    Attributes:
        toggle_on:
            Event triggered when the slider moves into an "on" state.
        toggle_off:
            Event triggered when the slider moves into an "off" state.
        slider_data_source_id:
            Reference to a model variable that stores the slider's current value.
        on_click_key:
            An optional interaction key used to associate click behaviour
            (e.g., analytics or event routing).
        action_type:
            Determines whether the slider updates a value or emits events
            when interacted with.
    """

    def __init__(self, data_source: Field | Parameter | Calculation | ContextVariable):
        super().__init__()

        self.slider_data_source_id = get_model_variable(data_source)

        self.toggle_on: ModelEvent | None = None
        self.toggle_off: ModelEvent | None = None

        self.action_type = ActionType.VALUE

        self.on_click_key: TemplateBindingKey | None = None

    def set_on_event(self, event: ModelEvent) -> "Slider":
        """
        Assigns an event to be fired when the slider transitions into the "on" state.

        Parameters:
            event (ModelEvent):
                The event to trigger when the slider switches from off to on.

        Notes:
            Setting an on-event automatically changes the slider's action_type
            to ActionType.EVENTS, indicating the slider now emits events rather
            than updating a value.
        """
        self.toggle_on = event
        self.action_type = ActionType.EVENTS
        return self

    def set_off_event(self, event: ModelEvent) -> "Slider":
        """
        Assigns an event to be fired when the slider transitions into the "off" state.

        Parameters:
            event (ModelEvent):
                The event to trigger when the slider switches from on to off.

        Notes:
            Setting an off-event automatically changes the slider's action_type
            to ActionType.EVENTS, indicating the slider now emits events rather
            than updating a value.
        """
        self.toggle_off = event
        self.action_type = ActionType.EVENTS
        return self


@typechecked
@json_type_info("text")
class Text(Element):
    """
    A text UI element used for displaying static or dynamic textual content.

    Attributes:
        value:
            The string content to be displayed.
        color:
            Optional CSS-compatible colour for the text.
        font_weight:
            The thickness of the displayed text.
        variant:
            The presentation style of the text (inline or paragraph).
        show_tool_tip:
            Whether the text should display a tooltip containing its full value. Useful when the
            displayed text is too long and may be truncated, but the user still needs access to
            the complete, non-truncated content.
    """

    def __init__(
        self,
        value: str | Parameter | Calculation | Field | TemplateBindingKey,
        color: str | None = None,
        font_weight: FontWeight | None = None,
        variant: TextVariant | None = None,
        show_tool_tip: bool = False,
    ):
        super().__init__()

        if isinstance(value, str):
            self.value = value
        elif value:
            self.value = f"${{{value.to_string()}}}"
        self.color = color
        self.font_weight = font_weight
        self.variant = variant
        self.show_tool_tip = show_tool_tip

    def set_color(self, color: str) -> "Text":
        """Sets the CSS colour for this text element."""
        self.color = color
        return self

    def set_font_weight(self, weight: FontWeight) -> "Text":
        """Sets the font weight for this text element."""
        self.font_weight = weight
        return self

    def set_variant(self, variant: TextVariant) -> "Text":
        """Sets the presentation variant (inline or paragraph) for this text element."""
        self.variant = variant
        return self


@typechecked
@json_type_info("list")
class ListElement(Element):
    """
    A display element that renders every row of a data table using a reusable
    element template.

    For each row in the source table, the template is instantiated and its
    placeholder values are resolved via field bindings. Placeholders are
    declared inside the template using :class:`TemplateBindingKey`; bindings
    are registered with :meth:`add_template_field_mapping`, which maps each
    placeholder key to the corresponding field in the source table.

    Attributes:
        data_source (ModelVariable | None):
            Model variable referencing the data source. Set when a Field or
            NamedValue is provided; ``None`` when a Table is provided directly.
        source_table (str | None):
            ID of the source table. Set when a Table is provided; ``None``
            when a Field or NamedValue is provided instead.
        template (Optional[Element]):
            The element used as a template for each row.
        field_bindings (dict[str, str]):
            Resolved mapping from placeholder names to source table field IDs.
            Populated by :meth:`add_template_field_mapping`; do not set directly.
        layout_direction (LayoutDirection):
            The direction in which rendered items are arranged.
            ``COLUMN`` stacks items vertically (default);
            ``ROW`` places them horizontally.
        wrap (Optional[bool]):
            When ``True``, items wrap onto new lines when the container width
            is exceeded. When ``False`` or ``None``, items are clipped or
            scrollable depending on the container.
        overflow_strategy (OverflowStrategy):
            Defines strategies for handling content that exceeds the bounds of
            its container.
        width (Optional[str]):
            Defines width of the list element.
        height (Optional[str]):
            Defines height of the list element.
        overflow_element (Optional[OverflowElement]):
            Element rendered in place of overflowing items when
            ``overflow_strategy`` is :attr:`OverflowStrategy.SUMMARISE`.
        row_gap (Optional[str]):
            Vertical spacing between rows.
        column_gap (Optional[str]):
            Horizontal spacing between columns.

    """

    def __init__(
        self,
        data_source: Table | Field | NamedValue,
        template: Element,
        layout_direction: LayoutDirection = LayoutDirection.COLUMN,
        overflow_strategy: OverflowStrategy = OverflowStrategy.SCROLL,
    ):
        super().__init__()

        if isinstance(data_source, NamedValue | Field):
            datatype = data_source.to_data_type()
            if not (isinstance(datatype, ObjectDataType) and datatype.is_array()):
                raise ValueError(f"Data source must be an object-array type, got {datatype}")

        self.data_source: ModelVariable | None = None
        self.source_table: str | None = None

        if isinstance(data_source, Field | NamedValue):
            self.data_source = get_model_variable(data_source)
        elif isinstance(data_source, Table):
            self.source_table = data_source.id

        if overflow_strategy == OverflowStrategy.SUMMARISE:
            raise ValueError("overflow_element is required when overflow_strategy is SUMMARISE.")

        self.template = template
        self.field_bindings: dict[str, str] = {}
        self.layout_direction = layout_direction
        self.wrap: bool = False
        self.overflow_strategy = overflow_strategy
        self.height: str | None = None
        self.width: str | None = None
        self.overflow_element: OverflowElement | None = None
        self.row_gap: str | None = None
        self.column_gap: str | None = None

    def set_wrap(self, wrap: bool) -> "ListElement":
        """Sets whether items wrap onto multiple lines."""
        self.wrap = wrap
        return self

    def set_size(self, height: str | None = None, width: str | None = None) -> "ListElement":
        """Sets the height and/or width of the list element."""
        self.height = height
        self.width = width
        return self

    def set_overflow_element(self, overflow_element: OverflowElement) -> "ListElement":
        """Sets the element rendered in place of overflowing items when strategy is SUMMARISE."""
        if self.overflow_strategy != OverflowStrategy.SUMMARISE:
            raise ValueError(
                "overflow_element is only applicable when overflow_strategy is SUMMARISE."
            )
        self.overflow_element = overflow_element
        return self

    def set_gap(self, gap: str | None = None, cross_axis_gap: str | None = None) -> "ListElement":
        """
        Sets the gap between items in the list.

        Args:
            gap: Spacing along the main axis direction.
            cross_axis_gap: Spacing along the cross axis direction.
        """
        if gap is not None or cross_axis_gap is not None:
            if self.layout_direction == LayoutDirection.ROW:
                self.column_gap = gap
                self.row_gap = cross_axis_gap
            else:
                self.row_gap = gap
                self.column_gap = cross_axis_gap
        return self

    def add_template_field_mapping(self, key: TemplateBindingKey, field: Field) -> None:
        """
        Registers a binding between a template placeholder and a source table field.

        Each call adds one entry to ``field_bindings``. The placeholder declared
        by ``key`` inside the template will be substituted with the value of
        ``field`` for each rendered row.

        Args:
            key (TemplateBindingKey):
                The placeholder key referenced inside the template via
                :class:`TemplateBindingKey`. Must match exactly the key used
                when constructing the template elements.
            field (Field):
                The source table field whose value replaces the placeholder
                at render time.

        Example::
            name_key = TemplateBindingKey("name")
            employee_list.add_template_field_mapping(name_key, name_field)
        """
        self.field_bindings[key.to_string()] = field.to_string()
