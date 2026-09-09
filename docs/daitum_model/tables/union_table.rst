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

Folding columns into rows
-------------------------

A :class:`~daitum_model.union_table.FoldedTable` — created with
:meth:`~daitum_model.ModelBuilder.add_folded_table` — turns wide columns of a
single source table into rows. It is a convenience over a union of the source
table with itself: one source copy per folded column group, each mapping a
different column onto a shared output column.

Suppose ``Roster`` records a wage per employee per day as columns
``Day1Wages … Day7Wages``, and we want the long shape
``(Employee, Day, Wages)`` with one row per employee per day:

.. code-block:: python

    from daitum_model import ModelBuilder, DataType

    model = ModelBuilder()

    roster = model.add_data_table("Roster")
    roster.add_data_field("Employee", DataType.STRING)
    for day in range(1, 8):
        roster.add_data_field(f"Day{day}Wages", DataType.DECIMAL)

    folded = model.add_folded_table("Roster_Long", roster)
    folded.add_column("Day", DataType.INTEGER)      # the fold label column
    folded.add_column("Wages", DataType.DECIMAL)    # the folded value column
    folded.carry(roster.get_field("Employee"))      # passed through unchanged

    for day in range(1, 8):
        folded.fold(Day=day, Wages=roster.get_field(f"Day{day}Wages"))

:meth:`~daitum_model.union_table.FoldedTable.add_column` declares the output
columns, and :meth:`~daitum_model.union_table.FoldedTable.carry` declares the
columns passed through unchanged in every output row.

Each :meth:`~daitum_model.union_table.FoldedTable.fold` call adds one group of
output rows, giving a value for every declared column. A value may be a source
:class:`~daitum_model.Field` (mapped directly) or a Python literal (folded in as
a constant of the column's declared type) — above, ``Wages`` is mapped from a
source column while ``Day`` is stamped with the constant ``day``.

When both columns being collapsed already exist on the source (for example
``Day1Label … Day7Label`` alongside ``Day1Wages … Day7Wages``), map each fold
directly and no constants are synthesised:

.. code-block:: python

    for day in range(1, 8):
        folded.fold(
            Day=roster.get_field(f"Day{day}Label"),
            Wages=roster.get_field(f"Day{day}Wages"),
        )

The underlying :class:`~daitum_model.union_table.UnionTable` is registered on
the model and is available as
:attr:`~daitum_model.union_table.FoldedTable.table`.

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

.. autoclass:: daitum_model.union_table.FoldedTable
    :members:
    :undoc-members:
    :show-inheritance:
