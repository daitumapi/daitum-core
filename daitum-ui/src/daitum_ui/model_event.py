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
Event system for defining user interactions and application behavior.

This module provides the ModelEvent class, which represents sequences of actions
that execute in response to user interactions (clicks, changes, etc.) or other
triggers. Events enable complex workflows including data manipulation, navigation,
modal dialogs, transactions, and more.

Main Components
---------------

**Core Classes:**
    - ModelEvent: Container for a sequence of actions to execute
    - EditorEvent: Wrapper connecting editor interactions to model events

**Action Categories:**
    The ModelEvent class supports 13 action types organized by purpose:

    UI Navigation:
        - add_show_modal_action(): Display modal dialogs
        - add_close_modal_action(): Close modal dialogs
        - add_switch_view_action(): Navigate to different views

    Data Operations:
        - add_set_table_value_action(): Set field values in table rows
        - add_set_name_value_action(): Update Parameters or Calculations
        - add_copy_values_action(): Copy values between rows
        - add_clear_values_action(): Clear field values in rows

    Row Management:
        - add_insert_row_action(): Insert new blank rows
        - add_duplicate_row_action(): Duplicate existing rows
        - add_delete_row_action(): Delete rows from tables

    State Management:
        - add_set_context_action(): Update context variable values

    Transaction Control:
        - add_begin_transaction(): Start data transaction
        - add_commit_transaction(): Save transaction changes
        - add_rollback_transaction(): Discard transaction changes

    External Operations:
        - add_run_report_action(): Execute reports
        - add_run_data_source_action(): Refresh data sources

Event Execution Model
---------------------

**Action Sequences:**
    ModelEvent contains an ordered list of actions that execute sequentially.
    Actions are executed in the order they were added to the event.

**Conditional Execution:**
    Every action supports optional conditional execution via the `condition`
    parameter. When provided, the action only executes if the condition
    context variable evaluates to true.

**Transaction Safety:**
    Use transaction actions to group data operations into atomic units:

    - BEGIN starts a transaction
    - COMMIT saves all changes
    - ROLLBACK discards all changes

    Transactions ensure data consistency when multiple operations must
    succeed or fail together.

Row Selection Modes
-------------------

Row operations support multiple selection strategies via RowSelectionMode:

- INDEX: Select row by numeric position
- KEY: Select row by unique key field value

When using KEY mode, provide a key_field to identify the matching field.

Insert and Delete Modes
------------------------

**InsertMode (row insertion):**
    - END_OF_TABLE: Insert at table end
    - START_OF_TABLE: Insert at table beginning
    - AFTER_TARGET: Insert after reference row
    - BEFORE_TARGET: Insert before reference row

**DeleteMode (row deletion):**
    - TARGET: Delete starting at target row
    - AFTER_TARGET: Delete starting after target row
    - BEFORE_TARGET: Delete starting before target row

Value Sources
-------------

Many actions accept values from multiple sources:

- **Value objects**: Constant values (IntegerValue, StringValue, etc.)
- **ContextVariable**: Dynamic values from context
- **int/str literals**: Direct constant values for row indices

The action automatically determines the appropriate source type.

Modal Dialogs
-------------

Modal actions support workflow patterns:

- show_modal with transactional=True automatically begins a transaction
- User can commit (save) or rollback (cancel) changes in the modal
- Close modal without transaction for non-data-modifying dialogs

Examples
--------
Simple button click event::

    from daitum_ui.model_event import ModelEvent

    # Create event that switches views
    on_click_event = ModelEvent()
    on_click_event.add_switch_view_action(view_id="detail_view")

Opening a modal dialog::

    # Event to show edit modal with transaction
    edit_event = ModelEvent()
    edit_event.add_show_modal_action(
        modal_id="edit_form_modal",
        transactional=True  # Automatically begins transaction
    )

Inserting a new row::

    from daitum_ui._events import InsertMode

    # Event to insert row at end of table
    insert_event = ModelEvent()
    insert_event.add_insert_row_action(
        target_table=customers_table,
        insertion_point=InsertMode.END_OF_TABLE,
        new_index=new_row_context_var  # Store new row index
    )

Deleting a row::

    from daitum_ui._events import RowSelectionMode

    # Event to delete selected row
    delete_event = ModelEvent()
    delete_event.add_delete_row_action(
        target_table=products_table,
        row_count=1,
        select_mode=RowSelectionMode.INDEX,
        row=selected_row_context_var
    )

Duplicating a row::

    from daitum_ui._events import RowSelectionMode, InsertMode

    # Event to duplicate current row
    duplicate_event = ModelEvent()
    duplicate_event.add_duplicate_row_action(
        target_table=orders_table,
        row=current_row_context_var,
        select_mode=RowSelectionMode.INDEX,
        insertion_point=InsertMode.AFTER_TARGET
    )

Setting table field values::

    from daitum_ui.data import StringValue

    # Event to update customer name
    update_name_event = ModelEvent()
    update_name_event.add_set_table_value_action(
        value_source=StringValue("John Doe"),
        target_table=customers_table,
        target_field=customers_table.name_field,
        target_row=selected_row_context_var
    )

Setting values from context variables::

    # Copy value from input context variable to table
    save_input_event = ModelEvent()
    save_input_event.add_set_table_value_action(
        value_source=user_input_context_var,  # ContextVariable
        target_table=settings_table,
        target_field=settings_table.value_field,
        target_row=0
    )

Updating context variables::

    from daitum_ui.data import IntegerValue
    from daitum_ui._events import ValueType

    # Event to set selected row ID
    select_row_event = ModelEvent()
    select_row_event.add_set_context_action(
        variable=selected_row_id_context_var,
        value=IntegerValue(42),
        value_type=ValueType.CONSTANT
    )

Copying values between rows::

    # Event to copy fields from source to target row
    copy_event = ModelEvent()
    copy_event.add_copy_values_action(
        source=source_row_context_var,
        target=target_row_context_var,
        table=products_table,
        fields=[
            products_table.name_field,
            products_table.price_field,
            products_table.category_field
        ]
    )

Clearing field values::

    # Event to clear fields in a row
    clear_event = ModelEvent()
    clear_event.add_clear_values_action(
        source_row=current_row_context_var,
        table=orders_table,
        fields=[
            orders_table.notes_field,
            orders_table.discount_field
        ]
    )

Transaction management::

    # Event with explicit transaction control
    save_event = ModelEvent()
    save_event.add_begin_transaction()
    save_event.add_set_table_value_action(...)
    save_event.add_set_table_value_action(...)
    save_event.add_commit_transaction()

    # Event to cancel changes
    cancel_event = ModelEvent()
    cancel_event.add_rollback_transaction()
    cancel_event.add_close_modal_action()

Conditional execution::

    # Only execute action if condition is true
    conditional_event = ModelEvent()
    conditional_event.add_switch_view_action(
        view_id="admin_panel",
        condition=is_admin_context_var  # Only if user is admin
    )

Complex multi-step workflow::

    # Save form and navigate workflow
    save_and_navigate_event = ModelEvent()

    # 1. Begin transaction
    save_and_navigate_event.add_begin_transaction()

    # 2. Save form values
    save_and_navigate_event.add_set_table_value_action(
        value_source=name_input_context_var,
        target_table=customers_table,
        target_field=customers_table.name_field,
        target_row=current_customer_context_var
    )
    save_and_navigate_event.add_set_table_value_action(
        value_source=email_input_context_var,
        target_table=customers_table,
        target_field=customers_table.email_field,
        target_row=current_customer_context_var
    )

    # 3. Commit transaction
    save_and_navigate_event.add_commit_transaction()

    # 4. Close modal
    save_and_navigate_event.add_close_modal_action()

    # 5. Refresh data
    save_and_navigate_event.add_run_data_source_action("customer_list_source")

    # 6. Navigate to list view
    save_and_navigate_event.add_switch_view_action("customer_list_view")

Running reports::

    # Event to generate and download report
    report_event = ModelEvent()
    report_event.add_run_report_action(report_name="monthly_sales_report")

Refreshing data sources::

    # Event to reload data from server
    refresh_event = ModelEvent()
    refresh_event.add_run_data_source_action(data_source_name="product_inventory")

Editor events for UI interactions::

    from daitum_ui.model_event import EditorEvent
    from daitum_ui._events import EditorEventType

    # Button click event
    button_click = EditorEvent(
        type=EditorEventType.ON_CLICK,
        event=save_and_navigate_event
    )

    # Value change event
    value_change = EditorEvent(
        type=EditorEventType.ON_CHANGE,
        event=update_calculation_event
    )

Setting named values (Parameters/Calculations)::

    from daitum_ui.data import DecimalValue

    # Update parameter value
    update_param_event = ModelEvent()
    update_param_event.add_set_name_value_action(
        value_source=DecimalValue(0.15),
        name_value_target=tax_rate_parameter
    )

Row operations with key-based selection::

    from daitum_ui._events import RowSelectionMode

    # Delete row by unique key instead of index
    delete_by_key_event = ModelEvent()
    delete_by_key_event.add_delete_row_action(
        target_table=users_table,
        row_count=1,
        select_mode=RowSelectionMode.KEY,
        row=user_id_context_var,
        key_field=users_table.user_id_field
    )

Value matching for copy operations::

    # Copy values using field matching instead of index
    copy_by_value_event = ModelEvent()
    copy_by_value_event.add_copy_values_action(
        source=source_product_id_context_var,
        target=target_product_id_context_var,
        table=products_table,
        fields=[products_table.price_field],
        match_field=products_table.product_id_field  # Match by ID
    )
"""

from dataclasses import dataclass

from daitum_model import Calculation, Field, Parameter, Table

from daitum_ui._buildable import Buildable
from daitum_ui.context_variable import ContextVariable

from ._events import (
    ActionType,
    ClearValuesArgs,
    ConstantSource,
    ContextVariableSource,
    CopyValuesArgs,
    DeleteRowArgs,
    DuplicateRowArgs,
    EditorEventType,
    EventArgs,
    InsertRowArgs,
    ModelTransactionArgs,
    NamedValueTarget,
    OpenModalArgs,
    RowSelectionMode,
    RunDataSourceArgs,
    RunReportArgs,
    SetContextEventArgs,
    SetContextEventArgsValue,
    SetValueArgs,
    SetViewArgs,
    Source,
    TableValueTarget,
    Target,
    ValueType,
)
from .data import Value


class ModelEvent(Buildable):
    """
    Represents a model-level event composed of a sequence of actions.

    Attributes:
        actions (List[EventArgs]):
            A list of actions (event argument instances) to be executed as part of the model event.
    """

    def __init__(self):
        """
        Initializes an empty ModelEvent with no actions.
        """
        self.actions: list[EventArgs] = []

    def add_show_modal_action(
        self,
        modal_id: str,
        transactional: bool = True,
        condition: ContextVariable | None = None,
    ):
        """
        Adds an action to show a modal dialog.

        Args:
            modal_id (str): The modal object to display.
            transactional (bool): If True, begins a transaction after showing the modal.
                Defaults to True.
            condition (Optional[ContextVariable]): Context variable controlling conditional
                execution of the action. If provided, the action only executes when the
                context variable evaluates to true.
        """
        action = OpenModalArgs(modal_id)
        action.condition_context_variable = condition.id if condition else None
        self.actions.append(action)
        if transactional:
            self.add_begin_transaction()

    def add_close_modal_action(self, condition: ContextVariable | None = None):
        """
        Adds an action to close any currently open modal.

        Args:
            condition (Optional[ContextVariable]): Context variable controlling conditional
                execution of the action. If provided, the action only executes when the
                context variable evaluates to true.
        """
        action = OpenModalArgs(None)
        action.condition_context_variable = condition.id if condition else None

        self.actions.append(action)

    def add_run_report_action(self, report_name: str, condition: ContextVariable | None = None):
        """
        Adds an action to run a specified report.

        Args:
            report_name (str): Name of the report to execute.
            condition (Optional[ContextVariable]): Context variable controlling conditional
                execution of the action. If provided, the action only executes when the
                context variable evaluates to true.
        """
        action = RunReportArgs(report_name)
        action.condition_context_variable = condition.id if condition else None
        self.actions.append(action)

    def add_switch_view_action(self, view_id: str, condition: ContextVariable | None = None):
        """
        Adds an action to change the currently active view.

        Args:
            view_id (str): The view object to switch to.
            condition (Optional[ContextVariable]): Context variable controlling conditional
                execution of the action. If provided, the action only executes when the
                context variable evaluates to true.
        """
        action = SetViewArgs(view_id)
        action.condition_context_variable = condition.id if condition else None
        self.actions.append(action)

    def add_begin_transaction(self, condition: ContextVariable | None = None):
        """
        Adds an action to begin a transaction.

        Args:
            condition (Optional[ContextVariable]): Context variable controlling conditional
                execution of the action. If provided, the action only executes when the
                context variable evaluates to true.
        """
        action = ModelTransactionArgs(ActionType.BEGIN)
        action.condition_context_variable = condition.id if condition else None
        self.actions.append(action)

    def add_rollback_transaction(self, condition: ContextVariable | None = None):
        """
        Adds an action to roll back the current transaction.

        Args:
            condition (Optional[ContextVariable]): Context variable controlling conditional
                execution of the action. If provided, the action only executes when the
                context variable evaluates to true.
        """
        action = ModelTransactionArgs(ActionType.ROLLBACK)
        action.condition_context_variable = condition.id if condition else None
        self.actions.append(action)

    def add_commit_transaction(self, condition: ContextVariable | None = None):
        """
        Adds an action to commit the current transaction.

        Args:
            condition (Optional[ContextVariable]): Context variable controlling conditional
                execution of the action. If provided, the action only executes when the
                context variable evaluates to true.
        """
        action = ModelTransactionArgs(ActionType.COMMIT)
        action.condition_context_variable = condition.id if condition else None
        self.actions.append(action)

    def add_set_context_action(
        self,
        variable: ContextVariable,
        value: Value,
        value_type: ValueType = ValueType.CONSTANT,
        condition: ContextVariable | None = None,
    ):
        """
        Adds an action to set a context variable's value.

        Args:
            variable (ContextVariable): The context variable to update.
            value (Value): The value to assign to the context variable.
            value_type (ValueType): Indicates the source or interpretation of the value.
                Defaults to CONSTANT.
            condition (Optional[ContextVariable]): Context variable controlling conditional
                execution of the action. If provided, the action only executes when the
                context variable evaluates to true.
        """
        values = SetContextEventArgsValue(
            variable_id=variable.id, value=value.get_value(), value_type=value_type
        )
        action = SetContextEventArgs([values])
        action.condition_context_variable = condition.id if condition else None
        self.actions.append(action)

    def add_copy_values_action(
        self,
        source: ContextVariable,
        target: ContextVariable,
        table: Table,
        fields: list[Field],
        condition: ContextVariable | None = None,
    ) -> "CopyValuesArgs":
        """
        Adds an action to copy values from one row to another within the same table.

        Args:
            source (ContextVariable): Context variable identifying the source row.
            target (ContextVariable): Context variable identifying the target row.
            table (Table): The table containing both source and target rows.
            fields (list[Field]): List of fields whose values will be copied from source to target.
            condition (Optional[ContextVariable]): Context variable controlling conditional
                execution of the action. If provided, the action only executes when the
                context variable evaluates to true.

        Returns:
            CopyValuesArgs: The created action. Set ``action.match_field`` and
                ``action.match_by_value`` directly for value-based row matching.
        """
        action = CopyValuesArgs(source.id, target.id, table.id)
        action.field_ids = [field.id for field in fields] if fields else []
        action.condition_context_variable = condition.id if condition else None
        self.actions.append(action)
        return action

    def add_clear_values_action(
        self,
        source_row: ContextVariable,
        table: Table,
        fields: list[Field],
        match_field: Field | None = None,
        condition: ContextVariable | None = None,
    ):
        """
        Adds an action to clear field values in a specific row of a table.

        Args:
            source_row (ContextVariable): Context variable identifying the row whose values
                will be cleared.
            table (Table): The table containing the row to be modified.
            fields (list[Field]): List of fields whose values will be cleared in the specified row.
            match_field (Optional[Field]): Field used for value-based row identification instead
                of index-based identification. If provided, the row is identified by comparing
                this field's value.
            condition (Optional[ContextVariable]): Context variable controlling conditional
                execution of the action. If provided, the action only executes when the
                context variable evaluates to true.
        """
        action = ClearValuesArgs(source_row.id, table.id)
        action.field_ids = [field.id for field in fields] if fields else []
        if match_field:
            action.match_field = match_field.id
            action.match_by_value = True
        action.condition_context_variable = condition.id if condition else None
        self.actions.append(action)

    def add_duplicate_row_action(
        self,
        target_table: Table,
        row: ContextVariable,
        select_mode: RowSelectionMode,
        condition: ContextVariable | None = None,
    ) -> "DuplicateRowArgs":
        """
        Adds an action to duplicate a row in a table.

        Args:
            target_table (Table): Table in which to duplicate a row.
            row (ContextVariable): Context variable holding the source row index or key.
            select_mode (RowSelectionMode): Determines how the source row is selected
                (by index, by key, etc.).
            condition (Optional[ContextVariable]): Context variable controlling conditional
                execution of the action. If provided, the action only executes when the
                context variable evaluates to true.

        Returns:
            DuplicateRowArgs: The created action. Set ``action.key_field``,
                ``action.insertion_point``, ``action.new_index_context_variable_id``, and
                ``action.append_table_to_new_variable`` directly for further configuration.
        """
        action = DuplicateRowArgs(target_table.id, row.id, select_mode)
        action.condition_context_variable = condition.id if condition else None
        self.actions.append(action)
        return action

    def add_insert_row_action(
        self,
        target_table: Table,
        select_mode: RowSelectionMode = RowSelectionMode.INDEX,
        row: ContextVariable | None = None,
        condition: ContextVariable | None = None,
    ) -> "InsertRowArgs":
        """
        Adds an action to insert a new blank row into a table.

        Args:
            target_table (Table): Table to insert the new row into.
            select_mode (RowSelectionMode): Defines how the reference row is selected
                (by index, by key, etc.). Defaults to INDEX.
            row (Optional[ContextVariable]): Context variable indicating the reference point
                for insertion. Not required when insertion_point is END_OF_TABLE or START_OF_TABLE.
            condition (Optional[ContextVariable]): Context variable controlling conditional
                execution of the action. If provided, the action only executes when the
                context variable evaluates to true.

        Returns:
            InsertRowArgs: The created action. Set ``action.key_field``,
                ``action.insertion_point``, ``action.new_index_context_variable_id``, and
                ``action.append_table_to_new_variable`` directly for further configuration.
        """
        action = InsertRowArgs(target_table.id, select_mode)
        action.row_context_variable_id = row.id if row else None
        action.condition_context_variable = condition.id if condition else None
        self.actions.append(action)
        return action

    def add_delete_row_action(
        self,
        target_table: Table,
        row_count: int,
        select_mode: RowSelectionMode,
        row: ContextVariable | None = None,
        condition: ContextVariable | None = None,
    ) -> "DeleteRowArgs":
        """
        Adds an action to delete one or more rows from a table.

        Args:
            target_table (Table): Table from which rows will be deleted.
            row_count (int): Number of consecutive rows to delete.
            select_mode (RowSelectionMode): Defines how the starting row is selected for deletion
                (by index, by key, etc.).
            row (Optional[ContextVariable]): Context variable holding the row index or key
                identifying the deletion reference point.
            condition (Optional[ContextVariable]): Context variable controlling conditional
                execution of the action. If provided, the action only executes when the
                context variable evaluates to true.

        Returns:
            DeleteRowArgs: The created action. Set ``action.key_field`` and
                ``action.delete_point`` directly for further configuration.
        """
        action = DeleteRowArgs(target_table.id, select_mode)
        action.row_count = row_count
        action.row_context_variable_id = row.id if row else None
        action.condition_context_variable = condition.id if condition else None
        self.actions.append(action)
        return action

    def add_run_data_source_action(
        self, data_source_name: str, condition: ContextVariable | None = None
    ):
        """
        Adds an action to run or refresh a data source.

        Args:
            data_source_name (str): Name of the data source to execute or refresh.
            condition (Optional[ContextVariable]): Context variable controlling conditional
                execution of the action. If provided, the action only executes when the
                context variable evaluates to true.
        """
        action = RunDataSourceArgs(data_source_name)
        action.condition_context_variable = condition.id if condition else None
        self.actions.append(action)

    def add_set_table_value_action(
        self,
        value_source: Value | ContextVariable,
        target_table: Table,
        target_field: Field,
        target_row: int | ContextVariable,
        condition: ContextVariable | None = None,
    ):
        """
        Adds an action to set a value in a specific table field and row.

        Args:
            value_source (Value | ContextVariable): The source of the value to set. Can be
                either a constant Value or a ContextVariable whose value will be used.
            target_table (Table): The table containing the field to be updated.
            target_field (Field): The field in the target table that will receive the new value.
                Must be a field that exists in the target_table.
            target_row (int | ContextVariable): Identifies the row to update.
            condition (Optional[ContextVariable]): Context variable controlling conditional
                execution of the action. If provided, the action only executes when the
                context variable evaluates to true.

        Raises:
            ValueError: If target_field is not a field in target_table.
        """
        if isinstance(value_source, Value):
            source: Source = ConstantSource(value_source.get_value())
        else:
            source = ContextVariableSource(value_source.id)

        if target_field not in target_table.get_fields():
            raise ValueError(f"{target_field} is not in the table: {target_table}.")

        if isinstance(target_row, int):
            row_source: Source = ConstantSource(target_row)
        else:
            row_source = ContextVariableSource(target_row.id)

        target = TableValueTarget(row_source, target_table.id, target_field.id)

        action = SetValueArgs(source, target)
        action.condition_context_variable = condition.id if condition else None
        self.actions.append(action)

    def add_set_name_value_action(
        self,
        value_source: Value | ContextVariable,
        name_value_target: Parameter | Calculation,
        condition: ContextVariable | None = None,
    ):
        """
        Adds an action to set the value of a named value (Parameter or Calculation).

        Args:
            value_source (Value | ContextVariable): The source of the value to set. Can be
                either a constant Value or a ContextVariable whose value will be used.
            name_value_target (Parameter | Calculation): The named value (Parameter or
                Calculation) that will receive the new value.
            condition (Optional[ContextVariable]): Context variable controlling conditional
                execution of the action. If provided, the action only executes when the
                context variable evaluates to true.
        """
        if isinstance(value_source, Value):
            source: Source = ConstantSource(value_source.get_value())
        else:
            source = ContextVariableSource(value_source.id)

        target: Target = NamedValueTarget(name_value_target.id)

        action = SetValueArgs(source, target)
        action.condition_context_variable = condition.id if condition else None
        self.actions.append(action)


@dataclass
class EditorEvent(Buildable):
    """
    Represents an event triggered from the editor (e.g. user interaction),
    which encapsulates a model event.

    Attributes:
        type (EditorEventType):
            The type of editor event that was triggered (ON_CLICK, ON_CHANGE).

        event (ModelEvent):
            The model event containing the list of actions to be executed in response.
    """

    type: EditorEventType
    event: ModelEvent
