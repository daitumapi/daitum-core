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

"""Rule: no dependency cycle among tables and calculations.

The platform orders tables and calculations in a single topological sort, so this one rule
walks the single combined :attr:`ModelGraph.build_order_edges` graph. It subsumes what used
to be three separate checks (table-only, calculation-only, and the cross-domain gap between
them): a cycle can run table -> table, calculation -> calculation, or alternate across the
boundary (a calculated field on table T reads a calculation C that aggregates T), and all
three are the same defect — a build order that cannot be linearised.

Intra-table field cycles are a different concern (field ordering within one table, with the
combo-field exception) and stay in :mod:`daitum_model.validation.rules.field_cycles`.
"""

from __future__ import annotations

from daitum_model.validation.engine import rule
from daitum_model.validation.errors import CircularDependencyError
from daitum_model.validation.graph import (
    ModelGraph,
    describe_node,
    detect_cycles,
    find_cycle_path,
)
from daitum_model.validation.report import ValidationReport


@rule
class NoCircularBuildOrderDependencies:
    """Detect cyclic dependencies among tables and calculations (combined build order)."""

    id = "no-circular-build-order-dependencies"

    def check(self, graph: ModelGraph, report: ValidationReport) -> None:
        edges = graph.build_order_edges
        for group in detect_cycles(edges):
            path = find_cycle_path(edges, group)
            report.add(
                CircularDependencyError(
                    rule_id=self.id,
                    location=" -> ".join(describe_node(node) for node in path),
                    message=(
                        "circular dependency in the table/calculation build order; "
                        "break the cycle so each table and calculation depends only on "
                        "ones built before it"
                    ),
                )
            )
