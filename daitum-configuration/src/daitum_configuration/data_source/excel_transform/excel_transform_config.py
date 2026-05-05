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

""":class:`ExcelTransformConfig` — Excel-based data source with sheet mappings."""

from typing import Any

from typeguard import typechecked

from daitum_configuration._buildable import Buildable
from daitum_configuration.data_source.data_source_config import DataSourceConfig
from daitum_configuration.data_source.data_source_type import DataSourceType
from daitum_configuration.data_source.excel_transform.import_option_overrides import (
    ImportOptionOverrides,
)


# pylint: disable=too-few-public-methods,too-many-instance-attributes
@typechecked
class _SheetMapping(Buildable):
    """Single source-to-target sheet pairing used inside :class:`ExcelTransformConfig`."""

    def __init__(self, source_sheet: str, target_sheet: str):
        self.source_sheet = source_sheet
        self.target_sheet = target_sheet


# pylint: disable=too-few-public-methods,too-many-instance-attributes
@typechecked
class ExcelTransformConfig(DataSourceConfig):
    """
    Data source that imports rows from an Excel workbook.

    Args:
        file_key: Internal storage key identifying the workbook file.
        file_name: Display-facing file name shown in the UI.
        sheet_mapping: ``(source_sheet, target_sheet)`` pairs feeding model tables.
    """

    def __init__(
        self,
        file_key: str,
        file_name: str,
        sheet_mapping: list[tuple[str, str]],
    ):
        self.file_key = file_key
        self.file_name = file_name
        self.debug_file: bool = False
        self.sheet_names: list[str] = []
        self.manual_sheet_names: bool = False
        self.sheet_mapping: list[_SheetMapping] = [
            _SheetMapping(source, target) for source, target in sheet_mapping
        ]
        self.import_object_references_as_keys: bool = False
        self.per_sheet_overrides: dict[str, ImportOptionOverrides] = {}
        super().__init__()

    def set_debug_file(self, debug_file: bool) -> "ExcelTransformConfig":
        """Emit a debug copy of the imported workbook."""
        self.debug_file = debug_file
        return self

    def set_manual_sheet_names(self, manual_sheet_names: bool) -> "ExcelTransformConfig":
        """Resolve sheet names manually rather than via the configured mapping."""
        self.manual_sheet_names = manual_sheet_names
        return self

    def set_import_object_references_as_keys(
        self, import_object_references_as_keys: bool
    ) -> "ExcelTransformConfig":
        """Treat object-reference cells as raw keys instead of resolved objects."""
        self.import_object_references_as_keys = import_object_references_as_keys
        return self

    def set_per_sheet_overrides(
        self, per_sheet_overrides: dict[str, ImportOptionOverrides]
    ) -> "ExcelTransformConfig":
        """Override import options per source sheet name."""
        self.per_sheet_overrides = per_sheet_overrides
        return self

    @property
    def type(self) -> DataSourceType:
        return DataSourceType.EXCEL_TRANSFORM

    def build(self) -> dict[str, Any]:
        """Serialise to a JSON-compatible dict."""
        return super().build()
