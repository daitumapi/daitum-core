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

"""Rule: tables must not depend on each other in a cycle."""

from __future__ import annotations

from daitum_model.validation.engine import rule
from daitum_model.validation.errors import CircularDependencyError
from daitum_model.validation.graph import ModelGraph, detect_cycles, find_cycle_path
from daitum_model.validation.report import ValidationReport


@rule
class NoCircularTableDependencies:
    """Detect cyclic dependencies among tables.

    Edges come from structural sources (derived source tables, join conditions, union
    sources) and object/map reference fields. The platform forbids circular table
    dependencies; this catches them at build time rather than on upload.
    """

    id = "no-circular-table-dependencies"

    def check(self, graph: ModelGraph, report: ValidationReport) -> None:
        for group in detect_cycles(graph.table_edges):
            path = find_cycle_path(graph.table_edges, group)
            report.add(
                CircularDependencyError(
                    rule_id=self.id,
                    location=f"tables {' -> '.join(path)}",
                    message=(
                        "circular dependency between tables; "
                        "break the cycle so each table depends only on tables built before it"
                    ),
                )
            )
