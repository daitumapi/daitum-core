DataTable
=========

A :class:`~daitum_model.tables.DataTable` holds plain rows of data — imported
records or decision variables that the optimiser writes to. It is the only
table type that supports decision variables and ``ComboField``.

Basic setup
-----------

The example below builds two data tables. ``Products`` holds imported product
data; ``Orders`` references a row in ``Products`` via an object reference
field and uses it to calculate the cost of the order:

.. code-block:: python

    from daitum_model import ModelBuilder, DataType

    model = ModelBuilder()

    # Products: imported data.
    products = model.add_data_table("Products")
    products.set_key_column("Product Id")
    products.add_data_field("Product Id", DataType.STRING)
    products.add_data_field("Price", DataType.DECIMAL)

    # Orders: a data field, an object reference field pointing at a Product,
    # and a calculated field that uses the referenced Product's price.
    orders = model.add_data_table("Orders")
    orders.set_key_column("Order Id")
    orders.add_data_field("Order Id", DataType.STRING)
    product = orders.add_object_reference_field("Product", products)
    quantity = orders.add_data_field("Quantity", DataType.INTEGER)
    orders.add_calculated_field("Order Cost", product["Price"] * quantity)

A ``DataTable`` accepts every field type described in :doc:`/daitum_model/fields`

``set_key_column`` designates the field used to uniquely identify each row —
``Product Id`` and ``Order Id`` above. This is the field used to look up and
reference rows in this table from elsewhere, for example when validating that
an ``add_object_reference_field`` value on another table matches an existing
row here. A table does not require a key column, but one is needed whenever
other tables reference it.

API Reference
-------------

.. autoclass:: daitum_model.tables.DataTable
    :members:
    :undoc-members:
    :show-inheritance:
