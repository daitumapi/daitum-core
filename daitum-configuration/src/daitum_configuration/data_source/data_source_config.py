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
This module defines the abstract base class for all data source configuration types.
It enforces a consistent interface for converting configuration objects to a dictionary
and specifying the configuration type. Subclasses are expected to implement the abstract
methods and can override the default behavior for change tracking.

Classes:
    DataSourceConfig: Abstract base class for data source configuration.
"""

from abc import ABC, abstractmethod
from typing import Any

from daitum_configuration.data_source.data_source_type import DataSourceType


class DataSourceConfig(ABC):
    """
    Abstract base class representing a configuration for a data source.

    Subclasses must define the `type` property and implement the `to_dict` method.
    They may also override `is_track_changes_supported` if change tracking is supported.
    """

    def __init__(self, track_changes_supported: bool = False):
        self._track_changes_supported = track_changes_supported

    @property
    @abstractmethod
    def type(self) -> DataSourceType:
        """
        Returns the type identifier for this data source configuration.
        """

    @abstractmethod
    def to_dict(self) -> dict[str, Any]:
        """
        Converts the data source configuration to a dictionary format.

        Returns:
            dict[str, Any]: A dictionary format of data source configuration.
        """
