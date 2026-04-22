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
This module defines the configuration for the MODEL_TRANSFORM data source type.
This data source takes input from the model and optional external sources such as data stores,
and uses a secondary v3 model to transform that data before importing it back into the model

Classes:
    ModelTransformConfig: The main configuration class.
"""

from daitum_model import Calculation, DataType, Parameter
from typeguard import typechecked

from daitum_configuration.data_source.data_source_config import DataSourceConfig
from daitum_configuration.data_source.data_source_type import DataSourceType
from daitum_configuration.data_source.data_store.data_filter import DataFilter
from daitum_configuration.data_source.model_transform.data_input_source_type import (
    DataInputSourceType,
)


@typechecked
class ModelTransformConfig(DataSourceConfig):
    """
    Configuration class for v3 model based data sources handling importing, transformation and
    mapping.

    Attributes:
        _file_key (str): Internal key identifying the ModelTransform file in the extra-files sub
            folder, must be file name excluding extension.
        _file_name (str): Display or original name of the file.
        _debug_file (bool): If true, the sub-model will be written to a file for debugging.
    """

    def __init__(self, file_key: str, file_name: str, debug_file: bool = False):
        self._file_key = file_key
        self._file_name = file_name
        self._inputs: list[dict] = []
        self._debug_file = debug_file
        super().__init__(track_changes_supported=True)

    def add_dynamic_values(self, timezone_key: Parameter | Calculation | None):
        """
        Option to inject dynamic values into input data.
        These will be injected in specific named values in the model.
        For non-UTC time related values, the optional timezone_key is required.
        Currently supported values are:
         - CURRENT_DATETIME_UTC (DATETIME)
         - CURRENT_DATE_UTC (DATE)
         - CURRENT_TIME_UTC (TIME)
         - CURRENT_DATETIME (DATETIME)
         - CURRENT_DATE (DATE)
         - CURRENT_TIME (TIME)

        Args:
            timezone_key: option reference to a timezone string in the model

        """
        if timezone_key is not None and timezone_key.to_data_type() != DataType.STRING:
            raise ValueError(f"Invalid timezone key with type {timezone_key.to_data_type()}")
        self._inputs.append(
            {
                "sourceType": DataInputSourceType.DYNAMIC_VALUES.value,
                "timezoneKey": timezone_key.id if timezone_key is not None else None,
            }
        )

    def add_datastore_input(
        self,
        data_store_key: str,
        tables: dict[str, str],
        model_filter: DataFilter | None = None,
        direct_data_pull: bool = False,
    ):
        """
        Adds datastore input

        Args:
            data_store_key: the storage key that identifies the datastore
            tables: a mapping of datastore table to sub-model table
            model_filter: optional filter to apply to the datastore data
            direct_data_pull: if true, will pull data directly from datastore's backing source

        """
        self._inputs.append(
            {
                "sourceType": DataInputSourceType.DATA_STORE.value,
                "dataStoreKey": data_store_key,
                "directDataPull": direct_data_pull,
                "modelFilter": model_filter.to_dict() if model_filter is not None else None,
                "tableMapping": tables,
            }
        )

    def add_datastore_interface_input(
        self,
        data_store_key: str,
        tables: dict[str, str],
        model_filter: DataFilter | None = None,
        direct_data_pull: bool = False,
    ):
        """
        Adds datastore interface input

        Args:
            data_store_key: the interface name/key
            tables: a mapping of datastore table to sub-model table
            model_filter: optional filter to apply to the datastore data
            direct_data_pull: if true, will pull data directly from datastore's backing source

        """
        self._inputs.append(
            {
                "sourceType": DataInputSourceType.DATA_STORE_INTERFACE.value,
                "dataStoreKey": data_store_key,
                "directDataPull": direct_data_pull,
                "modelFilter": model_filter.to_dict() if model_filter is not None else None,
                "tableMapping": tables,
            }
        )

    @property
    def type(self) -> DataSourceType:
        """
        Returns the type identifier for this data source configuration.
        """
        return DataSourceType.MODEL_TRANSFORM

    def to_dict(self) -> dict:
        """
        Serializes the instance into a dictionary representation for ModelTransformConfig.

        Returns:
            dict: A dictionary representation of the ModelTransformConfig instance.
        """
        return {
            "type": self.type.value,
            "fileKey": self._file_key,
            "fileName": self._file_name,
            "inputs": self._inputs,
            "debugFile": self._debug_file,
        }
