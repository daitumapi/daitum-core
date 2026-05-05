Quickstart
==========

This guide walks through building a small ``daitum-model`` model end-to-end.

Installation
------------

``daitum-model`` is published on PyPI:

.. code-block:: bash

    pip install daitum-model

To pin a specific version:

.. code-block:: bash

    pip install daitum-model==1.0.0

It is also bundled in the ``daitum-core`` meta-package alongside ``daitum-ui``
and ``daitum-configuration`` — see the top-level :doc:`/getting_started/quickstart`.

Source: `github.com/daitumapi/daitum-core <https://github.com/daitumapi/daitum-core>`_.

A minimal model
---------------

The :class:`~daitum_model.ModelBuilder` is the entry point. Build the model
incrementally with its factory methods, then call ``write_to_file()`` to emit
the JSON output:

.. code-block:: python

    from daitum_model import ModelBuilder, DataType
    import daitum_model.formulas as formulas

    model = ModelBuilder()

    # A data table with three input fields.
    products = model.add_data_table("Products")
    products.set_key_column("ProductId")
    products.add_data_field("ProductId", DataType.INTEGER)
    price = products.add_data_field("Price", DataType.DECIMAL)
    quantity = products.add_data_field("Quantity", DataType.INTEGER)

    # A calculated field. Formulas compose with Python operators or via
    # daitum_model.formulas helpers.
    products.add_calculated_field("TotalValue", price * quantity)

    # A model-level parameter and a model-level calculation.
    model.add_parameter("TaxRate", DataType.DECIMAL, 0.15, model_level=True)
    model.add_calculation(
        "TotalRevenue",
        formulas.SUM(products["TotalValue"]),
        model_level=True,
    )

    # Emit model-definition.json and the scenarios/named-values JSON files.
    model.write_to_file("output")

The objects returned by ``add_data_field`` and friends are
:class:`~daitum_model.Field` instances that can be used directly in formula
expressions, as shown by ``price * quantity``. ``products["TotalValue"]``
returns a :class:`~daitum_model.Formula` that references the named field.

Grouping with a derived table
-----------------------------

A :class:`~daitum_model.derived_table.DerivedTable` produces a grouped view
over a source table. Aggregated fields are added with an
:class:`~daitum_model.AggregationMethod`:

.. code-block:: python

    from daitum_model import AggregationMethod

    products.add_data_field("Category", DataType.STRING)
    category = products.field_definitions["Category"]

    summary = model.add_derived_table(
        "ProductsByCategory",
        source_table=products,
        group_by=[category],
    )
    summary.add_source_fields([category])
    summary.add_aggregated_field("TotalQuantity", quantity, AggregationMethod.SUM)
    summary.add_aggregated_field("AveragePrice", price, AggregationMethod.AVERAGE)

Where to next
-------------

- :doc:`model` — the full ``ModelBuilder`` API.
- :doc:`tables/index` — every table type.
- :doc:`formulas` — the formula language and built-in functions.
