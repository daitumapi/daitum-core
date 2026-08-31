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
    - `RosterAxis`: Whether a drop write identifies the destination row or
      column of the roster grid.
    - `RosterDropWrite`: A single write performed when a card is dropped —
      the axis it resolves, the identity field written, the field gating
      the write, and an optional edit override redirecting it to another
      table.
    - `RosterTaskDefinition`: Drag-and-drop behaviour for the cards in a
      shift column — whether cards are draggable, which rows may receive a
      drop, the writes performed on drop, and the requirement/capability
      matching used to gate valid drop targets.
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

from enum import Enum

from daitum_model import Calculation, Field, ObjectDataType, Parameter, Table
from typeguard import typechecked

from daitum_ui._buildable import Buildable, json_type_info
from daitum_ui._data import EditOverride
from daitum_ui.base_view import BaseView
from daitum_ui.elements import Card, TemplateBindingKey
from daitum_ui.filter_component import FilterableView, FilterComponent
from daitum_ui.model_event import ModelEvent


class RosterAxis(Enum):
    """
    Identifies which axis of the roster grid a drop write targets.

    Attributes:
        ROW:
            The write identifies the destination resource (row) — e.g. which
            staff member the dropped card is now assigned to.
        COLUMN:
            The write identifies the destination shift (column) — e.g. which
            day the dropped card is now assigned to.
    """

    ROW = "ROW"
    COLUMN = "COLUMN"


@typechecked
class RosterDropWrite(Buildable):
    """
    A single write performed when a card is dropped onto a target row.

    On drop, the roster records where the card landed by writing the target
    row's and/or target column's identities back to the model. Each
    `RosterDropWrite` describes one such write: the `axis` it resolves (row
    or column), the `identity_field` supplying the value written, and the
    `enabled_field` gating whether that write occurs. An optional
    `edit_override` redirects the write to a field on another table, used
    when the identity is displayed via a calculated value.

    Instances are created for you by
    `RosterTaskDefinition.add_drop_write(...)`; you do not normally
    construct them directly.

    Attributes:
        axis:
            Whether this write identifies the destination row (`ROW`) or the
            destination column (`COLUMN`).
        identity_field:
            Field ID whose value identifies the target row/column and is
            written on drop.
        enabled_field:
            Field ID of a per-row boolean gating whether this write is
            applied.
        edit_override:
            Optional redirect of the write to a field on another table, used
            when `identity_field` displays a calculated value.
    """

    def __init__(self, axis: RosterAxis, identity_field: Field, enabled_field: Field):
        """
        Args:
            axis:
                Whether the write targets the destination row or column.
            identity_field:
                Field whose value identifies the drop target and is written.
            enabled_field:
                Per-row boolean field gating whether the write occurs.
        """
        self.axis = axis
        self.identity_field = identity_field.id
        self.enabled_field = enabled_field.id
        self.edit_override: EditOverride | None = None


@typechecked
class RosterTaskDefinition(Buildable):
    """
    Drag-and-drop configuration for the cards rendered in a roster column.

    Attached to a `RosterColumn` via `RosterColumn.set_task_definition(...)`,
    this describes only how cards in that column behave when the user drags
    them — it does not affect rendering, data binding, or which fields are
    displayed.

    A card is dragged from one row onto another row of the same column. Drop
    behaviour is configured one of two ways:

    - **Swap fields** (`add_swap_field`): on drop, the values of the
      registered `swap_fields` are exchanged between the source and target
      rows. This is the simple path — usable when the roster is backed by a
      directly editable table and cards move within a single column. The
      column's `table_field_reference` is typically a calculation that
      recomputes from the swapped values; a data field that should also move
      must be added to `swap_fields` explicitly.
    - **Drop writes** (`add_drop_write`): on drop, each registered
      `drop_write` records where the card landed by writing the target row's
      and/or column's identity back to the model, optionally redirected to
      another table via an edit override. Use this when the swap path cannot
      apply — a roster over a derived projection, or a move that changes which
      column a card is in. Requires `drop_enabled_field` to gate which rows
      may receive a drop.

    The two paths are mutually exclusive on a single task definition.

    Attributes:
        enable_drag_and_drop_field:
            Field ID of a per-row boolean field on the source table that
            gates whether a given card is draggable.
        drop_enabled_field:
            Field ID of a per-row boolean field gating whether a given row
            may receive a drop. Only used by the drop-write path; `None` for
            swap-based task definitions.
        highlight_whole_column_on_drag:
            UI hint controlling drop-target highlighting. If True, every
            card in the column is shaded green/red up-front (so the user
            can see which rows are valid drops before dragging over them).
            If False, only the card currently hovered is highlighted.
        swap_fields:
            Complete list of field IDs whose values are swapped between the
            source and target rows when a drop occurs. Populated by
            `add_swap_field`; mutually exclusive with `drop_writes`.
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
        drop_writes:
            The writes performed when a card is dropped, in the order added.
            Populated by `add_drop_write`; mutually exclusive with
            `swap_fields`.
    """

    def __init__(
        self,
        enable_drag_and_drop_field: Field,
        highlight_whole_column_on_drag: bool,
        drop_enabled_field: Field | None = None,
    ):
        """
        Args:
            enable_drag_and_drop_field:
                Per-row boolean field gating whether each card is draggable.
            highlight_whole_column_on_drag:
                If True, highlight the whole destination column while dragging.
            drop_enabled_field:
                Per-row boolean field gating whether a row may receive a drop.
                Required for the drop-write path (`add_drop_write`); leave as
                `None` for the swap path (`add_swap_field`).
        """
        self.enable_drag_and_drop_field = enable_drag_and_drop_field.id
        self.drop_enabled_field = drop_enabled_field.id if drop_enabled_field is not None else None
        self.highlight_whole_column_on_drag: bool = highlight_whole_column_on_drag
        self.swap_fields: list[str] | None = None
        self.required_value_fields: list[str] | None = None
        self.capability_fields: list[str] | None = None
        self.drop_writes: list[RosterDropWrite] | None = None

    def add_swap_field(self, field: Field) -> "RosterTaskDefinition":
        """
        Register a field whose value is swapped between the source and
        target rows on drop.

        This is the simple drop path, usable when the roster is backed by a
        directly editable table and cards move within a single column. It is
        mutually exclusive with `add_drop_write`.

        Args:
            field:
                Field whose value moves with the card: on drop, the source
                row's value and the target row's value are exchanged.

        Returns:
            This `RosterTaskDefinition`, for fluent chaining.

        Raises:
            ValueError: If a drop write has already been registered via
                `add_drop_write`.
        """
        if self.drop_writes is not None:
            raise ValueError(
                "Cannot combine swap fields with drop writes on a single task definition; "
                "use add_swap_field or add_drop_write, not both."
            )
        if self.swap_fields is None:
            self.swap_fields = []
        self.swap_fields.append(field.id)
        return self

    def add_drop_write(  # noqa: PLR0913, PLR0917
        self,
        axis: RosterAxis,
        identity_field: Field,
        enabled_field: Field,
        target_reference_field: Field | None = None,
        target_field_id: Field | None = None,
        map_key_field: Field | None = None,
    ) -> "RosterTaskDefinition":
        """
        Register a write performed when a card is dropped onto a target row.

        The value written is the destination cell's identity, so
        `identity_field` must be an object reference. Optionally supply
        `target_reference_field` and `target_field_id` together to redirect
        the write to a field on another table (an edit override), used when
        the edited data lives on a table other than the one displayed.
        `target_field_id` must itself reference the same table that
        `identity_field` references — otherwise the write stores a value of a
        type the destination field cannot hold.

        Args:
            axis:
                Whether the write identifies the destination row or column.
                Each axis may be written at most once per task definition.
            identity_field:
                Object-reference field whose value identifies the drop target
                and is written.
            enabled_field:
                Per-row boolean field gating whether the write occurs.
            target_reference_field:
                Object-reference field in the displayed table pointing at the
                table to edit. Must be given together with `target_field_id`.
            target_field_id:
                Object-reference field in the referenced table where the value
                is written. Must belong to the table `target_reference_field`
                references, must itself reference the same table as
                `identity_field`, and must be given together with
                `target_reference_field`.
            map_key_field:
                For a map-type target field, the field holding the map key.

        Returns:
            This `RosterTaskDefinition`, for fluent chaining.

        Raises:
            ValueError: If swap fields have been registered via
                `add_swap_field`; if a drop write for `axis` already exists;
                if `identity_field` is not an object reference; if only one of
                `target_reference_field` and `target_field_id` is supplied;
                if `target_reference_field` is not an object reference; if
                `target_field_id` does not belong to the table
                `target_reference_field` references; or if `target_field_id`
                does not reference the same table as `identity_field`.
        """
        if self.swap_fields is not None:
            raise ValueError(
                "Cannot combine drop writes with swap fields on a single task definition; "
                "use add_swap_field or add_drop_write, not both."
            )
        if self.drop_writes and any(write.axis == axis for write in self.drop_writes):
            raise ValueError(
                f"A {axis.value} drop write is already defined; each axis may be written once."
            )

        identity_type = identity_field.to_data_type()
        if not isinstance(identity_type, ObjectDataType):
            raise ValueError(
                f"Drop write identity field '{identity_field.id}' must be an object reference "
                f"(got {identity_type})."
            )

        if (target_reference_field is None) != (target_field_id is None):
            raise ValueError(
                "target_reference_field and target_field_id must be supplied together."
            )

        write = RosterDropWrite(axis, identity_field, enabled_field)
        if target_reference_field is not None and target_field_id is not None:
            reference_type = target_reference_field.to_data_type()
            if not isinstance(reference_type, ObjectDataType):
                raise ValueError(
                    f"Drop write target_reference_field '{target_reference_field.id}' must be an "
                    f"object reference (got {reference_type})."
                )
            if target_field_id.table_id != reference_type.table_id:
                raise ValueError(
                    f"Drop write target_field_id '{target_field_id.id}' must belong to the table "
                    f"'{reference_type.table_id}' referenced by target_reference_field "
                    f"'{target_reference_field.id}'."
                )
            target_type = target_field_id.to_data_type()
            if (
                not isinstance(target_type, ObjectDataType)
                or target_type.table_id != identity_type.table_id
            ):
                raise ValueError(
                    f"Drop write edit override target_field_id '{target_field_id.id}' must "
                    f"reference the same table as identity field '{identity_field.id}' "
                    f"('{identity_type.table_id}'); got {target_type}."
                )
            write.edit_override = EditOverride(
                target_reference_field.id,
                target_field_id.id,
                map_key_field.id if map_key_field is not None else None,
            )
        if self.drop_writes is None:
            self.drop_writes = []
        self.drop_writes.append(write)
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
                `RosterTaskDefinition` describing draggability, which rows
                may receive a drop, the writes performed on drop, and
                requirement/capability matching for valid drop targets.

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
