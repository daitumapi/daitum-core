Context Variable
================

.. automodule:: daitum_ui.context_variable
    :no-index:
    :members:
    :show-inheritance:

Examples
--------

Creating a context variable with a calculated default from a parameter:

.. code-block:: python

    from daitum_model import Parameter

    # User role parameter
    user_role_param = Parameter(...)

    # Is admin flag derived from parameter
    is_admin = builder.add_context_variable(
        id="is_admin_flag",
        type=CVType.BOOLEAN,
        default_value=user_role_param  # Calculated from parameter
    )

Creating array context variables:

.. code-block:: python

    # List of selected item IDs
    selected_items = builder.add_context_variable(
        id="selected_item_ids",
        type=CVType.INTEGER,
        is_array=True
    )

    # List of filter tags
    active_tags = builder.add_context_variable(
        id="active_filter_tags",
        type=CVType.STRING,
        is_array=True
    )

String context variables for state:

.. code-block:: python

    # Current view mode
    view_mode = builder.add_context_variable(
        id="current_view_mode",
        type=CVType.STRING,
        default_value="grid"  # Default to grid view
    )

    # Search query
    search_query = builder.add_context_variable(
        id="search_text",
        type=CVType.STRING,
        default_value=""  # Empty by default
    )

Decimal context variables for numeric calculations:

.. code-block:: python

    # Calculated total price
    total_price = builder.add_context_variable(
        id="cart_total",
        type=CVType.DECIMAL,
        default_value=0.0
    )

    # User-entered discount percentage
    discount_percentage = builder.add_context_variable(
        id="discount_pct",
        type=CVType.DECIMAL,
        default_value=10.0
    )

Boolean context variables for flags:

.. code-block:: python

    # Show/hide detail panel
    show_details = builder.add_context_variable(
        id="show_detail_panel",
        type=CVType.BOOLEAN,
        default_value=False
    )

    # Edit mode toggle
    is_editing = builder.add_context_variable(
        id="is_edit_mode",
        type=CVType.BOOLEAN,
        default_value=False
    )

Using a calculation as a calculated default:

.. code-block:: python

    from daitum_model import Calculation

    # Calculation that computes if user has premium access
    has_premium_calc = Calculation(...)

    # Context variable using calculated default
    show_premium_features = builder.add_context_variable(
        id="show_premium_ui",
        type=CVType.BOOLEAN,
        default_value=has_premium_calc
    )

Workflow state management:

.. code-block:: python

    # Current step in multi-step form (0-indexed)
    current_step = builder.add_context_variable(
        id="wizard_step",
        type=CVType.INTEGER,
        default_value=0
    )

    # Completed steps array
    completed_steps = builder.add_context_variable(
        id="completed_wizard_steps",
        type=CVType.INTEGER,
        is_array=True
    )
