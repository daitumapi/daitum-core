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

"""Publish entries for a :class:`ModelTransformConfig`.

A publish entry writes the rows of one transform sub-model table to a data store once the
transform's checks pass. For a keyed store it replaces only the records the model owns; for a
standard store it is an ordinary update.
"""

from daitum_model import Calculation, Field, Parameter, Table
from daitum_model.data_types import ObjectDataType
from daitum_model.serialisation import Buildable
from typeguard import typechecked

from daitum_configuration.data_source.data_store.data_filter import DataFilter
from daitum_configuration.data_source.data_store.equality_data_filter import EqualityDataFilter
from daitum_configuration.data_source.data_store.overlap_data_filter import OverlapDataFilter
from daitum_configuration.data_source.data_store.set_data_filter import SetDataFilter
from daitum_configuration.data_source.model_transform.publish_target_type import (
    PublishTargetType,
)


def _require_table_fields(table_id: str, fields: list[Field], role: str) -> None:
    for field in fields:
        if field.table_id != table_id:
            raise ValueError(f"{role} field {field.id!r} must belong to table {table_id!r}")


@typechecked
class PublishExpansion(Buildable):
    """
    Publishes an object reference field as the referenced row(s) instead of its key value.

    A single reference becomes a nested object and an array reference an array of objects.
    Each expanded path becomes a sub-table of the target store's schema.

    Args:
        source_field: The ``OBJECT`` or ``OBJECT_ARRAY`` reference field to expand.
        field_mapping: Nested field name to the field of the referenced table supplying it.
            ``None`` publishes every field under its own id.
        expand: Reference fields of the referenced table to expand in turn, keyed by nested
            field name.
    """

    def __init__(
        self,
        source_field: Field,
        field_mapping: dict[str, Field] | None = None,
        expand: dict[str, "PublishExpansion"] | None = None,
    ):
        data_type = source_field.to_data_type()
        if not isinstance(data_type, ObjectDataType):
            raise ValueError(
                f"Expanded field {source_field.id!r} must be an object reference, got {data_type}"
            )
        self._table_id = source_field.table_id
        referenced = data_type.table_id
        _require_table_fields(referenced, list((field_mapping or {}).values()), "Mapped")
        for nested in (expand or {}).values():
            if nested._table_id != referenced:
                raise ValueError(
                    f"Nested expansion {nested.source_field!r} must belong to table {referenced!r}"
                )

        self.source_field: str = source_field.id
        self.field_mapping = (
            {name: field.id for name, field in field_mapping.items()}
            if field_mapping is not None
            else None
        )
        self.expand = expand


def _check_owned_scope(owned_scope: list[DataFilter]) -> None:
    """Mirror the platform's upload checks: only key/time filters on top-level fields."""
    for scope_filter in owned_scope:
        if isinstance(scope_filter, OverlapDataFilter):
            paths = [scope_filter.start_path, scope_filter.end_path or []]
        elif isinstance(scope_filter, (EqualityDataFilter, SetDataFilter)):
            paths = [scope_filter.path]
        else:
            raise ValueError(
                f"Owned scope only supports equality, set and overlap filters, "
                f"got {scope_filter.type.value}"
            )
        if any(len(path) > 1 for path in paths):
            raise ValueError("Owned scope filter paths must name a single top-level field")


@typechecked
class PublishConfig(Buildable):
    """
    Publishes the rows of one transform sub-model table to a data store.

    Created via :meth:`ModelTransformConfig.add_publish`; see that method for the arguments.
    """

    def __init__(  # noqa: PLR0913
        self,
        data_store_key: str,
        source_table: Table,
        *,
        target_type: PublishTargetType = PublishTargetType.DATA_STORE,
        field_mapping: dict[str, Field] | None = None,
        expand: dict[str, PublishExpansion] | None = None,
        owned_scope: list[DataFilter] | None = None,
        owns_entire_store: bool = False,
        write_on_failure_outputs: list[Table | Parameter | Calculation] | None = None,
        max_lock_wait_seconds: int | None = None,
        allow_empty_publish: bool = False,
    ):
        if owned_scope and owns_entire_store:
            raise ValueError("Set only one of owned_scope and owns_entire_store")
        _check_owned_scope(owned_scope or [])
        _require_table_fields(source_table.id, list((field_mapping or {}).values()), "Mapped")
        for expansion in (expand or {}).values():
            if expansion._table_id != source_table.id:
                raise ValueError(
                    f"Expanded field {expansion.source_field!r} must belong to table "
                    f"{source_table.id!r}"
                )
        if max_lock_wait_seconds is not None and max_lock_wait_seconds <= 0:
            raise ValueError("max_lock_wait_seconds must be positive")

        self.target_type = target_type
        self.data_store_key = data_store_key
        self.source_table = source_table.id
        self.field_mapping = (
            {name: field.id for name, field in field_mapping.items()}
            if field_mapping is not None
            else None
        )
        self.expand = expand
        self.owned_scope = owned_scope or []
        self.owns_entire_store = owns_entire_store
        self.write_on_failure_outputs = [output.id for output in write_on_failure_outputs or []]
        self.max_lock_wait_seconds = max_lock_wait_seconds
        self.allow_empty_publish = allow_empty_publish
