Quickstart
==========

This example builds a complete Daitum model for a resource allocation problem: given a
budget, allocate quantities of items to maximise total value while minimising cost. Each
item has diminishing returns — the more you buy, the less value each additional unit adds —
so the solver must spread the budget intelligently.

Model definition
----------------

Use :class:`daitum_model.ModelBuilder` to define tables, fields, and formulas.

.. code-block:: python

   import daitum_model.formulas as f
   from daitum_model import DataType, ModelBuilder

   model = ModelBuilder()

   # --- Table ---
   items = model.add_data_table("Items")
   items.set_key_column("Name")

   name = items.add_data_field("Name", DataType.STRING)
   unit_cost = items.add_data_field("Unit Cost", DataType.DECIMAL)
   base_value = items.add_data_field("Base Value", DataType.DECIMAL)
   quantity = items.add_data_field("Quantity", DataType.INTEGER)
   min_qty = items.add_data_field("Min Qty", DataType.INTEGER)
   max_qty = items.add_data_field("Max Qty", DataType.INTEGER)

   # Row-level cost
   row_cost = items.add_calculated_field("Row Cost", unit_cost * quantity)

   # Row-level value with diminishing returns: value grows logarithmically with quantity,
   # so each additional unit adds less value than the previous one.
   diminish_rate = model.add_parameter("DIMINISH_RATE", DataType.DECIMAL, 20.0)
   diminished_quantity = f.LOG(1.0 + diminish_rate * quantity) / f.LOG(1.0 + diminish_rate)
   row_value = items.add_calculated_field("Row Value", base_value * diminished_quantity)

   # --- Model-level aggregates ---
   total_cost = model.add_calculation("TOTAL_COST", f.SUM(items["Row Cost"]))
   total_value = model.add_calculation("TOTAL_VALUE", f.SUM(items["Row Value"]))

   # --- User-editable budget ---
   budget = model.add_parameter("BUDGET", DataType.DECIMAL, 10_000.0)

UI definition
-------------

Use :class:`daitum_ui.ui_builder.UiBuilder` to define what the user sees. Pass field IDs
to :meth:`~daitum_ui.tabular.TableView.add_field` to include columns in the table view, and
attach :meth:`~daitum_ui.tabular.ViewField.set_cell_style` to format numeric values. The
top-level dashboard combines a horizontal summary of model-level totals with the items
table beneath, arranged with :class:`~daitum_ui.layout.GridLayout`.

.. code-block:: python

    from daitum_ui.layout import FlexDirection
    from daitum_ui.tabular import ViewField
    from daitum_ui.ui_builder import UiBuilder
    from daitum_ui.form_view import FormVariant

    ui = UiBuilder()

    items_view = ui.add_table_view(items)
    items_view.add_field("Name")
    items_view.add_field("Unit Cost").set_cell_style(display_format="$#,##0.00")
    items_view.add_field("Base Value").set_cell_style(display_format="#,##0.00")
    items_view.add_field("Quantity")
    items_view.add_field("Min Qty")
    items_view.add_field("Max Qty")

    totals_view = ui.add_form_view()
    totals_view.set_columns(2, "min-content")
    totals_view.add_label("Budget", 0, 0).set_variant(FormVariant.HEADER)
    totals_view.add_label("Total Cost", 1, 0).set_variant(FormVariant.HEADER)
    totals_view.add_label("Total Value", 2, 0).set_variant(FormVariant.HEADER)

    totals_view.add_number_input(budget, 0, 1).set_display_format("$#,##0.00")
    totals_view.add_number_input(total_cost, 1, 1).set_display_format(
        "$#,##0.00"
    ).add_conditional_read_only(True)
    totals_view.add_number_input(total_value, 2, 1).set_display_format(
        "#,##0.00"
    ).add_conditional_read_only(True)

    dashboard_view = (
        ui.add_flex_view(display_name="Dashboard").set_flex_direction(FlexDirection.ROW).set_gap("30px")
    )
    dashboard_view.add_child(items_view, width="740px")
    dashboard_view.add_child(totals_view)

    ui.add_navigation_item(dashboard_view)
    ui.set_default_view(dashboard_view)

Configuration
-------------

Use :class:`daitum_configuration.ConfigurationBuilder` to wire up the algorithm, decision
variables, objectives, and constraints.

For field-based decision variables (where the solver adjusts a value per row), you must
provide the source table via ``dv_table``, and pass fields as the min/max bounds.

.. code-block:: python

   from daitum_configuration import (
       ConfigurationBuilder,
       DVType,
       ModelConfiguration,
       Priority,
       VariableNeighbourhoodSearch,
   )

   model_cfg = ModelConfiguration()

   (
       model_cfg.add_decision_variable(quantity, dv_table=items, dv_type=DVType.RANGE)
       .set_min(min_qty)
       .set_max(max_qty)
   )

   # Two competing objectives: spend less, gain more
   model_cfg.add_objective(total_cost, maximise=False, priority=Priority.LOW, name="Cost")
   model_cfg.add_objective(total_value, maximise=True, priority=Priority.HIGH, name="Value")

   # Hard constraint: total spend must not exceed the budget
   model_cfg.add_constraint(total_cost).set_upper_bound(budget).set_name("Budget")

   config = ConfigurationBuilder()
   algorithm = VariableNeighbourhoodSearch(offspring_size=16, time_limit=90)
   config.set_algorithm(algorithm)
   config.set_model_configuration(model_cfg)

Serialise to JSON
-----------------

Each artefact serialises to a ``dict``. Write the files alongside any input data prepared
through :func:`daitum_model.data_processor.prepare_data`, then bundle them into a ZIP
for upload to the Daitum platform.

.. code-block:: python

   import pathlib

   model_directory = pathlib.Path.cwd() / "model-files"
   data_directory = pathlib.Path.cwd() / "data"

   model.write_to_file(model_directory)
   ui.write_to_file(model_directory)
   config.write_to_file(model_directory)

   from daitum_model import data_processor

   data_processor.prepare_data(model, str(data_directory), str(model_directory))

   import shutil

   model_name = "BudgetOptimiser"
   shutil.make_archive(model_name, "zip", model_directory)

Next steps
----------

- Explore the :doc:`../tutorials/introduction` for a broader introduction to modelling concepts.
- Browse the API reference for :doc:`../daitum_model/index`, :doc:`../daitum_ui/index`,
  and :doc:`../daitum_configuration/index`.
