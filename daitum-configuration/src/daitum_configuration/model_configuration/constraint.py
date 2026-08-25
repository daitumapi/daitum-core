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
from daitum_model.references import Reference
from daitum_model.serialisation import Buildable
from typeguard import typechecked

from daitum_configuration.model_configuration.priority import Priority


class ConstraintType(Enum):
    """Constraint operator.

    EQUALITY
        The expression must equal the bound.
    INEQUALITY
        The expression must lie within the lower/upper bounds.
    """

    EQUALITY = "equality"
    INEQUALITY = "inequality"


# pylint: disable=too-many-instance-attributes,too-many-arguments,too-many-positional-arguments
@typechecked
class ConstraintSpecification(Buildable):
    """The nested ``specification`` object of a :class:`Constraint`.

    A bound is emitted either as a literal (``lowerBound``/``upperBound``) or, when it is a
    model named value, as a bare-id reference (``lowerBoundReference``/``upperBoundReference``).
    All keys are always present (``null`` where unset), and ``@type`` is the constraint type.
    """

    _always_emit = (
        "lower_bound",
        "upper_bound",
        "lower_bound_reference",
        "upper_bound_reference",
    )

    def __init__(  # noqa: PLR0913, PLR0917
        self,
        constraint_type: ConstraintType,
        lower: "float | Calculation | Parameter | None",
        upper: "float | Calculation | Parameter | None",
        lower_inclusive: bool,
        upper_inclusive: bool,
        priority: Priority,
        hard_score: int,
    ):
        self._type_name = constraint_type.value
        self.lower_bound = lower if isinstance(lower, float) else None
        self.upper_bound = upper if isinstance(upper, float) else None
        self.lower_bound_reference = self._reference(lower)
        self.upper_bound_reference = self._reference(upper)
        self.lower_bound_inclusive = lower_inclusive
        self.upper_bound_inclusive = upper_inclusive
        self.priority = priority
        self.hard_score = hard_score

    @staticmethod
    def _reference(bound: "float | Calculation | Parameter | None") -> str | None:
        if bound is None or isinstance(bound, float):
            return None
        return bound.to_string()


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
        """Serialise to a dict; bound/reference splitting is delegated to the spec object."""
        specification = ConstraintSpecification(
            self._constraint_type,
            self._lower_bound,
            self._upper_bound,
            self._lower_bound_inclusive,
            self._upper_bound_inclusive,
            self._priority,
            self._hard_score,
        )
        return {
            "cellReference": Reference(self._constraint).build(),
            "trackingId": self._tracking_id,
            "specification": specification.build(),
            "name": self._name,
        }
