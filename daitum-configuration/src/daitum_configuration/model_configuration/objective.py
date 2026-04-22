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
This module defines the `Objective` data model, used to represent an optimization objective.
The model includes a utility to serialize the objective into a structured dictionary format.

Features:
    - Automatically assigns a unique tracking ID to each objective using a static counter.
    - Validates input to ensure the objective reference is a string.
    - Includes metadata such as priority, weight, and maximization flag.

Examples:

.. code-block:: python

    obj = Objective("EXCESS USAGE")
    obj_dict = obj.to_dict()

Classes:
    - Objective: A class representing an optimization objective with serialization support.
"""

from daitum_model import Calculation, DataType
from typeguard import typechecked

from daitum_configuration.model_configuration.priority import Priority


# pylint: disable=too-many-arguments,too-many-positional-arguments,too-many-instance-attributes
# pylint: disable=too-many-branches,too-few-public-methods
@typechecked
class Objective:
    """
    Represents an optimization objective, storing its reference and providing
    a method to serialize it into a dictionary format for use in optimization systems.
    """

    # Class-level static variable for tracking ID
    _tracking_counter = 0

    def __init__(
        self,
        objective: Calculation,
        maximise: bool = False,
        priority: Priority = Priority.HIGH,
        weight: float = 1.0,
        name: str | None = None,
    ):
        """
        Initializes the Objective instance.

        Args:
            objective (Calculation): A `Calculation` object representing the optimization
                target.
            maximise (bool): Whether the objective should be maximised. Defaults to
                False (minimize).
            priority (Priority): The priority level of the objective. Defaults to
                Priority.HIGH.
            weight (float): The relative importance (weight) of the objective. Defaults
                to 1.0.
            name (Optional[str]): An optional human-readable name for the objective.
                Defaults to None.
        """

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

    def to_dict(self) -> dict:
        """
        Serializes the instance into a dictionary representation for optimization.

        Returns:
            dict: A dictionary formatted for use in optimization.
        """
        return {
            "cellReference": f"!!!{self._objective.to_string()}",
            "trackingId": self._tracking_id,
            "maximise": self._maximise,
            "priority": self._priority.value,
            "weight": self._weight,
            "name": self._name,
        }
