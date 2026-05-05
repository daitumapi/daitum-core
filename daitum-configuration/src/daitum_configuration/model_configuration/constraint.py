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

""":class:`Constraint` — a bound on a numeric calculation that the solver must satisfy."""

from enum import Enum
from typing import Any

from daitum_model import Calculation, DataType, Parameter
from typeguard import typechecked

from daitum_configuration._buildable import Buildable
from daitum_configuration.model_configuration.priority import Priority


class ConstraintType(Enum):
    """Constraint operator.

    Values:
        EQUALITY: The expression must equal the bound.
        INEQUALITY: The expression must lie within the lower/upper bounds.
    """

    EQUALITY = "equality"
    INEQUALITY = "inequality"


# pylint: disable=too-many-instance-attributes
# pylint: disable=too-many-branches,too-few-public-methods
@typechecked
class Constraint(Buildable):
    """
    A bound on a numeric :class:`~daitum_model.Calculation` that the solver must respect.

    Construct via :meth:`ModelConfiguration.add_constraint`; configure via the
    chained ``set_*`` methods. Default type is :attr:`ConstraintType.INEQUALITY`
    with ``upper_bound = 0`` and inclusive bounds.
    """

    _tracking_counter = 0

    def __init__(
        self,
        constraint: Calculation,
    ):
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
        """Set the constraint type (equality or inequality)."""
        self._constraint_type = constraint_type
        return self

    def set_lower_bound(self, lower_bound: float | Calculation | Parameter) -> "Constraint":
        """Set the lower bound. Pass a literal, :class:`~daitum_model.Calculation`, or
        :class:`~daitum_model.Parameter`."""
        self._lower_bound = lower_bound
        return self

    def set_upper_bound(self, upper_bound: float | Calculation | Parameter) -> "Constraint":
        """Set the upper bound. See :meth:`set_lower_bound` for accepted types."""
        self._upper_bound = upper_bound
        return self

    def set_lower_bound_inclusive(self, lower_bound_inclusive: bool) -> "Constraint":
        """Toggle inclusive/exclusive comparison on the lower bound."""
        self._lower_bound_inclusive = lower_bound_inclusive
        return self

    def set_upper_bound_inclusive(self, upper_bound_inclusive: bool) -> "Constraint":
        """Toggle inclusive/exclusive comparison on the upper bound."""
        self._upper_bound_inclusive = upper_bound_inclusive
        return self

    def set_priority(self, priority: Priority) -> "Constraint":
        """Set the constraint :class:`Priority`."""
        self._priority = priority
        return self

    def set_hard_score(self, hard_score: int) -> "Constraint":
        """Set the per-violation penalty applied to the solver's hard score."""
        self._hard_score = hard_score
        return self

    def set_name(self, name: str) -> "Constraint":
        """Set an optional display name."""
        self._name = name
        return self

    def build(self) -> dict[str, Any]:
        """Serialise to a JSON-compatible dict."""
        lower_bound_string: str | None = None
        upper_bound_string: str | None = None

        if self._lower_bound is not None and not isinstance(self._lower_bound, float):
            lower_bound_string = self._lower_bound.to_string()
        if self._upper_bound is not None and not isinstance(self._upper_bound, float):
            upper_bound_string = self._upper_bound.to_string()

        return {
            "cellReference": f"!!!{self._constraint.to_string()}",
            "trackingId": self._tracking_id,
            "specification": {
                "@type": self._constraint_type.value,
                "lowerBound": self._lower_bound if isinstance(self._lower_bound, float) else None,
                "upperBound": self._upper_bound if isinstance(self._upper_bound, float) else None,
                "lowerBoundReference": lower_bound_string,
                "upperBoundReference": upper_bound_string,
                "lowerBoundInclusive": self._lower_bound_inclusive,
                "upperBoundInclusive": self._upper_bound_inclusive,
                "priority": self._priority.value,
                "hardScore": self._hard_score,
            },
            "name": self._name,
        }
