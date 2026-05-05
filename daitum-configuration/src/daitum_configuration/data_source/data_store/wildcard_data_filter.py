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

""":class:`WildcardDataFilter` — a :class:`DataFilter` matching rows by glob pattern."""

from typing import Any

from daitum_model import Calculation, Parameter
from typeguard import typechecked

from daitum_configuration._buildable import json_type_info
from daitum_configuration.data_source.data_store.data_filter import DataFilter
from daitum_configuration.data_source.data_store.data_filter_type import DataFilterType


@json_type_info(DataFilterType.WILDCARD.value)
@typechecked
class WildcardDataFilter(DataFilter):
    """
    Match rows whose value at ``path`` matches the glob pattern resolved from ``source_key``.

    Args:
        path: Field path within each source row.
        source_key: Model named value supplying the glob pattern.
        value: Optional literal pattern emitted alongside the key.
        case_sensitive: Whether matching is case sensitive.
    """

    def __init__(
        self,
        path: list[str],
        source_key: Parameter | Calculation,
        value: str | None = None,
        case_sensitive: bool = False,
    ):
        self.path = path
        self.value = value
        self.case_sensitive = case_sensitive
        self._source_key = source_key

    @property
    def type(self) -> DataFilterType:
        return DataFilterType.WILDCARD

    def build(self) -> dict[str, Any]:
        """Serialise to a JSON-compatible dict."""
        result = super().build()
        result["sourceKey"] = f"!!!{self._source_key.to_string()}"
        return result
