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

""":class:`Objective` — a quantity to optimise within a :class:`ModelConfiguration`."""

from typing import Any

from daitum_model import Calculation, DataType
from typeguard import typechecked

from daitum_configuration._buildable import Buildable
from daitum_configuration.model_configuration.priority import Priority


# pylint: disable=too-many-arguments,too-many-positional-arguments,too-many-instance-attributes
# pylint: disable=too-many-branches,too-few-public-methods
@typechecked
class Objective(Buildable):
    """
    A numeric quantity the solver should maximise or minimise.

    Construct via :meth:`ModelConfiguration.add_objective`. The wrapped
    :class:`~daitum_model.Calculation` must be ``INTEGER`` or ``DECIMAL``.
    """

    _tracking_counter = 0

    def __init__(
        self,
        objective: Calculation,
        maximise: bool = False,
        priority: Priority = Priority.HIGH,
        weight: float = 1.0,
        name: str | None = None,
    ):
        objective_datatype = objective.to_data_type()
        if objective_datatype not in {DataType.INTEGER, DataType.DECIMAL}:
            raise ValueError(f"{objective_datatype} is not integer or decimal")

        self._objective = objective
        self._tracking_id = Objective._tracking_counter
        Objective._tracking_counter += 1
        self._maximise = maximise
        self._priority = priority
        self._weight = weight
        self._name = name

    @property
    def name(self) -> str | None:
        """Optional display name for this objective."""
        return self._name

    def build(self) -> dict[str, Any]:
        """Serialise to a JSON-compatible dict."""
        return {
            "cellReference": f"!!!{self._objective.to_string()}",
            "trackingId": self._tracking_id,
            "maximise": self._maximise,
            "priority": self._priority.value,
            "weight": self._weight,
            "name": self._name,
        }
