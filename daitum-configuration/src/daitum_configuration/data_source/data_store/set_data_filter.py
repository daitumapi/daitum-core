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

""":class:`SetDataFilter` — a :class:`DataFilter` matching rows by set membership."""

from daitum_model import Calculation, Parameter
from daitum_model.references import Reference
from daitum_model.serialisation import json_type_info
from typeguard import typechecked

from daitum_configuration.data_source.data_store.data_filter import DataFilter
from daitum_configuration.data_source.data_store.data_filter_type import DataFilterType


@json_type_info(DataFilterType.SET.value)
@typechecked
class SetDataFilter(DataFilter):
    """
    Match rows whose value at ``path`` is in a set of values resolved from ``source_keys``.

    Args:
        path: Field path within each source row.
        source_keys: Model named values supplying the allowed values.
        values: Optional literal value set emitted alongside the keys.
    """

    def __init__(
        self,
        path: list[str],
        source_keys: list[Parameter | Calculation],
        values: set[str] | None = None,
    ):
        self.path = path
        self.values = list(values) if values is not None else None
        # Emitted as the single ``sourceKey`` key (a list of references).
        self.source_key = [Reference(key) for key in source_keys]

    @property
    def type(self) -> DataFilterType:
        return DataFilterType.SET
