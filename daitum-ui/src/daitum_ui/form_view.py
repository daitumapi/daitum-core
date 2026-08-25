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
Form view components for the Daitum UI framework.

This module provides comprehensive form-building capabilities through the FormView class
and a rich collection of form elements. Forms are structured layouts for data entry,
editing, and display, organised in a flexible grid-based system with powerful data
binding and validation features.

Enums:
    - FormSize: Element sizing (EXTRA_SMALL, SMALL, MEDIUM, LARGE, EXTRA_LARGE, FIT_WIDTH)
    - FormVariant: Label styling variants (REGULAR, HEADER)
    - FormResize: Text area resize behaviour (NONE, BOTH, HORIZONTAL, VERTICAL)
    - FormIconSet: Icon catalogue for icon pickers (ALL, DAITUM, FONT_AWESOME, FA_PRO)

Classes:
    - FormElement: Base class for all form elements with layout and validation
    - FormView: Container view managing form layout and elements
    - FormLabel, FormTextInput, FormNumberInput, FormBasicTextArea: Text elements
    - FormCheckbox, FormSlider, FormIconCheckbox: Boolean input elements
    - FormDropdown: Object selection element
    - FormDatePicker, FormTimePicker, FormDateTimePicker: Date/time elements
    - FormButton: Action button element
    - FormReviewRating: Rating input element
    - FormColourPickerInput: Colour (hex) picker element
    - FormIconPicker: Icon selection picker element
    - FormLink: Hyperlink element for external navigation (e.g. model editor)

Example:
    >>> builder = UiBuilder()
    >>> filter_mode = MatchRowFilterMode()
    >>> filter_mode.set_filter_row("selected_customer_row")
    >>> form = builder.add_form_view(
    ...     display_name="Customer Details",
    ...     total_rows=6,
    ...     table=customers_table,
    ...     filter_mode=filter_mode,
    ... )
    >>> form.set_columns(num_columns=2, width="250px")
    >>>
    >>> # Header label spanning both columns
    >>> header = form.add_label("Customer Information", row=1, column=1)
    >>> header.set_column_span(2).set_variant(FormVariant.HEADER).set_size(FormSize.LARGE)
    >>>
    >>> # Text input bound to a field
    >>> form.add_label("Name:", row=2, column=1)
    >>> form.add_text_input(customers_table.name_field, row=2, column=2)
    >>>
    >>> # Number input with range validation
    >>> form.add_label("Age:", row=3, column=1)
    >>> age_input = form.add_number_input(customers_table.age_field, row=3, column=2)
    >>> age_input.set_range_validation(min_value=IntegerValue(18), max_value=IntegerValue(120))
"""

from dataclasses import dataclass
from enum import Enum
from typing import Any, TypeVar, cast

from daitum_model import (
    Baseline,
    Calculation,
    DataType,
    Field,
    ObjectDataType,
    Parameter,
    Severity,
    Table,
)
from daitum_model.formula import Operand
from daitum_model.named_values import NamedValue
from typeguard import typechecked

from daitum_ui._buildable import Buildable, json_type_info
from daitum_ui._data import (
    DataValidationRule,
    DefaultValueReference,
    ModelVariable,
    ModelVariableType,
)
from daitum_ui._events import EditorEventType
from daitum_ui.base_view import BaseView
from daitum_ui.data import (
    DataValidationType,
    DecimalValue,
    DefaultValueBehaviour,
    DefaultValueType,
    FilterMode,
    IntegerValue,
    ObjectValue,
    StringValue,
    ValidationFlag,
    Value,
)
from daitum_ui.elements import BaseElement
from daitum_ui.model_event import EditorEvent, ModelEvent
from daitum_ui.styles import HorizontalAlignment, IconConfig

from ._link_destination import LinkDestination, ModelEditorLinkDestination


class FormSize(Enum):
    """
    Defines the standard size options for form elements, controlling
    their overall scale and layout footprint.

    Attributes:
        EXTRA_SMALL:
            Extra small size, for very compact UI elements.
        SMALL:
            Small size, slightly larger than extra small.
        MEDIUM:
            Medium size, the default and most commonly used size.
        LARGE:
            Large size, for elements that require more prominence.
        EXTRA_LARGE:
            Extra large size, for very prominent or attention-grabbing elements.
        FIT_WIDTH:
            Adjusts the element to fit the width of its container.
    """

    EXTRA_SMALL = "EXTRA_SMALL"
    SMALL = "SMALL"
    MEDIUM = "MEDIUM"
    LARGE = "LARGE"
    EXTRA_LARGE = "EXTRA_LARGE"
    FIT_WIDTH = "FIT_WIDTH"


class FormVariant(Enum):
    """
    Defines visual style variants for form labels.

    Attributes:
        REGULAR:
            Standard styling.
        HEADER:
            Styling intended for header or section titles within forms.
    """

    REGULAR = "REGULAR"
    HEADER = "HEADER"


class FormResize(Enum):
    """
    Controls the resize behaviour of resizable elements such as text areas.

    Members:
        NONE:
            The element is not resizable by the user.
        BOTH:
            The element can be resized both horizontally and vertically.
        HORIZONTAL:
            The element can be resized horizontally only.
        VERTICAL:
            The element can be resized vertically only.
    """

    NONE = "NONE"
    BOTH = "BOTH"
    HORIZONTAL = "HORIZONTAL"
    VERTICAL = "VERTICAL"


class FormIconSet(Enum):
    """
    Catalogue of icons exposed by :class:`FormIconPicker`.

    Values match the portal ``IconPicker`` / modelv3 ``FormIconPicker.IconSet`` enum.
    """

    ALL = "ALL"
    DAITUM = "DAITUM"
    FONT_AWESOME = "FONT_AWESOME"
    FA_PRO = "FA_PRO"


@dataclass
@typechecked
class _FormColumn(Buildable):
    """
    Internal class representing a column definition in a form layout.

    Attributes:
        width (str): The CSS-compatible width specification for the column,
            such as "100px", "25%", or "min-content".
    """

    width: str


@dataclass
@typechecked
class FormElement(BaseElement):
    """
    Abstract base class representing a UI form element with data binding, layout,
    styling, and state management capabilities.

    Attributes:
        data_source_id (Optional[ModelVariable]):
            Reference to the data source variable backing this element's value.

        data_source_object_field_reference (Optional[str]):
            If the data source is of OBJECT type, this contains the reference field.

        row_start (int):
            Starting grid row index of the element in the form layout.

        column_start (int):
            Starting grid column index of the element in the form layout.

        row_span (int):
            Number of rows the element spans.

        column_span (int):
            Number of columns the element spans.

        horizontal_alignment (daitum_ui.styles.HorizontalAlignment):
            Horizontal alignment of the element within its grid cell.

        size (Optional[FormSize]):
            Visual size category of the element (e.g., small, medium, large).

        default_value_reference (Optional[DefaultValueReference]):
            Reference to a default value used by the element if no explicit data is bound.

        data_validation_rule (Optional[DataValidationRule]):
            Validation rules applied to user input on this element.

        tooltip_field (Optional[str]):
            The field ID or named value ID containing the value to display in the tooltip.

        editor_event (Optional[EditorEvent]):
            An event run when the user changes this element's value, instead of the element
            writing its own bound value. The picked value reaches the event as its
            ``editorValue`` context entry, and the event is responsible for every write it
            wants to make.
    """

    data_source_id: ModelVariable | None = None
    data_source_object_field_reference: str | None = None
    row_start: int = 0
    column_start: int = 0
    row_span: int = 1
    column_span: int = 1
    horizontal_alignment: HorizontalAlignment = HorizontalAlignment.LEFT
    size: FormSize | None = None
    default_value_reference: DefaultValueReference | None = None
    data_validation_rule: DataValidationRule | None = None
    tooltip_field: str | None = None
    display_format: str | None = None
    editor_event: EditorEvent | None = None

    def __post_init__(self):
        super().__init__()

    def set_default_value_reference(
        self,
        value: Field | Parameter | Calculation,
        behaviour: DefaultValueBehaviour = DefaultValueBehaviour.DEFAULT,
    ) -> "FormElement":
        """
        Set the default value reference for this field.

        This configures a reference value that can be used to reset the field's value
        to a predefined default. The reference can either be another field or a named value,
        with an associated behaviour determining how the reset behaves in the UI.

        Args:
            value (Field | Parameter | Calculation):
                The source of the default value. If a `Field` instance, the reference type is set to
                FIELD; otherwise, to a NAMED_VALUE.

            behaviour (DefaultValueBehaviour, optional):
                Controls the behaviour of the default value override.
        """
        value_type = (
            DefaultValueType.FIELD if isinstance(value, Field) else DefaultValueType.NAMED_VALUE
        )
        value_id = value.id if isinstance(value, Field) else value.id
        self.default_value_reference = DefaultValueReference(value_type, value_id, behaviour)
        return self

    def set_baseline_reset(
        self,
        baseline: Baseline | str,
        behaviour: DefaultValueBehaviour = DefaultValueBehaviour.DEFAULT,
    ) -> "FormElement":
        """
        Show a reset icon that reverts this element to its value at a baseline.

        The icon appears when the current value differs from the baseline value; clicking
        it reverts that one element. Only meaningful on editable elements.

        Args:
            baseline (Baseline | str): The baseline to revert to, or its name.
            behaviour (DefaultValueBehaviour, optional): Controls the reset behaviour.
                Defaults to `DefaultValueBehaviour.DEFAULT`.
        """
        baseline_name = baseline.name if isinstance(baseline, Baseline) else baseline
        self.default_value_reference = DefaultValueReference(
            DefaultValueType.BASELINE, baseline_name, behaviour
        )
        return self

    def set_list_validation(self, reference_field: str) -> "FormElement":
        """
        Sets a list-based data validation rule restricting input to values
        from a referenced field list.

        Args:
            reference_field (str): Name of the field that provides the allowed
                list of valid values for this input.

        Raises:
            ValueError: If called on an unsupported element type. Supported types are
                FormNumberInput, FormDatePicker, FormTimePicker, FormDateTimePicker and
                FormDropdown.
        """
        if not isinstance(
            self,
            FormNumberInput | FormDatePicker | FormTimePicker | FormDateTimePicker | FormDropdown,
        ):
            raise ValueError(f"`set_list_validation` is not supported for {type(self).__name__}")
        rule = DataValidationRule(
            type=DataValidationType.LIST,
            reference_field=reference_field,
        )
        self.data_validation_rule = rule
        return self

    def set_range_validation(
        self,
        min_value: str | Value | None = None,
        max_value: str | Value | None = None,
        flag: ValidationFlag = ValidationFlag.INCLUSIVE,
    ) -> "FormElement":
        """
        Sets a numeric range validation rule limiting input values to a specified range.

        Args:
            min_value (str, Value or None): The minimum allowed value. If an int or float, it is
            taken to be the literal min value. If a string, it is assumed to be a reference to
            a field or named value specifying the min value.
            max_value (str, Value or None): The maximum allowed value. If an int or float, it is
            taken to be the literal max value. If a string, it is assumed to be a reference to
            a field or named value specifying the max value.
            flag (ValidationFlag, optional): Specifies if the range bounds are inclusive
                or exclusive. Defaults to ValidationFlag.INCLUSIVE.

        Raises:
            ValueError: If called on an unsupported element type. Supported types are
                FormNumberInput, FormDatePicker, FormTimePicker and FormDateTimePicker.
        """
        if not isinstance(
            self, FormNumberInput | FormDatePicker | FormTimePicker | FormDateTimePicker
        ):
            raise ValueError(f"`set_range_validation` is not supported for {type(self).__name__}")

        if min_value is None and max_value is None:
            raise ValueError("`set_range_validation` requires `min_value` or `max_value`")

        rule = DataValidationRule(
            type=DataValidationType.RANGE,
            flag=flag,
        )
        if min_value:
            if isinstance(min_value, Value):
                rule.min_value = min_value
            elif isinstance(min_value, str):
                rule.min_value_column = min_value
            else:
                raise TypeError(
                    "min_value must be a Value or a string (field name or named value id)"
                )

        if max_value:
            if isinstance(max_value, Value):
                rule.max_value = max_value
            elif isinstance(max_value, str):
                rule.max_value_column = max_value
            else:
                raise TypeError(
                    "max_value must be a Value or a string (field name or named value id)"
                )

        self.data_validation_rule = rule
        return self

    def set_horizontal_alignment(self, alignment: HorizontalAlignment) -> "FormElement":
        """
        Sets the horizontal alignment of the element within its grid cell.

        Args:
            alignment (HorizontalAlignment): The desired horizontal alignment.
        """
        self.horizontal_alignment = alignment
        return self

    def set_display_format(self, display_format: str) -> "FormElement":
        """Sets the display format for editable elements."""
        self.display_format = display_format
        return self

    def set_size(self, size: "FormSize") -> "FormElement":
        """Sets the visual size of this element."""
        self.size = size
        return self

    def set_row_span(self, n: int) -> "FormElement":
        """Sets the number of rows this element spans."""
        self.row_span = n
        return self

    def set_column_span(self, n: int) -> "FormElement":
        """Sets the number of columns this element spans."""
        self.column_span = n
        return self

    def set_reference_field(self, field: str) -> "FormElement":
        """Sets the reference field for OBJECT-type data sources."""
        self.data_source_object_field_reference = field
        return self

    def set_tooltip_field(self, field: str) -> "FormElement":
        """Sets the field ID or named value ID to use as the tooltip text."""
        self.tooltip_field = field
        return self

    def set_on_change_event(self, event: ModelEvent) -> "FormElement":
        """
        Assigns an editor event run when the user changes this element's value.

        When set, the element no longer writes its own bound value on change; the event is
        run instead, receiving the picked value as its ``editorValue`` context entry, and is
        responsible for every write it wants to make. Only ``ON_CHANGE`` applies to form
        elements — buttons are triggered through :attr:`FormButton.on_click` instead.

        Args:
            event (ModelEvent): The event to execute when the element's value changes.

        Raises:
            ValueError: If an editor event has already been set.
        """
        if self.editor_event is not None:
            raise ValueError("ERROR - Editor Event has already been set")
        self.editor_event = EditorEvent(EditorEventType.ON_CHANGE, event)
        return self


@dataclass
@typechecked
@json_type_info("formLabel")
class FormLabel(FormElement):
    """
    A static or data-bound text label within a form.

    Displays a fixed string or a value bound to a field, parameter, or calculation.
    Use :attr:`variant` to control visual weight (``REGULAR`` for body text,
    ``HEADER`` for section headings).
    """

    display_string: str | None = None
    variant: FormVariant = FormVariant.REGULAR

    def set_variant(self, variant: FormVariant) -> "FormLabel":
        """Sets the visual variant of the label."""
        self.variant = variant
        return self


@json_type_info("formSlider")
class FormSlider(FormElement):
    """
    A slider (toggle switch) form element for boolean input.

    This component presents a sliding toggle UI for users to switch between
    True and False states, commonly used as an alternative to checkboxes
    for a more modern, touch-friendly interface.
    """

    pass


@json_type_info("formCheckbox")
class FormCheckbox(FormElement):
    """
    A standard checkbox form element for boolean input.

    This component provides a traditional checkbox UI for users to toggle
    between True (checked) and False (unchecked) states.
    """

    pass


@dataclass
@typechecked
@json_type_info("formIconCheckbox")
class FormIconCheckbox(FormElement):
    on_icon: IconConfig | None = None
    off_icon: IconConfig | None = None

    def set_off_icon(self, icon: IconConfig) -> "FormIconCheckbox":
        """Sets the icon displayed when the value is False."""
        self.off_icon = icon
        return self

    def set_on_icon(self, icon: IconConfig) -> "FormIconCheckbox":
        """Sets the icon displayed when the value is True."""
        self.on_icon = icon
        return self


@dataclass
@typechecked
@json_type_info("formTextInput")
class FormTextInput(FormElement):
    """
    A single-line text input bound to a ``STRING`` field, parameter, or calculation.

    Attributes:
        default_value (StringValue | None): Optional default text pre-filled when the
            bound value is absent.
    """

    default_value: StringValue | None = None


@dataclass
@typechecked
@json_type_info("formNumberInput")
class FormNumberInput(FormElement):
    """
    A numeric input bound to an ``INTEGER`` or ``DECIMAL`` field, parameter, or calculation.

    Supports range validation via :meth:`FormElement.set_range_validation`.

    Attributes:
        default_value (IntegerValue | DecimalValue | None): Optional numeric default
            pre-filled when the bound value is absent.
    """

    default_value: IntegerValue | DecimalValue | None = None


@dataclass
@typechecked
@json_type_info("formBasicTextArea")
class FormBasicTextArea(FormElement):
    """
    A multiline text area bound to a ``STRING`` field, parameter, or calculation.

    Attributes:
        default_value (StringValue | None): Optional default text.
        rows (int): Initial visible row count. Defaults to ``1``.
        resize (FormResize): User-resizability direction. Defaults to ``NONE``.
    """

    default_value: StringValue | None = None
    rows: int = 1
    resize: FormResize = FormResize.NONE


@dataclass
@typechecked
@json_type_info("formDatePicker")
class FormDatePicker(FormElement):
    """
    A date picker bound to a ``DATE`` field, parameter, or calculation.

    Supports range validation via :meth:`FormElement.set_range_validation`.

    Attributes:
        with_selector (bool): If ``True``, displays an inline calendar selector.
    """

    with_selector: bool = False


@dataclass
@typechecked
@json_type_info("formTimePicker")
class FormTimePicker(FormElement):
    """
    A time picker bound to a ``TIME`` field, parameter, or calculation.

    Supports range validation via :meth:`FormElement.set_range_validation`.

    Attributes:
        time_interval (int | None): Minute increment for the time selector (e.g. ``15``
            for quarter-hour steps). ``None`` uses the platform default.
    """

    time_interval: int | None = None


@dataclass
@typechecked
@json_type_info("formDateTimePicker")
class FormDateTimePicker(FormElement):
    """
    A combined date and time picker bound to a ``DATETIME`` field, parameter, or calculation.

    Supports range validation via :meth:`FormElement.set_range_validation`.

    Attributes:
        with_selector (bool): If ``True``, displays an inline calendar selector.
        time_interval (int | None): Minute increment for the time portion. ``None`` uses
            the platform default.
    """

    with_selector: bool = False
    time_interval: int | None = None


@dataclass
@typechecked
@json_type_info("formDropdown")
class FormDropdown(FormElement):
    """
    A dropdown (select) input bound to an ``OBJECT`` field, parameter, or calculation.

    Displays a list of object references from the bound table. The display label
    defaults to the table's key column; override it with :meth:`set_display_field`.
    Use :meth:`FormElement.set_list_validation` to restrict available choices.

    Attributes:
        is_searchable (bool): If ``True``, includes a search box within the dropdown.
        is_nullable (bool): If ``True``, allows the value to be cleared to null.
        default_value (ObjectValue | None): Optional default selection.
        choices (ModelVariable | None): Optional model variable supplying an alternative
            list of choices.
        object_reference_display_field (str | None): Field to display for each object choice.
    """

    is_searchable: bool = False
    is_nullable: bool = False
    default_value: ObjectValue | None = None
    choices: ModelVariable | None = None
    object_reference_display_field: str | None = None

    def set_display_field(self, field: str) -> "FormDropdown":
        """Sets the field to display for each object choice."""
        self.object_reference_display_field = field
        return self

    def set_searchable(self, searchable: bool) -> "FormDropdown":
        """Sets whether the dropdown is searchable."""
        self.is_searchable = searchable
        return self

    def set_nullable(self, nullable: bool) -> "FormDropdown":
        """Sets whether the dropdown is nullable."""
        self.is_nullable = nullable
        return self

    def set_choices(self, choices: ModelVariable) -> "FormDropdown":
        """Sets the model variable providing the list of available choices."""
        self.choices = choices
        return self


@dataclass
@typechecked
@json_type_info("formButton")
class FormButton(FormElement):
    """
    A clickable button that triggers a :class:`~daitum_ui.model_event.ModelEvent`.

    Attributes:
        text_value (str | None): Label displayed on the button.
        text_color (str | None): CSS-compatible text colour.
        background_color (str | None): CSS-compatible background colour.
        icon_source (str | None): DaitumIcon identifier (e.g. ``"fa.SAVE"``).
        icon_color (str | None): CSS-compatible icon colour.
        on_click (ModelEvent | None): Event executed when the button is clicked.
    """

    text_value: str | None = None
    text_color: str | None = None
    background_color: str | None = None
    icon_source: str | None = None
    icon_color: str | None = None
    on_click: ModelEvent | None = None

    def set_horizontal_alignment(self, alignment: "HorizontalAlignment") -> "FormButton":
        """Sets the horizontal alignment of the button."""
        self.horizontal_alignment = alignment
        return self

    def set_size(self, size: "FormSize") -> "FormButton":
        """Sets the visual size of the button."""
        self.size = size
        return self

    def set_text_color(self, color: str) -> "FormButton":
        """Sets the text colour of the button."""
        self.text_color = color
        return self

    def set_background_color(self, color: str) -> "FormButton":
        """Sets the background colour of the button."""
        self.background_color = color
        return self

    def set_icon_source(self, icon_source: str) -> "FormButton":
        """Sets the icon source for the button."""
        self.icon_source = icon_source
        return self

    def set_icon_color(self, color: str) -> "FormButton":
        """Sets the icon colour for the button."""
        self.icon_color = color
        return self


@dataclass
@typechecked
@json_type_info("formReviewRating")
class FormReviewRating(FormElement):
    """
    A star (or custom icon) rating input bound to a numeric field, parameter, or calculation.

    :attr:`FormSize.FIT_WIDTH` is not supported for this element.

    Attributes:
        fill_icon (IconConfig | None): Icon displayed for selected (filled) rating values.
        empty_icon (IconConfig | None): Icon displayed for unselected (empty) rating values.
        fill_color (str | None): CSS-compatible colour override for filled icons.
    """

    fill_icon: IconConfig | None = None
    empty_icon: IconConfig | None = None
    fill_color: str | None = None

    def __post_init__(self):
        """Validate that FIT_WIDTH is not used for review rating components."""
        super().__post_init__()
        if self.size == FormSize.FIT_WIDTH:
            raise ValueError("FormSize.FIT_WIDTH is not supported for review rating components.")

    def set_fill_icon(self, icon: IconConfig) -> "FormReviewRating":
        """Sets the icon used for filled (selected) rating values."""
        self.fill_icon = icon
        return self

    def set_empty_icon(self, icon: IconConfig) -> "FormReviewRating":
        """Sets the icon used for empty (unselected) rating values."""
        self.empty_icon = icon
        return self

    def set_fill_color(self, color: str) -> "FormReviewRating":
        """Sets the colour override for filled rating icons."""
        self.fill_color = color
        return self


@dataclass
@typechecked
@json_type_info("formColourPickerInput")
class FormColourPickerInput(FormElement):
    """
    Colour picker bound to a string field (typically a hex colour).

    Optional ``swatch_colours`` restricts the palette; when omitted, the UI may use its
    default theme palette. ``allow_custom`` enables free-form hex entry when supported.
    """

    swatch_colours: list[str] | None = None
    allow_custom: bool | None = None

    def set_swatch_colours(self, colours: list[str]) -> "FormColourPickerInput":
        """Sets the palette of swatch colours available in the colour picker."""
        self.swatch_colours = colours
        return self

    def set_allow_custom(self, allow: bool) -> "FormColourPickerInput":
        """Sets whether free-form hex colour entry is allowed."""
        self.allow_custom = allow
        return self


@dataclass
@typechecked
@json_type_info("formIconPicker")
class FormIconPicker(FormElement):
    """
    Icon picker bound to a string field (icon identifier, e.g. dot-path).

    ``icon_set`` selects which icon catalogue to show. Optional ``defaults`` lists
    icon ids shown first; ``preview_color`` sets icon tint in the dropdown.
    """

    icon_set: FormIconSet = FormIconSet.ALL
    defaults: list[str] | None = None
    preview_color: str | None = None

    def set_defaults(self, defaults: list[str]) -> "FormIconPicker":
        """Sets the list of icon IDs displayed first in the picker."""
        self.defaults = defaults
        return self

    def set_preview_color(self, color: str) -> "FormIconPicker":
        """Sets the CSS colour used to tint icons in the picker dropdown."""
        self.preview_color = color
        return self

    def set_icon_set(self, icon_set: FormIconSet) -> "FormIconPicker":
        """Sets the icon catalogue to display in the picker."""
        self.icon_set = icon_set
        return self


@dataclass
@typechecked
@json_type_info("formLink")
class FormLink(FormElement):
    """
    A form element that renders a hyperlink to an external destination.

    Use :meth:`FormView.add_model_editor_link` to create and add this element;
    do not instantiate it directly.

    Attributes:
        text_value (str):
            The visible label of the link. Defaults to ``"Open Model"``.
        destination (LinkDestination | None):
            The navigation target. Concrete subclasses of :class:`LinkDestination`
            specify where the link points (e.g. :class:`ModelEditorLinkDestination`).
    """

    text_value: str = "Open Model"
    destination: LinkDestination | None = None


_FE = TypeVar("_FE", bound=FormElement)


@typechecked
@json_type_info("form")
class FormView(BaseView):
    """
    Represents a structured form layout for displaying and editing data.

    A `FormView` arranges UI elements such as text fields, numeric inputs, dropdowns, checkboxes,
    date/time pickers, and buttons in a vertical, form-like layout. It can be bound to a source
    table, allowing for dynamic data depending on the specified table row.

    Attributes:
        total_rows (Optional[int]): The number of rows in the form layout.
        source_table (Optional[str]): The ID of the source table, if provided.
        form_columns (Optional[List[_FormColumn]]): Column layout definitions for the form.
        form_elements (List[FormElement]): The interactive components within the form.
        filter_mode (Optional[FilterMode]): The FilterMode selecting which single row of the
            source table the form displays. A `MatchRowFilterMode` resolves the row from a
            context variable holding its index (or, for a table with an id field, its key); a
            `MatchFieldFilterMode` resolves it by matching a context variable's value against
            `filter_target_field`, so a form can be pointed at a row by any field.
    """

    def __init__(
        self,
        display_name: str | None = None,
        hidden: bool = False,
        total_rows: int | None = None,
        table: Table | None = None,
        filter_mode: FilterMode | None = None,
    ):
        super().__init__(hidden)
        if display_name is not None:
            self._display_name = display_name

        self._table = table

        self.total_rows = total_rows
        self.source_table = self._table.id if self._table else None

        self.form_columns: list[_FormColumn] = []
        self.form_elements: list[FormElement] = []

        if self._table is not None:
            self.filter_mode = filter_mode

    def set_total_rows(self, rows: int) -> "FormView":
        """Sets the total number of rows in the form layout."""
        self.total_rows = rows
        return self

    def set_table(self, table: Table, filter_mode: FilterMode | None = None) -> "FormView":
        """Sets the source data table and optional row-selecting filter mode for this form.

        ``filter_mode`` may be any :class:`~daitum_ui.data.FilterMode` — a
        :class:`~daitum_ui.data.MatchRowFilterMode` (select the row by index or key) or a
        :class:`~daitum_ui.data.MatchFieldFilterMode` (select the row by matching a field value).
        """
        self._table = table
        self.source_table = table.id
        self.filter_mode = filter_mode
        return self

    def add_column(self, width: str):
        """
        Add a column to the form view with the specified width.

        Args:
            width (str): The CSS compatible width of the column, e.g., "100px", "20%",
                "min-content".
        """
        self.form_columns.append(_FormColumn(width=width))

    def set_columns(self, num_columns: int, width: str):
        """
        Defines a fixed number of columns in the form layout, all with the same width.

        This replaces any existing columns. Each column is assigned the same CSS-compatible
        width value, such as `"150px"`, `"25%"`, or `"min-content"`.

        Args:
            num_columns (int): The number of columns to create.
            width (str): The CSS-compatible width to apply to each column.
        """
        self.form_columns = [_FormColumn(width=width) for _ in range(num_columns)]

    def add_label(
        self,
        text: str | Field | Parameter | Calculation,
        row: int,
        column: int,
    ) -> FormLabel:
        """
        Adds a static or data-bound label element to the form at a specific grid position.

        The label can display either a fixed string or a bound variable (field, parameter, or
        calculation). It is placed according to the specified row and column. Use the returned
        element's setters to configure row_span, column_span, horizontal_alignment, size, variant,
        and reference_field.

        Args:
            text (str | Field | Parameter | Calculation): The text to display, either as a static
                string or a data-bound variable of string type.
            row (int): The starting row position of the label.
            column (int): The starting column position of the label.

        Returns:
            FormLabel: The label element created and added to the form.
        """
        display_string = text if isinstance(text, str) else None
        data_source = self._assert_and_return_variable(text)

        if not isinstance(text, str):
            assert data_source is not None
            data_type = text.to_data_type()
            assert isinstance(data_type, DataType) and not data_type.is_array()

        element = FormLabel(
            data_source_id=data_source,
            display_string=display_string,
            row_start=row,
            column_start=column,
        )

        if isinstance(text, Operand):
            element = self._set_element_states(text, element)

        self.form_elements.append(element)
        return element

    def add_text_input(
        self,
        text: Field | Parameter | Calculation,
        row: int,
        column: int,
    ) -> FormTextInput:
        """
        Adds a text input field to the form, bound to a string-based variable.

        This input allows users to view and edit text data from a field, parameter, or calculation.
        Use the returned element's attributes to set row_span, column_span, horizontal_alignment,
        and size.

        Args:
            text (Field | Parameter | Calculation): The data source to bind to,
                which must be of type `STRING`.
            row (int): The starting row position of the input.
            column (int): The starting column position of the input.

        Returns:
            FormTextInput: The input element created and added to the form.
        """
        element = FormTextInput(
            data_source_id=self._assert_and_return_variable(text, DataType.STRING),
            row_start=row,
            column_start=column,
        )

        element = self._set_element_states(text, element)

        self.form_elements.append(element)
        return element

    def add_slider(
        self,
        value: str | Field | Parameter | Calculation,
        row: int,
        column: int,
    ) -> FormSlider:
        """
        Adds a slider input to the form, bound to a boolean variable.

        Typically used for toggle-style input where a slider UI is preferred over a checkbox.
        Use the returned element's setters to configure horizontal_alignment and size.

        Args:
            value (str| Field | Parameter | Calculation): The boolean data source to bind to. If a
                string is provided, it is assumed to be a context variable ID.
            row (int): The row position of the slider.
            column (int): The column position of the slider.

        Returns:
            FormSlider: The slider element created and added to the form.
        """
        data_source = (
            ModelVariable(ModelVariableType.CONTEXT_VARIABLE, value)
            if isinstance(value, str)
            else self._assert_and_return_variable(value, DataType.BOOLEAN)
        )
        element = FormSlider(
            data_source_id=data_source,
            row_start=row,
            column_start=column,
        )

        self.form_elements.append(element)
        return element

    def add_check_box(
        self,
        value: str | Field | Parameter | Calculation,
        row: int,
        column: int,
    ) -> FormCheckbox:
        """
        Adds a checkbox input to the form, bound to a boolean variable.

        Used for simple on/off or true/false input. Use the returned element's setters
        to configure horizontal_alignment and size.

        Args:
            value (str | Field | Parameter | Calculation): The boolean data source to bind to. If a
                string is provided, it is assumed to be a context variable ID.
            row (int): The row position of the checkbox.
            column (int): The column position of the checkbox.

        Returns:
            FormCheckbox: The checkbox element created and added to the form.
        """
        data_source = (
            ModelVariable(ModelVariableType.CONTEXT_VARIABLE, value)
            if isinstance(value, str)
            else self._assert_and_return_variable(value, DataType.BOOLEAN)
        )

        element = FormCheckbox(
            data_source_id=data_source,
            row_start=row,
            column_start=column,
        )

        if isinstance(value, Operand):
            element = self._set_element_states(value, element)

        self.form_elements.append(element)
        return element

    def add_icon_check_box(
        self, value: str | Field | Parameter | Calculation, row: int, column: int
    ) -> FormIconCheckbox:
        """
        Adds an icon-based checkbox to the form, bound to a boolean variable.

        Instead of a standard checkbox, this component displays custom icons for the checked
        (`on_icon`) and unchecked (`off_icon`) states. Useful for visually enhanced toggle inputs.
        Set `off_icon`, `horizontal_alignment`, and `size` on the returned element.

        Args:
            value (str | Field | Parameter | Calculation): The boolean data source to bind to. If a
                string is provided, it is assumed to be a context variable ID.
            row (int): The row position of the icon checkbox.
            column (int): The column position of the icon checkbox.

        Returns:
            FormIconCheckbox: The icon checkbox element created and added to the form.
        """
        data_source = (
            ModelVariable(ModelVariableType.CONTEXT_VARIABLE, value)
            if isinstance(value, str)
            else self._assert_and_return_variable(value, DataType.BOOLEAN)
        )

        element = FormIconCheckbox(
            data_source_id=data_source,
            row_start=row,
            column_start=column,
        )

        if isinstance(value, Operand):
            element = self._set_element_states(value, element)

        self.form_elements.append(element)
        return element

    def add_drop_down(
        self,
        value: Field | Parameter | Calculation,
        row: int,
        column: int,
    ) -> FormDropdown:
        """
        Adds a dropdown input to the form, bound to an object-type variable.

        This component allows selection from a list of object references. The display label for
        each choice defaults to the table's key column; use the returned element's
        ``set_display_field()`` setter to override. Also use setters for ``is_searchable``,
        ``choices``, ``row_span``, ``column_span``, ``horizontal_alignment``, and ``size``.

        Args:
            value (Field | Parameter | Calculation): The object-type variable to bind the dropdown
                to. Must not be an array type.
            row (int): The row position of the dropdown.
            column (int): The column position of the dropdown.

        Raises:
            TypeError: If the bound variable is not an object type or is an array.

        Returns:
            FormDropdown: The dropdown element created and added to the form.
        """
        data_type = value.to_data_type()
        if not isinstance(data_type, ObjectDataType) or data_type.is_array():
            raise TypeError(f"ERROR - Dropdowns must be of type OBJECT. Received {data_type}.")

        data_source_table = cast(Table, data_type._source_table)
        display_field = data_source_table.key_column

        element = FormDropdown(
            data_source_id=self._assert_and_return_variable(value),
            row_start=row,
            column_start=column,
            object_reference_display_field=display_field,
        )

        element = self._set_element_states(value, element)

        self.form_elements.append(element)
        return element

    def add_date_time(
        self,
        value: Field | Parameter | Calculation,
        row: int,
        column: int,
        reference_field: str | None = None,
    ) -> FormElement:
        """
        Adds a date, time, or datetime picker to the form, based on the bound variable's type.

        The type of picker is automatically chosen depending on whether the data source is of
        type `DATE`, `TIME`, or `DATETIME`. Set ``display_format``, ``with_selector``,
        ``horizontal_alignment``, ``size``, and ``time_interval`` directly on the returned element.

        Args:
            value (Field | Parameter | Calculation): The variable to bind the picker to.
                Must be of type `DATE`, `TIME`, `DATETIME` or `OBJECT` (reference_field required).
            row (int): The row position of the picker.
            column (int): The column position of the picker.
            reference_field (Optional[str]): If provided, it is assumed that the value is of OBJECT
                type, and the reference field is the field in the reference table to display.

        Raises:
            ValueError: If the provided variable is not of type `DATE`, `TIME`, or `DATETIME`.

        Returns:
            FormElement: The appropriate date/time picker element (`FormDatePicker`,
                `FormTimePicker`, or `FormDateTimePicker`).
        """
        data_type = value.to_data_type()
        if reference_field is not None:
            assert isinstance(data_type, ObjectDataType) and not data_type.is_array()

            data_type = value[reference_field].to_data_type()

        if data_type == DataType.TIME:
            time_picker = FormTimePicker(
                data_source_id=self._assert_and_return_variable(value),
                row_start=row,
                column_start=column,
                data_source_object_field_reference=reference_field,
            )
            time_picker = self._set_element_states(value, time_picker)
            self.form_elements.append(time_picker)
            return time_picker
        elif data_type == DataType.DATETIME:
            date_time_picker = FormDateTimePicker(
                data_source_id=self._assert_and_return_variable(value),
                row_start=row,
                column_start=column,
                data_source_object_field_reference=reference_field,
            )
            date_time_picker = self._set_element_states(value, date_time_picker)
            self.form_elements.append(date_time_picker)
            return date_time_picker
        elif data_type == DataType.DATE:
            date_picker = FormDatePicker(
                data_source_id=self._assert_and_return_variable(value),
                row_start=row,
                column_start=column,
                data_source_object_field_reference=reference_field,
            )
            date_picker = self._set_element_states(value, date_picker)
            self.form_elements.append(date_picker)
            return date_picker

        raise ValueError(
            f"ERROR - Invalid data type for date/time picker "
            f"{data_type}. Expected TIME, DATETIME, or DATE."
        )

    def add_number_input(
        self,
        value: Field | Parameter | Calculation,
        row: int,
        column: int,
    ) -> FormNumberInput:
        """
        Adds a numeric input field to the form, bound to an integer or decimal variable.

        This component allows the user to enter or edit a numeric value. Set ``row_span``,
        ``column_span``, ``display_format``, ``horizontal_alignment``, and ``size`` directly
        on the returned element.

        Args:
            value (Field | Parameter | Calculation): The variable to bind the input to.
                Must be of type `INTEGER` or `DECIMAL`.
            row (int): The starting row position of the input.
            column (int): The starting column position of the input.

        Raises:
            TypeError: If the bound variable is not of type `INTEGER` or `DECIMAL`.

        Returns:
            FormNumberInput: The number input element created and added to the form.
        """
        data_type = value.to_data_type()
        if data_type not in [DataType.INTEGER, DataType.DECIMAL]:
            raise TypeError(
                f"ERROR - Number inputs must be of type INTEGER or DECIMAL. "
                f"Received {data_type}."
            )

        element = FormNumberInput(
            data_source_id=self._assert_and_return_variable(value),
            row_start=row,
            column_start=column,
        )

        element = self._set_element_states(value, element)
        self.form_elements.append(element)
        return element

    def add_text_area(
        self,
        text: Field | Parameter | Calculation,
        row: int,
        column: int,
    ) -> FormBasicTextArea:
        """
        Adds a multiline text area input to the form, bound to a string variable.

        The text area allows users to input or edit longer blocks of text. Set ``row_span``,
        ``column_span``, ``rows``, ``resize``, ``horizontal_alignment``, and ``size`` directly
        on the returned element.

        Args:
            text (Field | Parameter | Calculation): The variable to bind the text area to.
                Must be of type `STRING`.
            row (int): The starting row position of the text area.
            column (int): The starting column position of the text area.

        Returns:
            FormBasicTextArea: The configured text area element added to the form.
        """
        element = FormBasicTextArea(
            data_source_id=self._assert_and_return_variable(text, DataType.STRING),
            row_start=row,
            column_start=column,
        )
        element = self._set_element_states(text, element)
        self.form_elements.append(element)
        return element

    def add_button(
        self,
        text: str,
        on_click: ModelEvent,
        row: int,
        column: int,
    ) -> FormButton:
        """
        Adds a clickable button element to the form layout.

        Args:
            text (str): The label displayed on the button.
            on_click (ModelEvent): The event triggered when the button is clicked.
            row (int): Starting row position in the form grid.
            column (int): Starting column position in the form grid.

        Returns:
            FormButton: The button element added to the form. Set ``row_span`` and
                ``column_span`` directly on the returned element. Use set_* methods to configure
                appearance (text_color, background_color, icon_source, icon_color, size,
                horizontal_alignment).
        """
        element = FormButton(
            text_value=text,
            row_start=row,
            column_start=column,
            on_click=on_click,
        )

        self.form_elements.append(element)
        return element

    def add_review_rating(
        self,
        value: Field | Parameter | Calculation,
        row: int,
        column: int,
    ) -> FormReviewRating:
        """
        Adds a review rating element to the form layout.

        Args:
            value (Field | Parameter | Calculation): The variable to bind the review rating to.
            row (int): Starting row position in the form grid.
            column (int): Starting column position in the form grid.

        Returns:
            FormReviewRating: The review rating element added to the form. Set ``row_span``,
                ``column_span``, ``horizontal_alignment``, ``size``, ``fill_icon``,
                ``empty_icon``, and ``fill_color`` directly on the returned element.
        """
        element = FormReviewRating(
            data_source_id=self._assert_and_return_variable(value),
            row_start=row,
            column_start=column,
        )
        element = self._set_element_states(value, element)
        self.form_elements.append(element)
        return element

    def add_colour_picker_input(
        self,
        value: Field | Parameter | Calculation,
        row: int,
        column: int,
    ) -> FormColourPickerInput:
        """
        Adds a colour picker to the form, bound to a string variable (e.g. hex colour).

        Use the returned element's setters to configure row_span, column_span,
        horizontal_alignment, size, swatch_colours, and allow_custom.

        Args:
            value: The variable to bind; must be of type ``STRING``.
            row: Starting row in the form grid.
            column: Starting column in the form grid.

        Returns:
            FormColourPickerInput: The element added to the form.

        Raises:
            ValueError: If the bound variable is not of type ``STRING``.
        """
        element = FormColourPickerInput(
            data_source_id=self._assert_and_return_variable(value, DataType.STRING),
            row_start=row,
            column_start=column,
        )
        element = self._set_element_states(value, element)
        self.form_elements.append(element)
        return element

    def add_icon_picker(
        self,
        value: Field | Parameter | Calculation,
        row: int,
        column: int,
    ) -> FormIconPicker:
        """
        Adds an icon picker to the form, bound to a string variable (icon identifier).

        Use the returned element's setters to configure icon_set, row_span, column_span,
        horizontal_alignment, size, defaults, and preview_color.

        Args:
            value: The variable to bind; must be of type ``STRING``.
            row: Starting row in the form grid.
            column: Starting column in the form grid.

        Returns:
            FormIconPicker: The element added to the form.

        Raises:
            ValueError: If the bound variable is not of type ``STRING``.
        """
        element = FormIconPicker(
            data_source_id=self._assert_and_return_variable(value, DataType.STRING),
            row_start=row,
            column_start=column,
        )
        element = self._set_element_states(value, element)
        self.form_elements.append(element)
        return element

    def add_model_editor_link(  # noqa: PLR0913, PLR0917
        self,
        row: int,
        column: int,
        model_id: Field | Parameter | Calculation,
        scenario_id: Field | Parameter | Calculation | None = None,
        text_value: str = "Open Model",
        open_new_tab: bool = False,
    ) -> FormLink:
        """
        Adds a hyperlink element to the form that opens the Daitum model editor.

        ``model_id`` is required and must be an integer-typed value. ``scenario_id``
        is optional; when provided it identifies the scenario to pre-select within
        the model. Both ``Field`` values must belong to the form's source table.

        Args:
            row (int): Starting row position in the form grid.
            column (int): Starting column position in the form grid.
            model_id (Field | Parameter | Calculation): Integer value identifying
                the model to open. Must be of type ``INTEGER``.
            text_value (str): The visible label of the link. Defaults to
                ``"Open Model"``.
            scenario_id (Field | Parameter | Calculation | None): Integer value
                identifying the scenario to open within the selected model.
                Must be of type ``INTEGER``. Optional.
            open_new_tab (bool): If ``True``, the editor opens in a new browser tab.
                Defaults to ``False``.

        Raises:
            ValueError: If ``model_id`` or ``scenario_id`` is a ``Field`` not present
                in the form's source table, or if either value is not of type ``INTEGER``.

        Returns:
            FormLink: The link element created and added to the form.
        """
        if isinstance(model_id, Field):
            self._assert_field_in_table(model_id)
        self._assert_data_type(model_id, DataType.INTEGER)

        if scenario_id is not None:
            if isinstance(scenario_id, Field):
                self._assert_field_in_table(scenario_id)
            self._assert_data_type(scenario_id, DataType.INTEGER)

        element = FormLink(
            text_value=text_value,
            destination=ModelEditorLinkDestination(model_id, scenario_id, open_new_tab),
            row_start=row,
            column_start=column,
        )
        element = self._set_element_states(model_id, element)
        if scenario_id is not None:
            element = self._set_element_states(scenario_id, element)
        self.form_elements.append(element)
        return element

    def _set_element_states(self, value: Operand, element: _FE) -> _FE:  # noqa: PLR0912

        if isinstance(value, NamedValue):
            validation_values_list = value.get_validation_values()

            if validation_values_list and isinstance(validation_values_list, list):
                for validation_value in validation_values_list:

                    element.tooltip_field = validation_value.message_value.id

                    if validation_value.severity == Severity.INFO:
                        element.add_conditional_info(validation_value.invalid_value)
                    if validation_value.severity == Severity.WARNING:
                        element.add_conditional_warning(validation_value.invalid_value)

                    if validation_value.severity in [Severity.CRITICAL, Severity.ERROR]:
                        element.add_conditional_error(validation_value.invalid_value)
        elif isinstance(value, Field):
            validation_fields_list = value.get_validation_fields()

            if validation_fields_list and isinstance(validation_fields_list, list):
                for validation_field in validation_fields_list:

                    element.tooltip_field = validation_field.message_field.id

                    if validation_field.severity == Severity.INFO:
                        element.add_conditional_info(validation_field.invalid_field)

                    if validation_field.severity == Severity.WARNING:
                        element.add_conditional_warning(validation_field.invalid_field)

                    if validation_field.severity in [Severity.CRITICAL, Severity.ERROR]:
                        element.add_conditional_error(validation_field.invalid_field)

        return element

    def _assert_field_in_table(self, field: Field):
        """
        Validate that the given field exists in the form's source table.

        Args:
            field (Field): The field to validate.

        Raises:
            ValueError: If no source table is set or if the field is not present
                in the source table.
        """
        if self._table is None:
            raise ValueError("ERROR - Source table not provided.")
        if not any(field.id == table_field.id for table_field in self._table.get_fields()):
            raise ValueError(f"ERROR - Field {field.id} is not present in the source table.")

    @staticmethod
    def _assert_data_type(
        value: Field | Parameter | Calculation, data_type: DataType | ObjectDataType
    ):
        """
        Validate that a value has the expected data type.

        Args:
            value (Field | Parameter | Calculation): The value to check.
            data_type (DataType | ObjectDataType): The expected data type.

        Raises:
            ValueError: If the value's data type does not match the expected type.
        """
        if value.to_data_type() != data_type:
            raise ValueError(
                f"ERROR - Received invalid data type {value.to_data_type()}. "
                f"Expected {data_type}."
            )

    def _assert_and_return_variable(
        self, value: Any, data_type: DataType | ObjectDataType | None = None
    ) -> ModelVariable | None:
        """
        Validate and convert a value into a ModelVariable reference.

        This helper method checks if a value is a Field, Parameter, or Calculation,
        validates its data type if specified, and returns the appropriate ModelVariable
        reference. For fields, it also ensures the field exists in the source table.

        Args:
            value (Any): The value to process. Should be a Field, Parameter, or Calculation.
            data_type (Optional[DataType | ObjectDataType]): If provided, validates that
                the value matches this expected data type.

        Returns:
            ModelVariable | None: A ModelVariable reference wrapping the value's ID and type,
                or None if the value is not a Field, Parameter, or Calculation.

        Raises:
            ValueError: If the value is a Field not present in the source table, or if
                the data type does not match the expected type.
        """
        if isinstance(value, Field):
            self._assert_field_in_table(value)
            if data_type is not None:
                self._assert_data_type(value, data_type)
            return ModelVariable(ModelVariableType.FIELD, value.id)
        elif isinstance(value, Parameter | Calculation):
            if data_type is not None:
                self._assert_data_type(value, data_type)
            return ModelVariable(ModelVariableType.NAMED_VALUE, value.id)
        return None
