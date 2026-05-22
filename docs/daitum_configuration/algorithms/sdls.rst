Steepest Dynamic Local Search
=============================

Steepest Descent local search with a dynamic step-size schedule. Each
iteration perturbs every decision variable by ±``step_size`` and accepts
the best neighbour; when an iteration finds no improvement the step
shrinks toward ``..._lowest_step`` by ``..._step_change`` until the lowest
step has been reached.

Integer-typed and real-typed variables use independent step controls
(``integer_*`` and ``decimal_*``). :attr:`~daitum_configuration.SteepestDynamicLocalSearch.allow_neutral_walks`
permits accepting equal-objective neighbours, letting the search drift
across plateaus.

.. automodule:: daitum_configuration.algorithm_configuration.steepest_dynamic_local_search
