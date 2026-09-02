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

"""Rule: object/map reference fields must point at a table that exists in the model."""

from __future__ import annotations

from daitum_model.data_types import MapDataType, ObjectDataType
from daitum_model.validation.engine import rule
from daitum_model.validation.errors import TableReferenceError
from daitum_model.validation.graph import ModelGraph
from daitum_model.validation.report import ValidationReport


@rule
class ObjectMapTargetTablesExist:
    """Every object/map reference field must name a table registered in the model."""

    id = "object-map-target-tables-exist"

    def check(self, graph: ModelGraph, report: ValidationReport) -> None:
        for table in graph.tables.values():
            for field in table.field_definitions.values():
                data_type = field.data_type
                if isinstance(data_type, (ObjectDataType, MapDataType)):
                    if data_type.table_id not in graph.tables:
                        report.add(
                            TableReferenceError(
                                rule_id=self.id,
                                location=f"table '{table.id}'.field '{field.id}'",
                                message=(
                                    f"references table '{data_type.table_id}', "
                                    "which is not in the model"
                                ),
                            )
                        )
