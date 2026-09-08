Reports
=======

A :class:`~daitum_configuration.ReportProperty` attached to a
:class:`~daitum_configuration.ConfigurationBuilder` controls how a scenario's outputs are
exported. Register one per report with
:meth:`~daitum_configuration.ConfigurationBuilder.add_report_property`.

A report's contents come from a **model transform**
(:meth:`~daitum_configuration.ReportProperty.set_transform_file`): a self-contained sub-model,
evaluated against a snapshot of the scenario's data, whose declared outputs become the report.
:class:`~daitum_configuration.ReportExportFormat` selects the file produced — ``XLSX``,
``CSV``, ``JSON`` or ``MSDOS``. A transform-backed report requires a V3 model.

Attaching a transform
---------------------

Build the transform as in :doc:`/daitum_configuration/data_sources/model_transform`, upload it,
and reference the returned storage key from the report. In the report role each table output is
a sheet (XLSX) or file (CSV), and parameter outputs collapse into a single ``Named Values``
sheet.

.. code-block:: python

    from daitum_configuration import (
        ConfigurationBuilder,
        ReportExportFormat,
        ReportProperty,
    )

    # `transform_key` is the storage key of an uploaded ModelTransform.build() payload.
    summary = (
        ReportProperty(ReportExportFormat.XLSX)
        .set_name("Route Summary")
        .set_transform_file(transform_key)
    )

    config = ConfigurationBuilder().add_report_property("route_summary", summary)

``export_interface_key`` is a separate, optional setting: it names a predefined export
interface configured on the platform — a target the scenario's data is sent to — and doubles
as the report's fallback display name when :meth:`~daitum_configuration.ReportProperty.set_name`
is not called. It is not a template or a rendering mode.

API reference
-------------

.. automodule:: daitum_configuration.report_property.report_property

.. automodule:: daitum_configuration.report_property.report_data

.. automodule:: daitum_configuration.report_property.report_export_format
