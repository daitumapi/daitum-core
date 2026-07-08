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
Decoders for the model-transform family.

:class:`ModelTransformInput` discriminates on a domain ``sourceType`` key (a
:class:`DataInputSourceType`), so it gets a small dispatcher mirroring the data-source one.
:class:`ModelTransform` embeds a full sub-model: its decoder recursively invokes the model
decoder on the nested ``modelDefinition``. The embedded model is self-contained, so it is
decoded with a fresh :class:`LoadContext`, independent of the parent configuration's symbols.
"""

from __future__ import annotations

from typing import Any

from daitum_model import ModelBuilder
from daitum_model.decoding import LoadContext, LoadError, decode_into, register_decoder, require

from daitum_configuration.data_source.data_store.data_filter import DataFilter
from daitum_configuration.data_source.model_transform.data_input_source_type import (
    DataInputSourceType,
)
from daitum_configuration.data_source.model_transform.model_transform import ModelTransform
from daitum_configuration.data_source.model_transform.model_transform_input import (
    DataStoreInput,
    DataStoreInterfaceInput,
    DirectUploadInput,
    DynamicValuesInput,
    ModelTransformInput,
    _DataStoreLikeInput,
)
from daitum_configuration.data_source.model_transform.validation_severity import ValidationSeverity

#: DataInputSourceType value -> concrete input class.
_INPUT_TYPES: dict[str, type] = {
    DataInputSourceType.DYNAMIC_VALUES.value: DynamicValuesInput,
    DataInputSourceType.DATA_STORE.value: DataStoreInput,
    DataInputSourceType.DATA_STORE_INTERFACE.value: DataStoreInterfaceInput,
    DataInputSourceType.DIRECT_UPLOAD.value: DirectUploadInput,
}


def decode_model_transform_input(data: dict[str, Any], ctx: LoadContext) -> ModelTransformInput:
    """Dispatch on the ``sourceType`` key and reconstruct the matching input subclass.

    These inputs rename their constructor arguments when storing them (``tables`` ->
    ``table_mapping``) and a ``DynamicValuesInput`` keeps only an id string, so their
    serialised shape does not match their constructor signatures. We therefore restore each
    one's attributes directly (decoding the nested ``model_filter`` and the severity enums to
    their proper types) rather than reverse-engineering constructor arguments.
    """
    source_type = data.get("sourceType", "")
    concrete = _INPUT_TYPES.get(source_type)
    if concrete is None:
        raise LoadError(f"Unknown model-transform input sourceType: {source_type!r}")

    if concrete is DynamicValuesInput:
        dyn = DynamicValuesInput.__new__(DynamicValuesInput)
        dyn.timezone_key = data.get("timezoneKey")
        return dyn
    if concrete in (DataStoreInput, DataStoreInterfaceInput):
        store: _DataStoreLikeInput = concrete.__new__(concrete)  # type: ignore[call-overload]
        owner = concrete.__name__
        store.data_store_key = require(data, "dataStoreKey", owner)
        store.direct_data_pull = require(data, "directDataPull", owner)
        model_filter = data.get("modelFilter")
        store.model_filter = (
            decode_into(DataFilter, model_filter, ctx) if model_filter is not None else None
        )
        store.table_mapping = require(data, "tableMapping", owner)
        return store
    upload = DirectUploadInput.__new__(DirectUploadInput)
    upload.table_mapping = require(data, "tableMapping", "DirectUploadInput")
    upload.missing_header_severity = ValidationSeverity(
        require(data, "missingHeaderSeverity", "DirectUploadInput")
    )
    upload.unexpected_header_severity = ValidationSeverity(
        require(data, "unexpectedHeaderSeverity", "DirectUploadInput")
    )
    return upload


def decode_model_transform(data: dict[str, Any], _ctx: LoadContext) -> ModelTransform:
    """Decode a :class:`ModelTransform`, recursively decoding its embedded sub-model.

    The sub-model is a complete, self-contained model definition; it is decoded with its own
    fresh context. The output-mapping dicts are plain id-keyed data and pass through verbatim.
    """
    sub_model = decode_into(
        ModelBuilder, require(data, "modelDefinition", "ModelTransform"), LoadContext()
    )
    transform = ModelTransform(sub_model)
    transform._parameter_outputs = require(
        data, "parameterOutputs", "ModelTransform"
    )  # noqa: SLF001
    transform._table_outputs = require(data, "tableOutputs", "ModelTransform")  # noqa: SLF001
    return transform


def register() -> None:
    """Register the model-transform input dispatcher and the ModelTransform decoder."""
    register_decoder(ModelTransformInput, decode_model_transform_input)
    for concrete in _INPUT_TYPES.values():
        register_decoder(concrete, decode_model_transform_input)
    register_decoder(ModelTransform, decode_model_transform)
