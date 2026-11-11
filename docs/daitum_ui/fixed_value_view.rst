Fixed Value View
================

Fixed value view components for the UI Generator framework.

Provides the FixedValueView class for displaying data in a fixed grid layout. The
grid has a fixed number of rows and columns, and each cell displays either literal
text or a dynamic value from a Parameter or Calculation, positioned by row/column
index. Cells support styling and conditional formatting.

Examples
--------

.. code-block:: python

    # Define parameters
    max_users = Parameter("max_users", DataType.INTEGER, default_value=100)
    min_age = Parameter("min_age", DataType.INTEGER, default_value=18)
    system_name = Parameter("system_name", DataType.STRING, default_value="MyApp")

    # Create fixed value view
    builder = UiBuilder()
    config_view = builder.add_fixed_value_view(
        display_name="System Configuration",
        show_band_color=True,
        band_odd_row_background_color="#F0F0F0",
        band_even_row_background_color="#FFFFFF"
    )

    # Add column headers
    name_header = Cell("Setting Name", header_column=True)
    value_header = Cell("Value", header_column=True)
    config_view.add_column(name_header)
    config_view.add_column(value_header)

    # Add data rows
    # Row 0: System name
    config_view.add_cell(Cell("System Name"), row=0, col=0)
    config_view.add_cell(Cell(system_name), row=0, col=1)

    # Row 1: Max users
    config_view.add_cell(Cell("Maximum Users"), row=1, col=0)
    config_view.add_cell(Cell(max_users), row=1, col=1)

    # Row 2: Min age with conditional formatting
    config_view.add_cell(Cell("Minimum Age"), row=2, col=0)
    age_cell = Cell(min_age)
    # Highlight if age is below 21
    age_warning = Parameter("age_warning", DataType.BOOLEAN)
    warning_style = ColumnStyle(background_color="#FFEEEE")
    age_cell.add_conditional_formatting_rule(
        named_value=age_warning,
        override_styles=warning_style,
        stop_if_true=True
    )
    config_view.add_cell(age_cell, row=2, col=1)

.. autoclass:: daitum_ui.fixed_value_view.FixedValueView
    :members:
    :show-inheritance:

.. autoclass:: daitum_ui.fixed_value_view.Cell
    :members:
    :show-inheritance:
