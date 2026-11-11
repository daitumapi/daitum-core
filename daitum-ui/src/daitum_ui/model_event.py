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
Event system for defining user interactions and application behaviour.

A ModelEvent is an ordered sequence of actions executed in response to a user
interaction or other trigger; actions cover navigation, data manipulation, row
management, transactions, and external operations. Every action supports optional
conditional execution via the ``condition`` parameter, and data operations can be
grouped into atomic units with the transaction actions. EditorEvent connects an
editor interaction to a ModelEvent.

Example:
    >>> from daitum_ui.model_event import ModelEvent
    >>> on_click_event = ModelEvent()
    >>> on_click_event.add_switch_view_action(view_id="detail_view")

See the published documentation for further worked examples.
"""

from dataclasses import dataclass

from daitum_model import Baseline, Calculation, Field, Parameter, Table, TrackingGroup
from daitum_model.tracking import normalise_tracking_groups

from daitum_ui._buildable import Buildable
from daitum_ui.context_variable import ContextVariable

from ._events import (
    ActionType,
    CaptureBaselineArgs,
    ClearValuesArgs,
    ConstantSource,
    CopyValuesArgs,
    DeleteRowArgs,
    DuplicateRowArgs,
    EditorEventType,
    EventArgs,
    InsertRowArgs,
    ModelTransactionArgs,
    ModelVariableSource,
    NamedValueTarget,
    NavigateArgs,
    OpenModalArgs,
    RevertBaselineArgs,
    RowSelectionMode,
    RunDataSourceArgs,
    RunOptimisationArgs,
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
from ._link_destination import ModelEditorLinkDestination
from .data import Value


def _build_source(
    raw: Value | int | Field | Parameter | Calculation | ContextVariable,
) -> Source:
    """
    Builds the appropriate :class:`Source` from a raw argument.

    A ``Value`` (or bare ``int`` row index) becomes a :class:`ConstantSource`; a ``Field``,
    ``Parameter``, ``Calculation``, or ``ContextVariable`` becomes a :class:`ModelVariableSource`
    wrapping the corresponding :class:`ModelVariable`.
    """
    if isinstance(raw, Value):
        return ConstantSource(raw.get_value())

    if isinstance(raw, int):
        return ConstantSource(raw)

    from .elements import get_model_variable

    model_variable = get_model_variable(raw)
    if model_variable is None:
        raise TypeError(f"Cannot build a source from {raw!r}.")

    return ModelVariableSource(model_variable)


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

    def add_run_optimisation_action(self, condition: ContextVariable | None = None):
        """
        Adds an action to trigger an optimisation run.

        Args:
            condition (Optional[ContextVariable]): Context variable controlling conditional
                execution of the action. If provided, the action only executes when the
                context variable evaluates to true.
        """
        action = RunOptimisationArgs()
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

    def add_capture_baseline_action(
        self,
        baseline: Baseline | str,
        tracking_groups: list[str | TrackingGroup] | None = None,
        condition: ContextVariable | None = None,
    ):
        """
        Adds an action to capture a baseline.

        Args:
            baseline (Baseline | str): The baseline to capture, or its name.
            tracking_groups (Optional[List[str | TrackingGroup]]): Restrict the capture to a
                subset of the baseline's tracking groups. Omit to capture all of them.
            condition (Optional[ContextVariable]): Context variable controlling conditional
                execution of the action.
        """
        baseline_name = baseline.name if isinstance(baseline, Baseline) else baseline
        groups = normalise_tracking_groups(tracking_groups) if tracking_groups else None
        action = CaptureBaselineArgs(baseline=baseline_name, tracking_groups=groups)
        action.condition_context_variable = condition.id if condition else None
        self.actions.append(action)

    def add_revert_baseline_action(
        self,
        baseline: Baseline | str,
        tracking_groups: list[str | TrackingGroup] | None = None,
        condition: ContextVariable | None = None,
    ):
        """
        Adds an action to revert editable elements to a captured baseline.

        Args:
            baseline (Baseline | str): The baseline to revert to, or its name.
            tracking_groups (Optional[List[str | TrackingGroup]]): Restrict the revert to a
                subset of the baseline's tracking groups. Omit to revert all of them.
            condition (Optional[ContextVariable]): Context variable controlling conditional
                execution of the action.
        """
        baseline_name = baseline.name if isinstance(baseline, Baseline) else baseline
        groups = normalise_tracking_groups(tracking_groups) if tracking_groups else None
        action = RevertBaselineArgs(baseline=baseline_name, tracking_groups=groups)
        action.condition_context_variable = condition.id if condition else None
        self.actions.append(action)

    def add_set_table_value_action(
        self,
        value_source: Value | Field | Parameter | Calculation | ContextVariable,
        target_table: Table,
        target_field: Field,
        target_row: int | Field | Parameter | Calculation | ContextVariable,
        condition: ContextVariable | None = None,
    ):
        """
        Adds an action to set a value in a specific table field and row.

        Args:
            value_source (Value | Field | Parameter | Calculation | ContextVariable): The source
                of the value to set. A ``Value`` supplies a constant; a ``Field``, ``Parameter``,
                ``Calculation``, or ``ContextVariable`` supplies a value read from that model
                variable at runtime.
            target_table (Table): The table containing the field to be updated.
            target_field (Field): The field in the target table that will receive the new value.
                Must be a field that exists in the target_table.
            target_row (int | Field | Parameter | Calculation | ContextVariable): Identifies the
                row to update. An ``int`` is a constant row index; a model variable supplies the
                row index read at runtime.
            condition (Optional[ContextVariable]): Context variable controlling conditional
                execution of the action. If provided, the action only executes when the
                context variable evaluates to true.

        Raises:
            ValueError: If target_field is not a field in target_table.
        """
        source = _build_source(value_source)

        if target_field not in target_table.get_fields():
            raise ValueError(f"{target_field} is not in the table: {target_table}.")

        row_source = _build_source(target_row)

        target = TableValueTarget(row_source, target_table.id, target_field.id)

        action = SetValueArgs(source, target)
        action.condition_context_variable = condition.id if condition else None
        self.actions.append(action)

    def add_set_named_value_action(
        self,
        value_source: Value | Field | Parameter | Calculation | ContextVariable,
        named_value_target: Parameter | Calculation,
        condition: ContextVariable | None = None,
    ):
        """
        Adds an action to set the value of a named value (Parameter or Calculation).

        Args:
            value_source (Value | Field | Parameter | Calculation | ContextVariable): The source
                of the value to set. A ``Value`` supplies a constant; a ``Field``, ``Parameter``,
                ``Calculation``, or ``ContextVariable`` supplies a value read from that model
                variable at runtime.
            named_value_target (Parameter | Calculation): The named value (Parameter or
                Calculation) that will receive the new value.
            condition (Optional[ContextVariable]): Context variable controlling conditional
                execution of the action. If provided, the action only executes when the
                context variable evaluates to true.
        """
        source = _build_source(value_source)

        target: Target = NamedValueTarget(named_value_target.id)

        action = SetValueArgs(source, target)
        action.condition_context_variable = condition.id if condition else None
        self.actions.append(action)

    def add_model_editor_navigate_action(
        self,
        model_id: Field | Parameter | Calculation | ContextVariable,
        scenario_id: Field | Parameter | Calculation | ContextVariable | None = None,
        open_new_tab: bool = False,
        condition: ContextVariable | None = None,
    ):
        """
        Adds an action that navigates to the Daitum model editor.

        Both ``model_id`` and ``scenario_id`` are optional. When provided, they are
        resolved at runtime to identify the target model and scenario. Omitting
        them opens the editor without pre-selecting a model or scenario.

        Args:
            model_id (Field | Parameter | Calculation | ContextVariable):
                Value identifying the model to open. Must resolve to an integer.
            scenario_id (Field | Parameter | Calculation | ContextVariable | None):
                Value identifying the scenario to open within the selected model.
                Must resolve to an integer.
            open_new_tab (bool): If ``True``, the editor opens in a new browser tab.
                Defaults to ``False``.
            condition (Optional[ContextVariable]): Context variable controlling
                conditional execution of the action. If provided, the action only
                executes when the context variable evaluates to true.
        """
        model_editor_link = ModelEditorLinkDestination(model_id, scenario_id, open_new_tab)
        action = NavigateArgs(model_editor_link)
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
