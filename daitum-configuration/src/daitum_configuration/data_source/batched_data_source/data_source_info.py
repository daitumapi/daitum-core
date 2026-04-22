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
Defines the DataSourceInfo class, which represents individual data sources in a batched
data source configuration. This class captures metadata like the data source ID, type,
and an incremental order number for each data source instance.
"""

from typeguard import typechecked

from daitum_configuration.data_source.batched_data_source.batch_data_source_type import (
    BatchDataSourceType,
)
from daitum_configuration.data_source.data_source import DataSource


# pylint: disable=too-few-public-methods
@typechecked
class DataSourceInfo:
    """
    Represents a single data source within a batched configuration, including metadata
    such as its unique identifier, execution order, and batching behaviour.
    """

    def __init__(
        self,
        data_source: DataSource,
        order: int,
        batch_data_source_type: BatchDataSourceType = BatchDataSourceType.NONE_PARALLEL,
    ):
        self._order = order
        self._data_source_id = data_source._temp_export_id
        self._type = batch_data_source_type

    def to_dict(self) -> dict:
        """
        Serializes the instance into a dictionary representation for DataSourceInfo.

        Returns:
            dict: A dictionary representation of the DataSourceInfo instance, including the
                data source ID, order, and type.
        """
        return {
            "dataSourceId": self._data_source_id,
            "order": self._order,
            "type": self._type.value,
        }
