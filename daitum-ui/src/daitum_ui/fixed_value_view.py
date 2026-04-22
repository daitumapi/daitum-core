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
Fixed value view components for the UI Generator framework.

This module provides the FixedValueView class, which enables displaying structured
data in a fixed grid layout with customizable cells. Fixed value views are ideal for
presenting parameters, calculations, and constant values in an organized tabular
format with rich styling and conditional formatting capabilities.

Fixed value views create grid-based layouts where each cell can display either static
text or dynamic values from parameters and calculations. The grid structure is defined
with a fixed number of rows and columns, with cells positioned precisely using
row/column indexing.

Classes:
    - Cell: Represents a single cell with content, styling, and formatting rules
    - FixedValueView: Container view managing the fixed grid layout and cells

Example:
    >>> # Define parameters
    >>> max_users = Parameter("max_users", DataType.INTEGER, default_value=100)
    >>> min_age = Parameter("min_age", DataType.INTEGER, default_value=18)
    >>> system_name = Parameter("system_name", DataType.STRING, default_value="MyApp")
    >>>
    >>> # Create fixed value view
    >>> builder = UiBuilder()
    >>> config_view = builder.add_fixed_value_view(
    ...     display_name="System Configuration",
    ...     show_band_color=True,
    ...     band_odd_row_background_color="#F0F0F0",
    ...     band_even_row_background_color="#FFFFFF"
    ... )
    >>>
    >>> # Add column headers
    >>> name_header = Cell("Setting Name", header_column=True)
    >>> value_header = Cell("Value", header_column=True)
    >>> config_view.add_column(name_header)
    >>> config_view.add_column(value_header)
    >>>
    >>> # Add data rows
    >>> # Row 0: System name
    >>> config_view.add_cell(Cell("System Name"), row=0, col=0)
    >>> config_view.add_cell(Cell(system_name), row=0, col=1)
    >>>
    >>> # Row 1: Max users
    >>> config_view.add_cell(Cell("Maximum Users"), row=1, col=0)
    >>> config_view.add_cell(Cell(max_users), row=1, col=1)
    >>>
    >>> # Row 2: Min age with conditional formatting
    >>> config_view.add_cell(Cell("Minimum Age"), row=2, col=0)
    >>> age_cell = Cell(min_age)
    >>> # Highlight if age is below 21
    >>> age_warning = Parameter("age_warning", DataType.BOOLEAN)
    >>> warning_style = ColumnStyle(background_color="#FFEEEE")
    >>> age_cell.add_conditional_formatting_rule(
    ...     named_value=age_warning,
    ...     override_styles=warning_style,
    ...     stop_if_true=True
    ... )
    >>> config_view.add_cell(age_cell, row=2, col=1)
"""

from daitum_model import Calculation, Parameter
from daitum_model.named_values import NamedValue
from typeguard import typechecked

from daitum_ui._buildable import Buildable, json_type_info
from daitum_ui.base_view import BaseView
from daitum_ui.elements import ElementStates
from daitum_ui.styles import (
    CellStyle,
    ColumnStyle,
    ConditionalFormattingRule,
    ConditionalFormattingType,
)


@typechecked
class Cell(Buildable):
    """
    Represents a single cell within a table or grid layout.

    Attributes:
        cell_style (Optional[CellStyle]):
            Style configuration controlling the base visual appearance of the cell.
        header_column (bool):
            Whether this cell belongs to a header column. Header cells may be
            treated differently by the UI renderer.
        read_only (bool):
            Indicates whether the cell is editable by the end user.
        conditional_formatting_rules (List[ConditionalFormattingRule]):
            A list of rules that dynamically override the cell's appearance
            depending on data conditions.
        default_definition_id (Optional[str]):
            The named value ID of the default value (if provided).
        display_string (Optional[str]):
            A literal string to display when the cell contains textual content.
            For dynamic cells (Parameter/Calculation), this is typically empty.
        definition_id (Optional[str]):
            The named value ID associated with the Parameter or Calculation
            driving the cell's value. `None` when the cell contains a literal string.
    """

    def __init__(
        self,
        value: Parameter | Calculation | str,
        cell_style: CellStyle | None = None,
        header_column: bool = False,
        default_value: Parameter | Calculation | None = None,
        read_only: bool = False,
    ):
        """
        Initializes a Cell instance, which can display either a literal string
        or a dynamic value referenced by a Parameter or Calculation.

        Args:
            value (Parameter | Calculation | str):
                The content of the cell. A string is displayed directly.
                A Parameter or Calculation is stored as a reference via its
                `named_value_id`.
            cell_style (Optional[CellStyle]):
                Base visual styling for the cell.
            header_column (bool):
                Indicates whether this cell belongs to a header column. Default to False.
            default_value (Optional[Parameter | Calculation]):
                Optional default value used when no explicit value is provided.
                Stored by reference via `default_definition_id`. Defaults to None.
            read_only (bool):
                Whether the cell can be edited by the end user. Defaults to False.

        Raises:
            TypeError:
                If `value` is not a string, Parameter, or Calculation.
        """
        self.cell_style = cell_style
        self.header_column = header_column
        self.read_only = read_only
        self.conditional_formatting_rules: list[ConditionalFormattingRule] = []

        self.default_definition_id = default_value.id if default_value else None
        if isinstance(value, str):
            self.display_string: str | None = value
            self.definition_id = None
        elif isinstance(value, Parameter | Calculation):
            self.display_string = None
            self.definition_id = value.id
        else:
            raise TypeError(f"Invalid value type for Cell: {type(value)}")

        self._value = value

    def add_conditional_formatting_rule(
        self,
        named_value: Parameter | Calculation,
        override_styles: ColumnStyle,
        element_states: ElementStates | None = None,
        stop_if_true: bool = False,
        formatting_type: ConditionalFormattingType = ConditionalFormattingType.BOOLEAN,
    ) -> None:
        """
        Adds a conditional formatting rule to the cell.

        The rule describes how the cell's appearance should change when the condition
        defined by `condition_column` evaluates to true.

        Args:
            named_value:
                The data column whose value will be evaluated to determine whether
                the formatting rule should be applied. Either a Parameter or a Calculation.
            override_styles:
                The ColumnStyle instance specifying visual overrides when the rule triggers.
            element_states (ElementStates | None):
                The element state to apply if the condition is met.
            stop_if_true:
                If True, further conditional formatting rules will not be evaluated
                after this rule matches. Defaults to False.
            formatting_type:
                Indicates how the condition should be interpreted (e.g., Boolean, Numeric).
                Defaults to ConditionalFormattingType.BOOLEAN.
        """
        rule = ConditionalFormattingRule(
            named_value.id,
            override_styles,
            element_states,
            stop_if_true,
            formatting_type,
        )
        self.conditional_formatting_rules.append(rule)


@typechecked
@json_type_info("fixed layout")
class FixedValueView(BaseView):
    """
    A view representing a layout with a fixed number of rows and columns.

    Attributes:
        total_rows:
            Total number of rows. Rows start at index 0 (e.g., if the last added
            row index is 3, total_rows = 4).
        columns:
            List of column header Cell objects.
        cells:
            Nested mapping: {row_index -> {col_index -> Cell}}.
        show_dropdowns_below:
            Indicates whether table dropdowns should always be shown below the editing cell.
        show_band_color:
            Whether banded row colouring is enabled.
        band_odd_row_background_color:
            Background colour for odd-numbered rows (if show_band_color is True). Default to #F7F7F7
        band_even_row_background_color:
            Background colour for even-numbered rows (if show_band_color is True). Default to
            #FFFFFF
    """

    def __init__(
        self,
        display_name: str | None = None,
        hidden: bool = False,
        show_dropdowns_below: bool = True,
        show_band_color: bool = True,
    ):
        # Initialise BaseView fields
        super().__init__(hidden)
        if display_name is not None:
            self._display_name = display_name

        self.total_rows: int = 0
        self.columns: list[Cell] = []
        self.cells: dict[int, dict[int, Cell]] = {}

        self.show_dropdowns_below = show_dropdowns_below
        self.show_band_color = show_band_color

        self.band_odd_row_background_color: str = "#F7F7F7"
        self.band_even_row_background_color: str = "#FFFFFF"

    def set_band_colors(
        self,
        odd_row_background_color: str = "#F7F7F7",
        even_row_background_color: str = "#FFFFFF",
    ) -> "FixedValueView":
        """
        Sets the background colours for alternating row banding.

        Args:
            odd_row_background_color: Background colour for odd-numbered rows.
            even_row_background_color: Background colour for even-numbered rows.
        """
        self.band_odd_row_background_color = odd_row_background_color
        self.band_even_row_background_color = even_row_background_color
        return self

    def add_column(self, column: Cell) -> None:
        """
        Adds a column header cell to the view.

        Args:
            column:
                A Cell instance representing the column header to append.

        Raises:
            ValueError:
                If the provided cell is not marked as a header column.
        """
        if not column.header_column:
            column.header_column = True

        self.columns.append(column)

    def add_cell(self, cell: Cell, row: int, col: int) -> None:
        """
        Inserts a cell into the layout at the specified row and column.

        This method ensures the internal cell structure remains consistent:
            - Automatically initializes the row dictionary if it does not exist.
            - Ensures the column index is valid relative to the defined header columns.
            - Automatically updates `total_rows` when adding cells beyond the current range.

        Args:
            cell:
                The Cell instance to place into the layout.
            row:
                The zero-based row index where the cell should be inserted.
            col:
                The zero-based column index where the cell should be inserted.

        Raises:
            IndexError:
                If the provided column index is outside the range of the defined columns.
            ValueError:
                If row or column indices are negative.
        """

        # Basic sanity checks
        if row < 0 or col < 0:
            raise ValueError("Row and column indices must be non-negative integers.")

        # Column bounds check
        if col >= len(self.columns):
            raise IndexError(f"Column index {col} is out of range. ")

        if row not in self.cells:
            self.cells[row] = {}

        if cell.definition_id:
            cell = self._validation_value(cell)

        self.cells[row][col] = cell

        self.total_rows = max(self.total_rows, row + 1)

    def _validation_value(self, cell: Cell) -> Cell:
        from daitum_ui._validation import _add_validation_formatting

        if not isinstance(cell._value, NamedValue):
            raise ValueError("Invalid cell value type.")

        validation_values_list = cell._value.get_validation_values()
        combined_message_value = cell._value.get_combined_message_value()

        if (
            validation_values_list
            and isinstance(validation_values_list, list)
            and combined_message_value
        ):
            for validation_value in validation_values_list:
                cell = _add_validation_formatting(cell, validation_value, combined_message_value.id)

        return cell
