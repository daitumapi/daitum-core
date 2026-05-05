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

""":class:`DistanceMatrixConfig` — distance/duration matrix data source."""

from typeguard import typechecked

from daitum_configuration.data_source.data_source_config import DataSourceConfig
from daitum_configuration.data_source.data_source_type import DataSourceType
from daitum_configuration.data_source.distance_matrix.output_matrix import OutputMatrix


# pylint: disable=too-many-instance-attributes
@typechecked
class DistanceMatrixConfig(DataSourceConfig):
    """
    Computes a matrix of distances/durations between origin and destination points.

    Configure destinations via :meth:`set_to_sheet`. By default the destination
    sheet is the same as the origin sheet (square matrix). Each entry in
    ``outputs`` defines where one metric is written.

    Args:
        from_sheet_name: Source sheet for origin rows.
        from_longitude_column: Origin-row longitude column name.
        from_latitude_column: Origin-row latitude column name.
        outputs: One :class:`OutputMatrix` per metric to produce.
    """

    def __init__(
        self,
        from_sheet_name: str,
        from_longitude_column: str,
        from_latitude_column: str,
        outputs: list[OutputMatrix],
    ):
        self.from_sheet_name = from_sheet_name
        self.from_table_name: str | None = None
        self.from_longitude_column = from_longitude_column
        self.from_latitude_column = from_latitude_column
        self.to_sheet_name: str = ""
        self.to_table_name: str | None = None
        self.to_longitude_column: str = ""
        self.to_latitude_column: str = ""
        self.outputs = outputs
        super().__init__()

    def set_to_sheet(
        self,
        to_sheet_name: str,
        to_longitude_column: str,
        to_latitude_column: str,
    ) -> "DistanceMatrixConfig":
        """Set the destination sheet name and longitude/latitude columns."""
        self.to_sheet_name = to_sheet_name
        self.to_longitude_column = to_longitude_column
        self.to_latitude_column = to_latitude_column
        return self

    def set_from_table_name(self, from_table_name: str) -> "DistanceMatrixConfig":
        """Set the structured-table name for origin rows (alternative to a sheet name)."""
        self.from_table_name = from_table_name
        return self

    def set_to_table_name(self, to_table_name: str) -> "DistanceMatrixConfig":
        """Set the structured-table name for destination rows."""
        self.to_table_name = to_table_name
        return self

    @property
    def type(self) -> DataSourceType:
        return DataSourceType.DISTANCE_MATRIX
