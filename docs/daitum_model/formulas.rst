Formulas
========

Formula functions live in the ``daitum_model.formulas`` submodule:

.. code-block:: python

   from daitum_model import formulas

   result = formulas.SUM(formulas.ROWS(my_table["amount"]))

.. toctree::
   :maxdepth: 1
   :caption: Formula Reference:

   formulas/ABS
   formulas/AND
   formulas/ARRAY
   formulas/ARRAYMAX
   formulas/ARRAYMIN
   formulas/AVERAGE
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
