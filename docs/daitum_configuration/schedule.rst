Schedule
========

A :class:`~daitum_configuration.ScheduleConfiguration` is the execution plan
for a multi-phase optimisation. It pairs:

- a named map of :doc:`Algorithms <algorithms/index>`, and
- a tree of :class:`~daitum_configuration.StepConfiguration` nodes that
  reference those algorithms by key.

Attach a built schedule to a
:class:`~daitum_configuration.ConfigurationBuilder` with
:meth:`~daitum_configuration.ConfigurationBuilder.set_schedule_configuration`.
This is mutually exclusive with
:meth:`~daitum_configuration.ConfigurationBuilder.set_algorithm`, which is
shorthand for a one-step schedule.

Step types
----------

A :class:`~daitum_configuration.StepType` controls how a node executes:

- ``SINGLE`` — leaf node; invokes the algorithm at
  ``algorithm_config_key`` against the current best solution.
- ``SEQUENCE`` — container; runs children one after another, each seeded by
  the previous step's result.
- ``PARALLEL`` — container; runs children concurrently from the same seed
  and merges their results.

Containers may nest. A schedule with one ``SINGLE`` root is the simplest
case::

    from daitum_configuration import (
        GeneticAlgorithm,
        ScheduleConfiguration,
        StepConfiguration,
        StepType,
    )

    root = StepConfiguration(StepType.SINGLE, algorithm_config_key="ga")
    schedule = ScheduleConfiguration(root).add_algorithm("ga", GeneticAlgorithm())

.. _subproblem-features:

Subproblem and execution features
---------------------------------

Each :class:`~daitum_configuration.StepConfiguration` carries optional
fields that scope or control its execution. All are configured by chained
``add_*`` / ``set_*`` methods after construction. JSON keys are flattened
onto the step.

Tag-based filtering — ``add_included_tag``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Restrict the step to a subset of decision variables. A variable is included
when **every** tag attached to it appears in the step's
``includedTags``; variables with no tags are always included. Excluded
variables are held at their seed values.

Tags are sourced from the model via
:meth:`DecisionVariable.set_tag_source
<daitum_configuration.model_configuration.decision_variable.DecisionVariable.set_tag_source>`.

Parameter overrides — ``add_override_parameter``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Set model parameter values for the duration of this step. The model is
fully re-evaluated each evaluation, so override targets need not lie on
decision-dependent paths. Step-scoped overrides take precedence over
schedule-wide
:meth:`~daitum_configuration.ScheduleConfiguration.add_global_parameter`
entries.

Dynamic splitting — ``set_split_values_key``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Split the step into independent subproblems by model value.
``split_values_key`` is a model reference returning a comma-separated string
(for example ``"North,South,East,West"``). One subproblem is run per value,
with the value appended to ``includedTags`` so each subproblem optimises a
disjoint slice of variables. Subproblem variable sets must not overlap.

Conditional skipping — ``set_disabled_key``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Skip the step based on a model value. ``disabled_key`` is a model reference;
when its serialised value equals ``"true"`` the step is replaced with an
empty pass-through and the current best solution flows through unchanged.

Dynamic range recalculation — ``set_recalculate_ranges``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Narrow decision-variable bounds from current model state. The platform
reads each variable's range fields against the current best solution and
any applied overrides, then builds the subproblem with the resulting
bounds. New bounds must be a subset of the original; empty ranges exclude
the variable; single-value ranges fix it.

Deferred construction — ``set_deferred``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Delay step construction until just before execution. Required when any of
the above depends on values that earlier steps must first produce. When
deferred, the current best solution is passed in as the seed for evaluating
the model references.

Complete example
----------------

A three-phase optimisation that:

1. optimises each day of the week as an independent subproblem,
2. follows with a full optimisation using ranges recalculated from the
   result of phase 1, and
3. ends with an optional local-search refinement that may be skipped via a
   model flag.

.. code-block:: python

    from daitum_configuration import (
        GeneticAlgorithm,
        ScheduleConfiguration,
        StepConfiguration,
        StepType,
        VariableNeighbourhoodSearch,
    )

    per_day = (
        StepConfiguration(StepType.SINGLE, algorithm_config_key="ga")
        .set_split_values_key("DayOfWeek")
        .add_included_tag("PerDay")
        .add_override_parameter("dailyOptimisation", "true")
    )

    full_refit = (
        StepConfiguration(StepType.SINGLE, algorithm_config_key="ga")
        .set_deferred(True)
        .set_recalculate_ranges(True)
    )

    refinement = (
        StepConfiguration(StepType.SINGLE, algorithm_config_key="ls")
        .set_disabled_key("skipRefinement")
    )

    root = StepConfiguration(StepType.SEQUENCE)
    root.add_step(per_day).add_step(full_refit).add_step(refinement)

    schedule = (
        ScheduleConfiguration(root)
        .add_algorithm("ga", GeneticAlgorithm())
        .add_algorithm("ls", VariableNeighbourhoodSearch())
    )

JSON field reference
--------------------

Each ``StepConfiguration`` emits a flat object — none of the subproblem
fields nest under a sub-object. ``None``-valued fields are omitted.

.. list-table::
   :widths: 24 14 12 50
   :header-rows: 1

   * - JSON key
     - Type
     - Default
     - Notes
   * - ``type``
     - ``StepType``
     - required
     - ``SINGLE``, ``SEQUENCE``, or ``PARALLEL``.
   * - ``algorithmConfigKey``
     - string
     - —
     - Required for ``SINGLE``; forbidden for containers.
   * - ``steps``
     - list
     - —
     - Populated for containers via :meth:`add_step
       <daitum_configuration.StepConfiguration.add_step>`; absent for
       ``SINGLE``.
   * - ``includedTags``
     - list[string]
     - omitted
     - Tag whitelist; see :meth:`add_included_tag
       <daitum_configuration.StepConfiguration.add_included_tag>`.
   * - ``overrideParameters``
     - map[string, string]
     - omitted
     - Step-scoped parameter overrides.
   * - ``splitValuesKey``
     - string
     - omitted
     - Model reference for splitting into separable subproblems.
   * - ``disabledKey``
     - string
     - omitted
     - Model reference; step is skipped when its value is ``"true"``.
   * - ``recalculateRanges``
     - bool
     - ``false``
     - Recompute variable bounds from current model state.
   * - ``deferred``
     - bool
     - ``false``
     - Delay construction until just before execution.

API reference
-------------

.. automodule:: daitum_configuration.schedule_configuration.schedule_configuration

.. automodule:: daitum_configuration.schedule_configuration.step_configuration

.. automodule:: daitum_configuration.schedule_configuration.step_type
