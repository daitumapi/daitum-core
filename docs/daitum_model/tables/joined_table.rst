JoinedTable
===========

A :class:`~daitum_model.joined_table.JoinedTable` is the result of joining
two or more tables on one or more :class:`~daitum_model.joined_table.JoinCondition`
rows. The :class:`~daitum_model.JoinType` of each condition controls how
unmatched rows are handled.

Matching joins (``LEFT``, ``RIGHT``, ``INNER``, ``FULL``) require both a
``left_field`` and a ``right_field`` to match rows between the two tables. A
``CROSS`` join instead pairs every left row with every right row (the Cartesian
product) and takes no match fields — supplying ``left_field`` or ``right_field``
on a ``CROSS`` condition raises ``ValueError``.

Basic setup
-----------

Suppose we want to know the customer name behind each order. The example
below joins an ``Orders`` table to a ``Customers`` table on ``Customer Id``
so that customer details are available alongside every order:

.. code-block:: python

    from daitum_model import ModelBuilder, DataType, JoinCondition, JoinType

    model = ModelBuilder()

    orders = model.add_data_table("Orders")
    orders.set_key_column("Order Id")
    orders.add_data_field("Order Id", DataType.STRING)
    customer_id = orders.add_data_field("Customer Id", DataType.STRING)

    customers = model.add_data_table("Customers")
    customers.set_key_column("Id")
    customer_key = customers.add_data_field("Id", DataType.STRING)
    customers.add_data_field("Name", DataType.STRING)

    condition = JoinCondition(
        orders, customers, JoinType.LEFT, left_field=customer_id, right_field=customer_key
    )
    orders_with_customers = model.add_joined_table("OrdersWithCustomers", [condition])
    orders_with_customers.add_table_reference(orders)
    orders_with_customers.add_table_reference(customers)

A ``JoinCondition`` pairs a ``left_table`` with a ``right_table`` and, for a
matching join type such as ``LEFT``, requires the fields to match rows
between them — here, ``Orders.Customer Id`` and ``Customers.Id``.
``add_joined_table`` then builds the joined table from one or more
conditions. ``add_table_reference`` adds a field on the joined table that
references a source table's row, so its fields can be looked up from the
joined table.

API Reference
-------------

.. autoclass:: daitum_model.joined_table.JoinedTable
    :members:
    :undoc-members:
    :show-inheritance:

.. autoclass:: daitum_model.joined_table.JoinCondition
    :members:
    :undoc-members:
    :show-inheritance:

.. autoclass:: daitum_model.JoinType
    :members:
    :undoc-members:
