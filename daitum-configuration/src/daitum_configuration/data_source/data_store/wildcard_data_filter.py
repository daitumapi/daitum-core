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
Defines WildcardDataFilter, a concrete implementation of DataFilter that applies a wildcard
pattern to filter values at a specified data path.
"""

from typeguard import typechecked

from daitum_configuration.data_source.data_store.data_filter import DataFilter
from daitum_configuration.data_source.data_store.data_filter_type import DataFilterType


@typechecked
class WildcardDataFilter(DataFilter):
    """
    A data filter that matches rows where the value at the specified path
    satisfies a wildcard pattern.

    This filter traverses the data structure using the given path and applies
    a wildcard pattern (provided by `source_key`) to the value found. Optionally,
    a static value can be provided for comparison instead of extracting it from the data.
    """

    def __init__(
        self,
        path: list[str],
        source_key,
        value: str | None = None,
        case_sensitive: bool = False,
    ):
        """
        Initializes a WildcardDataFilter.

        Args:
            path (list[str]): A list representing the path to the value in the data.
            source_key: The wildcard pattern used to match the target value.
            value (str | None, optional): A static value to match instead of extracting
                it from the data. Defaults to None.
            case_sensitive (bool, optional): If True, matching is case-sensitive.
                Defaults to False.
        """

        self._path = path
        self._source_key = source_key
        self._value = value
        self._case_sensitive = case_sensitive

    @property
    def type(self) -> DataFilterType:
        """
        Returns the type identifier for this data filter.

        Returns:
            DataFilterType: The enum value representing a wildcard filter.
        """
        return DataFilterType.WILDCARD

    def to_dict(self) -> dict:
        """
        Serializes the filter configuration into a dictionary format.

        Returns:
            dict: A dictionary with type, path, and wildcard source key information.
        """
        return {
            "@type": self.type.value,
            "path": self._path,
            "value": self._value,
            "caseSensitive": self._case_sensitive,
            "sourceKey": f"!!!{self._source_key}",
        }
