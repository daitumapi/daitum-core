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
This module defines the ModelImportOptions class, representing configuration options
for data imports including column matching, file handling, and synchronization settings.
"""

from typeguard import typechecked


# pylint: disable=too-many-arguments,too-many-positional-arguments,too-many-instance-attributes
# pylint: disable=too-few-public-methods
@typechecked
class ModelImportOptions:
    """
    Data model representing import configuration options.
    """

    def __init__(self):
        """Initialises ModelImportOptions with default values."""
        self._match_column_count: bool = True
        self._expected_column_count: int = 0
        self._match_column_headers: bool = True
        self._preserve_ordering: bool = False
        self._match_existing_rows: bool = False
        self._clear_sheet: bool = True
        self._reset_decisions: bool = False
        self._close_on_success: bool = True
        self._skip_pre_processors: bool = False
        self._key_column: str | None = None
        self._locale_key: str | None = None
        self._sync_key: str | None = None

    def set_match_column_count(self, match_column_count: bool) -> "ModelImportOptions":
        """Sets whether column count must match."""
        self._match_column_count = match_column_count
        return self

    def set_expected_column_count(self, expected_column_count: int) -> "ModelImportOptions":
        """Sets the expected column count."""
        self._expected_column_count = expected_column_count
        return self

    def set_match_column_headers(self, match_column_headers: bool) -> "ModelImportOptions":
        """Sets whether column headers must match."""
        self._match_column_headers = match_column_headers
        return self

    def set_preserve_ordering(self, preserve_ordering: bool) -> "ModelImportOptions":
        """Sets whether row ordering is preserved."""
        self._preserve_ordering = preserve_ordering
        return self

    def set_match_existing_rows(self, match_existing_rows: bool) -> "ModelImportOptions":
        """Sets whether existing rows are matched."""
        self._match_existing_rows = match_existing_rows
        return self

    def set_clear_sheet(self, clear_sheet: bool) -> "ModelImportOptions":
        """Sets whether the sheet is cleared before import."""
        self._clear_sheet = clear_sheet
        return self

    def set_reset_decisions(self, reset_decisions: bool) -> "ModelImportOptions":
        """Sets whether decision variables are reset on import."""
        self._reset_decisions = reset_decisions
        return self

    def set_close_on_success(self, close_on_success: bool) -> "ModelImportOptions":
        """Sets whether the import dialog closes on success."""
        self._close_on_success = close_on_success
        return self

    def set_skip_pre_processors(self, skip_pre_processors: bool) -> "ModelImportOptions":
        """Sets whether pre-processors are skipped."""
        self._skip_pre_processors = skip_pre_processors
        return self

    def set_key_column(self, key_column: str) -> "ModelImportOptions":
        """Sets the key column for row matching."""
        self._key_column = key_column
        return self

    def set_locale_key(self, locale_key: str) -> "ModelImportOptions":
        """Sets the locale key for localised imports."""
        self._locale_key = locale_key
        return self

    def set_sync_key(self, sync_key: str) -> "ModelImportOptions":
        """Sets the synchronisation key."""
        self._sync_key = sync_key
        return self

    def get_sync_key(self) -> str:
        """
        Get the synchronization key, returning empty string if None or blank.
        """
        return self._sync_key if self._sync_key and self._sync_key.strip() else ""

    def generate_sync_key(self, user) -> str:
        """
        Generate a synchronization key combining user ID with the existing sync key.

        Args:
            user: User object with id attribute

        Returns:
            str: Generated synchronization key in format "user_id/sync_key"
        """

        return f"{user.id}/{self._sync_key}" if self._sync_key else ""

    def to_dict(self) -> dict:
        """
        Serializes the ModelImportOptions instance to a dictionary.

        Returns:
            dict: A dictionary representation of the ModelImportOptions instance.
        """
        return {
            "matchColumnCount": self._match_column_count,
            "expectedColumnCount": self._expected_column_count,
            "matchColumnHeaders": self._match_column_headers,
            "preserveOrdering": self._preserve_ordering,
            "matchExistingRows": self._match_existing_rows,
            "clearSheet": self._clear_sheet,
            "resetDecisions": self._reset_decisions,
            "closeOnSuccess": self._close_on_success,
            "skipPreProcessors": self._skip_pre_processors,
            "keyColumn": self._key_column,
            "localeKey": self._locale_key,
            "syncKey": self._sync_key,
        }
