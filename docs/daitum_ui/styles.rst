Styles
======

.. automodule:: daitum_ui.styles
    :no-index:
    :members:
    :show-inheritance:

Examples
--------

Creating cell styles with formatting:

.. code-block:: python

    from daitum_ui.styles import CellStyle

    # Currency cell with custom formatting
    price_cell_style = CellStyle(
        display_format="${value}",
        font_color="#2e7d32",
        horizontal_alignment=HorizontalAlignment.RIGHT,
        can_filter=True
    )

    # Date cell with formatting
    date_cell_style = CellStyle(
        display_format="yyyy-MM-dd",
        horizontal_alignment=HorizontalAlignment.CENTER
    )

Creating column styles with editors:

.. code-block:: python

    from daitum_ui.styles import ColumnStyle, PercentageEditor, MonthEditor

    # Percentage column with specialised editor
    completion_column = ColumnStyle(
        editor=PercentageEditor(),
        display_format="{value}%",
        frozen=False,
        can_filter=True
    )

    # Month column with month picker
    month_column = ColumnStyle(
        editor=MonthEditor(),
        frozen=True
    )

Using icon editors:

.. code-block:: python

    from daitum_ui.styles import IconCheckboxEditor, IconConfig
    from daitum_ui.icons import Icon

    # Checkbox column with custom icons
    status_column = ColumnStyle(
        editor=IconCheckboxEditor(
            on_icon=IconConfig(source=Icon.CHECK_CIRCLE, color="#4caf50"),
            off_icon=IconConfig(source=Icon.CANCEL, color="#f44336")
        )
    )

Conditional formatting:

.. code-block:: python

    from daitum_ui.styles import (
        ConditionalFormattingRule,
        ConditionalFormattingType,
        ColumnStyle
    )

    # Highlight overdue items (date before today)
    overdue_rule = ConditionalFormattingRule(
        condition_column="due_date",
        override_styles=ColumnStyle(
            background_color="#ffebee",
            font_color="#c62828"
        ),
        type=ConditionalFormattingType.BEFORE_TODAY,
        stop_if_true=True
    )

    # Highlight completed items (boolean condition)
    completed_rule = ConditionalFormattingRule(
        condition_column="is_completed",
        override_styles=ColumnStyle(
            background_color="#e8f5e9",
            strikethrough=True
        ),
        type=ConditionalFormattingType.BOOLEAN,
        stop_if_true=False
    )

Creating headers with custom styles:

.. code-block:: python

    # Column with distinct header style
    column_with_header = ColumnStyle(
        font_size=12,
        font_color="#333333",
        header_style=CellStyle(
            font_size=14,
            font_weight="bold",
            background_color="#1976d2",
            font_color="#ffffff",
            horizontal_alignment=HorizontalAlignment.CENTER
        )
    )

Frozen columns:

.. code-block:: python

    # Frozen ID column that stays visible during scrolling
    id_column = ColumnStyle(
        frozen=True,
        font_weight="bold",
        width=80,
        can_filter=False
    )

Read-only column styling:

.. code-block:: python

    # Column with distinct read-only appearance
    calculated_column = ColumnStyle(
        font_color="#666666",
        read_only_style=CellStyle(
            background_color="#fafafa",
            italic=True
        )
    )

Title styling:

.. code-block:: python

    from daitum_ui.styles import Title, Position

    # Title above content
    view_title = Title(
        value="Sales Dashboard",
        style=BaseStyle(
            font_size=24,
            font_weight="bold",
            font_color="#1a237e"
        ),
        position=Position.ABOVE_CONTENT
    )

Border styling:

.. code-block:: python

    # Cell with custom borders
    bordered_cell = CellStyle(
        border_top="2px solid #e0e0e0",
        border_bottom="2px solid #e0e0e0",
        border_left="1px solid #f5f5f5",
        border_right="1px solid #f5f5f5"
    )
