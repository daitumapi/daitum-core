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
Input subclasses for :class:`ModelTransformConfig`.

Each subclass corresponds to a :class:`DataInputSourceType` and emits the
appropriate ``sourceType`` discriminator on serialisation.
"""

from abc import ABC, abstractmethod
from typing import Any

from daitum_model import Calculation, Parameter

from daitum_configuration._buildable import Buildable
from daitum_configuration.data_source.data_store.data_filter import DataFilter
from daitum_configuration.data_source.model_transform.data_input_source_type import (
    DataInputSourceType,
)


class ModelTransformInput(Buildable, ABC):
    """Abstract base for an input feeding a :class:`ModelTransformConfig`."""

    @property
    @abstractmethod
    def source_type(self) -> DataInputSourceType:
        """The :class:`DataInputSourceType` discriminator."""

    def build(self) -> dict[str, Any]:
        """Serialise to a JSON-compatible dict with a leading ``sourceType`` key."""
        result = {"sourceType": self.source_type.value}
        result.update(super().build())
        return result


class DynamicValuesInput(ModelTransformInput):
    """Injects current-time/date values, optionally localised to ``timezone_key``."""

    def __init__(self, timezone_key: Parameter | Calculation | None):
        self.timezone_key = timezone_key.id if timezone_key is not None else None

    @property
    def source_type(self) -> DataInputSourceType:
        return DataInputSourceType.DYNAMIC_VALUES


class _DataStoreLikeInput(ModelTransformInput):
    """Shared shape for data-store and data-store-interface inputs."""

    def __init__(
        self,
        data_store_key: str,
        tables: dict[str, str],
        model_filter: DataFilter | None,
        direct_data_pull: bool,
    ):
        self.data_store_key = data_store_key
        self.direct_data_pull = direct_data_pull
        self.model_filter = model_filter
        self.table_mapping = tables


class DataStoreInput(_DataStoreLikeInput):
    """Reads rows directly from a data store."""

    @property
    def source_type(self) -> DataInputSourceType:
        return DataInputSourceType.DATA_STORE


class DataStoreInterfaceInput(_DataStoreLikeInput):
    """Reads rows through a data-store interface layer."""

    @property
    def source_type(self) -> DataInputSourceType:
        return DataInputSourceType.DATA_STORE_INTERFACE


class DirectUploadInput(ModelTransformInput):
    """Reads rows from a directly-uploaded CSV (or ZIP of CSVs)."""

    def __init__(self, tables: dict[str, str]):
        self.table_mapping = tables

    @property
    def source_type(self) -> DataInputSourceType:
        return DataInputSourceType.DIRECT_UPLOAD
