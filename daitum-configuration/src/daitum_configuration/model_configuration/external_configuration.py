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
:class:`ExternalModelConfiguration` and helpers for plugging an external evaluator into a model.

Use these mappings to declare which model tables, fields, and named values feed
the external evaluator's input entities and where its outputs should land.
"""

from typing import Any

from daitum_model import Calculation, Field, Parameter, Table

from daitum_configuration._buildable import Buildable


class ParameterMapping(Buildable):
    """Map a model :class:`~daitum_model.Parameter` or :class:`~daitum_model.Calculation`
    to an external evaluator parameter name."""

    def __init__(self, parameter_name: str, named_value: Parameter | Calculation):
        self._parameter_name = parameter_name
        self._named_value = named_value

    def build(self) -> dict[str, Any]:
        """Serialise to a JSON-compatible dict."""
        return {"parameterName": self._parameter_name, "location": self._named_value.id}


class ColumnMapping(Buildable):
    """Map an external-entity property name to a specific :class:`~daitum_model.Field`."""

    def __init__(self, property_name: str, column: Field):
        self._property_name = property_name
        self._column = column

    def build(self) -> dict[str, Any]:
        """Serialise to a JSON-compatible dict."""
        return {"propertyName": self._property_name, "columnName": self._column.id}


class InputDataMapping(Buildable):
    """Map a model :class:`~daitum_model.Table` to an external-evaluator input entity.

    Add per-column property mappings via :meth:`add_column_mapping`.
    """

    def __init__(
        self,
        entity_name: str,
        table: Table,
        column_mappings: list[ColumnMapping] | None = None,
    ):
        self._entity_name = entity_name
        self._table = table
        self._column_mappings: list[ColumnMapping] = (
            column_mappings if column_mappings is not None else []
        )

    def add_column_mapping(self, property_name: str, column: Field) -> "InputDataMapping":
        """Append a :class:`ColumnMapping` linking ``property_name`` to ``column``."""
        self._column_mappings.append(ColumnMapping(property_name, column))
        return self

    def build(self) -> dict[str, Any]:
        """Serialise to a JSON-compatible dict."""
        return {
            "entityName": self._entity_name,
            "tableName": self._table.id,
            "columnMappings": [cm.build() for cm in self._column_mappings],
        }


class OutputDataMapping(InputDataMapping):
    """Extension of :class:`InputDataMapping` that controls how outputs are written back.

    Args:
        key_column: Optional column on the target table used to match incoming
            rows; absent matches are inserted.
        preserve_order: Keep the row order produced by the evaluator.
        clear_existing: Clear the target table before writing outputs.
    """

    def __init__(  # noqa: PLR0913
        self,
        entity_name: str,
        table: Table,
        column_mappings: list[ColumnMapping] | None = None,
        key_column: str | None = None,
        preserve_order: bool = False,
        clear_existing: bool = True,
    ):
        super().__init__(entity_name, table, column_mappings)
        self._key_column = key_column
        self._preserve_order = preserve_order
        self._clear_existing = clear_existing

    def build(self) -> dict[str, Any]:
        """Serialise to a JSON-compatible dict."""
        result = super().build()
        result.update(
            {
                "mapByProperty": self._key_column,
                "preserveOrder": self._preserve_order,
                "clearExisting": self._clear_existing,
            }
        )
        return result


class ExternalModelConfiguration(Buildable):
    """All input, parameter, and output mappings used by an external evaluator.

    Args:
        requires_reload: Whether the evaluator should be reloaded between runs.
    """

    def __init__(self, requires_reload: bool = True):
        self._input_data_mappings: list[InputDataMapping] = []
        self._parameter_mappings: list[ParameterMapping] = []
        self._output_data_mappings: list[OutputDataMapping] = []
        self._requires_reload: bool = requires_reload

    def add_input_data_mapping(self, mapping: InputDataMapping) -> "ExternalModelConfiguration":
        """Register an :class:`InputDataMapping`."""
        self._input_data_mappings.append(mapping)
        return self

    def add_parameter_mapping(self, mapping: ParameterMapping) -> "ExternalModelConfiguration":
        """Register a :class:`ParameterMapping`."""
        self._parameter_mappings.append(mapping)
        return self

    def add_output_data_mapping(self, mapping: OutputDataMapping) -> "ExternalModelConfiguration":
        """Register an :class:`OutputDataMapping`."""
        self._output_data_mappings.append(mapping)
        return self

    def build(self) -> dict[str, Any]:
        """Serialise to a JSON-compatible dict."""
        return {
            "inputDataMappings": [m.build() for m in self._input_data_mappings],
            "parameterMappings": [m.build() for m in self._parameter_mappings],
            "outputDataMappings": [m.build() for m in self._output_data_mappings],
            "requiresReload": self._requires_reload,
        }
