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

""":class:`DataSourceType` discriminator enum for :class:`DataSourceConfig`."""

from enum import Enum


class DataSourceType(Enum):
    """Identifies the kind of data source emitted in the JSON output.

    Values:
        GEOLOCATION: Geocoding of address rows.
        DISTANCE_MATRIX: Computed distance/duration matrix.
        EXCEL_TRANSFORM: Spreadsheet-driven transform.
        DATA_STORE: External or internal data store.
        SET_FEATURES: Feature-flag toggles.
        BATCHED_DATA_SOURCE: Group of other data sources run together.
        RUN_REPORT: Run a report. Useful to batch reports with other data sources.
        MODEL_TRANSFORM: Secondary model used to transform data.
    """

    GEOLOCATION = "GEOLOCATION"
    DISTANCE_MATRIX = "DISTANCE_MATRIX"
    EXCEL_TRANSFORM = "EXCEL_TRANSFORM"
    DATA_STORE = "DATA_STORE"
    SET_FEATURES = "SET_FEATURES"
    BATCHED_DATA_SOURCE = "BATCHED_DATA_SOURCE"
    RUN_REPORT = "RUN_REPORT"
    MODEL_TRANSFORM = "MODEL_TRANSFORM"
