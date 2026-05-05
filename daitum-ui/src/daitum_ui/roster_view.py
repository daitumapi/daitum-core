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
Roster view components for the UI Generator framework.

This module provides the RosterView class, which enables displaying resource-based
scheduling and allocation data in a specialized tabular format. Roster views are
designed for scenarios where resources (employees, equipment, rooms, etc.) are
displayed as rows, with columns representing time periods, shifts, or allocation slots.

Key components:
    - Resource column: The first column identifying each resource (e.g., employee name)
    - Shift columns: Time-based or allocation columns (e.g., Monday, Tuesday, etc.)
    - Summary column: Optional aggregated metrics (e.g., total hours, utilization rate)

Classes:
    - RosterColumn: Configuration for individual columns within a roster view
    - RosterView: Complete roster view with resource and shift management

Example:
    >>> # Define the data source
    >>> shifts_table = Table("employee_shifts")
    >>>
    >>> # Create resource and summary columns
    >>> resource_col = RosterColumn(
    ...     table_field_reference=Field("employee_name", DataType.STRING),
    ...     minimum_width="200px"
    ... )
    >>> summary_col = RosterColumn(
    ...     table_field_reference=Field("total_hours", DataType.DECIMAL),
    ...     minimum_width="100px"
    ... )
    >>>
    >>> # Create and register the roster view
    >>> builder = UiBuilder()
    >>> roster_view = builder.add_roster_view(
    ...     source_table=shifts_table,
    ...     resource_column=resource_col,
    ...     summary_column=summary_col,
    ...     freeze_headers=True,
    ...     display_name="Weekly Schedule"
    ... )
    >>>
    >>> # Add shift columns for each day
    >>> monday_shift = roster_view.add_shift_column(
    ...     table_field_reference=Field("monday_hours", DataType.DECIMAL),
    ...     minimum_width="80px"
    ... )
    >>> tuesday_shift = roster_view.add_shift_column(
    ...     table_field_reference=Field("tuesday_hours", DataType.DECIMAL),
    ...     minimum_width="80px"
    ... )
"""

from daitum_model import Calculation, Field, Parameter, Table
from typeguard import typechecked

from daitum_ui._buildable import Buildable, json_type_info
from daitum_ui.base_view import BaseView
from daitum_ui.elements import Card, TemplateBindingKey
from daitum_ui.filter_component import FilterableView, FilterComponent
from daitum_ui.model_event import ModelEvent


@typechecked
class RosterColumn(Buildable):
    """
    Defines the configuration of a single column within a roster view.

    Attributes:
        table_field_reference:
            A `Field` object indicating which field in the source table
            provides the value for this column. If this is not supplied,
            `default_card_template_key` must be provided instead.
        default_card_template_key:
            The key referring to a card template in the parent `RosterView`
            used to render normal (non-header) cells for this column.
        header_card_template_key:
            Optional key referring to a card template to be used when
            rendering the column header.
        minimum_width:
            Optional CSS width hint specifying the minimum
            allowed width for the column.
        template_field_mappings:
            A mapping of template placeholder keys to model field IDs.
        model_event_mappings:
            A mapping of template placeholder keys to `ModelEvent` instances
            used to trigger actions when the UI interacts with the column.
    """

    def __init__(
        self,
        table_field_reference: Field | None = None,
        default_card_template_key: str | None = None,
        header_card_template_key: str | None = None,
        minimum_width: str | None = None,
    ):
        if table_field_reference is None and default_card_template_key is None:
            raise ValueError(
                f"{default_card_template_key} must be defined if {table_field_reference} "
                f"is not defined."
            )

        self.table_field_reference = table_field_reference.id if table_field_reference else None
        self.default_card_template_key = default_card_template_key
        self.header_card_template_key = header_card_template_key
        self.minimum_width = minimum_width

        self.template_field_mappings: dict[str, str] = {}
        self.model_event_mappings: dict[str, ModelEvent] = {}

    def add_template_field_mapping(
        self, key: TemplateBindingKey, value: Field | Calculation | Parameter
    ):
        """
        Associates a template placeholder key with a model field.

        Args:
            key:
                The placeholder key defined in the card template.
            value:
                Either a `Field`, `Calculation` or `Parameter` whose string will be
                substituted into the template at render time.
        """
        self.template_field_mappings[key.to_string()] = value.to_string()

    def add_model_event_mapping(self, key: TemplateBindingKey, event: ModelEvent):
        """
        Associates a template placeholder key with a `ModelEvent`.

        Args:
            key:
                The placeholder key in the template representing an
                interactive UI element.
            event:
                The `ModelEvent` that should be triggered when the UI
                element corresponding to this key is activated.
        """
        self.model_event_mappings[key.to_string()] = event


@typechecked
@json_type_info("roster")
class RosterView(BaseView, FilterableView):
    """
    Represents a roster-style tabular view where each resource (e.g., employee,
    machine, asset) is displayed as a row, and each roster column defines how
    its data is rendered.

    The view supports card templates, resource/shift/summary column definitions,
    and optional header-freezing behaviour.

    Attributes:
        source_table:
            The underlying data table (by table_id) providing the row data
            displayed in the roster.
        card_templates:
            A mapping of template keys to `Card` definitions used to render
            cell contents across all roster columns.
        resource_column:
            The `RosterColumn` defining the first column of the roster,
            typically representing the resource identifier or name.
        shift_columns:
            A list of shift-related columns that appear after the resource
            column. These typically represent daily or time-based shifts.
        summary_column:
            Optional `RosterColumn` providing aggregated values or computed
            metrics for each row.
        freeze_headers:
            Determines whether the roster's header row should remain fixed
            (frozen) while scrolling vertically.
    """

    def __init__(
        self,
        source_table: Table,
        display_name: str | None = None,
        hidden: bool = False,
    ):

        # Initialise BaseView fields
        BaseView.__init__(self, hidden)
        if display_name is not None:
            self._display_name = display_name
        FilterableView.__init__(self)

        self.source_table = source_table.id
        self.card_templates: dict[str, Card] = {}
        self.resource_column: RosterColumn | None = None
        self.shift_columns: list[RosterColumn] = []
        self.summary_column: RosterColumn | None = None
        self.freeze_headers: bool = False

    def set_resource_column(self, col: "RosterColumn") -> "RosterView":
        """Sets the resource column for this roster view."""
        self.resource_column = col
        return self

    def set_summary_column(self, col: "RosterColumn") -> "RosterView":
        """Sets the summary column for this roster view."""
        self.summary_column = col
        return self

    def set_freeze_headers(self, freeze_headers: bool) -> "RosterView":
        """Sets whether headers are frozen when scrolling."""
        self.freeze_headers = freeze_headers
        return self

    def set_use_filter(self, use_filter: "FilterComponent") -> "RosterView":
        """Attaches a filter component to this roster view."""
        self.use_filter = use_filter.filter_name
        self.show_filter = use_filter.filter_name
        return self

    def add_card_template(self, key: str, card: Card):
        """
        Registers a card template for use within the roster view.

        Card templates are referenced by their string keys within
        `RosterColumn` definitions to determine how individual cells
        are rendered.

        Args:
            key:
                Unique identifier for the card template.
            card:
                The `Card` object defining the template layout and content.
        """
        self.card_templates[key] = card

    def add_shift_column(
        self,
        table_field_reference: Field | None = None,
        default_card_template_key: str | None = None,
        header_card_template_key: str | None = None,
        minimum_width: str | None = None,
    ) -> RosterColumn:
        """
        Adds a new shift column to the roster view.

        Args:
            table_field_reference:
                The model `Field` providing the value for this shift column.
                Must be provided unless `default_card_template_key` is given.
            default_card_template_key:
                Template key used to render normal cells in this column.
            header_card_template_key:
                Optional template key used to render the column header.
            minimum_width:
                Optional width constraint for the column.

        Returns:
            RosterColumn:
                The created `RosterColumn` instance.
        """

        if default_card_template_key is not None:
            if default_card_template_key not in self.card_templates:
                raise ValueError(
                    f"Card template '{default_card_template_key}' not found in "
                    f"RosterView.card_templates."
                )

        if header_card_template_key is not None:
            if header_card_template_key not in self.card_templates:
                raise ValueError(
                    f"Card template '{header_card_template_key}' not found in "
                    f"RosterView.card_templates."
                )

        if table_field_reference is None and default_card_template_key is None:
            raise ValueError(
                f"{default_card_template_key} must be defined if "
                f"{table_field_reference} is not defined."
            )

        column = RosterColumn(
            table_field_reference,
            default_card_template_key,
            header_card_template_key,
            minimum_width,
        )
        self.shift_columns.append(column)
        return column
