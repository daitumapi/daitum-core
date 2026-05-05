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

""":class:`ImportOptionOverrides` — per-sheet overrides used by :class:`ExcelTransformConfig`."""

from typeguard import typechecked

from daitum_configuration._buildable import Buildable


# pylint: disable=too-many-instance-attributes
# pylint: disable=too-few-public-methods
@typechecked
class ImportOptionOverrides(Buildable):
    """
    Per-sheet overrides for column matching, ordering, and row reconciliation.

    Args:
        match_column_count: Reject the import if the column count differs.
        match_column_headers: Reject the import if column headers differ.
        match_existing_rows: Match incoming rows to existing rows by key.
        preserve_ordering: Preserve the source row order in the target.
    """

    def __init__(
        self,
        match_column_count: bool = False,
        match_column_headers: bool = False,
        match_existing_rows: bool = False,
        preserve_ordering: bool = False,
    ):
        self.match_column_count = match_column_count
        self.match_column_headers = match_column_headers
        self.match_existing_rows = match_existing_rows
        self.preserve_ordering = preserve_ordering
        self.clear_sheet: bool = False
        self.reset_decisions: bool = False
        self.expected_column_count: int | None = None
        self.key_column: str | None = None

    def set_clear_sheet(self, clear_sheet: bool) -> "ImportOptionOverrides":
        """Clear the sheet before writing imported rows."""
        self.clear_sheet = clear_sheet
        return self

    def set_reset_decisions(self, reset_decisions: bool) -> "ImportOptionOverrides":
        """Reset decision-variable values for any matched rows on import."""
        self.reset_decisions = reset_decisions
        return self

    def set_expected_column_count(self, expected_column_count: int) -> "ImportOptionOverrides":
        """Set the column count enforced when ``match_column_count`` is True."""
        self.expected_column_count = expected_column_count
        return self

    def set_key_column(self, key_column: str) -> "ImportOptionOverrides":
        """Set the column used to match incoming rows against existing ones."""
        self.key_column = key_column
        return self
