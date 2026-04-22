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
Type enum for model transform data inputs.
"""

from enum import Enum


class DataInputSourceType(Enum):
    """
    Type enum indicating the source of non-model data.

    Values:
        - DATA_STORE: Directly from a data store
        - DATA_STORE_INTERFACE: From a data store interface
        - DIRECT_UPLOAD: From directly uploaded csv or zip of csvs - not currently supported
    """

    DATA_STORE = "DATA_STORE"
    DATA_STORE_INTERFACE = "DATA_STORE_INTERFACE"
    DYNAMIC_VALUES = "DYNAMIC_VALUES"
    DIRECT_UPLOAD = "DIRECT_UPLOAD"
