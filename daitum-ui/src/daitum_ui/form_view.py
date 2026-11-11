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

A :class:`FormView` is a grid-based layout for displaying and editing the data of a single table
row (or model-level values). It is composed of **cells** — each a :class:`FormCell` wrapping one
:class:`~daitum_ui.elements.Element` together with its grid placement (row, column, spans, and
horizontal alignment).

Elements are first-class and defined in :mod:`daitum_ui.elements`; a form merely places them.
There are two ways to add an element:

* :meth:`FormView.add_form_element` — the generic adder. Place any pre-built element (including
  containers such as :class:`~daitum_ui.elements.Card`, :class:`~daitum_ui.elements.Badge`, or
  :class:`~daitum_ui.elements.Container`) at a grid position.
* A per-type ``add_*`` convenience method (``add_text``, ``add_text_input``, ``add_number_input``,
  ``add_drop_down``, ``add_date_time``, ``add_check_box``, ``add_slider``, …) — constructs the
  element (which self-validates its bound data type and wires in model-validation states),
  checks the bound field belongs to the form's source table, places it, and returns the element
  for fluent configuration.

Example:
    >>> form = builder.add_form_view(
    ...     display_name="Customer Details",
    ...     total_rows=6,
    ...     table=customers_table,
    ...     filter_mode=filter_mode,
    ... )
    >>> form.set_columns(num_columns=2, width="250px")
    >>> form.add_text("Name:", row=1, column=1)
    >>> form.add_text_input(customers_table.name_field, row=1, column=2)
"""

from dataclasses import dataclass

from daitum_model import (
    Calculation,
    DataType,
    Field,
    ObjectDataType,
    Parameter,
    Table,
)
from typeguard import typechecked

from daitum_ui._buildable import Buildable, json_type_info
from daitum_ui._data import ModelVariable, ModelVariableType
from daitum_ui.base_view import BaseView
from daitum_ui.data import FilterMode
from daitum_ui.elements import (
    ArrayElement,
    ArrayLayout,
    Button,
    Checkbox,
    ColorPicker,
    DateTimeMode,
    DateTimePicker,
    Dropdown,
    Element,
    IconCheckbox,
    IconElement,
    IconPicker,
    ListElement,
    ModelEditorLink,
    NumberInput,
    RangeBar,
    ReviewRating,
    Slider,
    Text,
    TextInput,
)
from daitum_ui.icons import Icon
from daitum_ui.model_event import ModelEvent
from daitum_ui.styles import HorizontalAlignment, IconConfig


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
class FormCell(Buildable):
    """
    One placed element within a :class:`FormView`'s grid.

    A cell wraps a single :class:`~daitum_ui.elements.Element` and the grid geometry describing
    where it sits. Build a cell directly and add it with :meth:`FormView.add_form_element`, or let
    a per-type ``add_*`` method build one for you.

    Attributes:
        element (Element): The element rendered in this cell.
        row_start (int): Starting (1-based) grid row.
        column_start (int): Starting (1-based) grid column.
        row_span (int): Number of rows the cell spans.
        column_span (int): Number of columns the cell spans.
        horizontal_alignment (HorizontalAlignment | None): Horizontal alignment within the cell.
    """

    element: Element
    row_start: int = 0
    column_start: int = 0
    row_span: int = 1
    column_span: int = 1
    horizontal_alignment: HorizontalAlignment | None = None


@typechecked
@json_type_info("form")
class FormView(BaseView):
    """
    A grid-based layout for displaying and editing a single table row.

    A ``FormView`` arranges elements — labels, inputs, dropdowns, pickers, buttons, and composed
    containers — in a CSS-grid of :class:`FormCell`\\s. It can be bound to a source table so its
    elements resolve against a single, filter-selected row.

    Attributes:
        total_rows (int | None): The number of rows in the form grid.
        source_table (str | None): The ID of the source table, if provided.
        form_columns (list[_FormColumn]): Column layout definitions.
        cells (list[FormCell]): The placed elements.
        filter_mode (FilterMode | None): Selects which single row of the source table the form
            displays. A ``MatchRowFilterMode`` resolves the row from a context variable holding its
            index (or, for a keyed table, its key); a ``MatchFieldFilterMode`` resolves it by
            matching a context variable's value against ``filter_target_field``.
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
        self.cells: list[FormCell] = []

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

    def build(self) -> dict:
        """Serialise the form, first checking a table-bound form selects a row.

        A form backed by a source table reads that table's fields, so it needs a ``filter_mode``
        to pick which single row to show — without one the frontend finds no row. A form with no
        source table (e.g. named-values only, the common case) has nothing to filter and is fine.
        """
        if self.source_table is not None and getattr(self, "filter_mode", None) is None:
            raise ValueError(
                f"Form view bound to table {self.source_table!r} has no filter_mode; set one "
                f"(e.g. MatchRowFilterMode) so the form knows which row to display."
            )
        built: dict = super().build()
        return built

    def add_form_element(  # noqa: PLR0913
        self,
        row: int,
        column: int,
        element: Element,
        *,
        horizontal_alignment: HorizontalAlignment | None = None,
        row_span: int = 1,
        column_span: int = 1,
    ) -> FormCell:
        """
        Place any element in the form grid, returning the created :class:`FormCell`.

        This is the generic, element-agnostic adder. Build an element (including a container such
        as :class:`~daitum_ui.elements.Card`, :class:`~daitum_ui.elements.Badge`, or
        :class:`~daitum_ui.elements.Container`) and position it. The per-type ``add_*`` methods are
        thin wrappers over this.

        Args:
            row (int): Starting (1-based) grid row.
            column (int): Starting (1-based) grid column.
            element (Element): The element to place.
            horizontal_alignment (HorizontalAlignment | None): Alignment within the cell.
            row_span (int): Number of rows the cell spans.
            column_span (int): Number of columns the cell spans.

        Returns:
            FormCell: The created cell (mutate it to adjust placement).
        """
        cell = FormCell(
            element=element,
            row_start=row,
            column_start=column,
            row_span=row_span,
            column_span=column_span,
            horizontal_alignment=horizontal_alignment,
        )
        self.cells.append(cell)
        return cell

    # Per-type convenience adders

    def add_text(
        self,
        text: str | Field | Parameter | Calculation,
        row: int,
        column: int,
    ) -> Text:
        """
        Add a static or data-bound text label at a grid position.

        Args:
            text: A static string, or a Field/Parameter/Calculation to display (read-only).
            row: Starting grid row.
            column: Starting grid column.

        Returns:
            Text: The created element (chain ``set_font_weight``, ``set_variant``, etc.).
        """
        if isinstance(text, str):
            element = Text(value=text)
        else:
            if isinstance(text, Field):
                self._assert_field_in_table(text)
            element = Text(data_source=text)
        self.add_form_element(row, column, element)
        return element

    def add_icon(self, icon_source: Icon, row: int, column: int) -> IconElement:
        """Add an icon element at a grid position."""
        element = IconElement(icon_source=icon_source)
        self.add_form_element(row, column, element)
        return element

    def add_button(
        self,
        text: str,
        on_click: ModelEvent,
        row: int,
        column: int,
    ) -> Button:
        """
        Add a clickable button at a grid position.

        Args:
            text: The button label.
            on_click: The event triggered when clicked.
            row: Starting grid row.
            column: Starting grid column.
        """
        element = Button(text_value=text, on_click=on_click)
        self.add_form_element(row, column, element)
        return element

    def add_model_editor_link(  # noqa: PLR0913, PLR0917
        self,
        row: int,
        column: int,
        model_id: Field | Parameter | Calculation,
        scenario_id: Field | Parameter | Calculation | None = None,
        text_value: str = "Open Model",
        open_new_tab: bool = False,
    ) -> ModelEditorLink:
        """
        Add a hyperlink that opens the Daitum model editor.

        ``model_id`` (and ``scenario_id`` when given) must be INTEGER-typed; a ``Field`` must
        belong to the form's source table.
        """
        if isinstance(model_id, Field):
            self._assert_field_in_table(model_id)
        self._assert_data_type(model_id, DataType.INTEGER)
        if scenario_id is not None:
            if isinstance(scenario_id, Field):
                self._assert_field_in_table(scenario_id)
            self._assert_data_type(scenario_id, DataType.INTEGER)

        element = ModelEditorLink(
            model_id=model_id,
            scenario_id=scenario_id,
            text_value=text_value,
            open_new_tab=open_new_tab,
        )
        self.add_form_element(row, column, element)
        return element

    def add_list(self, list_element: ListElement, row: int, column: int) -> ListElement:
        """Place a pre-built :class:`~daitum_ui.elements.ListElement` at a grid position."""
        self.add_form_element(row, column, list_element)
        return list_element

    def add_text_input(
        self,
        value: Field | Parameter | Calculation,
        row: int,
        column: int,
    ) -> TextInput:
        """Add a single-line text input bound to a STRING value."""
        if isinstance(value, Field):
            self._assert_field_in_table(value)
        element = TextInput(value)
        self.add_form_element(row, column, element)
        return element

    def add_text_area(
        self,
        value: Field | Parameter | Calculation,
        row: int,
        column: int,
        rows: int = 2,
    ) -> TextInput:
        """Add a multiline text area bound to a STRING value."""
        if isinstance(value, Field):
            self._assert_field_in_table(value)
        element = TextInput(value, rows=rows)
        self.add_form_element(row, column, element)
        return element

    def add_number_input(
        self,
        value: Field | Parameter | Calculation,
        row: int,
        column: int,
    ) -> NumberInput:
        """Add a numeric input bound to an INTEGER or DECIMAL value."""
        if isinstance(value, Field):
            self._assert_field_in_table(value)
        element = NumberInput(value)
        self.add_form_element(row, column, element)
        return element

    def add_drop_down(
        self,
        value: Field | Parameter | Calculation,
        row: int,
        column: int,
    ) -> Dropdown:
        """
        Add a dropdown bound to an OBJECT value.

        The display label defaults to the referenced table's key column; override with
        ``set_display_field`` on the returned element.
        """
        if isinstance(value, Field):
            self._assert_field_in_table(value)
        element = Dropdown(value)
        self.add_form_element(row, column, element)
        return element

    def add_date_time(
        self,
        value: Field | Parameter | Calculation,
        row: int,
        column: int,
        reference_field: str | None = None,
    ) -> DateTimePicker:
        """
        Add a date/time picker bound to a DATE, TIME, or DATETIME value.

        The picker ``mode`` is chosen from the resolved data type. When ``reference_field`` is
        given, ``value`` is an OBJECT reference and the referenced field supplies the type.
        """
        if isinstance(value, Field):
            self._assert_field_in_table(value)
        data_type = value.to_data_type()
        if reference_field is not None:
            assert isinstance(data_type, ObjectDataType) and not data_type.is_array()
            data_type = value[reference_field].to_data_type()

        if data_type == DataType.DATE:
            mode = DateTimeMode.DATE
        elif data_type == DataType.TIME:
            mode = DateTimeMode.TIME
        elif data_type == DataType.DATETIME:
            mode = DateTimeMode.DATE_TIME
        else:
            raise ValueError(
                f"ERROR - Invalid data type for date/time picker {data_type}. "
                f"Expected DATE, TIME, or DATETIME."
            )

        element = DateTimePicker(value, mode, object_field_reference=reference_field)
        self.add_form_element(row, column, element)
        return element

    def add_colour_picker_input(
        self,
        value: Field | Parameter | Calculation,
        row: int,
        column: int,
    ) -> ColorPicker:
        """Add a colour picker bound to a STRING value (e.g. a hex colour)."""
        if isinstance(value, Field):
            self._assert_field_in_table(value)
        element = ColorPicker(value)
        self.add_form_element(row, column, element)
        return element

    def add_icon_picker(
        self,
        value: Field | Parameter | Calculation,
        row: int,
        column: int,
    ) -> IconPicker:
        """Add an icon picker bound to a STRING value (an icon identifier)."""
        if isinstance(value, Field):
            self._assert_field_in_table(value)
        element = IconPicker(value)
        self.add_form_element(row, column, element)
        return element

    def add_array(
        self,
        value: Field | Parameter | Calculation,
        row: int,
        column: int,
        layout: ArrayLayout = ArrayLayout.BADGE,
    ) -> ArrayElement:
        """Add an element that shows and edits an ARRAY value's values."""
        if isinstance(value, Field):
            self._assert_field_in_table(value)
        element = ArrayElement(value, layout)
        self.add_form_element(row, column, element)
        return element

    def add_check_box(
        self,
        value: str | Field | Parameter | Calculation,
        row: int,
        column: int,
    ) -> Checkbox:
        """Add a checkbox bound to a boolean value (or a context variable id)."""
        element = Checkbox(self._boolean_source(value))
        self.add_form_element(row, column, element)
        return element

    def add_slider(
        self,
        value: str | Field | Parameter | Calculation,
        row: int,
        column: int,
    ) -> Slider:
        """Add a slider bound to a boolean value (or a context variable id)."""
        element = Slider(self._boolean_source(value))
        self.add_form_element(row, column, element)
        return element

    def add_icon_check_box(  # noqa: PLR0913
        self,
        value: str | Field | Parameter | Calculation,
        row: int,
        column: int,
        off_icon: IconConfig,
        on_icon: IconConfig,
    ) -> IconCheckbox:
        """Add an icon checkbox bound to a boolean value (or a context variable id).

        Both ``off_icon`` and ``on_icon`` are required — the frontend needs an icon for each
        state.
        """
        element = IconCheckbox(self._boolean_source(value), off_icon=off_icon, on_icon=on_icon)
        self.add_form_element(row, column, element)
        return element

    def add_review_rating(
        self,
        value: Field | Parameter | Calculation,
        row: int,
        column: int,
    ) -> ReviewRating:
        """Add a review rating bound to a numeric value."""
        if isinstance(value, Field):
            self._assert_field_in_table(value)
        element = ReviewRating(value)
        self.add_form_element(row, column, element)
        return element

    def add_range_bar(  # noqa: PLR0913, PLR0917
        self,
        value: Field | Parameter | Calculation,
        row: int,
        column: int,
        min_value: Field | Parameter | Calculation | None = None,
        max_value: Field | Parameter | Calculation | None = None,
    ) -> RangeBar:
        """
        Add a read-only range bar showing a numeric value between ``min_value`` and
        ``max_value`` (0 and 100 when not given).

        Returns:
            RangeBar: The created element (chain ``set_error_ranges``, ``set_indicator``,
            ``set_size``, etc.).
        """
        for source in (value, min_value, max_value):
            if isinstance(source, Field):
                self._assert_field_in_table(source)
        element = RangeBar(value, min_value=min_value, max_value=max_value)
        self.add_form_element(row, column, element)
        return element

    # Helpers

    def _boolean_source(
        self, value: str | Field | Parameter | Calculation
    ) -> ModelVariable | Field | Parameter | Calculation:
        """Resolve a boolean adder's ``value``: a ``str`` is a context-variable id (returned as a
        resolved ``ModelVariable``), otherwise a field/named value (field membership is checked
        here; the data type is checked by the element)."""
        if isinstance(value, str):
            return ModelVariable(ModelVariableType.CONTEXT_VARIABLE, value)
        if isinstance(value, Field):
            self._assert_field_in_table(value)
        return value

    def _assert_field_in_table(self, field: Field):
        """Validate that ``field`` exists in the form's source table.

        Raises:
            ValueError: If no source table is set or the field is not in it.
        """
        if self._table is None:
            raise ValueError("ERROR - Source table not provided.")
        if not any(field.id == table_field.id for table_field in self._table.get_fields()):
            raise ValueError(f"ERROR - Field {field.id} is not present in the source table.")

    @staticmethod
    def _assert_data_type(
        value: Field | Parameter | Calculation, data_type: DataType | ObjectDataType
    ):
        """Validate that ``value`` has the expected data type."""
        if value.to_data_type() != data_type:
            raise ValueError(
                f"ERROR - Received invalid data type {value.to_data_type()}. Expected {data_type}."
            )
