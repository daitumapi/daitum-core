Data Sources
============

A data source describes how external data lands in a model. Every concrete
data-source config inherits from
:class:`~daitum_configuration.data_source.data_source_config.DataSourceConfig`
and is registered on a :class:`~daitum_configuration.ConfigurationBuilder` via
the matching ``add_*`` method.

.. toctree::
    :maxdepth: 1
    :hidden:

    excel_transform
    data_store
    batched
    distance_matrix
    geo_location
    set_features
    model_transform
    run_report

Data source wrapper
-------------------

.. automodule:: daitum_configuration.data_source.data_source

Base configuration
------------------

.. automodule:: daitum_configuration.data_source.data_source_config

.. automodule:: daitum_configuration.data_source.data_source_type
