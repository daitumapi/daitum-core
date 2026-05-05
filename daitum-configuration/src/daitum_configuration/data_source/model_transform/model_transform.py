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

""":class:`ModelTransform` — wraps a sub-model used by :class:`ModelTransformConfig`."""

from typing import Any

from daitum_model import ModelBuilder, Table
from daitum_model.fields import ComboField, DataField

from daitum_configuration._buildable import Buildable


class ModelTransform(Buildable):
    """
    Sub-model that produces output tables consumed by a :class:`ModelTransformConfig`.

    Args:
        model_builder: The sub-model whose tables are mapped onto target-model
            tables via :meth:`add_output_table`.
    """

    def __init__(self, model_builder: ModelBuilder):
        self._model_definition: ModelBuilder = model_builder
        self._parameter_outputs: dict[str, str] = {}
        self._table_outputs: dict[str, dict] = {}

    def add_output_table(
        self,
        sub_model_table: Table,
        model_table: Table,
        field_mapping: dict[str, str] | None = None,
    ) -> "ModelTransform":
        """Route rows from ``sub_model_table`` into ``model_table``.

        Args:
            sub_model_table: Source table inside the sub-model.
            model_table: Destination table in the parent model.
            field_mapping: Map of sub-model field id to parent-model field id.
                When omitted, fields with matching ids are auto-paired
                (data and combo fields only).
        """
        mapping: dict[str, Any] = {"sourceName": sub_model_table.id}
        if field_mapping is not None:
            mapping["fieldMapping"] = field_mapping
        else:
            mapping["fieldMapping"] = {}
            sub_model_fields = [field.id for field in sub_model_table.get_fields()]
            for field in model_table.get_fields():
                if field.id in sub_model_fields and isinstance(field, (DataField, ComboField)):
                    mapping["fieldMapping"][field.id] = field.id

        self._table_outputs[model_table.id] = mapping
        return self

    def build(self) -> dict[str, Any]:
        """Serialise to a JSON-compatible dict including the embedded sub-model."""
        return {
            "parameterOutputs": self._parameter_outputs,
            "tableOutputs": self._table_outputs,
            "modelDefinition": self._model_definition.build(),
        }
