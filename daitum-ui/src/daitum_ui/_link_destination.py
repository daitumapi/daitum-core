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

from daitum_model import Calculation, Field, Parameter
from typeguard import typechecked

from daitum_ui._buildable import Buildable, json_type_info
from daitum_ui.context_variable import ContextVariable


@typechecked
@json_type_info("modelEditor")
class ModelEditorLinkDestination(Buildable):
    """
    A link destination that navigates to the Daitum model editor.

    The model and scenario to open can be specified as static model values
    (``Field``, ``Parameter``, ``Calculation``) or as a ``ContextVariable``
    resolved at runtime. ``scenario_id`` is optional; omitting it opens the
    editor without pre-selecting a scenario.

    Attributes:
        model_id (ModelVariable):
            Identifies the model to open. Resolved from the provided ``Field``,
            ``Parameter``, ``Calculation``, or ``ContextVariable`` at build time.
        scenario_id (ModelVariable | None):
            Identifies the scenario to open within the selected model. Resolved
            from the provided ``Field``, ``Parameter``, ``Calculation``, or
            ``ContextVariable`` at build time. ``None`` if not specified.
        open_new_tab (bool):
            Opens the editor in a new browser tab when ``True``. Defaults to
            ``False``.
    """

    def __init__(
        self,
        model_id: Field | Parameter | Calculation | ContextVariable,
        scenario_id: Field | Parameter | Calculation | ContextVariable | None = None,
        open_new_tab: bool = False,
    ):
        self.open_new_tab = open_new_tab

        from daitum_ui.elements import get_model_variable

        self.model_id = get_model_variable(model_id)
        self.scenario_id = get_model_variable(scenario_id) if scenario_id is not None else None
