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

""":class:`DataSourceInfo` — one entry inside a :class:`BatchedDataSourceConfig`."""

from typeguard import typechecked

from daitum_configuration._buildable import Buildable
from daitum_configuration.data_source.batched_data_source.batch_data_source_type import (
    BatchDataSourceType,
)
from daitum_configuration.data_source.data_source import DataSource


# pylint: disable=too-few-public-methods
@typechecked
class DataSourceInfo(Buildable):
    """
    One :class:`DataSource` reference inside a :class:`BatchedDataSourceConfig`.

    Args:
        data_source: The data source to include in the batch.
        order: Execution order within the batch (lower runs first).
        batch_data_source_type: Position within any surrounding parallel block.
    """

    def __init__(
        self,
        data_source: DataSource,
        order: int,
        batch_data_source_type: BatchDataSourceType = BatchDataSourceType.NONE_PARALLEL,
    ):
        self.data_source_id = data_source.temp_export_id
        self.order = order
        self.type = batch_data_source_type
