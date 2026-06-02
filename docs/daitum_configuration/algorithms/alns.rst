Adaptive Large Neighbourhood Search
===================================

Adaptive Large Neighbourhood Search (ALNS; Ropke & Pisinger, 2006) maintains a
single incumbent solution and, each iteration, generates one or more candidate
solutions by applying a *destroy* operator followed by a *repair* operator.
Operators are drawn from user-supplied pools by weighted random sampling, and
their weights are updated online so that operators that recently produced good
moves are picked more often.

The destroy/repair operator pools and the solution representation are defined
inside the user's external model (see the platform ``ALNSExternalModel``
interface); only the algorithm-level controls are configured here.

Iteration cycle
---------------

Each iteration:

1. Sample :attr:`candidates_per_iteration
   <daitum_configuration.algorithm_configuration.alns_algorithm.AdaptiveLargeNeighbourhoodSearch.candidates_per_iteration>`
   destroy operators and the same number of repair operators by weighted
   random selection.
2. Apply each destroy/repair pair to a copy of the incumbent to produce ``k``
   candidate solutions.
3. Evaluate the candidates (in parallel when ``k > 1``).
4. Decide whether the best candidate replaces the incumbent via the configured
   :attr:`acceptance_criterion
   <daitum_configuration.algorithm_configuration.alns_algorithm.AdaptiveLargeNeighbourhoodSearch.acceptance_criterion>`.
5. Reward the operator pairs that produced this iteration's candidates.
6. Every :attr:`segment_length
   <daitum_configuration.algorithm_configuration.alns_algorithm.AdaptiveLargeNeighbourhoodSearch.segment_length>`
   iterations, decay all operator weights by :attr:`decay_factor
   <daitum_configuration.algorithm_configuration.alns_algorithm.AdaptiveLargeNeighbourhoodSearch.decay_factor>`.

Operator reward schedule
------------------------

Each iteration's operator pairs are rewarded by tier:

- :attr:`new_best_reward
  <daitum_configuration.algorithm_configuration.alns_algorithm.AdaptiveLargeNeighbourhoodSearch.new_best_reward>`
  (:math:`\sigma_1`) — produced a new global best.
- :attr:`improving_reward
  <daitum_configuration.algorithm_configuration.alns_algorithm.AdaptiveLargeNeighbourhoodSearch.improving_reward>`
  (:math:`\sigma_2`) — improved on the current incumbent but did not become a
  new global best.
- :attr:`accepted_reward
  <daitum_configuration.algorithm_configuration.alns_algorithm.AdaptiveLargeNeighbourhoodSearch.accepted_reward>`
  (:math:`\sigma_3`) — did not improve but was accepted by the acceptance
  criterion.

Weights are then decayed at the end of each segment:

.. math::

    w_{t+1} = \rho \cdot w_t

where :math:`\rho` is :attr:`decay_factor
<daitum_configuration.algorithm_configuration.alns_algorithm.AdaptiveLargeNeighbourhoodSearch.decay_factor>`.

Soft restart on stagnation
--------------------------

:attr:`stagnation_limit
<daitum_configuration.algorithm_configuration.alns_algorithm.AdaptiveLargeNeighbourhoodSearch.stagnation_limit>`
sets the number of consecutive iterations without a new global best before the
algorithm triggers a soft restart on the incumbent. The default of ``0``
disables the soft restart; any non-zero value requires the external model to
implement a ``perturb()`` method (called to displace the incumbent without
losing the recorded global best).

Acceptance criteria
-------------------

The :class:`AcceptanceCriterion
<daitum_configuration.algorithm_configuration.alns_algorithm.AcceptanceCriterion>`
controls whether a candidate replaces the incumbent. Two strategies are built
in:

- **Simulated Annealing** — accepts improving moves and probabilistically
  accepts worsening moves based on a geometric temperature schedule. Configure
  via :meth:`AcceptanceCriterion.simulated_annealing
  <daitum_configuration.algorithm_configuration.alns_algorithm.AcceptanceCriterion.simulated_annealing>`
  with ``initial_temperature`` and ``cooling_rate`` (applied each iteration).
- **Greedy** — only accepts improving (or equal) moves. Configure via
  :meth:`AcceptanceCriterion.greedy
  <daitum_configuration.algorithm_configuration.alns_algorithm.AcceptanceCriterion.greedy>`.

Example
-------

.. code-block:: python

    from daitum_configuration import (
        AcceptanceCriterion,
        AdaptiveLargeNeighbourhoodSearch,
    )

    algorithm = AdaptiveLargeNeighbourhoodSearch(
        evaluations=5000,
        candidates_per_iteration=4,
        segment_length=100,
        decay_factor=0.8,
        acceptance_criterion=AcceptanceCriterion.simulated_annealing(
            initial_temperature=100.0,
            cooling_rate=0.9998,
        ),
    )

API reference
-------------

.. automodule:: daitum_configuration.algorithm_configuration.alns_algorithm
