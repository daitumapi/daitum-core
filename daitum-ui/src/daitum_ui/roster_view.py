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

A `RosterView` lays out resource-based scheduling data as a grid: resources
(employees, machines, rooms, ...) are rows and shifts (days, time slots, ...)
are columns. Each row is sourced from `source_table`, and cell contents are
rendered via `Card` templates registered on the view.

A roster is composed of:
    - A **resource column** identifying each row's resource (e.g. employee name).
    - One or more **shift columns** holding the per-slot values being rostered.
    - An optional **summary column** showing per-row aggregates
      (e.g. total hours).

Classes:
    - `RosterColumn`: Configuration of a single column within the roster.
    - `RosterTaskDefinition`: Drag-and-drop behaviour for the cards in a
      shift column — whether cards are draggable, which fields swap
      between rows on drop, and the requirement/capability matching used
      to gate valid drop targets.
    - `RosterView`: The view itself, owning the resource/shift/summary
      columns and the shared card templates.

Example:
    >>> shifts_table = Table("employee_shifts")
    >>>
    >>> builder = UiBuilder()
    >>> roster_view = builder.add_roster_view(
    ...     source_table=shifts_table,
    ...     display_name="Weekly Schedule",
    ... )
    >>> roster_view.set_freeze_headers(True)
    >>>
    >>> roster_view.set_resource_column(
    ...     RosterColumn(
    ...         table_field_reference=Field("employee_name", DataType.STRING),
    ...         minimum_width="200px",
    ...     )
    ... )
    >>> roster_view.set_summary_column(
    ...     RosterColumn(
    ...         table_field_reference=Field("total_hours", DataType.DECIMAL),
    ...         minimum_width="100px",
    ...     )
    ... )
    >>>
    >>> roster_view.add_shift_column(
    ...     table_field_reference=Field("monday_hours", DataType.DECIMAL),
    ...     minimum_width="80px",
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
class RosterTaskDefinition(Buildable):
    """
    Drag-and-drop configuration for the cards rendered in a roster column.

    Attached to a `RosterColumn` via `RosterColumn.set_task_definition(...)`,
    this describes only how cards in that column behave when the user drags
    them — it does not affect rendering, data binding, or which fields are
    displayed.

    Drags are always within a single column: a card is dragged from one row
    onto another row of the same column, and the drop swaps the values of
    the configured `swap_fields` between those two rows. The column's
    `table_field_reference` is typically a calculation that recomputes
    naturally from the swapped values; if it is a data field that should
    also move, add it to `swap_fields` explicitly.

    Attributes:
        enable_drag_and_drop_field:
            Field ID of a per-row boolean field on the source table that
            gates whether a given card is draggable.
        highlight_whole_column_on_drag:
            UI hint controlling drop-target highlighting. If True, every
            card in the column is shaded green/red up-front (so the user
            can see which rows are valid drops before dragging over them).
            If False, only the card currently hovered is highlighted.
        swap_fields:
            Complete list of field IDs whose values are swapped between
            the source and target rows when a drop occurs.
        required_value_fields:
            Field IDs on the dragged card carrying scalar requirement
            values. Paired positionally with `capability_fields` to gate
            which target rows are valid drop targets: a drop is only
            permitted when, for every index ``i``, the target row's
            `capability_fields[i]` (an array) contains the dragged card's
            `required_value_fields[i]` (a scalar of the matching type).
        capability_fields:
            Field IDs on the target row holding array-valued capabilities,
            aligned positionally with `required_value_fields`.
    """

    def __init__(self, enable_drag_and_drop_field: Field, highlight_whole_column_on_drag: bool):
        """
        Args:
            enable_drag_and_drop_field:
                Per-row boolean field gating whether each card is draggable.
            highlight_whole_column_on_drag:
                If True, highlight the whole destination column while dragging.
        """
        self.enable_drag_and_drop_field = enable_drag_and_drop_field.id
        self.highlight_whole_column_on_drag: bool = highlight_whole_column_on_drag
        self.swap_fields: list[str] | None = None
        self.required_value_fields: list[str] | None = None
        self.capability_fields: list[str] | None = None

    def add_swap_field(self, field: Field) -> "RosterTaskDefinition":
        """
        Register a field whose value is swapped between the source and
        target rows on drop.

        Args:
            field:
                Field whose value moves with the card: on drop, the source
                row's value and the target row's value are exchanged.
        """
        if self.swap_fields is None:
            self.swap_fields = []
        self.swap_fields.append(field.id)
        return self

    def add_requirement(
        self, required_field: Field, capability_field: Field
    ) -> "RosterTaskDefinition":
        """
        Add a (requirement, capability) pair gating valid drop targets.

        A drop is only permitted when the target row's `capability_field`
        (an array) contains the dragged card's `required_field` value (a
        scalar). The capability field's data type must therefore be the
        array form of the required field's data type.

        Args:
            required_field:
                Scalar field on the dragged card supplying the required
                value.
            capability_field:
                Array-valued field on the target row whose contents must
                include `required_field`'s value for the drop to be valid.

        Raises:
            ValueError: If `capability_field`'s data type is not the array
                form of `required_field`'s data type.
        """
        expected = required_field.to_data_type().to_array()
        if capability_field.to_data_type() != expected:
            raise ValueError(
                f"Capability field '{capability_field.id}' must be of type "
                f"{expected}; got {capability_field.to_data_type()}."
            )
        if self.required_value_fields is None:
            self.required_value_fields = []
        if self.capability_fields is None:
            self.capability_fields = []
        self.required_value_fields.append(required_field.id)
        self.capability_fields.append(capability_field.id)
        return self


@typechecked
class RosterColumn(Buildable):
    """
    Configuration for a single column within a `RosterView`.

    A column either binds directly to a source-table field (via
    `table_field_reference`) or renders its cells with a card template (via
    `default_card_template_key`); at least one of the two must be supplied.

    Attributes:
        table_field_reference:
            Field ID of the source-table field providing this column's
            value. Required unless `default_card_template_key` is set.
        default_card_template_key:
            Key of a card template registered on the parent `RosterView`
            used to render normal (non-header) cells for this column.
        header_card_template_key:
            Optional card-template key used to render the column header.
        minimum_width:
            Optional CSS width hint (e.g. ``"120px"``) setting the column's
            minimum width.
        template_field_mappings:
            Card-template placeholder keys (`TemplateBindingKey`) mapped to
            the model `Field`/`Calculation`/`Parameter` strings substituted
            in at render time.
        model_event_mappings:
            Card-template placeholder keys mapped to `ModelEvent` instances
            fired when the corresponding UI element is activated.
        task_definition:
            Optional `RosterTaskDefinition` configuring drag-and-drop
            behaviour for the cards rendered in this column. Has no effect
            on rendering or data binding.
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
        self.task_definition: RosterTaskDefinition | None = None

    def add_template_field_mapping(
        self, key: TemplateBindingKey, value: Field | Calculation | Parameter
    ) -> "RosterColumn":
        """
        Bind a card-template placeholder to a model value.

        Args:
            key:
                Placeholder key declared in the card template.
            value:
                `Field`, `Calculation`, or `Parameter` whose string form is
                substituted into the template at render time.

        Returns:
            This `RosterColumn`, for fluent chaining.
        """
        self.template_field_mappings[key.to_string()] = value.to_string()
        return self

    def add_model_event_mapping(self, key: TemplateBindingKey, event: ModelEvent) -> "RosterColumn":
        """
        Bind a card-template placeholder to a `ModelEvent`.

        Args:
            key:
                Placeholder key representing an interactive element in the
                card template.
            event:
                `ModelEvent` fired when that element is activated.

        Returns:
            This `RosterColumn`, for fluent chaining.
        """
        self.model_event_mappings[key.to_string()] = event
        return self

    def set_task_definition(self, task_definition: "RosterTaskDefinition") -> "RosterColumn":
        """
        Attach drag-and-drop configuration for cards in this column.

        Args:
            task_definition:
                `RosterTaskDefinition` describing draggability, which fields
                swap between rows on drop, and requirement/capability
                matching for valid drop targets.

        Returns:
            This `RosterColumn`, for fluent chaining.
        """
        self.task_definition = task_definition
        return self


@typechecked
@json_type_info("roster")
class RosterView(BaseView, FilterableView):
    """
    Resource-by-shift tabular view.

    Each row in `source_table` is rendered as a resource row; the columns
    are the resource column (leftmost identifier), the shift columns (one
    per slot being rostered), and an optional summary column.

    Attributes:
        source_table:
            Table ID of the source table whose rows back the roster.
        card_templates:
            Shared `Card` templates, keyed by the strings referenced from
            `RosterColumn.default_card_template_key` and
            `RosterColumn.header_card_template_key`.
        resource_column:
            Leftmost column identifying each row's resource. Required for
            the view to be valid.
        shift_columns:
            Ordered list of shift columns appearing after the resource
            column.
        summary_column:
            Optional rightmost column showing per-row aggregates.
        freeze_headers:
            If True, the header row stays fixed while the body scrolls
            vertically.
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
        """Set the resource (leftmost) column. Returns self for chaining."""
        self.resource_column = col
        return self

    def set_summary_column(self, col: "RosterColumn") -> "RosterView":
        """Set the optional summary (rightmost) column. Returns self for chaining."""
        self.summary_column = col
        return self

    def set_freeze_headers(self, freeze_headers: bool) -> "RosterView":
        """Set whether the header row stays fixed during vertical scrolling."""
        self.freeze_headers = freeze_headers
        return self

    def set_use_filter(self, use_filter: "FilterComponent") -> "RosterView":
        """
        Attach a `FilterComponent` to this view and display its UI.

        Sets both the bound filter (`use_filter`) and the displayed filter
        (`show_filter`) to `use_filter.filter_name`.
        """
        self.use_filter = use_filter.filter_name
        self.show_filter = use_filter.filter_name
        return self

    def add_card_template(self, key: str, card: Card):
        """
        Register a shared card template on the view.

        Card templates are looked up by `key` from
        `RosterColumn.default_card_template_key` and
        `RosterColumn.header_card_template_key`.

        Args:
            key:
                Unique identifier referenced from `RosterColumn` template
                keys.
            card:
                `Card` defining the template's layout and content.
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
        Append a shift column to the roster.

        At least one of `table_field_reference` and
        `default_card_template_key` must be supplied. Any card-template keys
        provided must already be registered via `add_card_template`.

        Args:
            table_field_reference:
                Source-table `Field` providing this column's value.
            default_card_template_key:
                Key of the card template used to render normal cells.
            header_card_template_key:
                Optional key of the card template used to render the header.
            minimum_width:
                Optional CSS minimum width (e.g. ``"80px"``).

        Returns:
            The newly created `RosterColumn`, already appended to
            `shift_columns`.

        Raises:
            ValueError: If a referenced card-template key is not registered,
                or if neither `table_field_reference` nor
                `default_card_template_key` is provided.
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
