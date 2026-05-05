Formulas
========

A :class:`~daitum_model.Formula` is a typed expression in a small modelling
language modelled loosely on Microsoft Excel. Formulas are used by
:class:`~daitum_model.fields.CalculatedField` and
:class:`~daitum_model.Calculation` to compute values from other fields and
named values.

Build expressions with Python operators or with the helper functions in
:mod:`daitum_model.formulas`:

.. code-block:: python

    import daitum_model.formulas as formulas
    from daitum_model.formula import CONST

    total = products["price"] * products["quantity"]            # Formula
    is_expensive = products["price"] > CONST(100)               # Formula
    summary = formulas.SUM(products["price"])                   # Formula

The Formula Class
-----------------

.. autoclass:: daitum_model.Formula
    :members:
    :undoc-members:
    :show-inheritance:

Built-in Formula Functions
--------------------------

The :mod:`daitum_model.formulas` submodule provides every built-in formula
function.
