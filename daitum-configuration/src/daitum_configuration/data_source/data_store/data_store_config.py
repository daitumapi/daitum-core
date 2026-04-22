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
This module defines the DataStoreConfig class, which extends the DataSourceConfig to provide
configuration support for data sources of type 'DATA_STORE'. It encapsulates metadata
such as data store keys, table mappings, filter logic, and options for debugging and
interface usage.

Classes:
    - DataStoreConfig: Configuration class for data stores, enabling structured serialisation
      and supporting optional filtering and debug options.
"""

from typeguard import typechecked

from daitum_configuration.data_source.data_source_config import DataSourceConfig
from daitum_configuration.data_source.data_source_type import DataSourceType
from daitum_configuration.data_source.data_store.data_filter import DataFilter


# pylint: disable=too-few-public-methods
@typechecked
class DataStoreConfig(DataSourceConfig):
    """
    Configuration class for data sources of type 'DATA_STORE'.

    This class provides structured configuration for connecting to a data store,
    including metadata for table mappings, optional model filters, and control
    flags for debug and data access behaviours.
    """

    def __init__(
        self,
        data_store_key: str,
        tables: dict[str, str],
    ):
        """
        Initialises a new instance of the DataStoreConfig class.

        Args:
            data_store_key (str): Key representing the data store.
            tables (dict[str, str]): Mapping of logical to physical table names.
        """
        self._data_store_key = data_store_key
        self._tables = tables
        self._model_filter: DataFilter | None = None
        self._debug_file: bool = False
        self._using_interface: bool = False
        self._direct_data_pull: bool = False
        super().__init__(track_changes_supported=True)

    def set_model_filter(self, model_filter: DataFilter) -> "DataStoreConfig":
        """
        Sets an optional filter to apply to the model.

        Args:
            model_filter (DataFilter): The filter to apply.

        Returns:
            DataStoreConfig: self, for method chaining.
        """
        self._model_filter = model_filter
        return self

    def set_debug_file(self, debug_file: bool) -> "DataStoreConfig":
        """
        Enables or disables debug file output.

        Args:
            debug_file (bool): If True, enables debug file output.

        Returns:
            DataStoreConfig: self, for method chaining.
        """
        self._debug_file = debug_file
        return self

    def set_using_interface(self, using_interface: bool) -> "DataStoreConfig":
        """
        Sets whether data is accessed via an interface.

        Args:
            using_interface (bool): If True, data is accessed via an interface.

        Returns:
            DataStoreConfig: self, for method chaining.
        """
        self._using_interface = using_interface
        return self

    def set_direct_data_pull(self, direct_data_pull: bool) -> "DataStoreConfig":
        """
        Enables or disables direct data pulling.

        Args:
            direct_data_pull (bool): If True, enables direct data pulling.

        Returns:
            DataStoreConfig: self, for method chaining.
        """
        self._direct_data_pull = direct_data_pull
        return self

    @property
    def type(self) -> DataSourceType:
        """
        Returns the type identifier for this data source configuration.
        """
        return DataSourceType.DATA_STORE

    def to_dict(self) -> dict:
        """
        Serialises the instance into a dictionary representation for DataStoreConfig.

        Returns:
            dict: A dictionary representation of the DataStoreConfig instance.
        """
        return {
            "type": self.type.value,
            "dataStoreKey": self._data_store_key,
            "debugFile": self._debug_file,
            "usingInterface": self._using_interface,
            "directDataPull": self._direct_data_pull,
            "modelFilter": self._model_filter.to_dict() if self._model_filter is not None else None,
            "tables": self._tables,
            "trackChangesSupported": self._track_changes_supported,
        }
