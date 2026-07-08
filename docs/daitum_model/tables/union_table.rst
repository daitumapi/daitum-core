UnionTable
==========

A :class:`~daitum_model.union_table.UnionTable` stacks rows from multiple
source tables. Field mappings declare which source-table fields feed each
union-table field, since source schemas may differ.

Basic setup
-----------

Suppose orders are recorded in two separate tables — one for online orders,
one for in-store orders — and we want a single table listing every order
regardless of where it was placed. The example below unions ``OnlineOrders``
and ``StoreOrders`` into ``AllOrders``:

.. code-block:: python

    from daitum_model import ModelBuilder, DataType

    model = ModelBuilder()

    online_orders = model.add_data_table("OnlineOrders")
    online_orders.add_data_field("Order Id", DataType.STRING)
    online_orders.add_data_field("Amount", DataType.DECIMAL)

    store_orders = model.add_data_table("StoreOrders")
    store_orders.add_data_field("Order Id", DataType.STRING)
    store_orders.add_data_field("Total", DataType.DECIMAL)

    all_orders = model.add_union_table("AllOrders", [online_orders, store_orders])
    all_orders.add_field("Order Id", DataType.STRING)
    all_orders.add_field("Amount", DataType.DECIMAL)

    all_orders.direct_field_mapping()
    all_orders.add_field_mapping(store_orders, "Amount", store_orders.get_field("Total"))

``add_union_table`` creates ``AllOrders`` with ``OnlineOrders`` and
``StoreOrders`` as source tables, but the union table starts out with no
fields or field mappings of its own — ``add_field`` declares the fields it
will expose, and each source table's rows must be mapped onto them field by
field.

``direct_field_mapping`` maps every union field to a source field of the same
id, wherever one exists — here, that maps ``Order Id`` for both source
tables, and also ``Amount`` for ``OnlineOrders``, whose field happens to share
that name. ``StoreOrders`` has no field called ``Amount``, so its rows would
otherwise have no value for that column; ``add_field_mapping`` fills the gap
by mapping ``StoreOrders.Total`` onto ``AllOrders.Amount`` explicitly. A
mapped source field must have the same data type as the union field it feeds.

API Reference
-------------

.. autoclass:: daitum_model.union_table.UnionTable
    :members:
    :undoc-members:
    :show-inheritance:

.. autoclass:: daitum_model.union_table.UnionSource
    :members:
    :undoc-members:
    :show-inheritance:
