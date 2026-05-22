# Copyright 2026 Daitum
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

""":class:`StepConfiguration` — one node in a :class:`ScheduleConfiguration` tree."""

from __future__ import annotations

from typeguard import typechecked

from daitum_configuration._buildable import Buildable
from daitum_configuration.schedule_configuration.step_type import StepType


# pylint: disable=too-few-public-methods
@typechecked
class StepConfiguration(Buildable):
    """
    One node in a :class:`ScheduleConfiguration` execution tree.

    A step is either a **leaf** — :attr:`StepType.SINGLE` referencing an
    algorithm by key — or a **container** — :attr:`StepType.PARALLEL` or
    :attr:`StepType.SEQUENCE` — holding child steps. Containers may nest
    arbitrarily.

    Subproblem and execution behaviour are configured via chained ``add_*`` /
    ``set_*`` methods after construction. Each maps to one
    :ref:`subproblem feature <subproblem-features>`:

    * :meth:`add_included_tag` — restrict the step to a subset of decision
      variables by tag (see :meth:`DecisionVariable.set_tag_source
      <daitum_configuration.model_configuration.decision_variable.DecisionVariable.set_tag_source>`).
    * :meth:`add_override_parameter` — set model parameter values for the
      duration of this step.
    * :meth:`set_split_values_key` — split the step into independent parallel
      subproblems based on a comma-separated model value.
    * :meth:`set_recalculate_ranges` — narrow decision-variable bounds based
      on current model state before executing this step.
    * :meth:`set_disabled_key` — skip the step when a model value equals
      ``"true"``.
    * :meth:`set_deferred` — delay step construction until just before
      execution; required when the configuration above depends on results of
      earlier steps.

    All six fields and ``add_step`` return ``self`` for fluent chaining.

    Args:
        step_type: :class:`StepType` of this node.
        algorithm_config_key: Algorithm key resolved against
            :meth:`ScheduleConfiguration.add_algorithm`. Required for
            ``SINGLE``; forbidden for container types. Container children
            are appended via :meth:`add_step`.

    Raises:
        ValueError: If ``algorithm_config_key`` does not match ``step_type``.

    Example::

        from daitum_configuration import StepConfiguration, StepType

        # A SEQUENCE: per-day separable optimisation, then a full
        # optimisation with narrowed ranges, then an optional refinement.
        root = StepConfiguration(StepType.SEQUENCE)
        root.add_step(
            StepConfiguration(StepType.SINGLE, algorithm_config_key="ga")
            .set_split_values_key("DayOfWeek")
            .add_included_tag("PerDay")
            .add_override_parameter("dailyOptimisation", "true")
        )
        root.add_step(
            StepConfiguration(StepType.SINGLE, algorithm_config_key="ga")
            .set_deferred(True)
            .set_recalculate_ranges(True)
        )
        root.add_step(
            StepConfiguration(StepType.SINGLE, algorithm_config_key="ls")
            .set_disabled_key("skipRefinement")
        )
    """

    def __init__(
        self,
        step_type: StepType,
        algorithm_config_key: str | None = None,
    ):
        if step_type == StepType.SINGLE:
            if algorithm_config_key is None:
                raise ValueError("algorithm_config_key is required for StepType.SINGLE.")
        elif algorithm_config_key is not None:
            raise ValueError(
                "algorithm_config_key is incompatible with StepType.PARALLEL "
                "or StepType.SEQUENCE; append child steps with add_step instead."
            )

        self.step_performance_ratios: list[float] | None = None
        self.parameter_overrides: dict[str, str] | None = None

        self.type = step_type
        self.steps: list[StepConfiguration] | None = None
        self.algorithm_config_key = algorithm_config_key

        self.included_tags: list[str] | None = None
        self.override_parameters: dict[str, str] | None = None
        self.split_values_key: str | None = None
        self.recalculate_ranges: bool = False
        self.disabled_key: str | None = None
        self.deferred: bool = False

    def add_step(self, step_configuration: StepConfiguration) -> StepConfiguration:
        """Append a child step to this container.

        Raises:
            ValueError: If this node is :attr:`StepType.SINGLE`.
        """
        if self.type == StepType.SINGLE:
            raise ValueError("Adding step is incompatible with the StepType.SINGLE.")
        if self.steps is None:
            self.steps = []
        self.steps.append(step_configuration)
        return self

    def add_included_tag(self, tag: str) -> StepConfiguration:
        """Append a tag to the variable filter for this step.

        Only decision variables whose tags are **all** in :attr:`included_tags`
        are optimised; variables with no tags are always included. Excluded
        variables are held at their seed values. Adding the same ``tag``
        twice is a no-op.

        Variable tags are sourced via
        :meth:`DecisionVariable.set_tag_source
        <daitum_configuration.model_configuration.decision_variable.DecisionVariable.set_tag_source>`.
        """
        if self.included_tags is None:
            self.included_tags = []
        if tag not in self.included_tags:
            self.included_tags.append(tag)
        return self

    def add_override_parameter(self, key: str, value: str) -> StepConfiguration:
        """Add a model parameter override applied during this step.

        ``key`` is a parameter name and ``value`` is a serialised model value.
        Overrides are applied before each evaluation in this step; the model
        is fully re-evaluated, so override targets need not lie on
        decision-dependent paths. Adding the same ``key`` twice replaces the
        previous value. Step-scoped overrides take precedence over
        :meth:`ScheduleConfiguration.add_global_parameter
        <daitum_configuration.schedule_configuration.schedule_configuration.ScheduleConfiguration.add_global_parameter>`.
        """
        if self.override_parameters is None:
            self.override_parameters = {}
        self.override_parameters[key] = value
        return self

    def set_split_values_key(self, split_values_key: str) -> StepConfiguration:
        """Split this step into independent subproblems by model value.

        ``split_values_key`` is a model reference returning a comma-separated
        string (for example ``"North,South,East,West"``). One subproblem is
        run per value, with the value appended to :attr:`included_tags` so
        each subproblem optimises a disjoint slice of decision variables.
        Subproblem variable sets must not overlap.
        """
        self.split_values_key = split_values_key
        return self

    def set_recalculate_ranges(self, recalculate_ranges: bool) -> StepConfiguration:
        """Narrow decision-variable bounds from current model state.

        When ``True``, the platform reads each variable's range fields against
        the current best solution and any applied parameter overrides, then
        builds the subproblem with the resulting bounds. The new bounds must
        be a subset of the original. Variables with empty new ranges are
        excluded; single-value ranges are fixed.

        Commonly combined with :meth:`set_deferred` so the recalculation
        happens after earlier steps have shaped the current best solution.
        """
        self.recalculate_ranges = recalculate_ranges
        return self

    def set_disabled_key(self, disabled_key: str) -> StepConfiguration:
        """Conditionally skip this step based on a model value.

        ``disabled_key`` is a model reference; when its serialised value
        equals ``"true"`` the step is replaced with an empty pass-through and
        the current best solution flows through unchanged.
        """
        self.disabled_key = disabled_key
        return self

    def set_deferred(self, deferred: bool) -> StepConfiguration:
        """Delay step construction until just before execution.

        Required when any of :meth:`add_included_tag`,
        :meth:`add_override_parameter`, :meth:`set_split_values_key`,
        :meth:`set_recalculate_ranges`, or :meth:`set_disabled_key` depends
        on results produced by earlier steps. When deferred, the current best
        solution is passed in as the seed for evaluating those model
        references.
        """
        self.deferred = deferred
        return self
