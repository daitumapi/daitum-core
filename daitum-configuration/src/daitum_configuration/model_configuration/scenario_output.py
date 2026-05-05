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

""":class:`ScenarioOutput` — a value exposed in scenario comparison views."""

from typing import Any

from daitum_model import Calculation, Field, Parameter, Table
from typeguard import typechecked

from daitum_configuration._buildable import Buildable


# pylint: disable=too-many-arguments,too-many-positional-arguments,too-many-instance-attributes
# pylint: disable=too-many-branches,too-few-public-methods
@typechecked
class ScenarioOutput(Buildable):
    """
    A named value or field surfaced as a scenario-comparison output.

    Construct via :meth:`ModelConfiguration.add_scenario_output`. Pass a
    :class:`~daitum_model.Calculation`/:class:`~daitum_model.Parameter` for
    model-level outputs, or a :class:`~daitum_model.fields.Field` plus its
    :class:`~daitum_model.Table` for per-row outputs.
    """

    _tracking_counter = 0

    def __init__(
        self,
        name: str,
        scenario_output_value: Calculation | Parameter | Field,
        scenario_output_table: Table | None = None,
    ):
        self._scenario_output: str | None = None
        self._tracking_id = ScenarioOutput._tracking_counter
        ScenarioOutput._tracking_counter += 1
        self._scenario_output_value = scenario_output_value
        self._scenario_output_table = scenario_output_table
        self._name = name

        self._set_scenario_output()

    def _set_scenario_output(self):
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
        table.get_field(field.id)
        self._scenario_output = f"{table.id}[{field.id}]"

    @property
    def name(self) -> str:
        """Display name for this scenario output."""
        return self._name

    @property
    def cell_reference(self) -> str:
        """Resolved cell reference (``!!!<id>`` form) used in serialisation."""
        return f"!!!{self._scenario_output}"

    def build(self) -> dict[str, Any]:
        """Serialise to a JSON-compatible dict."""
        return {
            "cellReference": self.cell_reference,
            "trackingId": self._tracking_id,
            "name": self._name,
        }
