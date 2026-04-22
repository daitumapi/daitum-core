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
This module defines the `Constraint` data model, which encapsulates the concept of a
constraint for use in optimisation. It provides a structured way to represent constraint
metadata and specification logic, and includes a utility method to convert the model
into a dictionary format.

Examples:

.. code-block:: python

    constraint = Constraint("some_constraint")
    constraint_dict = constraint.to_dict()

Classes:
    - Constraint: A dataclass that stores constraint information and provides a method to
      serialise it into a standardised dictionary format.
"""

from enum import Enum

from daitum_model import Calculation, DataType, Parameter
from typeguard import typechecked

from daitum_configuration.model_configuration.priority import Priority


class ConstraintType(Enum):
    """
    Enum representing the type of constraint.
    """

    EQUALITY = "equality"
    INEQUALITY = "inequality"


# pylint: disable=too-many-instance-attributes
# pylint: disable=too-many-branches,too-few-public-methods
@typechecked
class Constraint:
    """
    Represents a constraint applied to an optimisation problem, encapsulating its logical
    specification, bounds, inclusivity, priority, and penalty score.

    This class supports both equality and inequality constraints. It also provides serialisation
    into a standardised dictionary format.
    """

    # Class-level static variable for tracking ID
    _tracking_counter = 0

    def __init__(
        self,
        constraint: Calculation,
    ):
        """
        Initialises the Constraint instance.

        Args:
            constraint (Calculation): A `Calculation` representing the constraint target.
        """

        constraint_datatype = constraint.to_data_type()
        if constraint_datatype not in {DataType.INTEGER, DataType.DECIMAL}:
            raise ValueError(f"{constraint_datatype} is not integer or decimal")

        self._constraint = constraint
        self._tracking_id = Constraint._tracking_counter
        Constraint._tracking_counter += 1
        self._constraint_type: ConstraintType = ConstraintType.INEQUALITY
        self._lower_bound: float | None | Calculation | Parameter = None
        self._upper_bound: float | Calculation | Parameter = 0.0
        self._lower_bound_inclusive: bool = True
        self._upper_bound_inclusive: bool = True
        self._priority: Priority = Priority.MEDIUM
        self._hard_score: int = 0
        self._name: str | None = None

    def set_type(self, constraint_type: ConstraintType) -> "Constraint":
        """
        Sets the type of the constraint.

        Args:
            constraint_type (ConstraintType): The type of the constraint.

        Returns:
            Constraint: self, for method chaining.
        """
        self._constraint_type = constraint_type
        return self

    def set_lower_bound(self, lower_bound: float | None | Calculation | Parameter) -> "Constraint":
        """
        Sets the lower bound value or reference for the constraint.

        Args:
            lower_bound (float | None | Calculation | Parameter): The lower bound.

        Returns:
            Constraint: self, for method chaining.
        """
        self._lower_bound = lower_bound
        return self

    def set_upper_bound(self, upper_bound: float | Calculation | Parameter) -> "Constraint":
        """
        Sets the upper bound value or reference for the constraint.

        Args:
            upper_bound (float | Calculation | Parameter): The upper bound.

        Returns:
            Constraint: self, for method chaining.
        """
        self._upper_bound = upper_bound
        return self

    def set_lower_bound_inclusive(self, lower_bound_inclusive: bool) -> "Constraint":
        """
        Sets whether the lower bound is inclusive.

        Args:
            lower_bound_inclusive (bool): If True, the lower bound is inclusive.

        Returns:
            Constraint: self, for method chaining.
        """
        self._lower_bound_inclusive = lower_bound_inclusive
        return self

    def set_upper_bound_inclusive(self, upper_bound_inclusive: bool) -> "Constraint":
        """
        Sets whether the upper bound is inclusive.

        Args:
            upper_bound_inclusive (bool): If True, the upper bound is inclusive.

        Returns:
            Constraint: self, for method chaining.
        """
        self._upper_bound_inclusive = upper_bound_inclusive
        return self

    def set_priority(self, priority: Priority) -> "Constraint":
        """
        Sets the priority level of the constraint.

        Args:
            priority (Priority): The priority level.

        Returns:
            Constraint: self, for method chaining.
        """
        self._priority = priority
        return self

    def set_hard_score(self, hard_score: int) -> "Constraint":
        """
        Sets the penalty score for violating this constraint.

        Args:
            hard_score (int): The penalty score.

        Returns:
            Constraint: self, for method chaining.
        """
        self._hard_score = hard_score
        return self

    def set_name(self, name: str) -> "Constraint":
        """
        Sets an optional name for the constraint.

        Args:
            name (str): The name for the constraint.

        Returns:
            Constraint: self, for method chaining.
        """
        self._name = name
        return self

    def to_dict(self) -> dict:
        """
        Serialises the instance into a dictionary representation for optimisation.

        Returns:
            dict: A dictionary formatted for use in optimisation.
        """

        lower_bound_string: str | None = None
        upper_bound_string: str | None = None

        if self._lower_bound is not None:
            if not isinstance(self._lower_bound, float):
                lower_bound_string = self._lower_bound.to_string()
        if not isinstance(self._upper_bound, float):
            upper_bound_string = self._upper_bound.to_string()

        return {
            "cellReference": f"!!!{self._constraint.to_string()}",
            "trackingId": self._tracking_id,
            "specification": {
                "@type": self._constraint_type.value,
                "lowerBound": self._lower_bound,
                "upperBound": self._upper_bound,
                "lowerBoundReference": lower_bound_string,
                "upperBoundReference": upper_bound_string,
                "lowerBoundInclusive": self._lower_bound_inclusive,
                "upperBoundInclusive": self._upper_bound_inclusive,
                "priority": self._priority.value,
                "hardScore": self._hard_score,
            },
            "name": self._name,
        }
