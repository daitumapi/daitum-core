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

"""Rule: calculations must not reference each other in a cycle."""

from __future__ import annotations

from daitum_model.validation.engine import rule
from daitum_model.validation.errors import CircularDependencyError
from daitum_model.validation.graph import ModelGraph, detect_cycles, find_cycle_path
from daitum_model.validation.report import ValidationReport


@rule
class NoCircularNamedValueDependencies:
    """Detect cyclic dependencies among calculations.

    Edges come from each calculation's formula dependencies (only the calculation leaves;
    parameters are constants and cannot close a cycle). A calculation that transitively
    depends on itself can never be evaluated.
    """

    id = "no-circular-named-value-dependencies"

    def check(self, graph: ModelGraph, report: ValidationReport) -> None:
        for group in detect_cycles(graph.named_value_edges):
            path = find_cycle_path(graph.named_value_edges, group)
            report.add(
                CircularDependencyError(
                    rule_id=self.id,
                    location=f"calculations {' -> '.join(path)}",
                    message=(
                        "circular dependency between calculations; "
                        "break the cycle so no calculation transitively depends on itself"
                    ),
                )
            )
