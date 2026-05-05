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

""":class:`StochasticConfiguration` for multi-trial stochastic optimisation."""

from enum import Enum

from typeguard import typechecked

from daitum_configuration._buildable import Buildable


class MetricCombinationRule(Enum):
    """Rule for combining a metric across multiple stochastic trials."""

    MIN = "MIN"
    MAX = "MAX"
    MEAN = "MEAN"
    PVALUE_MAX = "PVALUE_MAX"
    PVALUE_MIN = "PVALUE_MIN"


# pylint: disable=too-many-arguments,too-many-positional-arguments,too-many-instance-attributes
# pylint: disable=too-many-branches,too-few-public-methods
@typechecked
class StochasticConfiguration(Buildable):
    """
    Configures the solver to run multiple evaluations per candidate solution.

    Args:
        runs: Number of evaluations per candidate.
        p: Confidence level used by the p-value-based combination rules.
        disable_evaluator_caching: When True, force fresh evaluation each run
            instead of using the evaluator's cache.
    """

    def __init__(self, runs: int, p: float, disable_evaluator_caching: bool):
        self.runs = runs
        self.p = p
        self.disable_evaluator_caching = disable_evaluator_caching
        self.metric_rules: dict[str, MetricCombinationRule] = {}

    def add_metric_rule(
        self, key: str, metric_rule: MetricCombinationRule
    ) -> "StochasticConfiguration":
        """Register a per-metric :class:`MetricCombinationRule`."""
        self.metric_rules[key] = metric_rule
        return self
