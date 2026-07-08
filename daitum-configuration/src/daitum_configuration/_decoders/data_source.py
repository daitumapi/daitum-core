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
Decoders for the data-source family.

The :class:`DataSourceConfig` hierarchy discriminates on a domain ``"type"`` key (a
:class:`DataSourceType` value) rather than the ``@type`` mechanism, so it gets a small
dispatcher mirroring the ``algorithmKey`` one in :mod:`algorithm`. Each concrete config is
otherwise a regular attribute walk, as are the wrapper and helper classes, so those decode
via the shared generic decoder.
"""

from __future__ import annotations

from typing import Any

from daitum_model.decoding import (
    LoadContext,
    LoadError,
    coerce,
    decode_into,
    generic,
    register_decoder,
    require,
    resolved_field_types,
)
from daitum_model.serialisation import camel_to_snake

from daitum_configuration._decoders._state import DictOf, ListOf, decode_with_state
from daitum_configuration.data_source.batched_data_source.batch_data_source_type import (
    BatchDataSourceType,
)
from daitum_configuration.data_source.batched_data_source.batched_data_source_config import (
    BatchedDataSourceConfig,
)
from daitum_configuration.data_source.batched_data_source.data_source_info import DataSourceInfo
from daitum_configuration.data_source.data_source import DataSource
from daitum_configuration.data_source.data_source_config import DataSourceConfig
from daitum_configuration.data_source.data_source_type import DataSourceType
from daitum_configuration.data_source.data_store.data_filter import DataFilter
from daitum_configuration.data_source.data_store.data_store_config import DataStoreConfig
from daitum_configuration.data_source.distance_matrix.distance_matrix_config import (
    DistanceMatrixConfig,
)
from daitum_configuration.data_source.distance_matrix.output_matrix import OutputMatrix
from daitum_configuration.data_source.excel_transform.excel_transform_config import (
    ExcelTransformConfig,
    _SheetMapping,
)
from daitum_configuration.data_source.excel_transform.import_option_overrides import (
    ImportOptionOverrides,
)
from daitum_configuration.data_source.geo_location_config import GeoLocationConfig
from daitum_configuration.data_source.model_transform.model_transform_config import (
    ModelTransformConfig,
)
from daitum_configuration.data_source.model_transform.model_transform_input import (
    ModelTransformInput,
)
from daitum_configuration.data_source.run_external_model.run_external_model_config import (
    RunExternalModelConfig,
)
from daitum_configuration.data_source.run_report.run_report_config import RunReportConfig
from daitum_configuration.data_source.set_features_config import SetFeaturesConfig
from daitum_configuration.data_source.track_changes_config import TrackChangesConfig

#: DataSourceType value -> (concrete class, decode spec).
#: A spec is (ctor_args, ctor_overrides, elements) passed to ``decode_with_state`` — the
#: required constructor arg names, any fixed placeholder ctor kwargs, and the element classes
#: for nested-Buildable attributes the raw value cannot reveal.
_CONFIGS: dict[str, tuple[type, tuple[tuple[str, ...], dict[str, Any], dict[str, Any]]]] = {
    DataSourceType.DATA_STORE.value: (
        DataStoreConfig,
        (("data_store_key", "tables"), {}, {"model_filter": DataFilter}),
    ),
    DataSourceType.EXCEL_TRANSFORM.value: (
        ExcelTransformConfig,
        # The constructor takes (source, target) tuples; the real sheet_mapping (a list of
        # _SheetMapping) is restored from data afterwards, so seed the ctor with an empty list.
        (
            ("file_key", "file_name"),
            {"sheet_mapping": []},
            {
                "sheet_mapping": ListOf(_SheetMapping),
                "per_sheet_overrides": DictOf(ImportOptionOverrides),
            },
        ),
    ),
    DataSourceType.MODEL_TRANSFORM.value: (
        ModelTransformConfig,
        (("file_key", "file_name"), {}, {"inputs": ListOf(ModelTransformInput)}),
    ),
    DataSourceType.DISTANCE_MATRIX.value: (
        DistanceMatrixConfig,
        (
            ("from_sheet_name", "from_longitude_column", "from_latitude_column"),
            {"outputs": []},
            {"outputs": ListOf(OutputMatrix)},
        ),
    ),
    DataSourceType.BATCHED_DATA_SOURCE.value: (
        BatchedDataSourceConfig,
        ((), {}, {"data_sources": ListOf(DataSourceInfo)}),
    ),
    DataSourceType.RUN_REPORT.value: (RunReportConfig, (("report_name",), {}, {})),
    DataSourceType.RUN_EXTERNAL_MODEL.value: (RunExternalModelConfig, ((), {}, {})),
    DataSourceType.GEOLOCATION.value: (
        GeoLocationConfig,
        (
            ("sheet_name", "address_column", "longitude_column", "latitude_column"),
            {},
            {},
        ),
    ),
    DataSourceType.SET_FEATURES.value: (SetFeaturesConfig, ((), {}, {})),
    # ``baseline`` (str) and ``mode`` (TrackChangesMode) are constructor args; ``mode`` coerces to
    # its enum via the constructor hint. ``trackingGroups`` (an optional list of names) is restored
    # afterwards verbatim, and ``trackChangesSupported`` (the base flag) is a plain bool.
    DataSourceType.TRACK_CHANGES.value: (TrackChangesConfig, (("baseline", "mode"), {}, {})),
}


def decode_data_source_config(data: dict[str, Any], ctx: LoadContext) -> DataSourceConfig:
    """Dispatch on the ``type`` key and decode into the matching concrete config."""
    type_value = data.get("type", "")
    entry = _CONFIGS.get(type_value)
    if entry is None:
        raise LoadError(f"Unknown data-source type: {type_value!r}")
    concrete, (ctor_args, ctor_overrides, elements) = entry
    # ``type`` is the discriminator (re-derived from the concrete class's property), not an
    # attribute to restore.
    fields = {k: v for k, v in data.items() if k != "type"}
    config: DataSourceConfig = decode_with_state(
        concrete, fields, ctx, ctor_args=ctor_args, ctor_overrides=ctor_overrides, elements=elements
    )
    return config


def decode_data_source(data: dict[str, Any], ctx: LoadContext) -> DataSource:
    """Decode the :class:`DataSource` wrapper (config nested, metadata flags restored).

    The (``@typechecked``) constructor requires a real :class:`DataSourceConfig`, so the
    nested config is decoded first and passed in; the remaining metadata flags — including the
    auto-incrementing ``temp_export_id`` — are then restored from ``data`` so ``build()``
    reproduces the original exactly.

    The constructor bumps :class:`DataSource`'s class-level ``_temp_export_id_counter``, but
    decoding restores the stored id, so the counter bump is an unwanted side effect; it is
    snapshotted and reset to keep decoding side-effect-free.
    """
    config = decode_into(DataSourceConfig, require(data, "config", "DataSource"), ctx)
    counter = DataSource._temp_export_id_counter
    try:
        source = DataSource(require(data, "name", "DataSource"), config)
    finally:
        DataSource._temp_export_id_counter = counter
    # The metadata flags (hidden, temp_export_id, post_optimise, notify/update, prompt_*) are
    # primitives restored verbatim; the typed attributes (``on_click`` -> ModelEvent, ``icon`` ->
    # Icon) are coerced from their declared types so they decode into real objects, not raw dicts.
    hints = resolved_field_types(DataSource)
    for camel_key, value in data.items():
        if camel_key in ("name", "config"):
            continue
        snake = camel_to_snake(camel_key)
        setattr(source, snake, coerce(value, hints.get(snake, Any), ctx))
    return source


def decode_data_source_info(data: dict[str, Any], ctx: LoadContext) -> DataSourceInfo:
    """Decode a :class:`DataSourceInfo` (a batched entry).

    Its ``@typechecked`` constructor requires a live :class:`DataSource` purely to read its
    ``temp_export_id``; the object itself is never stored (only the id, the order, and the
    batch type). Since ``build()`` emits exactly those three scalars, we decode them directly
    onto a fresh instance rather than fabricating a throwaway ``DataSource`` to feed the
    constructor.
    """
    info = DataSourceInfo.__new__(DataSourceInfo)
    info.data_source_id = require(data, "dataSourceId", "DataSourceInfo")
    info.order = require(data, "order", "DataSourceInfo")
    info.type = BatchDataSourceType(require(data, "type", "DataSourceInfo"))
    return info


def register() -> None:
    """Register the data-source config dispatcher, wrapper, and helper decoders."""
    register_decoder(DataSourceConfig, decode_data_source_config)
    for concrete, _ in _CONFIGS.values():
        register_decoder(concrete, decode_data_source_config)

    register_decoder(DataSource, decode_data_source)
    register_decoder(DataSourceInfo, decode_data_source_info)
    generic(_SheetMapping)
    generic(OutputMatrix)
    generic(ImportOptionOverrides)
