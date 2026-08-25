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
Data menu configuration for the Daitum UI framework.

This module provides the MenuConfiguration class, which controls the visibility of standard
menu items and lets you build a custom data menu from ordered entries (imports, data sources,
reports, dividers, and model events).

Keyword-only arguments:
    The ``add_*_entry`` methods use a bare ``*`` in their signatures to mark every argument
    after it as keyword-only. Arguments before the ``*`` (such as ``key`` or ``event``) may be
    passed positionally, but options like ``icon``, ``prompt_user``, and ``prompt_text`` must be
    passed by name. This keeps call sites self-documenting and prevents options from being passed
    in the wrong position::

        menu.add_import_sheet_entry("jobs", icon=Icon.UPLOAD, prompt_user=True)  # correct
        menu.add_import_sheet_entry("jobs", Icon.UPLOAD)                         # TypeError
"""

from typeguard import typechecked

from daitum_ui._buildable import Buildable
from daitum_ui._data_menu_item import DataMenuEntryType, DataMenuItem
from daitum_ui.data import Condition, to_condition
from daitum_ui.icons import Icon
from daitum_ui.model_event import ModelEvent


@typechecked
class MenuConfiguration(Buildable):
    """
    Configuration options controlling the visibility of various menu items.

    Each ``hide_*`` option is a :class:`~daitum_ui.data.Condition`; the menu item is hidden
    when the condition evaluates to true. A raw ``bool`` is accepted and coerced to a
    :class:`~daitum_ui.data.ConstantCondition`.

    Attributes:
        hide_optimisation:
            Condition controlling whether the optimisation menu option is hidden.
        hide_import:
            Condition controlling whether the main import menu option is hidden.
        hide_bulk_import:
            Condition controlling whether the bulk-import functionality is hidden.
        hide_import_into_sheets:
            Condition controlling whether the "import into sheets" functionality is hidden.
        data_menu:
            Custom data menu entries. When any entries are present, only those entries are
            displayed in the order they were added, superseding hide_import, hide_bulk_import,
            and hide_import_into_sheets. Other data source and report visibility conditions
            still apply.
    """

    def __init__(self) -> None:
        super().__init__()
        self.hide_optimisation: Condition = to_condition(False)
        self.hide_import: Condition = to_condition(False)
        self.hide_bulk_import: Condition = to_condition(False)
        self.hide_import_into_sheets: Condition = to_condition(False)
        self.data_menu: list[DataMenuItem] = []

    def add_import_sheet_entry(
        self,
        key: str,
        *,
        icon: Icon | None = None,
        prompt_user: bool = False,
        prompt_text: str | None = None,
        hidden: bool = False,
    ) -> DataMenuItem:
        """
        Adds an import-into-sheet entry targeting the table identified by key.

        Args:
            key: The table ID to import into.
            icon: Optional icon to display alongside the entry.
            prompt_user: Whether to show a confirmation prompt before importing.
            prompt_text: Text for the confirmation prompt; requires prompt_user=True.
            hidden: Whether the entry is hidden by default. Call ``set_conditional_hidden`` or
                ``set_permission_hidden`` on the returned entry to hide it dynamically.

        Returns:
            The created ``DataMenuItem``, so its visibility can be configured further.
        """
        entry = DataMenuItem(
            DataMenuEntryType.IMPORT_SHEET,
            key,
            icon=icon,
            prompt_user=prompt_user,
            prompt_text=prompt_text,
            hidden=hidden,
        )
        self.data_menu.append(entry)
        return entry

    def add_import_entry(
        self,
        *,
        icon: Icon | None = None,
        prompt_user: bool = False,
        prompt_text: str | None = None,
        hidden: bool = False,
    ) -> DataMenuItem:
        """
        Adds a general import entry for the current table.

        Args:
            icon: Optional icon to display alongside the entry.
            prompt_user: Whether to show a confirmation prompt before importing.
            prompt_text: Text for the confirmation prompt; requires prompt_user=True.
            hidden: Whether the entry is hidden by default. Call ``set_conditional_hidden`` or
                ``set_permission_hidden`` on the returned entry to hide it dynamically.

        Returns:
            The created ``DataMenuItem``, so its visibility can be configured further.

        Raises:
            ValueError: If an import entry has already been added.
        """
        if any(entry.type == DataMenuEntryType.IMPORT for entry in self.data_menu):
            raise ValueError("An import entry has already been added to the data menu.")
        entry = DataMenuItem(
            DataMenuEntryType.IMPORT,
            icon=icon,
            prompt_user=prompt_user,
            prompt_text=prompt_text,
            hidden=hidden,
        )
        self.data_menu.append(entry)
        return entry

    def add_bulk_import_entry(
        self,
        *,
        icon: Icon | None = None,
        prompt_user: bool = False,
        prompt_text: str | None = None,
        hidden: bool = False,
    ) -> DataMenuItem:
        """
        Adds a bulk import entry.

        Args:
            icon: Optional icon to display alongside the entry.
            prompt_user: Whether to show a confirmation prompt before importing.
            prompt_text: Text for the confirmation prompt; requires prompt_user=True.
            hidden: Whether the entry is hidden by default. Call ``set_conditional_hidden`` or
                ``set_permission_hidden`` on the returned entry to hide it dynamically.

        Returns:
            The created ``DataMenuItem``, so its visibility can be configured further.

        Raises:
            ValueError: If a bulk import entry has already been added.
        """
        if any(entry.type == DataMenuEntryType.BULK_IMPORT for entry in self.data_menu):
            raise ValueError("A bulk import entry has already been added to the data menu.")
        entry = DataMenuItem(
            DataMenuEntryType.BULK_IMPORT,
            icon=icon,
            prompt_user=prompt_user,
            prompt_text=prompt_text,
            hidden=hidden,
        )
        self.data_menu.append(entry)
        return entry

    def add_data_source_entry(
        self,
        key: str,
        *,
        icon: Icon | None = None,
        prompt_user: bool = False,
        prompt_text: str | None = None,
        hidden: bool = False,
    ) -> DataMenuItem:
        """
        Adds a data source entry that runs the data source identified by key.

        Args:
            key: The data source ID to run.
            icon: Optional icon to display alongside the entry.
            prompt_user: Whether to show a confirmation prompt before running.
            prompt_text: Text for the confirmation prompt; requires prompt_user=True.
            hidden: Whether the entry is hidden by default. Call ``set_conditional_hidden`` or
                ``set_permission_hidden`` on the returned entry to hide it dynamically.

        Returns:
            The created ``DataMenuItem``, so its visibility can be configured further.
        """
        entry = DataMenuItem(
            DataMenuEntryType.DATA_SOURCE,
            key,
            icon=icon,
            prompt_user=prompt_user,
            prompt_text=prompt_text,
            hidden=hidden,
        )
        self.data_menu.append(entry)
        return entry

    def add_report_entry(
        self,
        key: str,
        *,
        icon: Icon | None = None,
        prompt_user: bool = False,
        prompt_text: str | None = None,
        hidden: bool = False,
    ) -> DataMenuItem:
        """
        Adds a report entry that runs the report identified by key.

        Args:
            key: The report ID to run.
            icon: Optional icon to display alongside the entry.
            prompt_user: Whether to show a confirmation prompt before running.
            prompt_text: Text for the confirmation prompt; requires prompt_user=True.
            hidden: Whether the entry is hidden by default. Call ``set_conditional_hidden`` or
                ``set_permission_hidden`` on the returned entry to hide it dynamically.

        Returns:
            The created ``DataMenuItem``, so its visibility can be configured further.
        """
        entry = DataMenuItem(
            DataMenuEntryType.REPORT,
            key,
            icon=icon,
            prompt_user=prompt_user,
            prompt_text=prompt_text,
            hidden=hidden,
        )
        self.data_menu.append(entry)
        return entry

    def add_divider_entry(self) -> DataMenuItem:
        """Adds a visual divider between entries in the data menu."""
        entry = DataMenuItem(DataMenuEntryType.DIVIDER)
        self.data_menu.append(entry)
        return entry

    def add_event_entry(
        self,
        event: ModelEvent,
        label: str,
        *,
        icon: Icon | None = None,
        hidden: bool = False,
    ) -> DataMenuItem:
        """
        Adds a model event entry that triggers the given event.

        Args:
            event: The model event to trigger.
            label: Display text for the menu item.
            icon: Optional icon to display alongside the entry.
            hidden: Whether the entry is hidden by default. Call ``set_conditional_hidden`` or
                ``set_permission_hidden`` on the returned entry to hide it dynamically.

        Returns:
            The created ``DataMenuItem``, so its visibility can be configured further.
        """
        entry = DataMenuItem(
            DataMenuEntryType.EVENT,
            label=label,
            icon=icon,
            model_event=event,
            hidden=hidden,
        )
        self.data_menu.append(entry)
        return entry
