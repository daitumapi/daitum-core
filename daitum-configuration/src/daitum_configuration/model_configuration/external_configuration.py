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
Defines configuration classes for mapping external models to internal data structures.

This module provides utilities for linking parameters, tables, and fields to entities
used in external Java models.
"""

from dataclasses import dataclass, field

from daitum_model import Calculation, Field, Parameter, Table


@dataclass
class ParameterMapping:
    """
    Maps a model named_value to a named location in the external configuration.
    """

    parameter_name: str
    named_value: Parameter | Calculation

    def _build(self):
        return {"parameterName": self.parameter_name, "location": self.named_value.id}


@dataclass
class ColumnMapping:
    """
    Maps an entity property to a specific column in a data table.
    """

    property_name: str
    column: Field

    def _build(self):
        return {"propertyName": self.property_name, "columnName": self.column.id}


@dataclass
class InputDataMapping:
    """
    Defines how an input entity maps to a source data table and its columns.
    """

    entity_name: str
    table: Table
    column_mappings: list[ColumnMapping] = field(default_factory=list)

    def add_column_mapping(self, property_name: str, column: Field):
        """
        Add a property-to-column mapping to this input mapping.
        """
        self.column_mappings.append(ColumnMapping(property_name, column))

    def _build(self):
        return {
            "entityName": self.entity_name,
            "tableName": self.table.id,
            "columnMappings": [cm._build() for cm in self.column_mappings],
        }


@dataclass
class OutputDataMapping(InputDataMapping):
    """
    Defines how model outputs map to a target data table.
    Extends InputDataMapping with additional control over synchronization behavior.
    """

    key_column: str | None = None
    preserve_order: bool = False
    clear_existing: bool = True

    def _build(self):
        ret = super()._build()
        ret.update(
            {
                "mapByProperty": self.key_column,
                "preserveOrder": self.preserve_order,
                "clearExisting": self.clear_existing,
            }
        )
        return ret


class ExternalModelConfiguration:
    """
    Aggregates all data, parameter, and output mappings for an external model configuration.
    """

    def __init__(self, requires_reload: bool = True):
        self._input_data_mappings: list[InputDataMapping] = []
        self._parameter_mappings: list[ParameterMapping] = []
        self._output_data_mappings: list[OutputDataMapping] = []
        self._requires_reload: bool = requires_reload

    def add_input_data_mapping(self, mapping: InputDataMapping):
        """Add an input data mapping to the configuration."""
        self._input_data_mappings.append(mapping)

    def add_parameter_mapping(self, mapping: ParameterMapping):
        """Add a parameter mapping to the configuration."""
        self._parameter_mappings.append(mapping)

    def add_output_data_mapping(self, mapping: OutputDataMapping):
        """Add an output data mapping to the configuration."""
        self._output_data_mappings.append(mapping)

    def build(self):
        """Return a serializable dictionary representation of the external configuration."""
        return {
            "inputDataMappings": [idm._build() for idm in self._input_data_mappings],
            "parameterMappings": [pm._build() for pm in self._parameter_mappings],
            "outputDataMappings": [odm._build() for odm in self._output_data_mappings],
            "requiresReload": self._requires_reload,
        }
