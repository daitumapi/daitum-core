Named Values
============

Named values are model-level objects that can be referenced in formulas throughout the model. There are two types: **Calculations** and **Parameters**.

Calculation
~~~~~~~~~~~

A :class:`~daitum_model.Calculation` represents a named formula-based value that can be referenced throughout the model.

**Key features:**

- Defined by a :class:`~daitum_model.Formula`
- Data type inferred from the formula
- Can depend on other calculations, parameters, or table fields
- Added using :meth:`ModelBuilder.add_calculation() <daitum_model.ModelBuilder.add_calculation>`

**Attributes:**

- ``named_value_id``: Unique identifier for the calculation
- ``formula``: The formula defining the calculation
- ``depends_on_decision``: Whether it depends on decision variables
- ``model_level``: Whether it's a model-level value
- ``required_by_output``: Whether it's required in the output
- ``tracking_group``: Optional group for change tracking

**Examples:**

.. code-block:: python

    from daitum_model.formula import CONST, SUM, IF

    # Simple constant calculation
    model.add_calculation("tax_rate", CONST(0.15))

    # Calculation using table data
    model.add_calculation(
        "total_revenue",
        SUM(products["price"] * products["quantity"])
    )

    # Calculation using other named values
    model.add_parameter("threshold", DataType.DECIMAL, 1000.0)
    model.add_calculation(
        "is_high_value",
        IF(
            SUM(products["total_value"]) > model["threshold"],
            True,
            False
        )
    )


.. autoclass:: daitum_model.Calculation
    :no-index:
    :members:
    :undoc-members:
    :show-inheritance:

Parameter
~~~~~~~~~

A :class:`~daitum_model.Parameter` represents a named static value that can be referenced in formulas.

**Key features:**

- Holds a static value
- Explicitly typed with a :class:`~daitum_model.DataType`
- Can be changed without modifying formulas
- Added using :meth:`ModelBuilder.add_parameter() <daitum_model.ModelBuilder.add_parameter>`

**Attributes:**

- ``named_value_id``: Unique identifier for the parameter
- ``data_type``: The data type of the parameter
- ``value``: The static value
- ``model_level``: Whether it's a model-level value
- ``required_by_output``: Whether it's required in the output
- ``tracking_group``: Optional group for change tracking

**Examples:**

.. code-block:: python

    from daitum_model import DataType

    # Add numeric parameters
    model.add_parameter("discount_rate", DataType.DECIMAL, 0.1)
    model.add_parameter("max_orders", DataType.INTEGER, 100)

    # Add string parameter
    model.add_parameter("default_status", DataType.STRING, "Pending")

    # Add boolean parameter
    model.add_parameter("enable_discounts", DataType.BOOLEAN, True)

    # Use parameters in calculations
    model.add_calculation(
        "discounted_price",
        products["price"] * (1 - model["discount_rate"])
    )

.. autoclass:: daitum_model.Parameter
    :no-index:
    :members:
    :undoc-members:
    :show-inheritance:

Using Named Values
~~~~~~~~~~~~~~~~~~

**Accessing Named Values:**

.. code-block:: python

    # Access a calculation or parameter
    tax_rate = model["tax_rate"]
    discount = model["discount_rate"]

    # Use in formulas
    products.add_calculated_field(
        "price_with_tax",
        DataType.DECIMAL,
        formula=products["price"] * (1 + tax_rate)
    )

**Model-Level vs Scenario-Level:**

.. code-block:: python

    # Model-level calculation (default)
    model.add_calculation(
        "global_tax_rate",
        CONST(0.15),
        model_level=True
    )

    # Scenario-level parameter
    model.add_parameter(
        "scenario_discount",
        DataType.DECIMAL,
        0.1,
        model_level=False
    )

**Dependencies and Optimization:**

.. code-block:: python

    # Calculation that depends on decision variables
    model.add_calculation(
        "total_cost",
        SUM(products["quantity"] * products["unit_cost"]),
        depends_on_decision=True
    )

