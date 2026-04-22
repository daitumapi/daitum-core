Getting Started
===============

Installation
------------

Install the full suite with the meta-package:

.. code-block:: bash

   pip install daitum-core

Or install individual packages independently:

.. code-block:: bash

   pip install daitum-model
   pip install daitum-ui
   pip install daitum-configuration

Quick Example
-------------

.. code-block:: python

   from daitum_model import ModelBuilder, DataType, formulas
   from daitum_ui.ui_builder import UiBuilder
   from daitum_configuration import Configuration

   # 1. Define the model
   model = ModelBuilder()
   jobs = model.add_data_table("Jobs", key_column="ID")
   job_id = jobs.add_data_field("ID", DataType.STRING)
   cost = jobs.add_data_field("Cost", DataType.DECIMAL)
   total = model.add_calculation("TOTAL_COST", formulas.SUM(cost))

   # 2. Define the UI
   ui = UiBuilder()
   ui.add_table_view(jobs)

   # 3. Define the configuration
   config = Configuration()

   # 4. Serialise to dict (ready for JSON export)
   model_dict = model.to_dict()
   ui_dict = ui.build()
   config_dict = config.to_dict()
