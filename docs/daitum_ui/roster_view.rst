Roster View
===========

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

.. autoclass:: daitum_ui.roster_view.RosterView
    :no-index:
    :members:
    :show-inheritance:

.. autoclass:: daitum_ui.roster_view.RosterColumn
    :no-index:
    :members:
    :show-inheritance:
