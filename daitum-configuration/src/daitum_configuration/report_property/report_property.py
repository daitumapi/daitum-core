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

""":class:`ReportProperty` — export-time configuration for one report."""

from typeguard import typechecked

from daitum_configuration._buildable import Buildable
from daitum_configuration.report_property.report_data import ReportData
from daitum_configuration.report_property.report_export_format import ReportExportFormat


# pylint: disable=too-many-arguments,too-many-positional-arguments,too-many-instance-attributes
# pylint: disable=too-few-public-methods
@typechecked
class ReportProperty(Buildable):
    """
    Export configuration for a single report.

    Register on a :class:`~daitum_configuration.ConfigurationBuilder` via
    :meth:`~daitum_configuration.ConfigurationBuilder.add_report_property`;
    chain ``set_*`` methods to customise visibility and behaviour.

    Args:
        export_format: :class:`ReportExportFormat` (e.g. XLSX, CSV).
        export_interface_key: Optional key identifying the export interface
            template; used as a fallback display name.
    """

    def __init__(
        self,
        export_format: ReportExportFormat,
        export_interface_key: str | None = None,
    ):
        self.export_csv: bool = False
        self.export_format = export_format
        self.report_data: ReportData | None = None
        self.export_interface_key = export_interface_key
        self.file_name_key: str | None = None
        self.name: str | None = None
        self.order_index: int = 0
        self.visible_on_navigator: bool = False
        self.show_in_menu: bool = True
        self.advanced_user: bool = False

    def set_report_data(self, report_data: ReportData) -> "ReportProperty":
        """Attach :class:`ReportData` describing the rows that feed this report."""
        self.report_data = report_data
        return self

    def set_file_name_key(self, file_name_key: str) -> "ReportProperty":
        """Set the key of the model parameter supplying the export file name."""
        self.file_name_key = file_name_key
        return self

    def set_order_index(self, order_index: int) -> "ReportProperty":
        """Set the position of this report in the navigator."""
        self.order_index = order_index
        return self

    def set_export_csv(self, export_csv: bool) -> "ReportProperty":
        """Also export this report as CSV alongside its primary format."""
        self.export_csv = export_csv
        return self

    def set_visible_on_navigator(self, visible_on_navigator: bool) -> "ReportProperty":
        """Show this report in the side navigator."""
        self.visible_on_navigator = visible_on_navigator
        return self

    def set_name(self, name: str) -> "ReportProperty":
        """Set the display name; falls back to ``export_interface_key`` when unset."""
        self.name = name
        return self

    def set_show_in_menu(self, show_in_menu: bool) -> "ReportProperty":
        """Show this report in the export menu."""
        self.show_in_menu = show_in_menu
        return self

    def set_advanced_user(self, advanced_user: bool) -> "ReportProperty":
        """Restrict this report to advanced users."""
        self.advanced_user = advanced_user
        return self

    def report_name(self) -> str | None:
        """Return the display name, falling back to ``export_interface_key`` if unset."""
        if self.name is not None:
            return self.name

        if self.export_interface_key is not None:
            return self.export_interface_key

        return None
