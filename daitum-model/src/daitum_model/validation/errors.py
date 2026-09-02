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
Structured errors for the model-structure validation framework.

A :class:`ValidationIssue` is a *value object* describing one structural problem found in a
model — it is collected into a :class:`~daitum_model.validation.report.ValidationReport`
rather than raised. Only the aggregate :class:`ModelValidationError` is ever raised (from
``ModelBuilder.build()``), carrying every issue found in a single pass.

This is deliberately distinct from the runtime data-quality ``Validator`` hierarchy in
:mod:`daitum_model.validator`, which generates ``__invalid__`` / ``__message__`` calculated
fields for end users. Nothing here touches that system.

Every issue renders as ``"<location>: <message>."`` — the ``<NAME>: <reason>.`` shape used
by the formula ``Function`` error helpers — so build-time output reads consistently.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ValidationIssue:
    """One structural problem found during model validation.

    Attributes:
        rule_id: Stable machine id of the rule that produced this issue (e.g.
            ``"no-circular-table-dependencies"``); useful for programmatic filtering.
        location: A stable, human-readable path to the offending object, e.g.
            ``"table 'Orders'"`` or ``"calculation 'TOTAL_COST'"``.
        message: What is wrong and, where possible, how to fix it.
    """

    rule_id: str
    location: str
    message: str

    def render(self) -> str:
        """Return the canonical ``"<location>: <message>."`` string.

        A trailing full stop is appended only when the message does not already end with
        one, so callers may include their own terminal punctuation without doubling it.
        """
        suffix = "" if self.message.endswith(".") else "."
        return f"{self.location}: {self.message}{suffix}"

    def sort_key(self) -> tuple[str, str, str]:
        """Deterministic ordering key: ``(location, rule_id, message)``."""
        return (self.location, self.rule_id, self.message)


@dataclass(frozen=True)
class CircularDependencyError(ValidationIssue):
    """A cyclic dependency among tables or named values."""


@dataclass(frozen=True)
class FieldReferenceError(ValidationIssue):
    """A formula references a field that does not exist on its table."""


@dataclass(frozen=True)
class MissingSourceFieldError(ValidationIssue):
    """A derived/joined/union table references a field absent from its source table."""


@dataclass(frozen=True)
class TableReferenceError(ValidationIssue):
    """An object/map data type, or a structural source, names an unknown table."""


class ModelValidationError(Exception):
    """Raised by :meth:`ModelBuilder.build` when a model is structurally invalid.

    Carries every :class:`ValidationIssue` found in the pass, so a developer sees all
    problems at once rather than fixing and rebuilding one at a time.

    Attributes:
        issues: The structural problems found, in deterministic order.
    """

    def __init__(self, issues: list[ValidationIssue]) -> None:
        self.issues = sorted(issues, key=lambda issue: issue.sort_key())
        super().__init__(self._render())

    def _render(self) -> str:
        count = len(self.issues)
        noun = "problem" if count == 1 else "problems"
        lines = [f"Model validation found {count} {noun}:"]
        lines.extend(f"  {index}. {issue.render()}" for index, issue in enumerate(self.issues, 1))
        return "\n".join(lines)
