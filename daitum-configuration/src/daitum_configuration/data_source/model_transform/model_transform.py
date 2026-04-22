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
Contains classes for building model transforms.
Model transforms are simple ui-less v3 models that are used to transform data in a model and write
it back in various operations like the MODEL_TRANSFORM data source and template upgrade scripts.
"""

from typing import Any

from daitum_model import ModelBuilder, Table
from daitum_model.fields import ComboField, DataField


class ModelTransform:
    """
    Model transform builder class

    Attributes:
        _model_definition (ModelBuilder): a model builder defining the v3 model that this transform
            uses  (a.k.a sub model)
        _parameter_outputs (dict): maps from parameter in target model to named value in sub model
        _table_outputs (dict): maps from table in target model to table in sub model
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
    ):
        """
        Retrieves a field from the table.

        Args:
            sub_model_table (Table): the table in the sub model (this model transform's definition).
            model_table (Table): the table to write to in the target model.
            field_mapping (Optional[dict]): A mapping of field in target model to the field in the
                sub model. If not specified, it will map fields from the sub model to all datafields
                with matching names in the model
        """
        mapping: dict[str, Any] = {"sourceName": sub_model_table.id}
        if field_mapping is not None:
            mapping["fieldMapping"] = field_mapping
        else:
            mapping["fieldMapping"] = {}
            sub_model_fields = [field.id for field in sub_model_table.get_fields()]
            for field in model_table.get_fields():
                if field.id in sub_model_fields and (isinstance(field, (DataField, ComboField))):
                    mapping["fieldMapping"][field.id] = field.id

        self._table_outputs[model_table.id] = mapping

    def to_dict(self):
        """
        Converts to dict for json serialisation

        Returns: dict with properties matching the daitum platform spec

        """
        return {
            "parameterOutputs": self._parameter_outputs,
            "tableOutputs": self._table_outputs,
            "modelDefinition": self._model_definition.build(),
        }
