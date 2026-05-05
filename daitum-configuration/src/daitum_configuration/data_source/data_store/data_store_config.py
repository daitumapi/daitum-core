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

""":class:`DataStoreConfig` — data source backed by a managed data store."""

from typeguard import typechecked

from daitum_configuration.data_source.data_source_config import DataSourceConfig
from daitum_configuration.data_source.data_source_type import DataSourceType
from daitum_configuration.data_source.data_store.data_filter import DataFilter


# pylint: disable=too-few-public-methods,too-many-instance-attributes
@typechecked
class DataStoreConfig(DataSourceConfig):
    """
    Data source that reads rows from a stored dataset.

    Apply a :class:`~daitum_configuration.data_source.data_store.data_filter.DataFilter`
    via :meth:`set_model_filter` to restrict which rows are imported.

    Args:
        data_store_key: Key of the data store to read from.
        tables: Mapping from local model table name to the source table name.
    """

    def __init__(
        self,
        data_store_key: str,
        tables: dict[str, str],
    ):
        self.data_store_key = data_store_key
        self.debug_file: bool = False
        self.using_interface: bool = False
        self.direct_data_pull: bool = False
        self.model_filter: DataFilter | None = None
        self.tables = tables
        super().__init__(track_changes_supported=True)

    def set_model_filter(self, model_filter: DataFilter) -> "DataStoreConfig":
        """Apply a row-level :class:`DataFilter` to narrow the rows pulled in."""
        self.model_filter = model_filter
        return self

    def set_debug_file(self, debug_file: bool) -> "DataStoreConfig":
        """Emit a debug copy of the imported data."""
        self.debug_file = debug_file
        return self

    def set_using_interface(self, using_interface: bool) -> "DataStoreConfig":
        """Read through the data store's interface layer rather than directly."""
        self.using_interface = using_interface
        return self

    def set_direct_data_pull(self, direct_data_pull: bool) -> "DataStoreConfig":
        """Bypass any caching layer and pull rows directly each import."""
        self.direct_data_pull = direct_data_pull
        return self

    @property
    def type(self) -> DataSourceType:
        return DataSourceType.DATA_STORE
