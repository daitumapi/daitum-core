DerivedTable
============

A :class:`~daitum_model.derived_table.DerivedTable` is built from another
table with optional grouping, filtering and sorting. When grouping is
configured, fields can be added with an
:class:`~daitum_model.AggregationMethod` to summarise the source rows.

Basic setup
-----------

Filtered derived table
~~~~~~~~~~~~~~~~~~~~~~

A filtered derived table keeps only the source rows where a ``BOOLEAN`` field is
``True``. The example below builds an ``Orders`` table and a derived table,
``LargeOrders``, that keeps only the orders with a quantity over 10:

.. code-block:: python

    from daitum_model import ModelBuilder, DataType

    model = ModelBuilder()

    orders = model.add_data_table("Orders")
    orders.set_key_column("Order Id")
    orders.add_data_field("Order Id", DataType.STRING)
    quantity = orders.add_data_field("Quantity", DataType.INTEGER)
    is_large = orders.add_calculated_field("Is Large", quantity > 10)

    large_orders = model.add_derived_table("LargeOrders", orders, filter_field=is_large)
    large_orders.add_source_fields()

``filter_field`` must reference a ``BOOLEAN`` field on the source table.
``add_source_fields()`` with no arguments copies every field from ``Orders``
into ``LargeOrders``.

Grouped derived table
~~~~~~~~~~~~~~~~~~~~~

A grouped derived table collapses source rows that share the same value for
one or more fields, then summarises the remaining fields with an
:class:`~daitum_model.AggregationMethod`. The example below groups ``Orders``
by ``Customer`` and sums the quantity ordered by each customer:

.. code-block:: python

    from daitum_model import ModelBuilder, DataType, AggregationMethod

    model = ModelBuilder()

    orders = model.add_data_table("Orders")
    orders.set_key_column("Order Id")
    orders.add_data_field("Order Id", DataType.STRING)
    customer = orders.add_data_field("Customer", DataType.STRING)
    quantity = orders.add_data_field("Quantity", DataType.INTEGER)

    orders_by_customer = model.add_derived_table("OrdersByCustomer", orders, group_by=[customer])
    orders_by_customer.add_source_fields()
    orders_by_customer.add_aggregated_field("Total Quantity", quantity, AggregationMethod.SUM)

``group_by`` lists the fields used to group rows — here, one row is produced
per distinct ``Customer``. ``add_source_fields()`` adds the group-by fields
themselves, and ``add_aggregated_field`` adds a new field that aggregates a
field from the source table across each group.

Sorted derived table
~~~~~~~~~~~~~~~~~~~~~

A sorted derived table orders its rows by one or more fields. The example
below sorts ``Orders`` by ``Quantity`` from highest to lowest:

.. code-block:: python

    from daitum_model import ModelBuilder, DataType, SortDirection

    model = ModelBuilder()

    orders = model.add_data_table("Orders")
    orders.set_key_column("Order Id")
    orders.add_data_field("Order Id", DataType.STRING)
    quantity = orders.add_data_field("Quantity", DataType.INTEGER)

    orders_by_quantity = model.add_derived_table("OrdersByQuantity", orders)
    orders_by_quantity.add_source_fields()
    orders_by_quantity.add_sort_key(quantity, SortDirection.DESCENDING)

``add_sort_key`` can be called more than once to sort by additional fields —
each extra call breaks ties left over from the previous sort key.

API Reference
-------------

.. autoclass:: daitum_model.derived_table.DerivedTable
    :members:
    :undoc-members:
    :show-inheritance:

.. autoclass:: daitum_model.SortDirection
    :members:
    :undoc-members:

.. autoclass:: daitum_model.AggregationMethod
    :members:
    :undoc-members:
