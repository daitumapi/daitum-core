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

""":class:`ModelImportOptions` — model-level import defaults."""

from typeguard import typechecked

from daitum_configuration._buildable import Buildable


# pylint: disable=too-many-arguments,too-many-positional-arguments,too-many-instance-attributes
# pylint: disable=too-few-public-methods
@typechecked
class ModelImportOptions(Buildable):
    """
    Default import behaviour applied to every data source on the model.

    Construct with default flags, then customise via the chained ``set_*`` methods.
    """

    def __init__(self):
        self.match_column_count: bool = True
        self.expected_column_count: int = 0
        self.match_column_headers: bool = True
        self.preserve_ordering: bool = False
        self.match_existing_rows: bool = False
        self.clear_sheet: bool = True
        self.reset_decisions: bool = False
        self.close_on_success: bool = True
        self.skip_pre_processors: bool = False
        self.key_column: str | None = None
        self.locale_key: str | None = None
        self.sync_key: str | None = None

    def set_match_column_count(self, match_column_count: bool) -> "ModelImportOptions":
        """Reject imports whose column count differs from the target."""
        self.match_column_count = match_column_count
        return self

    def set_expected_column_count(self, expected_column_count: int) -> "ModelImportOptions":
        """Set the column count enforced when ``match_column_count`` is True."""
        self.expected_column_count = expected_column_count
        return self

    def set_match_column_headers(self, match_column_headers: bool) -> "ModelImportOptions":
        """Reject imports whose column headers differ from the target."""
        self.match_column_headers = match_column_headers
        return self

    def set_preserve_ordering(self, preserve_ordering: bool) -> "ModelImportOptions":
        """Preserve source row order in the target."""
        self.preserve_ordering = preserve_ordering
        return self

    def set_match_existing_rows(self, match_existing_rows: bool) -> "ModelImportOptions":
        """Match incoming rows against existing rows by ``key_column``."""
        self.match_existing_rows = match_existing_rows
        return self

    def set_clear_sheet(self, clear_sheet: bool) -> "ModelImportOptions":
        """Clear the sheet before writing imported rows."""
        self.clear_sheet = clear_sheet
        return self

    def set_reset_decisions(self, reset_decisions: bool) -> "ModelImportOptions":
        """Reset decision-variable values on matched rows."""
        self.reset_decisions = reset_decisions
        return self

    def set_close_on_success(self, close_on_success: bool) -> "ModelImportOptions":
        """Auto-close the import dialog on successful import."""
        self.close_on_success = close_on_success
        return self

    def set_skip_pre_processors(self, skip_pre_processors: bool) -> "ModelImportOptions":
        """Skip configured pre-processors during import."""
        self.skip_pre_processors = skip_pre_processors
        return self

    def set_key_column(self, key_column: str) -> "ModelImportOptions":
        """Set the column used to match incoming rows against existing ones."""
        self.key_column = key_column
        return self

    def set_locale_key(self, locale_key: str) -> "ModelImportOptions":
        """Set the locale used to parse incoming numbers, dates, and currency."""
        self.locale_key = locale_key
        return self

    def set_sync_key(self, sync_key: str) -> "ModelImportOptions":
        """Set the per-user synchronisation key used by :meth:`generate_sync_key`."""
        self.sync_key = sync_key
        return self

    def get_sync_key(self) -> str:
        """Return the sync key, or an empty string if unset or whitespace."""
        return self.sync_key if self.sync_key and self.sync_key.strip() else ""

    def generate_sync_key(self, user) -> str:
        """Build a per-user sync key in the form ``"<user_id>/<sync_key>"``.

        Args:
            user: Object exposing an ``id`` attribute.
        """
        return f"{user.id}/{self.sync_key}" if self.sync_key else ""
