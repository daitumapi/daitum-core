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

.. toctree::
   :maxdepth: 1
   :caption: Formula Reference:

   formulas/ABS
   formulas/AND
   formulas/ARRAY
   formulas/ARRAYMAX
   formulas/ARRAYMIN
   formulas/AVERAGE
   formulas/BINOMDIST
   formulas/BINOMINV
   formulas/BITAND
   formulas/BITMASK
   formulas/BITMASKSTRING
   formulas/BITOR
   formulas/BLANK
   formulas/CEILING
   formulas/CHAR
   formulas/CHOOSE
   formulas/CONST
   formulas/CONTAINS
   formulas/COS
   formulas/COUNT
   formulas/COUNTBLANKS
   formulas/COUNTDUPLICATES
   formulas/DATE
   formulas/DATETIME
   formulas/DAY
   formulas/DAYSBETWEEN
   formulas/DISTINCT
   formulas/DISTRIBUTE
   formulas/EOMONTH
   formulas/EXP
   formulas/FILTER
   formulas/FIND
   formulas/FINDDUPLICATES
   formulas/FLOOR
   formulas/FROMTIMEZONE
   formulas/GAMMADIST
   formulas/GAMMAINV
   formulas/GET
   formulas/HOUR
   formulas/HOURSBETWEEN
   formulas/IF
   formulas/IFBLANK
   formulas/IFERROR
   formulas/INDEX
   formulas/INTEGER
   formulas/INTERSECTION
   formulas/ISBLANK
   formulas/ISERROR
   formulas/LEFT
   formulas/LEN
   formulas/LOG
   formulas/LOOKUP
   formulas/LOOKUPARRAY
   formulas/LOWER
   formulas/MATCH
   formulas/MAX
   formulas/MEDIAN
   formulas/MIN
   formulas/MINUTE
   formulas/MOD
   formulas/MONTH
   formulas/MONTHSBETWEEN
   formulas/NEXT
   formulas/NORMDIST
   formulas/NORMINV
   formulas/NOT
   formulas/OR
   formulas/PLUSDAYS
   formulas/PLUSMINUTES
   formulas/POWER
   formulas/PREV
   formulas/RANK
   formulas/RIGHT
   formulas/ROUND
   formulas/ROW
   formulas/ROWS
   formulas/ROWVECTOR
   formulas/SECOND
   formulas/SETTIME
   formulas/SIN
   formulas/SIZE
   formulas/STDEV
   formulas/SUM
   formulas/TEXT
   formulas/TEXTJOIN
   formulas/TIME
   formulas/TOMAP
   formulas/TOTIMEZONE
   formulas/TRIM
   formulas/UNION
   formulas/UPPER
   formulas/VALUES
   formulas/WEEKDAY
   formulas/WEIBULL
   formulas/YEAR
