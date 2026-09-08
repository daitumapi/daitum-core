Model Transform
===============

A **model transform** is a self-contained sub-model paired with maps declaring what it
produces. The sub-model is an ordinary :class:`~daitum_model.ModelBuilder`; the maps expose
its tables and named values as *outputs*. The same file serves two roles, differing only in
what the outputs mean:

* As a **data source**, a :class:`~daitum_configuration.ModelTransformConfig` runs the sub-model
  over input data and routes each table output back into a table of the parent model.
* As a **report**, the sub-model is evaluated against a scenario snapshot and its outputs *are*
  the report — see :doc:`/daitum_configuration/reports`.

Building a transform
--------------------

Build the sub-model, then declare its outputs with
:class:`~daitum_configuration.ModelTransform`. Each role has its own pair of ``add_*`` methods,
phrased in that role's terms; use the ``data_source`` pair here. Whatever tables and named
values the sub-model declares as plain data are populated from same-named data on the host;
everything else is derived inside the sub-model with the usual derived tables, joins, unions and
calculations.

.. code-block:: python

    import daitum_model.formulas as f
    from daitum_model import DataType, ModelBuilder
    from daitum_configuration import ModelTransform

    # A sub-model whose input table mirrors a host table by id.
    sub = ModelBuilder()
    deliveries = sub.add_data_table("Deliveries")
    deliveries.set_key_column("Route")
    route = deliveries.add_data_field("Route", DataType.STRING)
    distance = deliveries.add_data_field("Distance", DataType.DECIMAL)
    cost = deliveries.add_calculated_field("Cost", distance * 1.85)

    total_cost = sub.add_calculation("TOTAL_COST", f.SUM(deliveries["Cost"]), model_level=True)

    # Fields and named value of the parent model this transform feeds back into.
    parent_table = parent.get_table("Deliveries")
    parent_route = parent_table.get_field("Route")
    parent_cost = parent_table.get_field("Cost")

    # Route each output back into the parent by object reference.
    transform = (
        ModelTransform(sub)
        .add_data_source_table(
            deliveries,
            parent_table,
            field_mapping={parent_route: route, parent_cost: cost},
        )
        .add_data_source_named_value(parent_total_cost, total_cost)
    )

    payload = transform.build()  # upload this JSON; reference it later by storage key

Omit ``field_mapping`` to auto-pair sub-model and parent fields with matching ids (data and
combo fields only).

The output maps
---------------

The two roles write the same underlying maps but expose them through separate methods, so each
reads in its own terms rather than sharing one signature:

.. list-table::
   :header-rows: 1
   :widths: 24 38 38

   * - Concept
     - Data source
     - Report
   * - table output
     - :meth:`~daitum_configuration.ModelTransform.add_data_source_table` — sub-model table →
       parent :class:`~daitum_model.Table`
     - :meth:`~daitum_configuration.ModelTransform.add_report_sheet` — sub-model table → sheet
       / file name (``str``)
   * - field mapping
     - parent :class:`~daitum_model.Field` → sub-model :class:`~daitum_model.Field`
     - column header (``str``) → sub-model :class:`~daitum_model.Field`
   * - named value
     - :meth:`~daitum_configuration.ModelTransform.add_data_source_named_value` — parent named
       value → sub-model named value
     - :meth:`~daitum_configuration.ModelTransform.add_report_named_value` — column header
       (``str``) → sub-model named value

The report methods are covered in :doc:`/tutorials/reports`.

API reference
-------------

.. automodule:: daitum_configuration.data_source.model_transform.model_transform_config

.. automodule:: daitum_configuration.data_source.model_transform.model_transform

.. automodule:: daitum_configuration.data_source.model_transform.model_transform_input

.. automodule:: daitum_configuration.data_source.model_transform.data_input_source_type
