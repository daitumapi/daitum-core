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
This module defines the DistanceMatrixConfig class, which is a configuration model
for setting up a distance matrix data source. It specifies both origin ("from") and
destination ("to") data sheets and associated geolocation columns. It also handles
output configurations such as distance, duration, or other matrix results.

Classes:
    DistanceMatrixConfig: Configuration model for a distance matrix data source.
"""

from typeguard import typechecked

from daitum_configuration.data_source.data_source_config import DataSourceConfig
from daitum_configuration.data_source.data_source_type import DataSourceType
from daitum_configuration.data_source.distance_matrix.output_matrix import OutputMatrix


# pylint: disable=too-many-instance-attributes
@typechecked
class DistanceMatrixConfig(DataSourceConfig):
    """
    Configuration class for a distance matrix data source.

    This class defines how to read and configure a geospatial distance matrix,
    using longitude and latitude columns from two different sheets or tables
    representing the origin ("from") and destination ("to") points.
    """

    def __init__(
        self,
        from_sheet_name: str,
        from_longitude_column: str,
        from_latitude_column: str,
        outputs: list[OutputMatrix],
    ):
        """
        Initialises a DistanceMatrixConfig instance.

        Args:
            from_sheet_name (str): Sheet name for origin data.
            from_longitude_column (str): Longitude column for origin data.
            from_latitude_column (str): Latitude column for origin data.
            outputs (list[OutputMatrix]): Output configuration list.
        """
        self._from_sheet_name = from_sheet_name
        self._from_longitude_column = from_longitude_column
        self._from_latitude_column = from_latitude_column
        self._outputs = outputs
        self._to_sheet_name: str = ""
        self._to_longitude_column: str = ""
        self._to_latitude_column: str = ""
        self._from_table_name: str | None = None
        self._to_table_name: str | None = None
        super().__init__()

    def set_to_sheet(
        self,
        to_sheet_name: str,
        to_longitude_column: str,
        to_latitude_column: str,
    ) -> "DistanceMatrixConfig":
        """
        Sets the destination sheet name and coordinate columns.

        Args:
            to_sheet_name (str): Sheet name for destination data.
            to_longitude_column (str): Longitude column for destination data.
            to_latitude_column (str): Latitude column for destination data.

        Returns:
            DistanceMatrixConfig: self, for method chaining.
        """
        self._to_sheet_name = to_sheet_name
        self._to_longitude_column = to_longitude_column
        self._to_latitude_column = to_latitude_column
        return self

    def set_from_table_name(self, from_table_name: str) -> "DistanceMatrixConfig":
        """
        Sets the optional table name for origin data.

        Args:
            from_table_name (str): Optional table name for origin.

        Returns:
            DistanceMatrixConfig: self, for method chaining.
        """
        self._from_table_name = from_table_name
        return self

    def set_to_table_name(self, to_table_name: str) -> "DistanceMatrixConfig":
        """
        Sets the optional table name for destination data.

        Args:
            to_table_name (str): Optional table name for destination.

        Returns:
            DistanceMatrixConfig: self, for method chaining.
        """
        self._to_table_name = to_table_name
        return self

    @property
    def type(self) -> DataSourceType:
        """
        Returns the type identifier for this data source configuration.

        Returns:
            DataSourceType: Enum indicating this is a DISTANCE_MATRIX type.
        """
        return DataSourceType.DISTANCE_MATRIX

    def to_dict(self) -> dict:
        """
        Serialises the instance into a dictionary representation for use in configuration
        files or data transmission.

        Returns:
            dict: A dictionary representation of the DistanceMatrixConfig instance.
        """
        return {
            "type": self.type.value,
            "fromSheetName": self._from_sheet_name,
            "fromTableName": self._from_table_name,
            "fromLongitudeColumn": self._from_longitude_column,
            "fromLatitudeColumn": self._from_latitude_column,
            "toSheetName": self._to_sheet_name,
            "toTableName": self._to_table_name,
            "toLongitudeColumn": self._to_longitude_column,
            "toLatitudeColumn": self._to_latitude_column,
            "outputs": [output.to_dict() for output in self._outputs],
            "trackChangesSupported": self._track_changes_supported,
        }
