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

""":class:`BatchedDataSourceConfig` — bundles other data sources into a single import."""

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
    A data source that runs other data sources in a configured order.

    Args:
        run_after_import_sheet: Optional sheet name whose import triggers this
            batch.
    """

    def __init__(self, run_after_import_sheet: str | None = None) -> None:
        self.data_sources: list[DataSourceInfo] = []
        self.run_after_import_sheet: str | None = run_after_import_sheet
        super().__init__(track_changes_supported=True)

    def add_data_source(
        self,
        data_source: DataSource,
        order: int,
        batch_data_source_type: BatchDataSourceType = BatchDataSourceType.NONE_PARALLEL,
    ) -> "BatchedDataSourceConfig":
        """Add ``data_source`` to this batch with the given execution ``order`` and
        :class:`BatchDataSourceType`."""
        self.data_sources.append(
            DataSourceInfo(
                data_source=data_source,
                order=order,
                batch_data_source_type=batch_data_source_type,
            )
        )
        return self

    @property
    def type(self) -> DataSourceType:
        return DataSourceType.BATCHED_DATA_SOURCE
