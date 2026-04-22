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
Defines RegexDataFilter, a concrete implementation of DataFilter that applies a regular
expression to the value at the specified path for filtering purposes.
"""

from daitum_model import Calculation, Parameter
from typeguard import typechecked

from daitum_configuration.data_source.data_store.data_filter import DataFilter
from daitum_configuration.data_source.data_store.data_filter_type import DataFilterType


@typechecked
class RegexDataFilter(DataFilter):
    """
    A data filter that matches rows where the value at a given path satisfies a regular expression.
    """

    def __init__(
        self,
        path: list[str],
        source_key: Parameter | Calculation,
        value: str | None = None,
    ):
        """
        Initializes an EqualityDataFilter instance.

        Args:
            path (list[str]): The hierarchical path to the field to evaluate.
            source_key (Parameter | Calculation): A reference to the value used for comparison.
            value (str | None, optional): An optional static value representation used
                for display or fallback. Defaults to None.
        """
        self._path = path
        self._source_key = source_key
        self._value = value

    @property
    def type(self) -> DataFilterType:
        """
        Returns the type identifier for this data filter.

        Returns:
            DataFilterType: The enum value for a regex-based filter.
        """
        return DataFilterType.REGEX

    # pylint: disable=duplicate-code
    def to_dict(self) -> dict:
        """
        Serializes the filter configuration to a dictionary format.

        Returns:
            dict: A dictionary including the filter type, path, and regex source key.
        """
        return {
            "@type": self.type.value,
            "path": self._path,
            "value": self._value,
            "sourceKey": f"!!!{self._source_key}",
        }
