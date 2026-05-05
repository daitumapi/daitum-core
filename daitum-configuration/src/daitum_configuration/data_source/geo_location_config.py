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

""":class:`GeoLocationConfig` — geocoding data source for address rows."""

from typeguard import typechecked

from daitum_configuration.data_source.data_source_config import DataSourceConfig
from daitum_configuration.data_source.data_source_type import DataSourceType


# pylint: disable=too-many-positional-arguments
# pylint: disable=too-many-instance-attributes,too-many-arguments
@typechecked
class GeoLocationConfig(DataSourceConfig):
    """
    Geocodes address rows and writes longitude/latitude back into the same sheet.

    Args:
        sheet_name: Source sheet containing the address rows.
        address_column: Column name supplying the free-text address.
        longitude_column: Column receiving the geocoded longitude.
        latitude_column: Column receiving the geocoded latitude.
    """

    def __init__(
        self,
        sheet_name: str,
        address_column: str,
        longitude_column: str,
        latitude_column: str,
    ):
        self.sheet_name = sheet_name
        self.table_name: str | None = None
        self.address_column = address_column
        self.longitude_column = longitude_column
        self.latitude_column = latitude_column
        self.longitude_bound: str | None = None
        self.longitude_bound_upper: str | None = None
        self.latitude_bound: str | None = None
        self.latitude_bound_upper: str | None = None
        self.preserve_existing_data = False
        self.region: str | None = None
        self.live_update = False
        self.run_on_data_import = False
        super().__init__()

    def set_table_name(self, table_name: str) -> "GeoLocationConfig":
        """Use a structured table rather than a sheet for the source rows."""
        self.table_name = table_name
        return self

    def set_preserve_existing_data(self, preserve: bool) -> "GeoLocationConfig":
        """Skip geocoding rows that already have coordinates."""
        self.preserve_existing_data = preserve
        return self

    def set_latitude_bounds(self, lower: str | None, upper: str | None) -> "GeoLocationConfig":
        """Reject geocoded latitudes outside the given bounds."""
        self.latitude_bound = lower
        self.latitude_bound_upper = upper
        return self

    def set_longitude_bounds(self, lower: str | None, upper: str | None) -> "GeoLocationConfig":
        """Reject geocoded longitudes outside the given bounds."""
        self.longitude_bound = lower
        self.longitude_bound_upper = upper
        return self

    def set_region(self, region: str) -> "GeoLocationConfig":
        """Bias the geocoder towards a region (e.g., ``"AU"``)."""
        self.region = region
        return self

    def set_live_update(self, live_update: bool) -> "GeoLocationConfig":
        """Re-geocode immediately when the address column changes in the UI."""
        self.live_update = live_update
        return self

    def set_run_on_data_import(self, run: bool) -> "GeoLocationConfig":
        """Run geocoding automatically as part of data import."""
        self.run_on_data_import = run
        return self

    @property
    def type(self) -> DataSourceType:
        return DataSourceType.GEOLOCATION
