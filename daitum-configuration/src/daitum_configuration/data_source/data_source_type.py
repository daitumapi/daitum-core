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
Defines the enumeration of supported data source types used to configure various
data-loading mechanisms.
"""

from enum import Enum


class DataSourceType(Enum):
    """
    Enumeration of the supported data source types.

    Values:
        - GEOLOCATION: Geolocation-based data source
        - DISTANCE_MATRIX: Distance matrix calculation source
        - EXCEL_TRANSFORM: Excel file transformation source
        - DATA_STORE: External or internal data store source
        - SET_FEATURES: Feature-setting transformation
        - BATCHED_DATA_SOURCE: Batch together multiple different data sources
        - RUN_REPORT: Run a report as a data source
        - MODEL_TRANSFORM: Run a v3 modelling language based data source
    """

    GEOLOCATION = "GEOLOCATION"
    DISTANCE_MATRIX = "DISTANCE_MATRIX"
    EXCEL_TRANSFORM = "EXCEL_TRANSFORM"
    DATA_STORE = "DATA_STORE"
    SET_FEATURES = "SET_FEATURES"
    BATCHED_DATA_SOURCE = "BATCHED_DATA_SOURCE"
    RUN_REPORT = "RUN_REPORT"
    MODEL_TRANSFORM = "MODEL_TRANSFORM"
