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
This module defines the ModelProperty class, a container for storing arbitrary properties
that should be tracked at a model level, including calculation flags and configurations.
"""

from typeguard import typechecked

from daitum_configuration.model_property.model_import_options import ModelImportOptions
from daitum_configuration.model_property.overlay_config import OverlayConfig


# pylint: disable=too-few-public-methods,too-many-positional-arguments
@typechecked
class ModelProperty:
    """
    Data model representing model-level properties and configurations.
    """

    def __init__(
        self,
        calculate_on_load: bool = False,
        calculation_enabled: bool = True,
        ignore_formula: bool = False,
        import_options: ModelImportOptions | None = None,
        overlay_config: OverlayConfig | None = None,
    ):
        """
        Initialize ModelProperties instance with values.
        """
        self._calculate_on_load = calculate_on_load
        self._calculation_enabled = calculation_enabled
        self._ignore_formula = ignore_formula
        self._import_options = import_options
        self._overlay_config = overlay_config

    def import_options(self) -> ModelImportOptions:
        """Initialise ModelImportOptions() if it has not been initialised."""
        return self._import_options if self._import_options is not None else ModelImportOptions()

    def overlay_config(self) -> OverlayConfig:
        """Initialise OverlayConfig() if it has not been initialised."""
        return self._overlay_config if self._overlay_config is not None else OverlayConfig()

    def has_defined_import_options(self) -> bool:
        """Check if import options have been explicitly set."""
        return self._import_options is not None

    def has_defined_overlay_config(self) -> bool:
        """Check if overlay config has been explicitly set."""
        return self._overlay_config is not None

    def to_dict(self) -> dict:
        """
        Serializes the ModelProperties instance to a dictionary.

        Returns:
            dict: A dictionary representation of the ModelProperties instance.
        """
        return {
            "calculateOnLoad": self._calculate_on_load,
            "calculationEnabled": self._calculation_enabled,
            "ignoreFormula": self._ignore_formula,
            "importOptions": (
                self._import_options.to_dict() if self._import_options is not None else None
            ),
            "overlayConfig": (
                self._overlay_config.to_dict() if self._overlay_config is not None else None
            ),
        }
