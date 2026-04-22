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
Module for defining optimization algorithm configurations.

This module provides the base class and shared infrastructure for all optimization
algorithm implementations in the Configuration Generator. It includes common parameters,
validation logic, and serialization utilities that are inherited by specific algorithm
implementations.

Key Components：
    - ``Algorithm``: Abstract base class providing shared parameters and functionality
      for all optimization algorithms. Includes common settings like time limits,
      evaluation budgets, convergence criteria, and random seed configuration.

    - ``NamedValue``: Type alias representing values that can be either numeric expressions,
      parameters, or calculations that will be resolved at runtime.

    - Helper methods for creating quantitative and qualitative parameter dictionaries
      that follow the standardized configuration format.

**Serialization:**

Algorithm configurations can be serialized to JSON-compatible dictionaries using the
``to_dict()`` method. The resulting dictionary includes:

    - ``algorithmKey``: Unique identifier for the algorithm type
    - ``parameters``: Dictionary of algorithm parameters with type annotations
      (quantitative or qualitative)

Each parameter is wrapped with metadata indicating whether it's quantitative (numeric)
or qualitative (categorical), along with the actual value.

Notes：
    - All numeric parameters can accept either concrete values or ``NamedValue`` instances
      that will be resolved dynamically at runtime (e.g., based on problem dimensions)
    - Parameter validation is performed in ``__post_init__`` via the ``_validate()`` method
    - The module uses type unions (e.g., ``int | NamedValue``) requiring Python 3.10+
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any

from daitum_model import Calculation, Parameter

from daitum_configuration.algorithm_configuration.numeric_expression import NumericExpression

NamedValue = NumericExpression | Parameter | Calculation


# pylint: disable=too-many-arguments,too-many-positional-arguments,too-many-instance-attributes
# pylint: disable=too-many-branches
@dataclass
class Algorithm(ABC):
    """
    Abstract base class for optimization algorithm configurations.

    Provides common parameters and functionality for all optimization algorithms.
    This class should be inherited by specific algorithm implementations.

    Note:
        - Child classes should add algorithm-specific parameters via a 'config' attribute
          that will be included when exporting to dictionary format.
    """

    log_info: bool = False
    evaluations: int | NamedValue = 100000 * NumericExpression("NUM_VARIABLES")
    max_evaluations_without_improvement: int | NamedValue = 10000 * NumericExpression(
        "NUM_VARIABLES"
    )
    max_time_without_improvement: int | NamedValue = 300
    min_improvement: float | NamedValue = 0.000001
    max_restart_count: int | NamedValue = 0
    prng_seed: int | None = None
    time_limit: int | NamedValue = 60

    def __post_init__(self):
        """Runs validation for all common fields."""
        self._validate()

    def _validate(self):
        self._validate_eval_params()
        self._validate_time_params()

    def _validate_eval_params(self):
        if not isinstance(self.log_info, bool):
            raise TypeError("log_info must be bool")

        if not isinstance(self.evaluations, int | NamedValue):
            raise TypeError("evaluations must be int or NamedValue")
        if isinstance(self.evaluations, int) and self.evaluations < 1:
            raise ValueError("evaluations must not be less than 1")

        if not isinstance(self.max_evaluations_without_improvement, int | NamedValue):
            raise TypeError("max_evaluations_without_improvement must be int or NamedValue")
        if (
            isinstance(self.max_evaluations_without_improvement, int)
            and self.max_evaluations_without_improvement < 1
        ):
            raise ValueError("max_evaluations_without_improvement must not be less than 1")

        if not isinstance(self.min_improvement, float | NamedValue):
            raise TypeError("min_improvement must be float or NamedValue")
        if isinstance(self.min_improvement, float) and self.min_improvement < 0:
            raise ValueError("min_improvement must be non-negative")

        if not isinstance(self.max_restart_count, int | NamedValue):
            raise TypeError("max_restart_count must be int or NamedValue")
        if isinstance(self.max_restart_count, int) and self.max_restart_count < 0:
            raise ValueError("max_restart_count must be non-negative")

        if self.prng_seed:
            if not isinstance(self.prng_seed, int | NamedValue):
                raise TypeError("prng_seed must be int or NamedValue")

    def _validate_time_params(self):
        if not isinstance(self.max_time_without_improvement, int | NamedValue):
            raise TypeError("max_time_without_improvement must be int or NamedValue")
        if (
            isinstance(self.max_time_without_improvement, int)
            and self.max_time_without_improvement < 1
        ):
            raise ValueError("max_time_without_improvement must not be less than 1")

        if not isinstance(self.time_limit, int | NamedValue):
            raise TypeError("time_limit must be int or NamedValue")
        if isinstance(self.time_limit, int) and self.time_limit < 0:
            raise ValueError("time_limit must be non-negative")

    @abstractmethod
    def to_dict(self) -> dict[str, Any]:
        """
        Converts the algorithm configuration to a dictionary format.

        Returns:
            Dict[str, Any]: A dictionary with the algorithm key and its parameters.
        """

    @staticmethod
    def _create_quantitative(value: Any | None) -> dict[str, Any]:
        """
        Create a quantitative parameter dictionary.

        Args:
            value (Optional[Any]): The value to be converted into a quantitative dictionary.

        Returns:
            Dict[str, Any]: A dictionary representing a quantitative parameter.
        """
        if isinstance(value, bool):
            return {"@type": "quantitative", "value": value}
        if isinstance(value, Parameter | Calculation):
            return {"@type": "quantitative", "value": f"!!!{value.id}"}
        return {"@type": "quantitative", "value": str(value) if value is not None else None}

    @staticmethod
    def _create_qualitative(
        value: Any | None, parameters: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """
        Create a qualitative parameter dictionary.

        Args:
            value (Any): The qualitative value.
            parameters (Optional[Dict[str, Any]]): Additional parameters related to the
                qualitative value.

        Returns:
            Dict[str, Any]: A dictionary representing a qualitative parameter.
        """
        if isinstance(value, bool):
            return {
                "@type": "qualitative",
                "value": value,
                "parameters": parameters or {},
            }
        if isinstance(value, Parameter | Calculation):
            return {
                "@type": "quantitative",
                "value": f"!!!{value.id}",
                "parameters": parameters or {},
            }
        return {
            "@type": "qualitative",
            "value": str(value) if value is not None else None,
            "parameters": parameters or {},
        }
