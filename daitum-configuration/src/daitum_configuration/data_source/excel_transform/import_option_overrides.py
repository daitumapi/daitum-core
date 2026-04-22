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
This module defines the ImportOptionOverrides class, which allows fine-grained control
over how data is imported from external sources like Excel sheets. It provides options
to enforce structure, preserve ordering, and manage existing data during import.

Classes:
    ImportOptionOverrides: Configures custom import behaviour for a given data source or sheet.

"""

from typeguard import typechecked


# pylint: disable=too-many-instance-attributes
# pylint: disable=too-few-public-methods
@typechecked
class ImportOptionOverrides:
    """
    Represents customisation options for importing data, such as validation, structure
    enforcement, and row matching behaviour.
    """

    def __init__(
        self,
        match_column_count: bool = False,
        match_column_headers: bool = False,
        match_existing_rows: bool = False,
        preserve_ordering: bool = False,
    ):
        """
        Initialises an ImportOptionOverrides instance with optional import validation and
        behaviour settings.

        Args:
            match_column_count (bool): Whether to enforce exact column count during import.
            match_column_headers (bool): Whether to validate that headers match expected ones.
            match_existing_rows (bool): Whether to attempt row matching with existing data.
            preserve_ordering (bool): Whether to preserve the order of rows from the source.
        """
        self._match_column_count = match_column_count
        self._match_column_headers = match_column_headers
        self._match_existing_rows = match_existing_rows
        self._preserve_ordering = preserve_ordering
        self._clear_sheet: bool = False
        self._reset_decisions: bool = False
        self._expected_column_count: int | None = None
        self._key_column: str | None = None

    def set_clear_sheet(self, clear_sheet: bool) -> "ImportOptionOverrides":
        """
        Sets whether to clear existing data in the sheet before import.

        Args:
            clear_sheet (bool): If True, clears existing data before import.

        Returns:
            ImportOptionOverrides: self, for method chaining.
        """
        self._clear_sheet = clear_sheet
        return self

    def set_reset_decisions(self, reset_decisions: bool) -> "ImportOptionOverrides":
        """
        Sets whether to reset prior decisions on rows during import.

        Args:
            reset_decisions (bool): If True, resets prior decisions on rows.

        Returns:
            ImportOptionOverrides: self, for method chaining.
        """
        self._reset_decisions = reset_decisions
        return self

    def set_expected_column_count(self, expected_column_count: int) -> "ImportOptionOverrides":
        """
        Sets the number of columns expected in the source.

        Args:
            expected_column_count (int): Number of columns expected in the source.

        Returns:
            ImportOptionOverrides: self, for method chaining.
        """
        self._expected_column_count = expected_column_count
        return self

    def set_key_column(self, key_column: str) -> "ImportOptionOverrides":
        """
        Sets the name of the key column for row matching.

        Args:
            key_column (str): Name of the key column for row matching.

        Returns:
            ImportOptionOverrides: self, for method chaining.
        """
        self._key_column = key_column
        return self

    def to_dict(self) -> dict:
        """
        Serialises the instance into a dictionary representation for ImportOptionOverrides.

        Returns:
            dict: A dictionary representation of the ImportOptionOverrides instance.
        """
        return {
            "matchColumnCount": self._match_column_count,
            "matchColumnHeaders": self._match_column_headers,
            "matchExistingRows": self._match_existing_rows,
            "preserveOrdering": self._preserve_ordering,
            "clearSheet": self._clear_sheet,
            "resetDecisions": self._reset_decisions,
            "expectedColumnCount": self._expected_column_count,
            "keyColumn": self._key_column,
        }
