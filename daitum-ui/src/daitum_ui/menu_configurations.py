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

from enum import Enum

from typeguard import typechecked

from daitum_ui._buildable import Buildable


@typechecked
class DataMenuEntryType(Enum):
    """
    Enum representing the types of item the can be displayed in custom data menus.

    Types include:
        IMPORT_SHEET: import into a specified table in the model (key is table id)
        IMPORT: import into current table in model (key unused)
        BULK_IMPORT: bulk import into model (key unused)
        DATA_SOURCE: run data source specified by key
        REPORT: run report specified by key
        DIVIDER: divider element (key unused)
    """

    IMPORT_SHEET = "IMPORT_SHEET"
    IMPORT = "IMPORT"
    BULK_IMPORT = "BULK_IMPORT"
    DATA_SOURCE = "DATA_SOURCE"
    REPORT = "REPORT"
    DIVIDER = "DIVIDER"


@typechecked
class MenuConfigurations(Buildable):
    """
    Configuration options controlling the visibility of various menu items.

    Attributes:
       hide_optimisation:
           Whether to hide the optimisation menu option.
       hide_import:
           Whether to hide the main import menu option.
       hide_bulk_import:
           Whether to hide the bulk-import functionality.
       hide_import_into_sheets:
           Whether to hide the "import into sheets" functionality.
       data_menu:
           Whether to hide the "import into sheets" functionality.
    """

    def __init__(self):
        super().__init__()
        self.hide_optimisation: bool = False
        self.hide_import: bool = False
        self.hide_bulk_import: bool = False
        self.hide_import_into_sheets: bool = False
        self.data_menu: list[dict[str, str | None]] = list()

    def add_data_menu_entry(self, entry_type: DataMenuEntryType, key: str | None = None):
        """
        Adds an item to the data menu of the model.
        If any entries are added, then only those entries will be displayed, in the order they are
        added here. Other conditions that data sources/reports will also apply, but this will
        supersede the hide_import, hide_bulk_import and hide_import_into_sheets options

        Args:
            entry_type (DataMenuEntryType): the type of entry to show
            key (str):
                The view instance to be marked as the default view.
        """
        self.data_menu.append({"key": key, "type": entry_type.value})
