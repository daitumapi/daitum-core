Modal
=====

.. automodule:: daitum_ui.modal
    :no-index:
    :members:
    :show-inheritance:

Examples
--------

A view-only modal with just a close button (no transactions):

.. code-block:: python

    builder = UiBuilder()
    info_view = builder.add_form_view(display_name="Information")

    info_modal = builder.add_modal(
        view=info_view,
        height="400px",
        width="600px",
        title="Information"
    )
    # Default close button is already configured

An edit modal with save and cancel buttons (transactional):

.. code-block:: python

    edit_form_view = builder.add_form_view(display_name="Edit Form")

    edit_modal = builder.add_modal(
        view=edit_form_view,
        height="500px",
        width="700px",
        title="Edit Customer"
    )

    # Add save button (commits changes)
    edit_modal.add_save_button()

    # Replace close with cancel button (discards changes)
    edit_modal.add_cancel_button()

A modal whose title is driven by a context variable:

.. code-block:: python

    customer_name_var = builder.add_context_variable(
        id="modal_title_name",
        type=CVType.STRING,
        default_value=""
    )

    customer_detail_view = builder.add_form_view(display_name="Customer Details")

    customer_modal = builder.add_modal(
        view=customer_detail_view,
        height="600px",
        width="800px",
        title=customer_name_var  # Title updates from context
    )
    customer_modal.add_save_button()
    customer_modal.add_cancel_button()

A modal with a reset button, allowing the form to be restored to its original values:

.. code-block:: python

    data_entry_view = builder.add_form_view(display_name="Data Entry")

    form_modal = builder.add_modal(
        view=data_entry_view,
        height="450px",
        width="650px",
        title="Data Entry"
    )
    form_modal.add_save_button()
    form_modal.add_cancel_button()
    form_modal.add_reset_button()  # Allows user to reset form

A modal with a delete button wired to a custom destructive event:

.. code-block:: python

    delete_event = ModelEvent()
    delete_event.add_begin_transaction()
    delete_event.add_delete_row_action(
        target_table=customers_table,
        row_count=1,
        select_mode=RowSelectionMode.INDEX,
        row=current_customer_context_var
    )
    delete_event.add_commit_transaction()
    delete_event.add_close_modal_action()

    delete_confirmation_view = builder.add_form_view(
        display_name="Delete Confirmation"
    )

    delete_modal = builder.add_modal(
        view=delete_confirmation_view,
        height="300px",
        width="500px",
        title="Confirm Delete"
    )
    delete_modal.add_delete_button(on_click=delete_event)
    delete_modal.add_cancel_button()

Customising button appearance with colours and icons:

.. code-block:: python

    custom_view = builder.add_form_view(display_name="Custom Form")

    styled_modal = builder.add_modal(
        view=custom_view,
        height="500px",
        width="700px",
        title="Custom Styling"
    )

    # Custom save button with icon and colours
    styled_modal.add_save_button(
        text_color="#ffffff",
        background_color="#4caf50",
        icon_source=Icon.CHECK,
        icon_color="#ffffff"
    )

    # Custom cancel button
    styled_modal.add_cancel_button(
        text_color="#f44336",
        background_color="#ffebee"
    )

Attaching a custom event to a button:

.. code-block:: python

    custom_save_event = ModelEvent()
    custom_save_event.add_commit_transaction()
    custom_save_event.add_run_data_source_action("refresh_list")
    custom_save_event.add_close_modal_action()
    custom_save_event.add_switch_view_action("list_view")

    form_view = builder.add_form_view(display_name="Form View")

    custom_modal = builder.add_modal(
        view=form_view,
        height="500px",
        width="700px",
        title="Custom Save"
    )
    custom_modal.add_save_button(on_click=custom_save_event)
    custom_modal.add_cancel_button()

Adding custom footer elements alongside the standard buttons:

.. code-block:: python

    from daitum_ui.elements import Text

    complex_form_view = builder.add_form_view(display_name="Complex Form")

    help_modal = builder.add_modal(
        view=complex_form_view,
        height="600px",
        width="800px",
        title="Complex Form"
    )
    help_modal.add_save_button()
    help_modal.add_cancel_button()

    # Add help text to footer
    help_text = Text(
        value="* Required fields",
        color="#666666"
    )
    help_modal.add_footer(help_text)

A full-featured edit modal using every button type:

.. code-block:: python

    comprehensive_edit_view = builder.add_form_view(
        display_name="Comprehensive Edit"
    )

    full_modal = builder.add_modal(
        view=comprehensive_edit_view,
        height="700px",
        width="900px",
        title="Edit Record"
    )

    # Primary action
    full_modal.add_save_button(
        background_color="#2196f3"
    )

    # Secondary actions
    full_modal.add_cancel_button()
    full_modal.add_reset_button()

    # Destructive action
    full_modal.add_delete_button(on_click=delete_event)

Opening a modal from an event (begins a transaction automatically):

.. code-block:: python

    from daitum_ui.model_event import ModelEvent
    from daitum_ui.elements import Button

    show_edit_modal_event = ModelEvent()
    show_edit_modal_event.add_show_modal_action(
        modal_id=edit_modal.id,
        transactional=True  # Begins transaction automatically
    )

    # Attach to button click
    edit_button = Button(
        text_value="Edit",
        on_click=show_edit_modal_event
    )

A confirmation dialog pattern with a relabelled save button:

.. code-block:: python

    confirmation_view = builder.add_form_view(
        display_name="Confirmation"
    )

    confirm_modal = builder.add_modal(
        view=confirmation_view,
        height="250px",
        width="450px",
        title="Confirm Action"
    )

    confirm_event = ModelEvent()
    confirm_event.add_commit_transaction()
    # ... add custom actions ...
    confirm_event.add_close_modal_action()

    confirm_modal.add_save_button(
        text_color="#ffffff",
        background_color="#f44336"
    )
    confirm_modal.save_button.text_value = "Confirm"  # Change button text

    confirm_modal.add_cancel_button()

Responsive modal sizing using viewport and percentage dimensions:

.. code-block:: python

    large_view = builder.add_table_view(table=large_table)
    quick_action_view = builder.add_form_view(display_name="Quick Action")

    # Modal with percentage-based dimensions
    responsive_modal = builder.add_modal(
        view=large_view,
        height="80vh",  # 80% of viewport height
        width="90%",    # 90% of viewport width
        title="Large Modal"
    )
    responsive_modal.add_close_button()

    # Small modal for quick actions
    small_modal = builder.add_modal(
        view=quick_action_view,
        height="200px",
        width="400px",
        title="Quick Action"
    )
    small_modal.add_save_button()
    small_modal.add_cancel_button()
