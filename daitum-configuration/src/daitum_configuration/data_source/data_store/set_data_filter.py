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
Defines SetDataFilter, a concrete implementation of DataFilter that matches rows where the
value at a specified path is contained in a set of source keys.
"""

from inspect import Parameter

from daitum_model import Calculation
from typeguard import typechecked

from daitum_configuration.data_source.data_store.data_filter import DataFilter
from daitum_configuration.data_source.data_store.data_filter_type import DataFilterType


@typechecked
class SetDataFilter(DataFilter):
    """
    A data filter that includes rows where the value at the specified path is found within
    a defined set of values, either provided directly or resolved from source keys.
    """

    def __init__(
        self,
        path: list[str],
        source_keys: list[Parameter | Calculation],
        values: set[str] | None = None,
    ):
        """
        Initializes a SetDataFilter instance.

        Args:
            path (list[str]): The hierarchical path to the field in the data row to be evaluated.
            source_keys (list[Parameter | Calculation]): A list of data sources (e.g., parameters
                or calculations) whose values will be used to construct the filtering set.
            values (set[str] | None, optional): An optional static set of values to compare
                against.
        """
        self._path = path
        self._source_keys = source_keys
        self._values = values

    @property
    def type(self) -> DataFilterType:
        """
        Returns the filter type.

        Returns:
            DataFilterType: The enum value representing a set-based filter.
        """
        return DataFilterType.SET

    def to_dict(self) -> dict:
        """
        Serializes the filter configuration to a dictionary format.

        Returns:
            dict: A dictionary including the filter type, path, and set of source keys.
        """
        return {
            "@type": self.type.value,
            "path": self._path,
            "values": self._values,
            "sourceKey": [f"!!!{key}" for key in self._source_keys],
        }
