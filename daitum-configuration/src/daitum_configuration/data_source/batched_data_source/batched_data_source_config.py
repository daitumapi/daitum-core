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
Defines the BatchedDataSourceConfig class, which represents a configuration for a batched
data source composed of multiple individual data sources. This configuration supports
change tracking and can be serialized for further processing or storage.
"""

from typeguard import typechecked

from daitum_configuration.data_source.batched_data_source.batch_data_source_type import (
    BatchDataSourceType,
)
from daitum_configuration.data_source.batched_data_source.data_source_info import DataSourceInfo
from daitum_configuration.data_source.data_source import DataSource
from daitum_configuration.data_source.data_source_config import DataSourceConfig
from daitum_configuration.data_source.data_source_type import DataSourceType


@typechecked
class BatchedDataSourceConfig(DataSourceConfig):
    """
    Configuration class for a batched data source, which aggregates multiple data sources
    into a single unit of configuration. Useful in scenarios where data is processed in
    parallel or grouped batches.
    """

    def __init__(self, run_after_import_sheet: str | None = None) -> None:
        """
        Initializes an empty BatchedDataSourceConfig with no data sources.
        """
        self._data_sources: list[DataSourceInfo] = []
        self._run_after_import_sheet: str | None = run_after_import_sheet
        super().__init__(track_changes_supported=True)

    def add_data_source(
        self,
        data_source: DataSource,
        order: int,
        batch_data_source_type: BatchDataSourceType = BatchDataSourceType.NONE_PARALLEL,
    ) -> None:
        """
        Creates and adds a DataSourceInfo object to the batched data source configuration.

        Args:
            data_source (DataSource): The data source to be included in the batch.
            order (int): The execution order of the data source within the batch.
            batch_data_source_type (BatchDataSourceType, optional): Defines how the data source
                participates in the batch. Defaults to NONE_PARALLEL.
        """
        data_source_info = DataSourceInfo(
            data_source=data_source, order=order, batch_data_source_type=batch_data_source_type
        )
        self._data_sources.append(data_source_info)

    @property
    def type(self) -> DataSourceType:
        """
        Returns the type identifier for this data source configuration.

        Returns:
            DataSourceType: Enum value indicating this is a batched data source.
        """
        return DataSourceType.BATCHED_DATA_SOURCE

    def to_dict(self) -> dict:
        """
        Serializes the instance into a dictionary representation for BatchedDataSourceConfig.

        Returns:
            dict: A dictionary representation of the BatchedDataSourceConfig instance.
        """
        return {
            "type": self.type.value,
            "dataSources": [data_source.to_dict() for data_source in self._data_sources],
            "trackChangesSupported": self._track_changes_supported,
            "runAfterImportSheet": self._run_after_import_sheet,
        }
