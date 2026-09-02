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
The accumulator that collects :class:`ValidationIssue`s during a validation pass.

A :class:`ValidationReport` gathers issues from every rule without raising, so a single
pass can report all problems at once. ``ModelBuilder.build()`` calls
:meth:`ValidationReport.raise_if_errors` to turn a non-empty report into a
:class:`ModelValidationError`; ``ModelBuilder.validate()`` returns the report directly for
programmatic inspection.
"""

from __future__ import annotations

from collections.abc import Iterable, Iterator

from daitum_model.validation.errors import ModelValidationError, ValidationIssue


class ValidationReport:
    """Collects the structural issues found during a model validation pass."""

    def __init__(self) -> None:
        self._issues: list[ValidationIssue] = []

    @property
    def issues(self) -> list[ValidationIssue]:
        """The collected issues, sorted deterministically by location then rule."""
        return sorted(self._issues, key=lambda issue: issue.sort_key())

    def add(self, issue: ValidationIssue) -> None:
        """Record a single issue."""
        self._issues.append(issue)

    def extend(self, issues: Iterable[ValidationIssue]) -> None:
        """Record several issues."""
        self._issues.extend(issues)

    @property
    def ok(self) -> bool:
        """``True`` when no issues have been recorded."""
        return not self._issues

    def by_rule(self, rule_id: str) -> list[ValidationIssue]:
        """Return the issues produced by a given rule, in deterministic order."""
        return [issue for issue in self.issues if issue.rule_id == rule_id]

    def raise_if_errors(self) -> None:
        """Raise :class:`ModelValidationError` if any issue has been recorded."""
        if self._issues:
            raise ModelValidationError(self.issues)

    def __bool__(self) -> bool:
        return bool(self._issues)

    def __len__(self) -> int:
        return len(self._issues)

    def __iter__(self) -> Iterator[ValidationIssue]:
        return iter(self.issues)
