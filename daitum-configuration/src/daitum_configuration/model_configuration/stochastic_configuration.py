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

"""
This module defines configuration tools for handling stochastic optimization runs
and metric evaluation strategies. It includes support for combining results from
multiple stochastic trials using various rules, such as minimum, maximum, mean,
and p-value-based approaches.

Classes:
    - MetricCombinationRule (Enum): Defines how to aggregate results from multiple runs.
    - StochasticConfiguration: Stores and manages configuration for stochastic optimization.
"""

from enum import Enum

from typeguard import typechecked


class MetricCombinationRule(Enum):
    """
    Rules for combining metrics between multiple trials of stochastic optimisation.
    """

    MIN = "MIN"
    """Use the lowest value of all the trials."""

    MAX = "MAX"
    """Use the highest value of all the trials."""

    MEAN = "MEAN"
    """Use the mean value of all the trials. This is the default if not specified."""

    PVALUE_MAX = "PVALUE_MAX"
    """
    Use the p-value to determine the value returned (i.e. same way as objective value),
    where higher values are considered better.
    """

    PVALUE_MIN = "PVALUE_MIN"
    """
    Use the p-value to determine the value returned (i.e. same way as objective value),
    where lower values are considered better.
    """


# pylint: disable=too-many-arguments,too-many-positional-arguments,too-many-instance-attributes
# pylint: disable=too-many-branches,too-few-public-methods
@typechecked
class StochasticConfiguration:
    """
    Configuration class for stochastic optimization that handles multiple evaluation
    runs and metric combination strategies.
    """

    def __init__(self, runs: int, p: float, disable_evaluator_caching: bool):
        """
        Initializes the StochasticConfiguration with the given parameters.

        Args:
            runs (int): Number of times each stochastic trial is to be run.
            p (float): P-value threshold used when applying p-value based metric rules.
            disable_evaluator_caching (bool): Flag to disable caching in the evaluator.
        """
        self._runs = runs
        self._p = p
        self._disable_evaluator_caching = disable_evaluator_caching
        self._metric_rules: dict[str, MetricCombinationRule] = {}

    def add_metric_rule(self, key: str, metric_rule: MetricCombinationRule):
        """
        Adds a metric combination rule for a specific metric key.

        Args:
            key (str): The name of the metric for which to apply the rule.
            metric_rule (MetricCombinationRule): The rule used to combine multiple trials for
                this metric.
        """
        self._metric_rules[key] = metric_rule

    def to_dict(self):
        """
        Serializes the stochastic configuration to a dictionary representation.

        Returns:
            A dictionary containing the runs, p, disable_evaluator_caching
            and metric_rules.
        """
        return {
            "runs": self._runs,
            "p": self._p,
            "disable_evaluator_caching": self._disable_evaluator_caching,
            "metric_rules": self._metric_rules,
        }
