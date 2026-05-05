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
from typing import Any

from daitum_model import Calculation, DataType, Field, ObjectDataType, Parameter, Table
from typeguard import typechecked

from ._buildable import Buildable, json_type_info
from ._data import DataValidationRule, DefaultValueReference, EditOverride
from ._events import EditorEventType
from .base_view import BaseView
from .data import (
    Condition,
    DataValidationType,
    DefaultValueBehaviour,
    DefaultValueType,
    FilterMode,
    ValidationFlag,
    Value,
)
from .elements import ElementStates
from .filter_component import FilterableView, FilterComponent
from .model_event import EditorEvent, ModelEvent
from .styles import (
    BaseStyle,
    CellStyle,
    ColumnStyle,
    ConditionalFormattingRule,
    ConditionalFormattingType,
    Editor,
)


class DisplayState(Enum):
    """
    Specifies the display state of a `TableView` or `TreeView`.

    Attributes:
        STANDARD: Standard view with black text and borders
        READ_ONLY: Read only view with grey text and borders
        PRESENTATION: Read only view with black text and no borders
    """

    STANDARD = "STANDARD"
    READ_ONLY = "READ_ONLY"
    PRESENTATION = "PRESENTATION"


class ViewField(Buildable):
    """
    Defines the configuration and behaviour of a single field within a view.

    This class acts as a declarative definition only; it does not contain any
    runtime UI logic. All configuration is serialized via `Buildable` for
    consumption by the UI renderer.

    Args:
        field_id (str):
            The unique identifier of the underlying data field.

        display_name (Optional[str | Parameter | Calculation], optional):
            The display label for the field. May be a static string or a reference
            to a named value (parameter or calculation). Defaults to None.

        readonly (bool | Field, optional):
            Controls whether the field is read-only. If a boolean is provided,
            the field is always read-only or editable. If a `Field` is provided,
            its value is used as a dynamic read-only condition. Defaults to False.
    """

    def __init__(
        self,
        field_id: str,
        readonly: bool | Field = False,
    ):
        self.field_id: str = field_id
        self.is_display_name_reference: bool = False
        self.display_name: str | None = None

        if isinstance(readonly, Field):
            self.readonly_condition_column: str = readonly.id
        else:
            self.readonly: bool = readonly

        self.column_hide_variable: str | None = None
        self.header_column: bool = False

        self.editor_event: EditorEvent | None = None
        self.edit_override: EditOverride | None = None
        self.default_value_reference: DefaultValueReference | None = None
        self.data_validation_rule: DataValidationRule | None = None
        self.conditional_formatting_rules: list[ConditionalFormattingRule] | None = None

        self.column_style: ColumnStyle | None = None

    def set_display_name(self, name: str | Parameter | Calculation) -> "ViewField":
        """Sets the display label for this field."""
        self.is_display_name_reference = isinstance(name, Parameter | Calculation)
        self.display_name = name.id if isinstance(name, Parameter | Calculation) else name
        return self

    def set_column_hide_variable(self, column_hide_variable: str) -> "ViewField":
        """Sets the context variable that controls column visibility."""
        self.column_hide_variable = column_hide_variable
        return self

    def set_width(self, width: int) -> "ViewField":
        """Sets the column width in pixels."""
        if self.column_style is None:
            self.column_style = ColumnStyle()
        self.column_style.width = width
        return self

    def set_header_column(self, header_column: bool) -> "ViewField":
        """Sets whether this field is treated as a header column."""
        self.header_column = header_column
        return self

    def set_display_field(self, display_field: str) -> "ViewField":
        """Sets an alternative field to display instead of the underlying field value."""
        if self.column_style is None:
            self.column_style = ColumnStyle()
        self.column_style.display_field = display_field
        return self

    def set_on_click_event(self, event: ModelEvent) -> "ViewField":
        """
        Assigns an editor event to be triggered when the editor is clicked.

        Args:
            event (ModelEvent): The event to execute on editor click.

        Raises:
            ValueError: If an editor event has already been set.
        """
        if self.editor_event is not None:
            raise ValueError("ERROR - Editor Event has already been set")
        self.editor_event = EditorEvent(EditorEventType.ON_CLICK, event)
        return self

    def set_on_change_event(self, event: ModelEvent) -> "ViewField":
        """
        Assigns an editor event to be triggered when the editor's value changes.

        Args:
            event (ModelEvent): The event to execute on editor value change.

        Raises:
            ValueError: If an editor event has already been set.
        """
        if self.editor_event is not None:
            raise ValueError("ERROR - Editor Event has already been set")
        self.editor_event = EditorEvent(EditorEventType.ON_CHANGE, event)
        return self

    def set_list_validation(self, reference_field: str) -> "ViewField":
        """
        Sets a list-based data validation rule for this field.

        Args:
            reference_field (str): The name of the field that provides the list of valid values.
        """
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
    ) -> "ViewField":
        """
        Sets a range-based data validation rule for this field.

        Args:
            min_value (str, Value or None): A fixed `Value` or the name of the field or named value
                providing min value dynamically.
            max_value (str, Value or None): A fixed `Value` or the name of the field or named value
                providing max value dynamically.
            flag (ValidationFlag, optional): Whether the boundaries are inclusive or exclusive.
                Defaults to INCLUSIVE.
        """

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

    def add_conditional_formatting_rule(
        self,
        condition_column: str,
        override_styles: ColumnStyle,
        element_states: ElementStates | None = None,
        stop_if_true: bool = False,
        formatting_type: ConditionalFormattingType = ConditionalFormattingType.BOOLEAN,
    ) -> "ViewField":
        """
        Adds a new conditional formatting rule to the current configuration.

        The rule applies specified style overrides to a column when a condition based
        on another column's value is met. Optionally, further rules can be stopped from
        processing once this rule evaluates as true.

        Args:
            condition_column (str):
                The name of the column whose value is evaluated as the condition for
                applying this formatting rule.

            override_styles (ColumnStyle):
                The styles to apply when the condition is true. These styles override
                the existing column styles.

            element_states (ElementStates | None):
                The element state to apply if the condition is met.

            stop_if_true (bool, optional):
                If True, no further conditional formatting rules will be applied after
                this rule if its condition evaluates to true. Defaults to False.

            formatting_type (ConditionalFormattingType, optional):
                The type of condition to apply (e.g., BOOLEAN, AFTER_TODAY, BEFORE_TODAY).
                Defaults to ConditionalFormattingType.BOOLEAN.
        """
        rule = ConditionalFormattingRule(
            condition_column, override_styles, element_states, stop_if_true, formatting_type
        )
        if self.conditional_formatting_rules is None:
            self.conditional_formatting_rules = []
        self.conditional_formatting_rules.append(rule)

        return self

    def set_default_value_reference(
        self,
        value: Field | Parameter | Calculation,
        behaviour: DefaultValueBehaviour = DefaultValueBehaviour.DEFAULT,
    ) -> "ViewField":
        """
        Set the default value reference for this field.

        This configures a reference value that can be used to reset the field's value
        to a predefined default. The reference can either be another field or a named value,
        with an associated behaviour determining how the reset behaves in the UI.

        Args:
            value (Field | Parameter | Calculation):
                The source of the default value. If a `Field` instance, the reference type
                is set to FIELD; otherwise, it is treated as a NAMED_VALUE.

            behaviour (DefaultValueBehaviour, optional):
                Controls the behavior of the default value override, such as showing a reset icon.
                Defaults to `DefaultValueBehaviour.DEFAULT`.
        """
        value_type = (
            DefaultValueType.FIELD if isinstance(value, Field) else DefaultValueType.NAMED_VALUE
        )
        value_id = value.id if isinstance(value, Field) else value.id
        self.default_value_reference = DefaultValueReference(value_type, value_id, behaviour)
        return self

    def set_edit_override(
        self, target_reference_field: str, target_field_id: str, map_key_field: str | None = None
    ) -> "ViewField":
        """
        Set an edit override that redirects edits from the visible table to another underlying
        table.

        This is required when the field being edited does not directly belong to the displayed
        table, but rather to a related table referenced by a field.

        Args:
            target_reference_field (str):
                The field in the displayed table containing a reference to the row/table to edit.

            target_field_id (str):
                The field ID in the referenced table where the actual value should be edited.

            map_key_field (Optional[str], optional):
                If the target field is a map-type, this field contains the map key to identify
                the correct entry. Defaults to None.
        """
        self.edit_override = EditOverride(target_reference_field, target_field_id, map_key_field)
        return self

    def set_cell_style(self, **kwargs) -> "ViewField":
        """
        Update the styling properties for the cells in this column.

        This method ensures that the column_style object exists and then updates
        its attributes based on the provided keyword arguments.

        Args:
            **kwargs: Style attributes to set on the column's cell style.
        """
        if self.column_style is None:
            self.column_style = ColumnStyle()
        self._update_style(self.column_style, kwargs)
        return self

    def set_header_style(self, **kwargs) -> "ViewField":
        """
        Update the styling properties for the header cell of this column.

        Ensures that the header_style is initialized before applying updates.

        Args:
            **kwargs: Style attributes to set on the column header's style.
        """
        if self.column_style is None:
            self.column_style = ColumnStyle()
        if self.column_style.header_style is None:
            self.column_style.header_style = CellStyle()
        self._update_style(self.column_style.header_style, kwargs)
        return self

    def set_read_only_style(self, **kwargs) -> "ViewField":
        """
        Update the styling properties applied when this column is read-only.

        Ensures that the read_only_style is initialized before applying updates.

        Args:
            **kwargs: Style attributes to set on the read-only column style.
        """
        if self.column_style is None:
            self.column_style = ColumnStyle()
        if self.column_style.read_only_style is None:
            self.column_style.read_only_style = CellStyle()
        self._update_style(self.column_style.read_only_style, kwargs)
        return self

    def set_column_config(
        self, frozen: bool | None = None, editor: Editor | None = None
    ) -> "ViewField":
        """
        Configure column-level settings such as freezing behavior and editor configuration.

        This method ensures the column style is initialized, then applies the provided
        settings to control whether the column is frozen (i.e., remains visible during
        horizontal scrolling) and/or sets the editor used for the column's cells.

        Args:
            frozen (Optional[bool], optional):
                If provided, sets whether the column is frozen. A frozen column stays fixed during
                horizontal scroll. If None, the frozen setting is not modified.

            editor (Optional[Editor], optional):
                If provided, assigns the editor configuration to be used for the column's cells.
                If None, the editor setting is not modified.
        """
        if self.column_style is None:
            self.column_style = ColumnStyle()
        if frozen is not None:
            self.column_style.frozen = frozen
        if editor is not None:
            self.column_style.editor = editor
        return self

    @staticmethod
    def _update_style(style_obj, values: dict):
        for key, value in values.items():
            if hasattr(style_obj, key):
                setattr(style_obj, key, value)
            else:
                raise AttributeError(f"{type(style_obj).__name__} has no attribute '{key}'")


class TreeViewField(ViewField):
    """
    Extends ViewField to support hierarchical/tree structures.

    Attributes:
        children (List[str]):
            Field definitions for each level of the hierarchy.
            If a child is None or has a null name, it will be skipped for that level.

        dynamic (bool):
            If True, this column is dynamic and will be duplicated based on values
            in the deepest level of the hierarchy.

        default_display_value (Any):
            Default value to use for dynamic columns when no row exists in the child table.

        override_type (Optional[DataType]):
            Data type override for the field, if applicable.
    """

    def __init__(
        self,
        field_id: str,
        readonly: bool | Field = False,
    ):
        super().__init__(field_id, readonly)
        self.dynamic: bool = False
        self.default_display_value: Any | None = None
        self.override_type: DataType | None = None

    def set_children(self, children: list[str]) -> "TreeViewField":
        """Sets the child field names for each level of the hierarchy."""
        self.children = [ViewField(child) for child in children]
        return self

    def set_dynamic(self, dynamic: bool) -> "TreeViewField":
        """Sets whether this column is dynamic and duplicated per value in the deepest level."""
        self.dynamic = dynamic
        return self

    def set_override_type(self, override_type: "DataType") -> "TreeViewField":
        """Sets the data type override for display purposes."""
        self.override_type = override_type
        return self

    def set_default_display_value(self, value: Any) -> "TreeViewField":
        """Sets the default display value for dynamic columns when no row exists."""
        self.default_display_value = value
        return self


@dataclass
class NestedHeaders(Buildable):
    """
    Represents a nested header definition for a table, allowing labels
    to span multiple columns and optionally be collapsible.

    Attributes:
        label (Optional[str]): The display label of the header.
        colspan (Optional[int]): Number of columns this header spans.
        collapsible (bool): Whether the header group can be collapsed. Defaults to True.
        is_label_reference (bool): Indicates if the label is a reference to another value.
            Defaults to False.
    """

    label: str | None = None
    colspan: int | None = None
    collapsible: bool = True
    is_label_reference: bool = False


@typechecked
class BaseTableView(BaseView, FilterableView):
    """
    Defines a simple, single-table view with various display and interaction configurations.

    Attributes:
        table (str): The ID of the table this view is built on.
        fields (List[ViewField]): Field definitions to be included in the view,
            in display order.
        can_move_rows (bool): Whether the user can move rows around.
        can_change_size (bool): Whether the table can grow/shrink in size.
        can_sort (bool): Whether sorting is enabled.
        can_filter (bool): Whether filtering is enabled.
        show_band_color (bool): Whether to apply alternating row banding.
        band_odd_row_background_color (Optional[str]): Background color for odd banded rows.
        band_even_row_background_color (Optional[str]): Background color for even banded rows.
        background_color (Optional[str]): Background color for the table itself.
        row_height (Optional[int]): Fixed height for each row.
        column_width_adjustable (bool): Whether users can manually resize columns.
        header_style (Optional[BaseStyle]): Style applied to all headers.
        read_only_style (Optional[BaseStyle]): Style applied to read-only columns.
        show_row_number (bool): Whether to display row numbers.
        header_height (Optional[int]): Height of the table headers.
        nested_headers (List[NestedHeaders]): List of nested header configurations.
        table_height (Optional[str]): Explicit height for the table, if any.
        only_display_nested_headers (bool): Whether to show only the nested headers,
            hiding field-level headers.
        show_dropdowns_below (bool): Whether dropdowns always appear below the editing cell.
    """

    def __init__(
        self,
        table: Table,
        display_name: str | None = None,
        hidden: bool = False,
    ):
        """
        Initialize a BaseTableView instance.

        Args:
            table (Table): The data table on which the view is based.
            display_name (str | None, optional): Display name of the view. Defaults to the table's
            ID if not provided.
            hidden (bool, optional): Whether the view is hidden in the UI. Defaults to False.
        """
        BaseView.__init__(self, hidden)
        if display_name is not None:
            self._display_name = display_name
        FilterableView.__init__(self, None)
        self._table: Table = table
        self.table: str = table.id
        self.fields: list[ViewField] = []

        self.display_state = DisplayState.STANDARD
        self.display_state_condition: Condition | None = None

        self.can_move_rows: bool = True
        self.can_change_size: bool = True
        self.can_sort: bool = True
        self.can_filter: bool = True

        self.show_band_color: bool = True
        self.band_odd_row_background_color: str | None = None
        self.band_even_row_background_color: str | None = None
        self.background_color: str | None = None
        self.row_height: int | None = None
        self.column_width_adjustable: bool = False

        self.header_style: BaseStyle | None = None
        self.read_only_style: BaseStyle | None = None
        self.show_row_number: bool = False
        self.header_height: int | None = None

        self.nested_headers: list[NestedHeaders] | None = None
        self.table_height: str | None = None
        self.only_display_nested_headers: bool = False
        self.show_dropdowns_below: bool = True

    def set_disable_table_controls(self, disable: bool) -> "BaseTableView":
        """Disables or enables user controls (row movement, resizing, sorting, filtering)."""
        self.can_move_rows = not disable
        self.can_change_size = not disable
        self.can_sort = not disable
        self.can_filter = not disable
        return self

    def set_display_state(
        self, state: DisplayState, condition: Condition | None = None
    ) -> "BaseTableView":
        """Sets the display state and optional condition for the view."""
        self.display_state = state
        self.display_state_condition = condition
        return self

    def set_use_filter(self, use_filter: FilterComponent) -> "BaseTableView":
        """Sets the filter component for this view."""
        FilterableView.__init__(self, use_filter)
        return self


def _validation_view_field(field: Field, view_field: ViewField) -> ViewField:
    from ._validation import _add_validation_formatting

    validation_fields_list = field.get_validation_fields()
    combined_message_field = field.get_combined_message_field()

    if (
        validation_fields_list
        and isinstance(validation_fields_list, list)
        and combined_message_field
    ):
        for validation_field in validation_fields_list:
            view_field = _add_validation_formatting(
                view_field, validation_field, combined_message_field.id
            )

    return view_field


@json_type_info("standard")
class TableView(BaseTableView):
    """
    A UI component that displays data in a tabular format with rows and columns

    Designed to resemble a spreadsheet or Excel-like interface, TableView supports
    structured data presentation, allowing for features like sorting, filtering,
    cell formatting, and interactive editing.

    Attributes:
        filter_mode (Optional[daitum_ui.data.FilterMode]): An optional filtering strategy
            applied to the table.
    """

    def __init__(
        self,
        table: Table,
        display_name: str | None = None,
        hidden: bool = False,
    ):
        """
        Initializes a TableView with an underlying table and optional settings.

        Args:
            table (Table): The data table to base the view on.
            display_name (Optional[str]): Optional name for display.
                Defaults to the ID of the underlying table.
            hidden (bool): If True, the view is not visible in the UI. Defaults to False
        """
        BaseTableView.__init__(self, table, display_name, hidden)
        self._hidden_conditions: list[Condition] | None = None
        self.filter_mode: FilterMode | None = None

    def add_field(
        self,
        field_id,
        readonly: bool | Field = False,
        allow_reset: bool = False,
    ) -> ViewField:
        """
        Adds a column to the table view.

        Args:
            field_id (str): ID of the field to include.
            readonly (Optional[Union[bool, Field]]): Optional readonly condition.
            allow_reset (bool): If True, adds a default value reset reference to the field.

        Returns:
            ViewField: The constructed view field.

        Raises:
            ValueError: If the field ID does not exist in the source table.
        """
        table_field = self._table.get_field(field_id)
        view_field = ViewField(field_id, readonly)

        self.fields.append(_validation_view_field(table_field, view_field))

        if allow_reset:
            if table_field.tracking_group is None:
                raise ValueError("allow_reset invalid on fields without change tracking set")
            tracked_field = self._table.get_field(table_field.tracking_id)
            view_field.set_default_value_reference(tracked_field)

        return view_field


@json_type_info("tree")
class TreeView(BaseTableView):
    """
    A table view that supports hierarchical tree structures.

    Attributes:
        row_number_depth (int): The depth level at which row numbering applies.
        dynamic_field_source (Optional[str]): ID of the field used for determining dynamic
            column duplication.
        children_fields (List[str]): List of field names used to define children at each tree level.
        table_evaluation_order (List[str]): Order in which tables should be evaluated.
    """

    def __init__(
        self,
        table: Table,
        display_name: str | None = None,
        hidden: bool = False,
    ):
        """
        Initializes a TreeView with support for nested children and dynamic fields.

        Args:
            table (Table): The data table backing this view.
            display_name (Optional[str]): Optional name to display for the view.
            hidden (bool): If True, the view is not visible in the UI. Defaults to False.
        """
        BaseTableView.__init__(self, table, display_name, hidden)
        self._hidden_conditions: list[Condition] | None = None
        self.row_number_depth: int = 0
        self.dynamic_field_source: str | None = None

        self.children_fields: list[str] | None = None
        self.table_evaluation_order: list[str] | None = None

        self._tables: list[Table] = []

    def set_table_evaluation_order(self, *table_evaluation_order: Table) -> "TreeView":
        """
        Sets the evaluation order of tables involved in the tree.

        Args:
            table_evaluation_order (Table): One or more tables.
        """
        self._tables = list(table_evaluation_order)
        self.table_evaluation_order = [table.id for table in self._tables]
        return self

    def set_children_field(self, *children_field: str):
        """
        Sets the field names used to identify child relationships at each level of the hierarchy.

        Each field must:
        - Exist in the corresponding table (table at the same index in the hierarchy).
        - Be of type `ObjectArray`.
        - Refer back to the correct source table.

        Args:
            *children_field (str): One field name per hierarchy level. The number of fields must be
                exactly one less than the number of tables in the hierarchy.

        Raises:
            ValueError: If the number of provided field names is incorrect.
            ValueError: If a field name does not exist in the corresponding table.
            ValueError: If a field is not an ObjectArray type.
            ValueError: If a field does not refer back to the correct source table.
        """
        expected_fields = len(self._tables) - 1
        if not self._tables or len(children_field) != expected_fields:
            raise ValueError(
                f"Expected {expected_fields} child field(s), but got {len(children_field)}."
            )

        children_fields = list(children_field)
        for index, child in enumerate(children_fields):
            table = self._tables[index]

            # Check field exists
            if not any(table_field.id == child for table_field in table.get_fields()):
                raise ValueError(f"The field '{child}' does not exist in the table '{table.id}'.")

            # Get and check data type
            children_field_type = table.get_field(child).data_type
            if (
                not isinstance(children_field_type, ObjectDataType)
                or not children_field_type.is_array()
            ):
                raise ValueError(
                    f"The field '{child}' in table '{table.id}' must be an ObjectArray type. "
                    f"Received: {children_field_type}"
                )

            # Check reference to correct table
            referral_table = self._tables[index + 1].id
            source_table = children_field_type._source_table.id
            if source_table != referral_table:
                raise ValueError(
                    f"The field '{child}' must refer back to the table '{referral_table}'. "
                    f"Received reference to: {source_table}"
                )

        self.children_fields = children_fields
        return self

    def add_field(
        self,
        field_id,
        children: list[str] | str | None = None,
        read_only: bool = False,
        allow_reset: bool = False,
    ) -> TreeViewField:
        """
        Adds a tree-aware field to the view.

        Args:
            field_id (str): ID of the field to add.
            children (Optional[List[str] | str]): Child field names per hierarchy level.
            allow_reset (bool): If True, adds a default value reset reference to the field.

        Returns:
            TreeViewField: The created tree field.

        Raises:
            ValueError: If the field ID does not exist in the backing table.
        """
        if not self._tables or not self.children_fields:
            raise ValueError(
                "Table evaluation order and children fields must be set before proceeding."
            )
        if not any(table_field.id == field_id for table_field in self._table.get_fields()):
            raise ValueError(f"The field {field_id} does not exist in the table")

        if children is None:
            children = [field_id for _ in range(len(self.children_fields))]
        elif isinstance(children, str):
            children = [children]

        for index, child in enumerate(children, start=1):
            table = self._tables[index]
            if not any(table_field.id == child for table_field in table.get_fields()):
                raise ValueError(f"The field {child} does not exist in the table {table.id}")

        view_field = TreeViewField(field_id, read_only)
        view_field.set_children(children)

        deepest_child = self._tables[-1].get_field(children[-1])

        self.fields.append(_validation_view_field(deepest_child, view_field))

        if allow_reset:
            if deepest_child.tracking_group is None:
                raise ValueError("allow_reset invalid on fields without change tracking set")
            tracked_field = self._table.get_field(deepest_child.tracking_id)
            view_field.set_default_value_reference(tracked_field)

        return view_field
