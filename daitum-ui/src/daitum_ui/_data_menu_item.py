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
from daitum_ui.icons import Icon
from daitum_ui.model_event import ModelEvent


@typechecked
class DataMenuEntryType(Enum):
    """
    Enum representing the types of item that can be displayed in custom data menus.

    Types include:
        IMPORT_SHEET: import into a specified table in the model (key is table id)
        IMPORT: import into current table in model (key unused)
        BULK_IMPORT: bulk import into model (key unused)
        DATA_SOURCE: run data source specified by key
        REPORT: run report specified by key
        DIVIDER: divider element (key unused)
        EVENT: run a model event (model_event object required, key unused)
    """

    IMPORT_SHEET = "IMPORT_SHEET"
    IMPORT = "IMPORT"
    BULK_IMPORT = "BULK_IMPORT"
    DATA_SOURCE = "DATA_SOURCE"
    REPORT = "REPORT"
    DIVIDER = "DIVIDER"
    EVENT = "EVENT"


_KEY_REQUIRED_TYPES = frozenset(
    {
        DataMenuEntryType.IMPORT_SHEET,
        DataMenuEntryType.DATA_SOURCE,
        DataMenuEntryType.REPORT,
    }
)


@typechecked
class DataMenuItem(Buildable):
    """
    A single entry in a custom data menu.

    Attributes:
        type:
            The type of menu entry.
        key:
            Identifier for the resource this entry targets. Required for IMPORT_SHEET,
            DATA_SOURCE, and REPORT; unused for IMPORT, BULK_IMPORT, DIVIDER, and EVENT.
        label:
            Display text for the menu item. Required for EVENT entries; optional elsewhere.
        icon:
            Optional icon displayed alongside the entry.
        prompt_user:
            Whether to show a confirmation prompt before triggering the action.
        prompt_text:
            Text displayed in the confirmation prompt; requires prompt_user=True.
        model_event:
            The model event to trigger. Required for EVENT entries.
    """

    def __init__(  # noqa: PLR0913
        self,
        type: DataMenuEntryType,
        key: str | None = None,
        label: str | None = None,
        icon: Icon | None = None,
        prompt_user: bool = False,
        prompt_text: str | None = None,
        model_event: ModelEvent | None = None,
    ) -> None:
        super().__init__()
        if type in _KEY_REQUIRED_TYPES and key is None:
            raise ValueError(f"key is required for DataMenuEntryType.{type.name}.")
        if type == DataMenuEntryType.EVENT and model_event is None:
            raise ValueError("model_event is required for DataMenuEntryType.EVENT.")
        if type == DataMenuEntryType.EVENT and label is None:
            raise ValueError("label is required for DataMenuEntryType.EVENT.")
        if prompt_text is not None:
            prompt_user = True
        self.type = type
        self.key = key
        self.label = label
        self.icon = icon
        self.prompt_user = prompt_user
        self.prompt_text = prompt_text
        self.model_event = model_event
