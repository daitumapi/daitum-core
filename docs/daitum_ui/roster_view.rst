Roster View
===========

A roster view presents resource-by-shift scheduling data as a grid. Each row
in the source table is rendered as a resource (e.g. an employee, machine, or
room) and the columns are the shifts (e.g. days, time slots, or allocation
buckets) being rostered. Cell contents are rendered with shared `Card`
templates registered on the view.

A roster is composed of three parts:

* **Resource column** — the leftmost column identifying each row's resource.
* **Shift columns** — one column per slot being rostered, appearing after the
  resource column in the order they are added.
* **Summary column** — an optional rightmost column showing per-row
  aggregates (e.g. total hours).

Cards rendered in a shift column can optionally be made drag-and-droppable by
attaching a :class:`~daitum_ui.roster_view.RosterTaskDefinition` to the
column. Drags are always within a single column — dragging a card from one
row onto another row of the same column swaps the configured fields between
those two rows.

Basic setup
-----------

Create the view, set the resource and (optional) summary columns, and add
one shift column per slot being rostered:

.. code-block:: python

    roster_view = builder.add_roster_view(
        source_table=roster_table, display_name="Weekly Roster"
    )

    roster_view.set_resource_column(
        RosterColumn(table_field_reference=roster_table.get_field("employee"))
    )

    for shift in ("mon", "tue", "wed"):
        roster_view.add_shift_column(
            table_field_reference=roster_table.get_field(f"shift_{shift}"),
            minimum_width="120px",
        )

Card templates and per-column bindings
--------------------------------------

A single `Card` template is typically reused across every shift column.
Placeholders in the template (e.g. ``${[start]}``) are filled in per-column
by mapping each placeholder to that column's source field:

.. code-block:: python

    shift_card = Card()
    shift_card.add_element(Text("${[start]} - ${[end]}"))
    roster_view.add_card_template("shift", shift_card)

    for shift in ("mon", "tue", "wed"):
        column = roster_view.add_shift_column(
            default_card_template_key="shift", minimum_width="120px"
        )
        column.add_template_field_mapping(
            TemplateBindingKey("[start]"), roster_table.get_field(f"start_{shift}")
        )
        column.add_template_field_mapping(
            TemplateBindingKey("[end]"), roster_table.get_field(f"end_{shift}")
        )

Drag-and-drop
-------------

The helper below builds drag-and-drop configuration for one shift column of
a roster. Each shift has its own set of per-column fields (availability,
location, start/end times, capability lists), so the helper is parameterised
by ``shift`` and called once per shift column.

.. code-block:: python

    def build_shift_drag_and_drop(
        roster_table: Table, shift: str
    ) -> RosterTaskDefinition:
        """Drag-and-drop config for one shift column of a roster."""
        task_def = RosterTaskDefinition(
            enable_drag_and_drop_field=roster_table.get_field(f"available_{shift}"),
            highlight_whole_column_on_drag=True,
        )

        # Fields whose values are exchanged between the source and target
        # rows on drop. The column's table_field_reference is typically a
        # calculation that recomputes from these — include it here only if
        # it is a data field that should also move.
        for field_name in (
            f"location_{shift}",
            f"start_time_{shift}",
            f"end_time_{shift}",
        ):
            task_def.add_swap_field(roster_table.get_field(field_name))

        # Gate valid drop targets: a drop is only allowed when the target
        # row's <capability> array contains the dragged card's <required>
        # value, for each pair below.
        requirements = [
            (f"location_{shift}",   f"location_options_{shift}"),
            (f"shift_type_{shift}", f"shift_type_options_{shift}"),
        ]
        for required, capability in requirements:
            task_def.add_requirement(
                required_field=roster_table.get_field(required),
                capability_field=roster_table.get_field(capability),
            )

        return task_def

    # Attach to a shift column on the roster view:
    monday = roster_view.add_shift_column(
        table_field_reference=roster_table.get_field("monday_shift"),
        minimum_width="80px",
    )
    monday.set_task_definition(build_shift_drag_and_drop(roster_table, "monday"))

API Reference
-------------

.. autoclass:: daitum_ui.roster_view.RosterView
    :no-index:
    :members:
    :show-inheritance:

.. autoclass:: daitum_ui.roster_view.RosterColumn
    :no-index:
    :members:
    :show-inheritance:

.. autoclass:: daitum_ui.roster_view.RosterTaskDefinition
    :no-index:
    :members:
    :show-inheritance:
