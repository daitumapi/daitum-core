Reports
=======

This tutorial covers how to define **reports** — the exportable outputs a scenario produces
for end users. You will learn what a report is, how to back one with a model transform so it
computes its own contents in V3 formulas, how those outputs map to sheets and columns, and how
the report is exported as XLSX, CSV or JSON.

Overview
--------

A report is an **export configuration**. It describes how a scenario's data is turned into a
downloadable file — an XLSX workbook, a CSV, or JSON — and where the report appears for the
user (the export menu, the side navigator).

Reports are configured with :class:`~daitum_configuration.ReportProperty` and registered on
the :class:`~daitum_configuration.ConfigurationBuilder`, one per report, with
:meth:`~daitum_configuration.ConfigurationBuilder.add_report_property`. They are part of the
model *configuration*, alongside the algorithm, decision variables, and data sources.

A report's contents come from a **model transform** — a self-contained sub-model, attached
with :meth:`~daitum_configuration.ReportProperty.set_transform_file`. The sub-model is
evaluated against a snapshot of the scenario's data and its declared outputs become the
report. Because the report's calculations are V3 formulas, they are checked by the model
parser at upload and live in a plain-text file you can diff, rather than in a spreadsheet.

A transform-backed report requires a **V3 model**.

A minimal report
----------------

Create a :class:`~daitum_configuration.ReportProperty` with an export format, attach a
transform (covered below) by its storage key, and register it:

.. code-block:: python

    from daitum_configuration import (
        ConfigurationBuilder,
        ReportExportFormat,
        ReportProperty,
    )

    # `transform_key` is the storage key of an uploaded transform (see below).
    summary = (
        ReportProperty(ReportExportFormat.XLSX)
        .set_name("Route Summary")
        .set_transform_file(transform_key)
        .set_visible_on_navigator(True)
    )

    config = ConfigurationBuilder().add_report_property("route_summary", summary)

The first argument to ``add_report_property`` is a key that identifies the report within the
configuration; the second is the ``ReportProperty`` itself. ``set_name`` gives the display
name.

:class:`~daitum_configuration.ReportExportFormat` selects the file produced:

* ``XLSX`` — one sheet per output, bold header row, cells typed from each column's data type.
* ``CSV`` — one CSV per output. A single output is a bare ``<report>.csv``; several become a
  ``<report>.zip`` of ``<output>.csv`` entries.
* ``MSDOS`` — as CSV, but CRLF line endings and windows-1252 encoding.
* ``JSON`` — ``{ "<output>": [ { "<column>": value, ... } ], "Named Values": [ { ... } ] }``.

Visibility and behaviour
------------------------

Chain ``set_*`` methods to control where the report appears and how it exports:

.. list-table::
   :header-rows: 1
   :widths: 34 66

   * - Method
     - Effect
   * - ``set_name(name)``
     - Display name; falls back to ``export_interface_key`` when unset.
   * - ``set_visible_on_navigator(True)``
     - Show the report in the side navigator.
   * - ``set_show_in_menu(True)``
     - Show the report in the export menu (default ``True``).
   * - ``set_advanced_user(True)``
     - Restrict the report to advanced users.
   * - ``set_order_index(n)``
     - Position the report in the navigator.
   * - ``set_export_csv(True)``
     - Also emit a CSV alongside the primary format.
   * - ``set_file_name_key(key)``
     - Take the export file name from a model named value.

Building the transform
----------------------

A model transform lets the report compute its own contents. Build it exactly as in
:doc:`/daitum_configuration/data_sources/model_transform` — a self-contained
:class:`~daitum_model.ModelBuilder` sub-model, plus the output maps declaring what it produces.

The sub-model's *inputs* need no configuration: every plain data table and named value it
declares is populated from the same-named table/field or named value on the host model. So a
report transform declares the host tables it wants as plain data tables (matching ids and
field ids) and derives everything else with derived tables, joins, filters, unions and
calculations.

.. note::

   Fields the host model does not have come through as their default value, not as an error.
   A transform that silently produces empty columns is usually a field-id mismatch between
   the sub-model's input table and the host.

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

    # Declare the report outputs. A sheet is named by a string; its columns map a header
    # to the sub-model field supplying it. Order is preserved: sheets in the order added,
    # columns in the order given.
    transform = (
        ModelTransform(sub)
        .add_report_sheet(
            "Deliveries",
            source=deliveries,
            columns={"Route": route, "Distance (km)": distance, "Cost": cost},
        )
        .add_report_named_value("Total Cost", total_cost)
    )

    payload = transform.build()  # upload this JSON; reference it later by storage key

The transform is stored out-of-band: you upload ``transform.build()`` and the platform returns
a storage key, which you pass to
:meth:`~daitum_configuration.ReportProperty.set_transform_file` as shown above.

How the outputs become report content
--------------------------------------

The report methods take strings where the output is named and
:class:`~daitum_model.Field` objects where it reads from the sub-model:

.. list-table::
   :header-rows: 1
   :widths: 40 60

   * - Argument
     - Report meaning
   * - ``add_report_sheet`` ``name``
     - Output name: the XLSX sheet name / CSV file name.
   * - ``add_report_sheet`` ``source``
     - The sub-model :class:`~daitum_model.Table` whose rows populate the sheet.
   * - ``columns`` key
     - Column header.
   * - ``columns`` value
     - The sub-model :class:`~daitum_model.Field` supplying the column.
   * - ``add_report_named_value`` ``name``
     - A column of the single ``Named Values`` sheet.
   * - ``add_report_named_value`` ``source``
     - The sub-model parameter or calculation supplying it.

Both maps are read in **declaration order**, so the order in your code is the order of sheets
and of columns — nothing sorts them. All named values collapse into one sheet named
``Named Values``, one column per value with a single row.

Output names must be non-blank, unique, at most 31 characters, and free of ``[]:*?/\`` — they
become Excel sheet names and zip entry names. No output name may collide with ``Named Values``
when parameter outputs are present. Column names must be non-blank and unique within their
output. These rules are enforced at upload with a 400 error, not silently sanitised at render
time.

Export interfaces
-----------------

``export_interface_key`` is a separate, optional mechanism. It names a **predefined export
interface** configured on the platform — a target the scenario's data is sent to — rather than
a template or a rendering mode for the report's own file. When set, it also serves as the
report's fallback display name if :meth:`~daitum_configuration.ReportProperty.set_name` is
not called.

.. code-block:: python

    report = (
        ReportProperty(ReportExportFormat.XLSX, export_interface_key="route-export")
        .set_transform_file(transform_key)
    )

Next Steps
----------

Continue with the :doc:`integration` tutorial to connect your model to external systems, or
see the :doc:`/daitum_configuration/reports` reference for the full
:class:`~daitum_configuration.ReportProperty` API.
