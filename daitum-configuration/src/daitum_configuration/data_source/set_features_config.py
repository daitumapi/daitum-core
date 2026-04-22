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
This module defines the SetFeaturesConfig class, which represents a configuration
used to toggle features on or off in a data pipeline.

Classes:
    - SetFeaturesConfig: A configuration class that holds boolean feature flags
      for enabling or disabling specific functionalities.
"""

from typeguard import typechecked

from daitum_configuration.data_source.data_source_config import DataSourceConfig
from daitum_configuration.data_source.data_source_type import DataSourceType


@typechecked
class SetFeaturesConfig(DataSourceConfig):
    """
    Configuration class for setting feature flags.

    This class enables or disables specific system features by using a dictionary
    of feature names mapped to boolean values. It is useful for conditional
    behavior based on user or system-level preferences.
    """

    def __init__(
        self,
        feature_settings: dict[str, bool] | None = None,
    ):
        """
        Initializes a SetFeaturesConfig instance.

        Args:
            feature_settings (dict[str, bool] | None): Optional dictionary specifying
                feature names and their enabled/disabled status.
        """
        self._feature_settings = feature_settings
        super().__init__()

    @property
    def type(self) -> DataSourceType:
        """
        Returns the type identifier for this data source configuration.

        Returns:
            DataSourceType: Enum indicating this is a SET_FEATURES type configuration.
        """
        return DataSourceType.SET_FEATURES

    def to_dict(self) -> dict:
        """
        Serializes the instance into a dictionary representation for exporting or
        persisting the feature configuration.

        Returns:
            - A dictionary representation of the SetFeaturesConfig instance,
              including the type, feature flags, and change-tracking support flag.
        """
        return {
            "type": self.type.value,
            "featureSettings": self._feature_settings,
            "trackChangesSupported": self._track_changes_supported,
        }
