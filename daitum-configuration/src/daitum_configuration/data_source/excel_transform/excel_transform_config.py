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
This module defines the ExcelTransformConfig class, a concrete implementation of
DataSourceConfig for Excel-based data sources that require sheet mappings and
optional import behaviours. It supports customisation of sheet naming, object
reference handling, and per-sheet import options.

Classes:
    ExcelTransformConfig: Represents configuration for transforming Excel data.
"""

from typing import Any

from typeguard import typechecked

from daitum_configuration.data_source.data_source_config import DataSourceConfig
from daitum_configuration.data_source.data_source_type import DataSourceType
from daitum_configuration.data_source.excel_transform.import_option_overrides import (
    ImportOptionOverrides,
)


# pylint: disable=too-few-public-methods
@typechecked
class ExcelTransformConfig(DataSourceConfig):
    """
    Configuration class for Excel-based data sources requiring transformation and mapping.
    """

    def __init__(
        self,
        file_key: str,
        file_name: str,
        sheet_mapping: list[tuple[str, str]],
    ):
        """
        Initialises an ExcelTransformConfig instance.

        Args:
            file_key (str): Identifier used to locate the file internally.
            file_name (str): Display or user-facing file name.
            sheet_mapping (list[tuple[str, str]]): List of (source_sheet, destination_sheet)
                tuples.
        """
        self._file_key = file_key
        self._file_name = file_name
        self._sheet_mapping = sheet_mapping
        self._debug_file: bool = False
        self._manual_sheet_names: bool = False
        self._import_object_references_as_keys: bool = False
        self._per_sheet_overrides: dict[str, ImportOptionOverrides] = {}
        super().__init__()

    def set_debug_file(self, debug_file: bool) -> "ExcelTransformConfig":
        """
        Enables or disables debugging output.

        Args:
            debug_file (bool): If True, enables debugging output.

        Returns:
            ExcelTransformConfig: self, for method chaining.
        """
        self._debug_file = debug_file
        return self

    def set_manual_sheet_names(self, manual_sheet_names: bool) -> "ExcelTransformConfig":
        """
        Enables or disables manual sheet naming.

        Args:
            manual_sheet_names (bool): If True, enables manual sheet naming.

        Returns:
            ExcelTransformConfig: self, for method chaining.
        """
        self._manual_sheet_names = manual_sheet_names
        return self

    def set_import_object_references_as_keys(
        self, import_object_references_as_keys: bool
    ) -> "ExcelTransformConfig":
        """
        Sets whether object references are imported as keys.

        Args:
            import_object_references_as_keys (bool): If True, imports object references
                as keys.

        Returns:
            ExcelTransformConfig: self, for method chaining.
        """
        self._import_object_references_as_keys = import_object_references_as_keys
        return self

    def set_per_sheet_overrides(
        self, per_sheet_overrides: dict[str, ImportOptionOverrides]
    ) -> "ExcelTransformConfig":
        """
        Sets per-sheet import option overrides.

        Args:
            per_sheet_overrides (dict[str, ImportOptionOverrides]): Dictionary of
                overrides for specific sheets.

        Returns:
            ExcelTransformConfig: self, for method chaining.
        """
        self._per_sheet_overrides = per_sheet_overrides
        return self

    def _per_sheet_overrides_dict(self) -> dict[str, dict[str, Any]]:
        """
        Converts per-sheet overrides into a serialisable dictionary.

        This is useful when exporting the configuration or preparing it for
        transformation processing engines.

        Returns:
            dict[str, dict[str, Any]]: A dictionary mapping sheet names to their
            respective import override settings.
        """
        sheet_overrides_dict = {}
        for key, value in self._per_sheet_overrides.items():
            sheet_overrides_dict[key] = value.to_dict()

        return sheet_overrides_dict

    @property
    def type(self) -> DataSourceType:
        """
        Returns the type identifier for this data source configuration.
        """
        return DataSourceType.EXCEL_TRANSFORM

    def to_dict(self) -> dict:
        """
        Serialises the instance into a dictionary representation for ExcelTransformConfig.

        Returns:
            dict: A dictionary representation of the ExcelTransformConfig instance.
        """
        return {
            "type": self.type.value,
            "fileKey": self._file_key,
            "fileName": self._file_name,
            "debugFile": self._debug_file,
            "sheetNames": [],
            "manualSheetNames": self._manual_sheet_names,
            "sheetMapping": [
                {"sourceSheet": source, "targetSheet": target}
                for source, target in self._sheet_mapping
            ],
            "trackChangesSupported": self._track_changes_supported,
            "importObjectReferencesAsKeys": self._import_object_references_as_keys,
            "perSheetOverrides": (
                self._per_sheet_overrides_dict() if self._per_sheet_overrides else {}
            ),
        }
