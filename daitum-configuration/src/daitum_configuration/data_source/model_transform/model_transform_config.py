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

""":class:`ModelTransformConfig` — data source backed by a secondary modelling-language model."""

from daitum_model import Calculation, DataType, Parameter
from typeguard import typechecked

from daitum_configuration.data_source.data_source_config import DataSourceConfig
from daitum_configuration.data_source.data_source_type import DataSourceType
from daitum_configuration.data_source.data_store.data_filter import DataFilter
from daitum_configuration.data_source.model_transform.model_transform_input import (
    DataStoreInput,
    DataStoreInterfaceInput,
    DirectUploadInput,
    DynamicValuesInput,
    ModelTransformInput,
)


@typechecked
class ModelTransformConfig(DataSourceConfig):
    """
    Data source that runs a secondary model and feeds its outputs back into the parent.

    Inputs to the secondary model are registered via the ``add_*_input`` methods.

    Args:
        file_key: Storage key identifying the secondary-model file.
        file_name: Display-facing file name for the secondary model.
        debug_file: Emit a debug copy of the transform inputs/outputs.
    """

    def __init__(self, file_key: str, file_name: str, debug_file: bool = False):
        self.file_key = file_key
        self.file_name = file_name
        self.inputs: list[ModelTransformInput] = []
        self.debug_file = debug_file
        super().__init__(track_changes_supported=True)

    def add_dynamic_values(
        self, timezone_key: Parameter | Calculation | None
    ) -> "ModelTransformConfig":
        """Inject current-time/date variants as inputs.

        Args:
            timezone_key: Optional model named value of type ``STRING`` supplying
                an IANA timezone for non-UTC time variants.
        """
        if timezone_key is not None and timezone_key.to_data_type() != DataType.STRING:
            raise ValueError(f"Invalid timezone key with type {timezone_key.to_data_type()}")
        self.inputs.append(DynamicValuesInput(timezone_key))
        return self

    def add_datastore_input(
        self,
        data_store_key: str,
        tables: dict[str, str],
        model_filter: DataFilter | None = None,
        direct_data_pull: bool = False,
    ) -> "ModelTransformConfig":
        """Register a data-store input feeding the secondary model."""
        self.inputs.append(DataStoreInput(data_store_key, tables, model_filter, direct_data_pull))
        return self

    def add_datastore_interface_input(
        self,
        data_store_key: str,
        tables: dict[str, str],
        model_filter: DataFilter | None = None,
        direct_data_pull: bool = False,
    ) -> "ModelTransformConfig":
        """Register a data-store-interface input feeding the secondary model."""
        self.inputs.append(
            DataStoreInterfaceInput(data_store_key, tables, model_filter, direct_data_pull)
        )
        return self

    def add_direct_upload_input(self, tables: dict[str, str]) -> "ModelTransformConfig":
        """Register a direct-upload (CSV) input feeding the secondary model."""
        self.inputs.append(DirectUploadInput(tables))
        return self

    @property
    def type(self) -> DataSourceType:
        return DataSourceType.MODEL_TRANSFORM
