DerivedTable
============

A :class:`~daitum_model.derived_table.DerivedTable` is built from another
table with optional grouping, filtering, sorting and pivoting. When grouping is
configured, fields can be added with an
:class:`~daitum_model.AggregationMethod` to summarise the source rows.

Grouping, filtering and pivoting are configured fluently on the table after it
is created:

- :meth:`~daitum_model.derived_table.DerivedTable.group_by` sets the group-by
  fields (each chainable method returns the table).
- :meth:`~daitum_model.derived_table.DerivedTable.set_filter_field` restricts
  the source rows.
- :meth:`~daitum_model.derived_table.DerivedTable.add_sort_key` orders the
  output rows.
- :meth:`~daitum_model.derived_table.DerivedTable.add_aggregated_field` and
  :meth:`~daitum_model.derived_table.DerivedTable.add_pivot` add summarised and
  pivoted columns.

.. note::

    Passing ``group_by=`` or ``filter_field=`` to
    :meth:`~daitum_model.ModelBuilder.add_derived_table` is deprecated in favour
    of :meth:`~daitum_model.derived_table.DerivedTable.group_by` and
    :meth:`~daitum_model.derived_table.DerivedTable.set_filter_field`. The
    keyword arguments still work but emit a warning.

Basic setup
-----------

Filtered derived table
~~~~~~~~~~~~~~~~~~~~~~~~

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

    large_orders = model.add_derived_table("LargeOrders", orders)
    large_orders.set_filter_field(is_large)
    large_orders.add_source_fields()

:meth:`~daitum_model.derived_table.DerivedTable.set_filter_field` must reference
a ``BOOLEAN`` field on the source table; rows are filtered before grouping and
pivoting. ``add_source_fields()`` with no arguments copies every field from
``Orders`` into ``LargeOrders``.

Grouped derived table
~~~~~~~~~~~~~~~~~~~~~~~

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

    orders_by_customer = model.add_derived_table("OrdersByCustomer", orders)
    orders_by_customer.group_by(customer)
    orders_by_customer.add_source_fields()
    orders_by_customer.add_aggregated_field("Total Quantity", quantity, AggregationMethod.SUM)

:meth:`~daitum_model.derived_table.DerivedTable.group_by` lists the fields used
to group rows — here, one row is produced per distinct ``Customer``. Called
with no arguments it collapses the whole (filtered) source into a single output
row. ``add_source_fields()`` adds the group-by fields themselves, and
``add_aggregated_field`` adds a new field that aggregates a field from the
source table across each group.

Sorted derived table
~~~~~~~~~~~~~~~~~~~~~~

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

Pivoted derived table
~~~~~~~~~~~~~~~~~~~~~~~

A pivot turns the values of one source field into explicit output columns. It
is configured on a grouped derived table with
:meth:`~daitum_model.derived_table.DerivedTable.add_pivot`, then one column per
value with :meth:`~daitum_model.derived_table.DerivedTable.Pivot.add_column`.

Suppose ``Readings`` records a ``Value`` per ``Location`` and ``Hour``, and we
want one row per location with a column per hour of the day. The example below
groups by ``Location`` and pivots ``Hour`` into columns ``H0 … H23``:

.. code-block:: python

    from daitum_model import ModelBuilder, DataType, AggregationMethod

    model = ModelBuilder()

    readings = model.add_data_table("Readings")
    location = readings.add_data_field("Location", DataType.STRING)
    hour = readings.add_data_field("Hour", DataType.INTEGER)
    value = readings.add_data_field("Value", DataType.DECIMAL)

    report = model.add_derived_table("Report", readings)
    report.group_by(location)
    report.add_source_fields([location])

    # A "Total" aggregate column alongside the pivot columns.
    report.add_aggregated_field("Total", value, AggregationMethod.SUM)

    # One column per hour. add_column is chainable.
    pivot = report.add_pivot(hour, value)
    for h in range(24):
        pivot.add_column(f"H{h}", h)

Each :meth:`~daitum_model.derived_table.DerivedTable.Pivot.add_column` declares
one output column. A pivot column is simply a **keyed aggregated field**: it
aggregates the pivot's value field over only the source rows whose key field
equals the column's key value. Cell ``(Location, H0)`` therefore holds the
``Value`` aggregated across the rows in that group where ``Hour == 0``, using
the pivot's aggregation method (``FIRST`` by default). ``add_pivot`` accepts an
explicit :class:`~daitum_model.AggregationMethod` when more than one source row
can reach the same cell; ``REFERENCE`` is not permitted.

When **no** source row in a group matches a column's key value, the cell holds
that aggregation method's empty result — the same value the method returns over
an empty set of rows. This is method-dependent:

- ``SUM``, ``COUNT``, ``AVERAGE``, ``MIN``, ``MAX`` — zero.
- ``FIRST``, ``LAST``, ``EQUAL`` — blank.

Array aggregations return an empty array, and each remaining method returns its
own empty-set result. So an empty ``SUM`` cell is ``0``, not blank — choose the
aggregation method with the empty-cell value you want in mind.

Because a pivot column is just an aggregated field, plain aggregated fields and
pivot columns sit side by side in the same ``aggregatedFields`` block, as shown
by the ``Total`` column above — the pivot columns simply carry a ``keyField`` /
``keyValue`` pair that ``Total`` does not. Each pivot column is synthesised as a
read-only field of the derived type, so it can be referenced from formulas
elsewhere in the model (for example ``SUM(Report[H0])``).

The ``key_value`` of each column is a constant scalar (``0``, ``"Monday"``, …),
not a field — pivot columns are declared up front, so their routing keys are
fixed in the model definition rather than discovered from the data at run time.
To turn *discovered* field values into rows instead of columns, use an ordinary
:meth:`~daitum_model.derived_table.DerivedTable.group_by` rather than a pivot.

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
