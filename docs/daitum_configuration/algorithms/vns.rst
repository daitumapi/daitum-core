Variable Neighbourhood Search
=============================

A (μ+λ) evolutionary algorithm with a self-adapting per-individual mutation
rate.

Self-adapting mutation rate
---------------------------

Each individual carries its own mutation rate in its genome. When the
algorithm produces an offspring from a parent, the rate is perturbed by a
lognormal step:

.. math::

    \text{childRate} = \text{parentRate} \times \exp\!\bigl(\tau \cdot
    \mathcal{N}(0, 1)\bigr)

where :math:`\tau` is :attr:`mutation_rate_tau
<daitum_configuration.algorithm_configuration.vns_algorithm.VariableNeighbourhoodSearch.mutation_rate_tau>`.
The result is clamped to ``[minimum_mutation_rate, maximum_mutation_rate]``.
Larger :math:`\tau` widens the per-generation step in log-space, letting the population
explore more aggressively; smaller :math:`\tau` keeps each offspring close to its
parent's rate.

Population structure
--------------------

The population is (μ+λ):

- :attr:`population_size
  <daitum_configuration.algorithm_configuration.vns_algorithm.VariableNeighbourhoodSearch.population_size>`
  is **λ** — the total number of offspring per generation.
- :attr:`offspring_size
  <daitum_configuration.algorithm_configuration.vns_algorithm.VariableNeighbourhoodSearch.offspring_size>`
  is the offspring count per parent, so the number of parents is
  **μ = population_size / offspring_size**.
- :attr:`selection
  <daitum_configuration.algorithm_configuration.vns_algorithm.VariableNeighbourhoodSearch.selection>`
  chooses the μ parents each generation (same operator types as
  :class:`~daitum_configuration.GeneticAlgorithm`).

Example
-------

.. code-block:: python

    from daitum_configuration import (
        Selection,
        SelectionType,
        VariableNeighbourhoodSearch,
    )

    algorithm = VariableNeighbourhoodSearch(
        population_size=128,
        offspring_size=16,           # μ = 128 / 16 = 8 parents
        initial_mutation_rate=0.2,
        mutation_rate_tau=0.5,
        selection=Selection.selection(SelectionType.TOURNAMENT_SELECTION, pool_size=4),
    )

API reference
-------------

.. automodule:: daitum_configuration.algorithm_configuration.vns_algorithm
