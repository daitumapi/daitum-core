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

""":class:`ModelProperty` — model-level UI/calculation flags and import options."""

from typeguard import typechecked

from daitum_configuration._buildable import Buildable
from daitum_configuration.model_property.model_import_options import ModelImportOptions
from daitum_configuration.model_property.overlay_config import OverlayConfig


# pylint: disable=too-few-public-methods,too-many-positional-arguments
@typechecked
class ModelProperty(Buildable):
    """
    Model-level UI and calculation flags.

    Args:
        calculate_on_load: Run formulas immediately after a model loads.
        calculation_enabled: Master toggle for all formula calculations.
        ignore_formula: Skip formulas during evaluation (data passes through
            untransformed).
        import_options: Default :class:`ModelImportOptions` applied to imports.
        overlay_config: :class:`OverlayConfig` controlling solver-result overlays.
    """

    def __init__(
        self,
        calculate_on_load: bool = False,
        calculation_enabled: bool = True,
        ignore_formula: bool = False,
        import_options: ModelImportOptions | None = None,
        overlay_config: OverlayConfig | None = None,
    ):
        self.calculate_on_load = calculate_on_load
        self.calculation_enabled = calculation_enabled
        self.ignore_formula = ignore_formula
        self.import_options = import_options
        self.overlay_config = overlay_config
