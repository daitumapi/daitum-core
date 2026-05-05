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

""":class:`InequalityDataFilter` — a :class:`DataFilter` matching numeric range rows."""

from typing import Any

from daitum_model import Calculation, Parameter
from typeguard import typechecked

from daitum_configuration._buildable import json_type_info
from daitum_configuration.data_source.data_store.data_filter import DataFilter
from daitum_configuration.data_source.data_store.data_filter_type import DataFilterType


# pylint: disable=too-many-positional-arguments
@json_type_info(DataFilterType.INEQUALITY.value)
@typechecked
class InequalityDataFilter(DataFilter):
    """
    Match rows whose numeric value at ``path`` falls within a range.

    Args:
        path: Field path within each source row.
        lower_key: Lower bound source — a literal or model named value.
        upper_key: Upper bound source — a literal or model named value.
        lower: Optional literal lower-bound value emitted alongside the key.
        upper: Optional literal upper-bound value emitted alongside the key.
    """

    def __init__(
        self,
        path: list[str],
        lower_key: float | Parameter | Calculation,
        upper_key: float | Parameter | Calculation,
        lower: float | None = None,
        upper: float | None = None,
    ):
        self.path = path
        self.lower = lower
        self.upper = upper
        self._lower_key = lower_key
        self._upper_key = upper_key

    @property
    def type(self) -> DataFilterType:
        return DataFilterType.INEQUALITY

    def build(self) -> dict[str, Any]:
        """Serialise to a JSON-compatible dict."""
        result = super().build()
        result["lowerKey"] = f"!!!{self._format(self._lower_key)}"
        result["upperKey"] = f"!!!{self._format(self._upper_key)}"
        return result

    @staticmethod
    def _format(key: float | Parameter | Calculation) -> str:
        if isinstance(key, (int, float)):
            return str(key)
        return key.to_string()
