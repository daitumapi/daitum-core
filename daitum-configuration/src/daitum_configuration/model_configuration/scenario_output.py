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

from daitum_model import Calculation, Field, Parameter, Table
from daitum_model.serialisation import Buildable
from typeguard import typechecked


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
        # Public attributes are emitted in declaration order: cellReference, trackingId, name.
        self.cell_reference = f"!!!{self._resolve(scenario_output_value, scenario_output_table)}"
        self.tracking_id = ScenarioOutput._tracking_counter
        ScenarioOutput._tracking_counter += 1
        self.name = name

    @staticmethod
    def _resolve(value: Calculation | Parameter | Field, table: Table | None) -> str:
        if table is None:
            if not isinstance(value, (Calculation, Parameter)):
                raise ValueError("Scenario output value is not a calculation or parameter")
            return value.to_string()
        if not isinstance(value, Field):
            raise ValueError("Scenario output value is not a field")
        table.get_field(value.id)
        return f"{table.id}[{value.id}]"
