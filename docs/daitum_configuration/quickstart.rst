Quickstart
==========

This guide walks through configuring an optimisation run for a small
``daitum-model`` model. It assumes you have already defined the model itself —
see :doc:`/daitum_model/quickstart` for that.

Installation
------------

``daitum-configuration`` is published on PyPI:

.. code-block:: bash

    pip install daitum-configuration

To pin a specific version:

.. code-block:: bash

    pip install daitum-configuration==1.0.0

It is also bundled in the ``daitum-core`` meta-package alongside ``daitum-model``
and ``daitum-ui`` — see the top-level :doc:`/getting_started/quickstart`.

Source: `github.com/daitumapi/daitum-core <https://github.com/daitumapi/daitum-core>`_.

A minimal configuration
-----------------------

The :class:`~daitum_configuration.ConfigurationBuilder` is the entry point. It
composes a :class:`~daitum_configuration.ModelConfiguration` (decision variables,
objectives, constraints) with an
:class:`~daitum_configuration.algorithm_configuration.algorithm.Algorithm` and
writes the result to ``model-configuration.json``:

.. code-block:: python

    import daitum_model.formulas as f
    from daitum_model import DataType, ModelBuilder

    model = ModelBuilder()

    # A data table whose Quantity field is the decision variable.
    items = model.add_data_table("Items")
    items.set_key_column("Name")
    items.add_data_field("Name", DataType.STRING)
    unit_cost = items.add_data_field("Unit Cost", DataType.DECIMAL)
    quantity = items.add_data_field("Quantity", DataType.INTEGER)
    min_qty = items.add_data_field("Min Qty", DataType.INTEGER)
    max_qty = items.add_data_field("Max Qty", DataType.INTEGER)
    items.add_calculated_field("Row Cost", unit_cost * quantity)

    # Model-level totals and a user-editable budget.
    total_cost = model.add_calculation(
        "TOTAL_COST", f.SUM(items["Row Cost"]), model_level=True
    )
    budget = model.add_parameter("BUDGET", DataType.DECIMAL, 10_000.0, model_level=True)

    from daitum_configuration import (
        ConfigurationBuilder,
        DVType,
        ModelConfiguration,
        Priority,
        VariableNeighbourhoodSearch,
    )

    model_cfg = ModelConfiguration()

    # Per-row decision variable: quantity bounded by the Min/Max Qty fields.
    (
        model_cfg.add_decision_variable(quantity, dv_table=items, dv_type=DVType.RANGE)
        .set_min(min_qty)
        .set_max(max_qty)
    )

    # Minimise total cost.
    model_cfg.add_objective(total_cost, maximise=False, priority=Priority.HIGH, name="Cost")

    # Hard constraint: total spend must not exceed the budget.
    model_cfg.add_constraint(total_cost).set_upper_bound(budget).set_name("Budget")

    config = ConfigurationBuilder()
    config.set_algorithm(VariableNeighbourhoodSearch())
    config.set_model_configuration(model_cfg)

    # Emit model-configuration.json into ./output.
    config.write_to_file("output")

Decision-variable bounds may be supplied in two ways. When ``dv_table`` is
supplied (a per-row variable), pass :class:`~daitum_model.fields.Field`
references to ``set_min``/``set_max`` so each row uses its own bound. For a
model-level :class:`~daitum_model.Parameter` decision variable, pass plain
numeric literals or another ``Parameter``/``Calculation``.

Where to next
-------------

- :doc:`configuration` — the full ``ConfigurationBuilder`` API.
- :doc:`model_configuration/index` — decision variables, objectives, constraints.
- :doc:`algorithms/index` — algorithm choices and their parameters.
- :doc:`data_sources/index` — wiring source data into the model.
