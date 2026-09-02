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
The rule engine that drives a model validation pass.

A :class:`Rule` inspects a :class:`~daitum_model.validation.graph.ModelGraph` and appends
any problems it finds to a :class:`~daitum_model.validation.report.ValidationReport` — it
never raises, so one pass can report every problem at once. Rules register themselves via
the :func:`rule` class decorator, so adding a check is a single new file plus one decorator;
:func:`validate_model` runs the whole registry.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol, TypeVar, runtime_checkable

from daitum_model.validation.graph import ModelGraph
from daitum_model.validation.report import ValidationReport

if TYPE_CHECKING:
    from daitum_model.model import ModelBuilder


@runtime_checkable
class Rule(Protocol):
    """A single, independent structural check.

    Implementations set a stable ``id`` (used as the ``rule_id`` on emitted issues and for
    programmatic filtering) and append issues to the report in :meth:`check`.
    """

    id: str

    def check(self, graph: ModelGraph, report: ValidationReport) -> None:
        """Inspect *graph* and append any issues found to *report*."""


#: Every registered rule, in registration order. Populated by the :func:`rule` decorator as
#: the ``rules`` subpackage is imported.
RULES: list[Rule] = []

_RuleT = TypeVar("_RuleT", bound=type)


def rule(cls: _RuleT) -> _RuleT:
    """Class decorator registering a stateless :class:`Rule` singleton in :data:`RULES`."""
    RULES.append(cls())
    return cls


def validate_model(model: ModelBuilder) -> ValidationReport:
    """Run every registered rule over *model* and return the collected report.

    Does not raise; callers decide what to do with the report (``build()`` calls
    :meth:`ValidationReport.raise_if_errors`, ``validate()`` returns it directly).
    """
    from . import rules  # noqa: F401  pylint: disable=import-outside-toplevel,cyclic-import

    graph = ModelGraph.from_model(model)
    report = ValidationReport()
    for registered in RULES:
        registered.check(graph, report)
    return report
