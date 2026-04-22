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
This module defines the abstract base class `DataFilter`, which provides an interface for
implementing specific row-filtering logic based on a data path. Subclasses must implement
type identification and serialization to dictionary format.

Classes:
    DataFilter: Abstract base class for data filtering configurations.
"""

from abc import ABC, abstractmethod
from typing import Any

from typeguard import typechecked

from daitum_configuration.data_source.data_store.data_filter_type import DataFilterType


@typechecked
class DataFilter(ABC):
    """
    Abstract base class for defining data filters.

    Data filters are used to select rows based on the value at a specified hierarchical path
    (e.g., nested fields in JSON or structured data). This class provides the foundational
    structure for implementing concrete filters with specific behaviors.
    """

    @property
    @abstractmethod
    def type(self) -> DataFilterType:
        """
        Returns the type identifier for this data filter configuration.
        """

    @abstractmethod
    def to_dict(self) -> dict[str, Any]:
        """
        Converts the data filter configuration to a dictionary format.

        Returns:
            dict[str, Any]: A dictionary format of data filter configuration.
        """
