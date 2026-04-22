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

from abc import ABC
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from typeguard import typechecked

from ._buildable import Buildable, json_type_info


@typechecked
class ValueType(Enum):
    """
    Enum representing the source type when setting a ContextVariable.

    Types include:
        CONSTANT: A fixed literal value.
        ACTIVE_ROW: The currently active row in the table.
        MODEL_VALUE: A value taken from a specific named value.
        FIELD_VALUE: A value taken from a specific field in a table.
        CONTEXT: A value obtained from another context variable.
        EDITOR_VALUE: A value provided by the user or editor interface.
    """

    CONSTANT = "CONSTANT"
    ACTIVE_ROW = "ACTIVE_ROW"
    MODEL_VALUE = "MODEL_VALUE"
    FIELD_VALUE = "FIELD_VALUE"
    CONTEXT = "CONTEXT"
    EDITOR_VALUE = "EDITOR_VALUE"


@typechecked
class ActionType(Enum):
    """
    Enum representing the types of transaction actions that can be performed on a model.

    Actions include:
        BEGIN: Start a new transaction.
        ROLLBACK: Cancel the current transaction, reverting changes.
        COMMIT: Finalize the current transaction, saving changes.
    """

    BEGIN = "BEGIN"
    ROLLBACK = "ROLLBACK"
    COMMIT = "COMMIT"


@typechecked
class RowSelectionMode(Enum):
    """
    Specifies how a row should be selected from a table.

    Options:
        INDEX: Selects a row based on its row ID.
        KEY: Selects a row based on its string key.
    """

    INDEX = "INDEX"
    KEY = "KEY"


@typechecked
class InsertMode(Enum):
    """
    Specifies where a new row should be inserted in a table.

    Options:
        START_OF_TABLE: Insert at the beginning of the table.
        END_OF_TABLE: Insert at the end of the table.
        AFTER_TARGET: Insert after a target row.
        BEFORE_TARGET: Insert before a target row.
    """

    START_OF_TABLE = "START_OF_TABLE"
    END_OF_TABLE = "END_OF_TABLE"
    AFTER_TARGET = "AFTER_TARGET"
    BEFORE_TARGET = "BEFORE_TARGET"


@typechecked
class DeleteMode(Enum):
    """
    Specifies the starting point for deleting rows from a table.

    Options:
        START_OF_TABLE: Begin deleting from the start of the table.
        END_OF_TABLE: Begin deleting from the end of the table.
        TARGET: Begin deleting from a specific row identified by context.
    """

    START_OF_TABLE = "START_OF_TABLE"
    END_OF_TABLE = "END_OF_TABLE"
    TARGET = "TARGET"


@typechecked
class EditorEventType(Enum):
    """
    Defines types of user-triggered editor events.

    Options:
        ON_CHANGE: Triggered when a value is changed.
        ON_CLICK: Triggered when a user clicks an interactive element.
    """

    ON_CHANGE = "ON_CHANGE"
    ON_CLICK = "ON_CLICK"


@typechecked
class Source(ABC, Buildable):
    """
    Abstract base class for all value sources.

    A source is a definition of where a value originates from during evaluation.
    Examples include constants or values from context variables.
    """

    pass


@typechecked
class Target(ABC, Buildable):
    """
    Abstract base class for all value targets.

    A target is a destination where a value should be written.
    Examples include specific fields in a table or named context variables.
    """

    pass


@json_type_info("CONSTANT")
@dataclass
@typechecked
class ConstantSource(Source):
    """
    A source that provides a constant, literal value.

    Attributes:
        value (Any):

            The static value to be used. This can be a number, string, boolean,
            list, or dictionary depending on the context of usage.
    """

    value: Any


@json_type_info("CONTEXT_VARIABLE")
@dataclass
@typechecked
class ContextVariableSource(Source):
    """
    A source that retrieves a value from a context variable.

    Attributes:
        context_variable_id (str):
            The identifier of the context variable from which to read the value.
    """

    context_variable_id: str


@json_type_info("TABLE_VALUE")
@dataclass
@typechecked
class TableValueTarget(Target):
    """
    A target that sets a value in a specific field of a row in a table.

    The target row is determined by a `Source`, and optionally by matching a specific
    field value for disambiguation.

    Attributes:
        row_source (Source):
            A `Source` that identifies the row (e.g., by index or key) where the value should
            be set.

        table_id (str):
            The ID of the table containing the row and field to update.

        field_id (str):
            The ID of the field within the table row to set the value on.

        match_field (Optional[str]):
            The field to compare when `match_by_value` is enabled.

        match_by_value (bool):
            If True, the row is identified by comparing the `match_field` value
            rather than using a positional or direct lookup from `row_source`.
    """

    row_source: Source
    table_id: str
    field_id: str
    match_field: str | None = None
    match_by_value: bool = False


@json_type_info("NAMED_VALUE")
@dataclass
@typechecked
class NamedValueTarget(Target):
    """
    A target that assigns a value to a named context variable.

    Attributes:
        named_value_id (str):
            The identifier of the named context variable to assign the value to.
    """

    named_value_id: str


@typechecked
@dataclass(kw_only=True)
class EventArgs(ABC, Buildable):
    """
    Base class for all event argument types used in the UI.

    Each event is associated with a `condition_context_variable`, which determines
    whether the event should be executed.

    This variable refers to the ID of a `ContextVariable` whose runtime value is used
    to evaluate the condition. Typically, this value is expected to be boolean (or
    convertible to a boolean) to control event triggering.

    Attributes:
        condition_context_variable (str):
            ID of the context variable used to determine whether the event should be triggered.
    """

    condition_context_variable: str | None = None


@json_type_info("RUN_REPORT")
@dataclass
@typechecked
class RunReportArgs(EventArgs):
    """
    Arguments for triggering the execution of a report.

    Attributes:
        report_name (str):
            The name of the report to run. Must match a report defined in the current model.
    """

    report_name: str


@json_type_info("RUN_DATA_SOURCE")
@dataclass
@typechecked
class RunDataSourceArgs(EventArgs):
    """
    Arguments for triggering the execution or refresh of a data source.

    Attributes:
        data_source_name (str):
            The name of the data source to run. This must correspond to a defined data source
            in the model.
    """

    data_source_name: str


@json_type_info("SET_VIEW")
@dataclass
@typechecked
class SetViewArgs(EventArgs):
    """
    Arguments for changing the active view in the UI.

    Attributes:
        view_id (str):
            The ID of the view to display. This will replace the currently active view.
    """

    view_id: str


@json_type_info("OPEN_MODAL")
@dataclass
@typechecked
class OpenModalArgs(EventArgs):
    """
    Arguments for opening a modal dialog in the UI.

    Attributes:
        modal_id (str):
            The identifier of the modal to open. This triggers the display of the specified modal
            window.
    """

    modal_id: str | None


@dataclass
@typechecked
class SetContextEventArgsValue(Buildable):
    """
    Represents a single value assignment to a context variable.

    Attributes:
        variable_id (str):
            The identifier of the context variable to set.
        value (Any):
            The value to assign to the context variable. The actual type may vary depending on the
            value_type.
        value_type (ValueType):
            The source type of the value, indicating how the value should be interpreted.
    """

    variable_id: str
    value: Any
    value_type: ValueType


@json_type_info("SET_CONTEXT")
@dataclass
@typechecked
class SetContextEventArgs(EventArgs):
    """
    Event arguments for setting one or more context variables.

    Attributes:
        values (List[SetContextEventArgsValue]): A list of value assignments to apply to context
        variables.
    """

    values: list[SetContextEventArgsValue]


@json_type_info("TRANSACTION")
@dataclass
@typechecked
class ModelTransactionArgs(EventArgs):
    """
    Arguments for controlling a model transaction event.

    Attributes:
        action_type (ActionType): The transaction action to perform.
    """

    action_type: ActionType


@json_type_info("DUPLICATE_ROW")
@dataclass
@typechecked
class DuplicateRowArgs(EventArgs):
    """
    Inserts a new row into the target table and copies values from a selected row into it.

    This supports union tables by using key-based matching. Each source data table should
    have a generated key consistent with the format produced by `append_table_to_new_variable`.

    Attributes:
        target_table_id (str):
            The target table to find the row to duplicate. This can be a data table,
            union table, or a non-grouped derived table.

            Selection uses similar logic to `TableLookup.getValueAt` to locate the underlying
            data table row for duplication.

        row_context_variable_id (str):
            The context variable holding the row number (index) in the target table to duplicate.

        select_mode (RowSelectionMode):
            Specifies how to interpret `row_context_variable_id` for selecting the row.
            Only the first matching row will be selected.

        limited_fields (bool, optional):
            If True, only a subset of fields will be copied to the new row, specified by
            `field_ids`. Defaults to False.

        field_ids (Dict[str, List[str]], optional):
            A mapping from table IDs to lists of field IDs. Used only if `limited_fields` is
            True. Specifies which fields to copy to the new row. Keys must correspond to tables
            that can be inserted into based on `target_table_id`.

        insertion_point (InsertMode, optional):
            Where in the underlying table the new row will be inserted.
            Defaults to `InsertMode.AFTER_TARGET`.

        new_index_context_variable_id (Optional[str], optional):
            If specified, the index of the newly inserted row will be stored in this context
            variable. This can be the same as or different from `row_context_variable_id`.

        append_table_to_new_variable (bool, optional):
            If True, when setting `new_index_context_variable_id`, the table ID will be appended
            to the row index in the format `{tableID}-{index}`. This helps construct a composite
            key to identify the new row, even if the original row was part of a union table.

        key_field (Optional[str], optional):
            If `select_mode` is key-based, this should specify the key field to match on.
    """

    target_table_id: str
    row_context_variable_id: str
    select_mode: RowSelectionMode
    limited_fields: bool = False
    field_ids: dict[str, list[str]] = field(default_factory=dict)
    insertion_point: InsertMode = InsertMode.AFTER_TARGET
    append_table_to_new_variable: bool = False
    key_field: str | None = None
    new_index_context_variable_id: str | None = None


@json_type_info("INSERT_ROW")
@dataclass
@typechecked
class InsertRowArgs(EventArgs):
    """
    Inserts a new row into the specified target table.

    This supports union tables via key-based matching. Each source data table involved in a union
    should have a generated key consistent with the format created when
    `append_table_to_new_variable` is enabled.

    Attributes:
        target_table_id (str):
            The ID of the target table into which the new row will be inserted.
            This may refer to a data table, union table, or non-grouped derived table.
            Selection logic is similar to `TableLookup.getValueAt`.

        row_context_variable_id (str):
            Context variable holding the row index or key value used as a reference point
            for insertion (e.g., insert after or before this row).

        select_mode (RowSelectionMode):
            Specifies how `row_context_variable_id` is interpreted for selecting the reference row.
            Only the first matching row is selected.

        key_field (Optional[str], optional):
            If `select_mode` is key-based, this defines the field used for key matching.

        insertion_point (InsertMode, optional):
            Specifies where to insert the new row in relation to the reference row.
            Defaults to `InsertMode.END_OF_TABLE`.

        new_index_context_variable_id (Optional[str], optional):
            If set, the index of the inserted row will be stored in this context variable.
            This can be the same as or different from `row_context_variable_id`.

        append_table_to_new_variable (bool, optional):
            If True, appends the table ID to the row index in the format `{tableID}-{index}`.
            Useful for constructing composite keys that identify the inserted row uniquely,
            especially when dealing with union tables.
    """

    target_table_id: str
    select_mode: RowSelectionMode
    row_context_variable_id: str | None = None
    key_field: str | None = None
    insertion_point: InsertMode = InsertMode.END_OF_TABLE
    new_index_context_variable_id: str | None = None
    append_table_to_new_variable: bool = False


@json_type_info("DELETE_ROW")
@dataclass
@typechecked
class DeleteRowArgs(EventArgs):
    """
    Deletes one or more rows from a target data table.

    Supports both index-based and key-based row matching to align with duplication workflows.
    The deletion can begin from a specific point in the table, such as the start, end,
    or a row identified via a context variable.

    Attributes:
        target_table_id (str):
            The ID of the data table from which rows will be deleted.
            This must be a concrete data table (not a union or derived table).

        select_mode (RowSelectionMode):
            Determines how to interpret the row specified by `row_context_variable_id`.
            Only the first matching row is considered.

        row_count (int, optional):
            The number of rows to delete. Defaults to 1.

        row_context_variable_id (Optional[str], optional):
            Optional. Refers to a context variable that provides the row index or key value
            to use when `delete_point` is set to `DeleteMode.TARGET`.

        key_field (Optional[str], optional):
            If `select_mode` is key-based, this specifies the field to use for key matching.

        delete_point (DeleteMode, optional):
            Indicates the point in the table where deletion should begin.
            Options include:

                - `START_OF_TABLE`: Delete from the top of the table.
                - `END_OF_TABLE`: Delete from the bottom of the table (default).
                - `TARGET`: Delete from the row specified by `row_context_variable_id`.
    """

    target_table_id: str
    select_mode: RowSelectionMode
    row_count: int = 1
    row_context_variable_id: str | None = None
    key_field: str | None = None
    delete_point: DeleteMode = DeleteMode.END_OF_TABLE


@json_type_info("CLEAR_VALUES")
@dataclass
@typechecked
class ClearValuesArgs(EventArgs):
    """
    Clears values from specific fields in a row of the given table.

    Rows can optionally be matched by comparing field values rather than by index.

    Attributes:
        match_field (str):
            The field ID used for value-based row matching.

        source_row_context_variable (str):
            Context variable holding the row index or key to use for identifying the row.

        table_id (str):
            ID of the table containing the row whose fields are to be cleared.

        match_by_value (bool):
            If True, the row is matched using the value of `match_field` instead of by index.

        field_ids (List[str]):
            List of field IDs to clear within the selected row.
    """

    source_row_context_variable: str
    table_id: str
    field_ids: list[str] = field(default_factory=list)
    match_field: str | None = None
    match_by_value: bool = False


@json_type_info("COPY_VALUES")
@dataclass
@typechecked
class CopyValuesArgs(EventArgs):
    """
    Copies values from a source row to a destination row within the same table.

    Supports value-based or index-based row matching, and partial field selection.

    Attributes:
        match_field (str):
            Field ID to use for row matching if `match_by_value` is True.

        source_row_context_variable (str):
            Context variable containing the index or key for the source row.

        destination_row_context_variable (str):
            Context variable containing the index or key for the destination row.

        table_id (str):
            ID of the table in which the operation is performed.

        field_ids (List[str]):
            List of field IDs to copy from the source row to the destination row.

        match_by_value (bool):
            If True, row selection is done by matching `match_field` values instead of by index.
    """

    source_row_context_variable: str
    destination_row_context_variable: str
    table_id: str
    match_field: str | None = None
    field_ids: list[str] = field(default_factory=list)
    match_by_value: bool = False


@json_type_info("SET_VALUE")
@dataclass
@typechecked
class SetValueArgs(EventArgs):
    """
    Sets a value on a target field or context variable from a specified source.

    Attributes:
        value_source (Source):
            Source of the value to assign. This may reference a constant, context variable,
            editor-provided input, or a field value.

        target (Target):
            The target destination for the value. Can be a field or a context variable.
    """

    value_source: Source
    target: Target
