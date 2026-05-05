Model Builder
=============

The :class:`~daitum_model.ModelBuilder` is the entry point for defining a model.
Use its factory methods to add tables and named values, then call
``write_to_file()`` to emit the model definition JSON.

Related pages:

- :doc:`tables/index` — the table types (data, derived, joined, union)
- :doc:`fields` — fields that live on tables
- :doc:`named_values` — calculations and parameters
- :doc:`formulas` — the formula language and built-in functions

.. autoclass:: daitum_model.ModelBuilder
    :members:
    :undoc-members:
    :show-inheritance:
