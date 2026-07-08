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
Decoders for the :class:`ExternalModelConfiguration` family.

Each mapping stores a model object's bare ``id`` (a parameter/calculation ``location``, a
field ``columnName``, a table ``tableName``); the constructors take the live model object and
read its id. So we resolve each id back to its object from the symbol table and call the
constructor — recovering a byte-identical round-trip without poking private state.
"""

from __future__ import annotations

from typing import Any

from daitum_model.decoding import LoadContext, register_decoder, require

from daitum_configuration.model_configuration.external_configuration import (
    ColumnMapping,
    ExternalModelConfiguration,
    InputDataMapping,
    OutputDataMapping,
    ParameterMapping,
)


def decode_parameter_mapping(data: dict[str, Any], ctx: LoadContext) -> ParameterMapping:
    return ParameterMapping(
        require(data, "parameterName", "ParameterMapping"),
        ctx.resolve(require(data, "location", "ParameterMapping")),
    )


def decode_column_mapping(data: dict[str, Any], ctx: LoadContext) -> ColumnMapping:
    return ColumnMapping(
        require(data, "propertyName", "ColumnMapping"),
        ctx.resolve(require(data, "columnName", "ColumnMapping")),
    )


def _column_mappings(data: dict[str, Any], ctx: LoadContext) -> list[ColumnMapping]:
    return [decode_column_mapping(c, ctx) for c in data.get("columnMappings", [])]


def decode_input_data_mapping(data: dict[str, Any], ctx: LoadContext) -> InputDataMapping:
    return InputDataMapping(
        require(data, "entityName", "InputDataMapping"),
        # Resolve the table shadow-proof: a field/named value may share the table's id.
        ctx.resolve_table(require(data, "tableName", "InputDataMapping")),
        _column_mappings(data, ctx),
    )


def decode_output_data_mapping(data: dict[str, Any], ctx: LoadContext) -> OutputDataMapping:
    return OutputDataMapping(
        require(data, "entityName", "OutputDataMapping"),
        ctx.resolve_table(require(data, "tableName", "OutputDataMapping")),
        _column_mappings(data, ctx),
        key_column=data.get("mapByProperty"),
        preserve_order=require(data, "preserveOrder", "OutputDataMapping"),
        clear_existing=require(data, "clearExisting", "OutputDataMapping"),
    )


def decode_external_configuration(
    data: dict[str, Any], ctx: LoadContext
) -> ExternalModelConfiguration:
    """Reconstruct an :class:`ExternalModelConfiguration` and its three mapping lists."""
    config = ExternalModelConfiguration(
        requires_reload=require(data, "requiresReload", "ExternalModelConfiguration")
    )
    config.input_data_mappings = [
        decode_input_data_mapping(m, ctx) for m in data.get("inputDataMappings", [])
    ]
    config.parameter_mappings = [
        decode_parameter_mapping(m, ctx) for m in data.get("parameterMappings", [])
    ]
    config.output_data_mappings = [
        decode_output_data_mapping(m, ctx) for m in data.get("outputDataMappings", [])
    ]
    return config


def register() -> None:
    """Register the external-configuration decoders."""
    register_decoder(ParameterMapping, decode_parameter_mapping)
    register_decoder(ColumnMapping, decode_column_mapping)
    register_decoder(InputDataMapping, decode_input_data_mapping)
    register_decoder(OutputDataMapping, decode_output_data_mapping)
    register_decoder(ExternalModelConfiguration, decode_external_configuration)
