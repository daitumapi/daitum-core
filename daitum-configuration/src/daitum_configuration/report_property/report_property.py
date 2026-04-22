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
This module defines the ReportProperty class, which encapsulates all metadata
and configuration related to exporting a report. It includes information such as
file format, file name key, visibility, ordering, and associated report data.

Classes:
    - ReportProperty: Represents export properties for a single report.
"""

from typing import Any

from typeguard import typechecked

from daitum_configuration.report_property.report_data import ReportData
from daitum_configuration.report_property.report_export_format import ReportExportFormat


# pylint: disable=too-many-arguments,too-many-positional-arguments,too-many-instance-attributes
# pylint: disable=too-few-public-methods
@typechecked
class ReportProperty:
    """
    Represents the configuration properties for exporting a report.
    """

    def __init__(
        self,
        export_format: ReportExportFormat,
        export_interface_key: str,
    ):
        """Initialises a ReportProperty."""
        self._export_format = export_format
        self._export_interface_key = export_interface_key
        self._export_csv: bool = False
        self._report_data: ReportData | None = None
        self._file_name_key: str | None = None
        self._name: str | None = None
        self._order_index: int = 0
        self._visible_on_navigator: bool = False
        self._show_in_menu: bool = True
        self._advanced_user: bool = False

    def set_report_data(self, report_data: ReportData) -> "ReportProperty":
        """Sets the report data."""
        self._report_data = report_data
        return self

    def set_file_name_key(self, file_name_key: str) -> "ReportProperty":
        """Sets the file name key."""
        self._file_name_key = file_name_key
        return self

    def set_order_index(self, order_index: int) -> "ReportProperty":
        """Sets the order index."""
        self._order_index = order_index
        return self

    def set_export_csv(self, export_csv: bool) -> "ReportProperty":
        """Sets whether the report is exported as CSV."""
        self._export_csv = export_csv
        return self

    def set_visible_on_navigator(self, visible_on_navigator: bool) -> "ReportProperty":
        """Sets whether the report is visible on the navigator."""
        self._visible_on_navigator = visible_on_navigator
        return self

    def set_name(self, name: str) -> "ReportProperty":
        """Sets the display name for the report."""
        self._name = name
        return self

    def set_show_in_menu(self, show_in_menu: bool) -> "ReportProperty":
        """Sets whether the report is shown in the menu."""
        self._show_in_menu = show_in_menu
        return self

    def set_advanced_user(self, advanced_user: bool) -> "ReportProperty":
        """Sets whether the report is for advanced users only."""
        self._advanced_user = advanced_user
        return self

    def report_name(self) -> str:
        """
        Returns the report name, falling back to export_interface_key if name is not set.

        Returns:
            str: The report name if available; otherwise, the export interface key.
        """
        return self._name if self._name is not None else self._export_interface_key

    def to_dict(self) -> dict[str, Any]:
        """
        Serializes the ReportProperty instance into a dictionary for easy JSON conversion.

        Returns:
            dict[str, Any]: A dictionary representation of this report configuration.
        """
        return {
            "exportCsv": self._export_csv,
            "exportFormat": self._export_format.value,
            "reportData": self._report_data.to_dict() if self._report_data else None,
            "exportInterfaceKey": self._export_interface_key,
            "fileNameKey": self._file_name_key,
            "name": self._name,
            "orderIndex": self._order_index,
            "visibleOnNavigator": self._visible_on_navigator,
            "showInMenu": self._show_in_menu,
            "advancedUser": self._advanced_user,
        }
