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
This module defines the `ScenarioOutput` class, which encapsulates logic for handling
output values from a scenario within a model. It supports different types of outputs
such as `Calculation`, `Parameter`, and `Field`, and handles references to output
tables when applicable.

Classes:
    - ScenarioOutput: Represents an output from a scenario, with internal tracking and
      reference formatting.
"""

from daitum_model import Calculation, Field, Parameter, Table
from typeguard import typechecked


# pylint: disable=too-many-arguments,too-many-positional-arguments,too-many-instance-attributes
# pylint: disable=too-many-branches,too-few-public-methods
@typechecked
class ScenarioOutput:
    """
    Represents a scenario output reference, which can be based on a Calculation,
    Parameter, or Field, optionally associated with a Table.
    """

    # Class-level static variable for tracking ID
    _tracking_counter = 0

    def __init__(
        self,
        name: str,
        scenario_output_value: Calculation | Parameter | Field,
        scenario_output_table: Table | None = None,
    ):
        """
        Initializes a ScenarioOutput object.

        Args:
            name str: A human-readable name for the output reference.
            scenario_output_value (Calculation | Parameter | Field): The value
                defining the scenario output.
            scenario_output_table (Optional[Table]): The table the output is
                associated with, if applicable.
        """
        self._scenario_output: str | None = None
        self._tracking_id = ScenarioOutput._tracking_counter
        ScenarioOutput._tracking_counter += 1
        self._scenario_output_value = scenario_output_value
        self._scenario_output_table = scenario_output_table
        self._name = name

        self._set_scenario_output()

    def _set_scenario_output(self):
        """
        Determines how to set the scenario output string based on the type of
        `scenario_output_value` and whether it is associated with a table.

        Raises:
            ValueError: If the value type does not match the table association context.
        """
        if self._scenario_output_table is None:
            if not isinstance(self._scenario_output_value, (Calculation, Parameter)):
                raise ValueError("Scenario output value is not a calculation or parameter")
            self._scenario_output = self._scenario_output_value.to_string()
        else:
            if not isinstance(self._scenario_output_value, Field):
                raise ValueError("Scenario output value is not a field")
            self._set_scenario_output_field(
                self._scenario_output_value, self._scenario_output_table
            )

    def _set_scenario_output_field(self, field: Field, table: Table):
        """
        Sets the scenario output string for a field associated with a table.

        Args:
            field (Field): The field to reference.
            table (Table): The table containing the field.

        Returns:
            ValueError: If the field does not exist in the table.
        """
        table.get_field(field.id)

        self._scenario_output = f"{table.id}[{field.id}]"

    def to_dict(self) -> dict:
        """
        Serializes the scenario output to a dictionary representation.

        Returns:
            dict: A dictionary containing the cell reference, tracking ID, and name.
        """
        return {
            "cellReference": f"!!!{self._scenario_output}",
            "trackingId": self._tracking_id,
            "name": self._name,
        }
