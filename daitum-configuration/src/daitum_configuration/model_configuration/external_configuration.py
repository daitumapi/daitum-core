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
from daitum_model.serialisation import Buildable


class ParameterMapping(Buildable):
    """Map a model :class:`~daitum_model.Parameter` or :class:`~daitum_model.Calculation`
    to an external evaluator parameter name."""

    def __init__(self, parameter_name: str, named_value: Parameter | Calculation):
        self.parameter_name = parameter_name
        self.location = named_value.id


class ColumnMapping(Buildable):
    """Map an external-entity property name to a specific :class:`~daitum_model.Field`."""

    def __init__(self, property_name: str, column: Field):
        self.property_name = property_name
        self.column_name = column.id


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
        self.entity_name = entity_name
        self.table_name = table.id
        self.column_mappings: list[ColumnMapping] = (
            column_mappings if column_mappings is not None else []
        )

    def add_column_mapping(self, property_name: str, column: Field) -> "InputDataMapping":
        """Append a :class:`ColumnMapping` linking ``property_name`` to ``column``."""
        self.column_mappings.append(ColumnMapping(property_name, column))
        return self


class OutputDataMapping(InputDataMapping):
    """Extension of :class:`InputDataMapping` that controls how outputs are written back.

    Args:
        key_column: Optional column on the target table used to match incoming
            rows; absent matches are inserted.
        preserve_order: Keep the row order produced by the evaluator.
        clear_existing: Clear the target table before writing outputs.
    """

    def __init__(  # noqa: PLR0913, PLR0917
        self,
        entity_name: str,
        table: Table,
        column_mappings: list[ColumnMapping] | None = None,
        key_column: str | None = None,
        preserve_order: bool = False,
        clear_existing: bool = True,
    ):
        super().__init__(entity_name, table, column_mappings)
        # Emitted after the inherited keys: mapByProperty, preserveOrder, clearExisting.
        # ``map_by_property`` is emitted even when None, so it is handled in ``build``
        # below rather than as a plain attribute (the default walk drops None values).
        self._map_by_property = key_column
        self.preserve_order = preserve_order
        self.clear_existing = clear_existing

    def build(self) -> dict[str, Any]:
        """Serialise to a dict, always emitting ``mapByProperty`` (even when null)."""
        result = super().build()
        # Insert mapByProperty ahead of preserveOrder/clearExisting to match key order.
        ordered: dict[str, Any] = {}
        for key, value in result.items():
            if key == "preserveOrder":
                ordered["mapByProperty"] = self._map_by_property
            ordered[key] = value
        return ordered


class ExternalModelConfiguration(Buildable):
    """All input, parameter, and output mappings used by an external evaluator.

    Args:
        requires_reload: Whether the evaluator should be reloaded between runs.
    """

    def __init__(self, requires_reload: bool = True):
        # Emitted in declaration order to match the platform shape.
        self.input_data_mappings: list[InputDataMapping] = []
        self.parameter_mappings: list[ParameterMapping] = []
        self.output_data_mappings: list[OutputDataMapping] = []
        self.requires_reload: bool = requires_reload

    def add_input_data_mapping(self, mapping: InputDataMapping) -> "ExternalModelConfiguration":
        """Register an :class:`InputDataMapping`."""
        self.input_data_mappings.append(mapping)
        return self

    def add_parameter_mapping(self, mapping: ParameterMapping) -> "ExternalModelConfiguration":
        """Register a :class:`ParameterMapping`."""
        self.parameter_mappings.append(mapping)
        return self

    def add_output_data_mapping(self, mapping: OutputDataMapping) -> "ExternalModelConfiguration":
        """Register an :class:`OutputDataMapping`."""
        self.output_data_mappings.append(mapping)
        return self
