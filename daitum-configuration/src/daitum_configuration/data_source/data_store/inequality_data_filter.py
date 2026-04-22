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
This module defines the InequalityDataFilter class, a concrete implementation of the
DataFilter abstract base class. It filters rows based on inequality comparison with
a specified source key at a given data path.

Classes:
    InequalityDataFilter: A data filter that matches values at a path to a source key.
"""

from inspect import Parameter

from daitum_model import Calculation
from typeguard import typechecked

from daitum_configuration.data_source.data_store.data_filter import DataFilter
from daitum_configuration.data_source.data_store.data_filter_type import DataFilterType


# pylint: disable=too-many-positional-arguments
@typechecked
class InequalityDataFilter(DataFilter):
    """
    A data filter that matches rows where the value at the specified path falls within a
        specified range.

    The range is defined by dynamic lower and upper bounds, provided via `Parameter` or
        `Calculation` references.
    Optional static fallback values for each bound can also be provided for display or
        evaluation purposes.
    """

    def __init__(
        self,
        path: list[str],
        lower_key: float | Parameter | Calculation,
        upper_key: float | Parameter | Calculation,
        lower: float | None = None,
        upper: float | None = None,
    ):
        """
        Initializes an InequalityDataFilter instance.

        Args:
            path (list[str]): The hierarchical path to the field being evaluated.
            lower_key (float | Parameter | Calculation): A reference defining the dynamic
                lower bound.
            upper_key (float | Parameter | Calculation): A reference defining the dynamic
                upper bound.
            lower (float | None, optional): An optional static lower bound for display or
                fallback.
            upper (float | None, optional): An optional static upper bound for display or
                fallback.
        """
        self._path = path
        self._lower_key = lower_key
        self._upper_key = upper_key
        self._lower = lower
        self._upper = upper

    @property
    def type(self) -> DataFilterType:
        """
        Returns the filter type.

        Returns:
            DataFilterType: The enum value for inequality filter.
        """
        return DataFilterType.INEQUALITY

    def to_dict(self) -> dict:
        """
        Serializes the instance into a dictionary representation for InequalityDataFilter.

        Returns:
            dict: A dictionary representation of the InequalityDataFilter instance.
        """
        return {
            "@type": self.type.value,
            "path": self._path,
            "lower": self._lower,
            "upper": self._upper,
            "lowerKey": f"!!!{self._lower_key}",
            "upperKey": f"!!!{self._upper_key}",
        }
