Tables
======

A model holds rows of data in tables. Every table is a subclass of
:class:`~daitum_model.Table` and exposes a fluent builder API for adding
fields and validators.

The four concrete table types each address a different shape of data:

- :doc:`data_table` — raw data and decision variables
- :doc:`derived_table` — grouped, sorted, filtered view of a source table
- :doc:`joined_table` — rows produced by joining two or more tables
- :doc:`union_table` — rows stacked from multiple source tables

.. toctree::
    :maxdepth: 1
    :hidden:

    data_table
    derived_table
    joined_table
    union_table

.. autoclass:: daitum_model.Table
    :members:
    :undoc-members:
    :show-inheritance:
