Excel Processors
================

.. note::
   Excel processors are deprecated and should not be used for new models. Use
   :doc:`data_processors` instead, which supersede excel processors with a more
   general transformation model that works across all supported data sources.

Overview
--------

Excel processors are Excel workbooks that take the data from the model and transform it into a form the model can consume directly. A processor embeds Excel formulas into its output
sheets so that each cell's value is resolved at import time.

Setting up a Processor
---------------------------------

Use ``ExcelTransformConfig`` from ``daitum_configuration`` to declare an Excel data source.
Each instance maps one or more source sheets in the uploaded workbook to target sheets in
the model.

.. code-block:: python

   import daitum_configuration as cg

   example_processor = cg.ExcelTransformConfig(
        file_key="Processor",
        file_name="Processor.xlsx",
        sheet_mapping=[
            ("Sheet_Name_1", "Model_Table_Name_1"),
            ("Sheet_Name_2", "Model_Table_Name_2"),
        ],
    )
    example_processor.set_manual_sheet_names(True)
    example_processor.set_debug_file(True)

Each element of ``sheet_mapping`` is a ``(source_sheet, target_sheet)`` pair. The source
sheet name is the tab in the uploaded workbook; the target sheet name is the model table
that receives the rows.

``set_manual_sheet_names(True)`` tells the platform to resolve tab names literally rather
than through its auto-discovery logic.

``set_debug_file(True)`` enables debugging of the processor calculations.

Migration
---------

If you have an existing model that relies on excel processors, migrate to data processors:

- Replace excel processor definitions with the equivalent data processor configuration.
- Update input mappings to reference the standard data source bindings rather than
  Excel-specific ones.
- Re-validate downstream tables to confirm processed outputs match the previous behaviour.

See the :doc:`data_processors` tutorial for the current approach.

Next Steps
----------

Continue with the :doc:`data_processors` tutorial to learn the current data transformation
workflow.
