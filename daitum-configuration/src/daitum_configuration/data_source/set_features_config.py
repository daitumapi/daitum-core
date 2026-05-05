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

""":class:`SetFeaturesConfig` — feature-flag data source."""

from typeguard import typechecked

from daitum_configuration.data_source.data_source_config import DataSourceConfig
from daitum_configuration.data_source.data_source_type import DataSourceType


@typechecked
class SetFeaturesConfig(DataSourceConfig):
    """
    Toggles named feature flags when the data source runs.

    Args:
        feature_settings: Map of feature key to enabled flag.
    """

    def __init__(
        self,
        feature_settings: dict[str, bool] | None = None,
    ):
        self.feature_settings = feature_settings
        super().__init__()

    @property
    def type(self) -> DataSourceType:
        return DataSourceType.SET_FEATURES
