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
This module defines the EqualityDataFilter class, a concrete implementation of the
DataFilter abstract base class. It filters rows based on equality comparison with
a specified source key at a given data path.

Classes:
    EqualityDataFilter: A data filter that matches values at a path to a source key.
"""

from daitum_model import Calculation, Parameter
from typeguard import typechecked

from daitum_configuration.data_source.data_store.data_filter import DataFilter
from daitum_configuration.data_source.data_store.data_filter_type import DataFilterType


@typechecked
class EqualityDataFilter(DataFilter):
    """
    A data filter that matches rows where the value at a specified path equals a given source key.

    This filter supports dynamic values via a `Parameter` or `Calculation` reference, and optionally
    includes a static fallback value for display or evaluation purposes.
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
        Returns the filter type.

        Returns:
            DataFilterType: The enum value for equality filter.
        """
        return DataFilterType.EQUALITY

    def to_dict(self) -> dict:
        """
        Serializes the instance into a dictionary representation for EqualityDataFilter.

        Returns:
            dict: A dictionary representation of the EqualityDataFilter instance.
        """
        return {
            "@type": self.type.value,
            "path": self._path,
            "value": self._value,
            "sourceKey": f"!!!{self._source_key}",
        }
