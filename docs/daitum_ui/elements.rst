Elements
========

.. automodule:: daitum_ui.elements
    :no-index:
    :members:
    :show-inheritance:

Examples
--------

An interactive button bound to an event:

.. code-block:: python

    save_button = Button(
        text_value="Save",
        background_color="#007bff",
        on_click=save_event
    )

A checkbox with conditional state management:

.. code-block:: python

    agree_checkbox = Checkbox(data_source=agreement_field)
    agree_checkbox.add_conditional_required(True)
    agree_checkbox.add_conditional_disabled(is_locked_field)

A card container holding labelled fields:

.. code-block:: python

    user_card = Card(
        layout_style=LayoutStyle.GRID,
        row_spacing=RowSpacing.RELAXED,
        border_radius="8px"
    )
    user_card.add_element(Text(value="Name:"))
    user_card.add_element(Text(value=user_table.name_field))

A checkbox that triggers events instead of writing its bound value:

.. code-block:: python

    notify_checkbox = Checkbox(data_source=notification_field)
    notify_checkbox.set_on_event(enable_notifications_event)
    notify_checkbox.set_off_event(disable_notifications_event)

A list element rendering every row of a table through a card template.
``TemplateBindingKey`` declares a placeholder inside the template, and
``add_template_field_mapping`` connects each placeholder to a real field:

.. code-block:: python

    name_key = TemplateBindingKey("name")
    role_key = TemplateBindingKey("role")

    template_card = Card(layout_style=LayoutStyle.LIST)
    template_card.add_element(Text(value=name_key, font_weight=FontWeight.BOLD))
    template_card.add_element(Text(value=role_key))

    employee_list = ListElement(
        data_source=employees_table,
        template=template_card,
        layout_direction=LayoutDirection.COLUMN,
    )
    employee_list.add_template_field_mapping(name_key, name_field)
    employee_list.add_template_field_mapping(role_key, role_field)

A list element with a summarise overflow:

.. code-block:: python

    overflow = OverflowElement()
    overflow.add_element(Text(value="More items..."))

    employee_list = ListElement(
        data_source=employees_table,
        template=template_card,
        overflow_strategy=OverflowStrategy.SUMMARISE,
        overflow_element=overflow,  # Required when strategy is SUMMARISE
    )
