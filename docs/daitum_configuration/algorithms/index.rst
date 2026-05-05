Algorithms
==========

Every algorithm inherits from the abstract
:class:`~daitum_configuration.algorithm_configuration.algorithm.Algorithm`,
which provides the parameters common to every solver — evaluation budget, time
limits, stopping criteria, restart count, and PRNG seed.

Numeric algorithm parameters accept either a plain number or a
:class:`~daitum_configuration.NumericExpression`, which lets values scale with
the problem size at runtime.

.. toctree::
    :maxdepth: 1
    :hidden:

    genetic
    cmaes
    vns

Algorithm base
--------------

.. automodule:: daitum_configuration.algorithm_configuration.algorithm

NumericExpression
-----------------

.. automodule:: daitum_configuration.algorithm_configuration.numeric_expression
