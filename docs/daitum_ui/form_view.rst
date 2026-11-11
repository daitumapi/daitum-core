Form View
=========

Form view components for the Daitum UI framework.

A :class:`~daitum_ui.form_view.FormView` is a grid-based layout for displaying and editing the
data of a single table row (or model-level values). It is composed of **cells** — each a
:class:`~daitum_ui.form_view.FormCell` wrapping one :class:`~daitum_ui.elements.Element` together
with its grid placement (row, column, spans, and horizontal alignment).

Elements are first-class and defined in :mod:`daitum_ui.elements`; a form merely places them.
Add them either with the generic :meth:`~daitum_ui.form_view.FormView.add_form_element` (any
pre-built element, including containers such as :class:`~daitum_ui.elements.Card`) or with a
per-type ``add_*`` convenience method (``add_text``, ``add_text_input``, ``add_number_input``,
``add_drop_down``, ``add_date_time``, ``add_check_box``, ``add_slider``, …), which builds the
element, validates its bound data type, places it, and returns it for further configuration.

Example::

    builder = UiBuilder()
    filter_mode = MatchRowFilterMode()
    filter_mode.set_filter_row("selected_customer_row")
    form = builder.add_form_view(
        display_name="Customer Details",
        total_rows=6,
        table=customers_table,
        filter_mode=filter_mode,
    )
    form.set_columns(num_columns=2, width="250px")

    # Header label spanning both columns, placed with the generic adder
    header = Text("Customer Information", font_weight=FontWeight.BOLD)
    form.add_form_element(1, 1, header, column_span=2)

    # Text input bound to a field
    form.add_text("Name:", row=2, column=1)
    form.add_text_input(customers_table.name_field, row=2, column=2)

    # Number input with range validation
    form.add_text("Age:", row=3, column=1)
    age_input = form.add_number_input(customers_table.age_field, row=3, column=2)
    age_input.set_range_validation(min_value=IntegerValue(18), max_value=IntegerValue(120))

Examples
--------

Placing a composed container (such as a :class:`~daitum_ui.elements.Card`) via the generic
:meth:`~daitum_ui.form_view.FormView.add_form_element`:

.. code-block:: python

    card = Card(layout_style=LayoutStyle.LIST)
    card.add_element(Text("Summary"))
    form.add_form_element(4, 1, card, column_span=2)

.. autoclass:: daitum_ui.form_view.FormView
    :no-index:
    :members:
    :show-inheritance:

.. autoclass:: daitum_ui.form_view.FormCell
    :no-index:
    :members:
    :show-inheritance:
