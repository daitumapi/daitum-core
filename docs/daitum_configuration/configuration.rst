Configuration Builder
=====================

The :class:`~daitum_configuration.ConfigurationBuilder` is the entry point for
assembling a configuration. Use ``set_*`` methods to attach an algorithm, model
configuration, schedule, and model property; use ``add_*`` methods to register
data sources and report properties; call ``write_to_file()`` to emit
``model-configuration.json``.

Related pages:

- :doc:`model_configuration/index` — decision variables, objectives, constraints
- :doc:`algorithms/index` — algorithm choices
- :doc:`schedule` — multi-step optimisation
- :doc:`data_sources/index` — data source configurations
- :doc:`reports` — report properties
- :doc:`model_properties` — model-level UI/calculation flags

.. automodule:: daitum_configuration.configuration
