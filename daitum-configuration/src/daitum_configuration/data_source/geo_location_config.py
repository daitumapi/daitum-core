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
This module defines the GeoLocationConfig class, a configuration model for enabling
geocoding functionality in spreadsheet-based data sources. It supports automatic
conversion of addresses into geographic coordinates (latitude and longitude), with
optional parameters to control geocoding behavior such as data preservation,
bounds, and regional targeting.

Classes:
    - GeoLocationConfig: Represents a geolocation configuration for address-to-coordinate
      transformation.
"""

from typeguard import typechecked

from daitum_configuration.data_source.data_source_config import DataSourceConfig
from daitum_configuration.data_source.data_source_type import DataSourceType


# pylint: disable=too-many-positional-arguments
# pylint: disable=too-many-instance-attributes,too-many-arguments
@typechecked
class GeoLocationConfig(DataSourceConfig):
    """
    Configuration class for enabling geolocation in data sources.

    This class configures how addresses in a spreadsheet should be geocoded to
    geographic coordinates. It includes the source sheet, address column, and
    target columns for latitude and longitude, along with optional features like
    bounding boxes, region specification, and runtime behavior control.
    """

    def __init__(
        self,
        sheet_name: str,
        address_column: str,
        longitude_column: str,
        latitude_column: str,
    ):
        """
        Initializes a GeoLocationConfig instance.

        Args:
            sheet_name (str): Worksheet name where geolocation data resides.
            address_column (str): Column name with address values to geocode.
            longitude_column (str): Target column for storing longitude results.
            latitude_column (str): Target column for storing latitude results.
        """
        self._sheet_name = sheet_name
        self._table_name: str | None = None
        self._address_column = address_column
        self._longitude_column = longitude_column
        self._latitude_column = latitude_column
        self._latitude_bound: str | None = None
        self._latitude_bound_upper: str | None = None
        self._longitude_bound: str | None = None
        self._longitude_bound_upper: str | None = None
        self._preserve_existing_data = False
        self._region: str | None = None
        self._live_update = False
        self._run_on_data_import = False
        super().__init__()

    def set_table_name(self, table_name: str) -> "GeoLocationConfig":
        """Sets the optional structured table name."""
        self._table_name = table_name
        return self

    def set_preserve_existing_data(self, preserve: bool) -> "GeoLocationConfig":
        """Sets whether to preserve preexisting coordinates."""
        self._preserve_existing_data = preserve
        return self

    def set_latitude_bounds(self, lower: str | None, upper: str | None) -> "GeoLocationConfig":
        """Sets the optional latitude bounding constraints."""
        self._latitude_bound = lower
        self._latitude_bound_upper = upper
        return self

    def set_longitude_bounds(self, lower: str | None, upper: str | None) -> "GeoLocationConfig":
        """Sets the optional longitude bounding constraints."""
        self._longitude_bound = lower
        self._longitude_bound_upper = upper
        return self

    def set_region(self, region: str) -> "GeoLocationConfig":
        """Sets the optional region hint for geocoding (e.g., 'AU')."""
        self._region = region
        return self

    def set_live_update(self, live_update: bool) -> "GeoLocationConfig":
        """Sets whether to enable live updates on address change."""
        self._live_update = live_update
        return self

    def set_run_on_data_import(self, run: bool) -> "GeoLocationConfig":
        """Sets whether to run geocoding on data import."""
        self._run_on_data_import = run
        return self

    @property
    def type(self) -> DataSourceType:
        """
        Returns the type identifier for this data source configuration.

        Returns:
            DataSourceType: Enum indicating this is a GEOLOCATION type configuration.
        """
        return DataSourceType.GEOLOCATION

    def to_dict(self) -> dict:
        """
        Serializes the GeoLocationConfig instance into a dictionary suitable for
        configuration export or runtime execution.

        Returns:
            - A dictionary representation of the GeoLocationConfig instance,
              including all relevant settings.
        """
        return {
            "type": self.type.value,
            "sheetName": self._sheet_name,
            "tableName": self._table_name,
            "addressColumn": self._address_column,
            "longitudeColumn": self._longitude_column,
            "latitudeColumn": self._latitude_column,
            "longitudeBound": self._longitude_bound,
            "longitudeBoundUpper": self._longitude_bound_upper,
            "latitudeBound": self._latitude_bound,
            "latitudeBoundUpper": self._latitude_bound_upper,
            "preserveExistingData": self._preserve_existing_data,
            "region": self._region,
            "liveUpdate": self._live_update,
            "runOnDataImport": self._run_on_data_import,
            "trackChangesSupported": self._track_changes_supported,
        }
