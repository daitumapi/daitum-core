Model Event
===========

.. automodule:: daitum_ui.model_event
    :no-index:
    :members:
    :show-inheritance:

Examples
--------

Opening a modal dialog (``transactional=True`` automatically begins a transaction):

.. code-block:: python

    edit_event = ModelEvent()
    edit_event.add_show_modal_action(
        modal_id="edit_form_modal",
        transactional=True,  # Automatically begins transaction
    )

Inserting a new row:

.. code-block:: python

    from daitum_ui._events import InsertMode

    insert_event = ModelEvent()
    insert_event.add_insert_row_action(
        target_table=customers_table,
        insertion_point=InsertMode.END_OF_TABLE,
        new_index=new_row_context_var,  # Store new row index
    )

Deleting a row:

.. code-block:: python

    from daitum_ui._events import RowSelectionMode

    delete_event = ModelEvent()
    delete_event.add_delete_row_action(
        target_table=products_table,
        row_count=1,
        select_mode=RowSelectionMode.INDEX,
        row=selected_row_context_var,
    )

Duplicating a row:

.. code-block:: python

    from daitum_ui._events import RowSelectionMode, InsertMode

    duplicate_event = ModelEvent()
    duplicate_event.add_duplicate_row_action(
        target_table=orders_table,
        row=current_row_context_var,
        select_mode=RowSelectionMode.INDEX,
        insertion_point=InsertMode.AFTER_TARGET,
    )

Setting table field values:

.. code-block:: python

    from daitum_ui.data import StringValue

    update_name_event = ModelEvent()
    update_name_event.add_set_table_value_action(
        value_source=StringValue("John Doe"),
        target_table=customers_table,
        target_field=customers_table.name_field,
        target_row=selected_row_context_var,
    )

Setting values from context variables:

.. code-block:: python

    save_input_event = ModelEvent()
    save_input_event.add_set_table_value_action(
        value_source=user_input_context_var,  # ContextVariable
        target_table=settings_table,
        target_field=settings_table.value_field,
        target_row=0,
    )

Updating context variables:

.. code-block:: python

    from daitum_ui.data import IntegerValue
    from daitum_ui._events import ValueType

    select_row_event = ModelEvent()
    select_row_event.add_set_context_action(
        variable=selected_row_id_context_var,
        value=IntegerValue(42),
        value_type=ValueType.CONSTANT,
    )

Copying values between rows:

.. code-block:: python

    copy_event = ModelEvent()
    copy_event.add_copy_values_action(
        source=source_row_context_var,
        target=target_row_context_var,
        table=products_table,
        fields=[
            products_table.name_field,
            products_table.price_field,
            products_table.category_field,
        ],
    )

Clearing field values:

.. code-block:: python

    clear_event = ModelEvent()
    clear_event.add_clear_values_action(
        source_row=current_row_context_var,
        table=orders_table,
        fields=[
            orders_table.notes_field,
            orders_table.discount_field,
        ],
    )

Transaction management:

.. code-block:: python

    save_event = ModelEvent()
    save_event.add_begin_transaction()
    save_event.add_set_table_value_action(...)
    save_event.add_set_table_value_action(...)
    save_event.add_commit_transaction()

    cancel_event = ModelEvent()
    cancel_event.add_rollback_transaction()
    cancel_event.add_close_modal_action()

Conditional execution (the action only runs if the condition is true):

.. code-block:: python

    conditional_event = ModelEvent()
    conditional_event.add_switch_view_action(
        view_id="admin_panel",
        condition=is_admin_context_var,  # Only if user is admin
    )

A complex multi-step workflow saving a form and navigating:

.. code-block:: python

    save_and_navigate_event = ModelEvent()

    # 1. Begin transaction
    save_and_navigate_event.add_begin_transaction()

    # 2. Save form values
    save_and_navigate_event.add_set_table_value_action(
        value_source=name_input_context_var,
        target_table=customers_table,
        target_field=customers_table.name_field,
        target_row=current_customer_context_var,
    )
    save_and_navigate_event.add_set_table_value_action(
        value_source=email_input_context_var,
        target_table=customers_table,
        target_field=customers_table.email_field,
        target_row=current_customer_context_var,
    )

    # 3. Commit transaction
    save_and_navigate_event.add_commit_transaction()

    # 4. Close modal
    save_and_navigate_event.add_close_modal_action()

    # 5. Refresh data
    save_and_navigate_event.add_run_data_source_action("customer_list_source")

    # 6. Navigate to list view
    save_and_navigate_event.add_switch_view_action("customer_list_view")

Running reports:

.. code-block:: python

    report_event = ModelEvent()
    report_event.add_run_report_action(report_name="monthly_sales_report")

Refreshing data sources:

.. code-block:: python

    refresh_event = ModelEvent()
    refresh_event.add_run_data_source_action(data_source_name="product_inventory")

Editor events for UI interactions:

.. code-block:: python

    from daitum_ui.model_event import EditorEvent
    from daitum_ui._events import EditorEventType

    button_click = EditorEvent(
        type=EditorEventType.ON_CLICK,
        event=save_and_navigate_event,
    )

    value_change = EditorEvent(
        type=EditorEventType.ON_CHANGE,
        event=update_calculation_event,
    )

Setting named values (Parameters/Calculations):

.. code-block:: python

    from daitum_ui.data import DecimalValue

    update_param_event = ModelEvent()
    update_param_event.add_set_named_value_action(
        value_source=DecimalValue(0.15),
        named_value_target=tax_rate_parameter,
    )

Row operations with key-based selection:

.. code-block:: python

    from daitum_ui._events import RowSelectionMode

    delete_by_key_event = ModelEvent()
    delete_by_key_event.add_delete_row_action(
        target_table=users_table,
        row_count=1,
        select_mode=RowSelectionMode.KEY,
        row=user_id_context_var,
        key_field=users_table.user_id_field,
    )

Value matching for copy operations:

.. code-block:: python

    copy_by_value_event = ModelEvent()
    copy_by_value_event.add_copy_values_action(
        source=source_product_id_context_var,
        target=target_product_id_context_var,
        table=products_table,
        fields=[products_table.price_field],
        match_field=products_table.product_id_field,  # Match by ID
    )

Navigating to the model editor:

.. code-block:: python

    navigate_event = ModelEvent()
    navigate_event.add_model_editor_navigate_action(
        model_id=model_id_field,
        scenario_id=scenario_id_field,
        open_new_tab=True,
    )
