Named Value View
================

.. automodule:: daitum_ui.named_value_view
    :no-index:
    :members:
    :show-inheritance:

Examples
--------

Vertical orientation for a detailed view:

.. code-block:: python

    details_view = builder.add_named_value_view(
        display_name="Customer Details",
        orientation=Orientation.VERTICAL,
    )
    details_view.add_value(
        ViewField(customer_name, display_name="Name")
    )
    details_view.add_value(
        ViewField(customer_email, display_name="Email")
    )
    details_view.add_value(
        ViewField(member_since, display_name="Member Since")
    )
