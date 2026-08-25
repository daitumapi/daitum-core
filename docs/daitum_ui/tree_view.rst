Tree View
=========

The ``TreeView`` displays hierarchical data in a tree structure. In most models you do not instantiate ``TreeView`` directly.
Instead, create it via the :class:`~daitum_ui.ui_builder.UiBuilder` API, ``UiBuilder.add_tree_view()``,
which registers the view with the UI definition and ensures it is included in the build output.

Basic Example
-------------

A tree view needs a parent table and a child table linked by an object array field. The example
below groups an ``Orders`` table by ``Customer``, uses ``REFERENCES`` to collect each customer's
orders into their parent row, and sums the quantity ordered as a second aggregation:

.. code-block:: python

    from daitum_model import AggregationMethod, DataType, ModelBuilder
    from daitum_ui.ui_builder import UiBuilder

    model = ModelBuilder()

    # Orders is the child-level table -- one row per order.
    orders = model.add_data_table("Orders")
    orders.set_key_column("Order Id")
    orders.add_data_field("Order Id", DataType.STRING)
    customer = orders.add_data_field("Customer", DataType.STRING)
    quantity = orders.add_data_field("Quantity", DataType.INTEGER)

    # OrdersByCustomer groups Orders into one parent row per customer.
    orders_by_customer = model.add_derived_table("OrdersByCustomer", orders, group_by=[customer])
    orders_by_customer.add_source_fields()
    orders_by_customer.add_aggregated_field("Total Quantity", quantity, AggregationMethod.SUM)

    # REFERENCES collects each group's Orders rows into an object array -- these
    # become the tree's child rows.
    orders_by_customer.add_aggregated_field(
        "Orders", orders.get_field("Order Id"), AggregationMethod.REFERENCE
    )

    builder = UiBuilder()

    # Build the tree from the customer rows down to their order rows.
    tree_view = builder.add_tree_view(table=orders_by_customer, display_name="Orders by Customer")
    tree_view.row_number_depth = 1
    tree_view.set_table_evaluation_order(orders_by_customer, orders)
    tree_view.set_children_field("Orders")

    # Customer only appears on the parent row; leave the child rows blank for it.
    tree_view.add_field("Customer", children=[None])

    # Total Quantity is the parent's sum; each child row shows its own Quantity instead.
    tree_view.add_field("Total Quantity", children="Quantity")

``set_table_evaluation_order`` lists the tables from parent to child, and ``set_children_field``
names the ``REFERENCE`` field that links each parent row to its child rows. For each column added
with ``add_field``, the ``children`` argument controls what is shown at the child level: ``None``
for a blank cell, or another field name -- as with ``Total Quantity`` mapping to ``Quantity`` -- to
show a different field from the child table.

API Reference
-------------

.. autoclass:: daitum_ui.tabular.TreeView
    :no-index:
    :members:
    :show-inheritance:

Supporting Types
----------------

.. autoclass:: daitum_ui.tabular.TreeViewField
    :no-index:
    :members:
    :show-inheritance:
