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

""":class:`ModelTransformConfig` — data source backed by a secondary modelling-language model."""

from daitum_model import Calculation, DataType, Field, ModelBuilder, Parameter, Table
from daitum_model.serialisation import Buildable
from daitum_model.validation_list import (
    FIELD_NAME_FIELD,
    MESSAGE_FIELD,
    ROW_FIELD,
    SUBGROUP_FIELD,
    TYPE_FIELD,
    VALUE_FIELD,
    get_validation_list_table,
)
from typeguard import typechecked

from daitum_configuration.data_source.data_source_config import DataSourceConfig
from daitum_configuration.data_source.data_source_type import DataSourceType
from daitum_configuration.data_source.data_store.data_filter import DataFilter
from daitum_configuration.data_source.model_transform.model_transform_input import (
    DataStoreInput,
    DataStoreInterfaceInput,
    DirectUploadInput,
    DynamicValuesInput,
    ModelTransformInput,
)
from daitum_configuration.data_source.model_transform.validation_severity import ValidationSeverity
from daitum_configuration.no_data_policy import NoDataPolicy


@typechecked
class _LogTableColumns(Buildable):
    """Maps log-entry roles to the columns of a :class:`ModelTransformConfig` log table.

    Each attribute is the id of the log-table field that receives that part of a
    log entry. ``severity`` and ``message`` are always populated; the remaining
    location fields are only set when the transform can attribute the entry to a
    specific source cell.
    """

    def __init__(  # noqa: PLR0913, PLR0917
        self,
        severity: str,
        message: str,
        sheet: str | None = None,
        row: str | None = None,
        column: str | None = None,
        value: str | None = None,
    ):
        self.severity = severity
        self.message = message
        self.sheet = sheet
        self.row = row
        self.column = column
        self.value = value


def _require_column(field: Field, table: Table, *allowed: DataType) -> None:
    """Raise if *field* is not part of *table* or its data type is not one of *allowed*."""
    if field.table_id != table.id:
        raise ValueError(f"Log table column {field.id!r} must belong to table {table.id!r}")
    if field.to_data_type() not in allowed:
        expected = " or ".join(t.value for t in allowed)
        raise ValueError(
            f"Log table column {field} must be of type {expected}, got {field.to_data_type()}"
        )


@typechecked
class ModelTransformConfig(DataSourceConfig):
    """
    Data source that runs a secondary model and feeds its outputs back into the parent.

    Inputs to the secondary model are registered via the ``add_*_input`` methods.

    Args:
        file_key: Storage key identifying the secondary-model file.
        file_name: Display-facing file name for the secondary model.
        debug_file: Emit a debug copy of the transform inputs/outputs.
    """

    def __init__(self, file_key: str, file_name: str, debug_file: bool = False):
        self.file_key = file_key
        self.file_name = file_name
        self.inputs: list[ModelTransformInput] = []
        self.debug_file = debug_file
        self.no_data_policy: NoDataPolicy = NoDataPolicy.ALLOW
        self.failure_named_value: str | None = None
        self.log_table: str | None = None
        self.log_table_columns: _LogTableColumns | None = None

        super().__init__(track_changes_supported=True)

    def add_dynamic_values(
        self, timezone_key: Parameter | Calculation | None
    ) -> "ModelTransformConfig":
        """Inject current-time/date variants as inputs.

        Args:
            timezone_key: Optional model named value of type ``STRING`` supplying
                an IANA timezone for non-UTC time variants.
        """
        if timezone_key is not None and timezone_key.to_data_type() != DataType.STRING:
            raise ValueError(f"Invalid timezone key with type {timezone_key.to_data_type()}")
        self.inputs.append(DynamicValuesInput(timezone_key))
        return self

    def add_datastore_input(
        self,
        data_store_key: str,
        tables: dict[str, str],
        model_filter: DataFilter | None = None,
        direct_data_pull: bool = False,
    ) -> "ModelTransformConfig":
        """Register a data-store input feeding the secondary model."""
        self.inputs.append(DataStoreInput(data_store_key, tables, model_filter, direct_data_pull))
        return self

    def add_datastore_interface_input(
        self,
        data_store_key: str,
        tables: dict[str, str],
        model_filter: DataFilter | None = None,
        direct_data_pull: bool = False,
    ) -> "ModelTransformConfig":
        """Register a data-store-interface input feeding the secondary model."""
        self.inputs.append(
            DataStoreInterfaceInput(data_store_key, tables, model_filter, direct_data_pull)
        )
        return self

    def add_direct_upload_input(
        self,
        tables: dict[str, str],
        missing_header_severity: ValidationSeverity = ValidationSeverity.ERROR,
        unexpected_header_severity: ValidationSeverity = ValidationSeverity.ERROR,
    ) -> "ModelTransformConfig":
        """Register a direct-upload (CSV) input feeding the secondary model.

        ``missing_header_severity`` and ``unexpected_header_severity`` control
        how header mismatches at upload time are surfaced; both default to
        :attr:`ValidationSeverity.ERROR`.
        """
        self.inputs.append(
            DirectUploadInput(tables, missing_header_severity, unexpected_header_severity)
        )
        return self

    def set_no_data_policy(self, no_data_policy: NoDataPolicy) -> "ModelTransformConfig":
        """Fail this data source when the transform writes no output rows, per the given policy.

        Only table outputs are counted; parameter-only transforms have no rows, so the policy is
        ignored for them — leave those on the default ``ALLOW``. Defaults to ``ALLOW``.
        """
        self.no_data_policy = no_data_policy
        return self

    def add_log_table(self, model: ModelBuilder) -> "ModelTransformConfig":
        """Build the model's validation list table and write the transform's log into it.

        Calls :func:`~daitum_model.validation_list.get_validation_list_table` on *model*,
        which aggregates every table's validation errors into a single sorted table, then
        registers that table as this transform's log table. That helper is idempotent, so
        the same model can also present the table as a validation list view without
        building it twice. Each log entry the transform emits becomes a row in it, with
        the entry's parts written to the validation list's standard columns:

        =========  ===========================
        Log role   Validation list column
        =========  ===========================
        severity   ``__Type__``
        message    ``__Message__``
        sheet      ``__Subgroup__``
        row        ``__Row__``
        column     ``__Field__``
        value      ``__Value__``
        =========  ===========================

        Args:
            model: The model builder whose tables are scanned for validation errors. Every
                table with a validated field must carry a validation group, set via
                ``Table.set_validation_group(...)``.

        Returns:
            This config, for chaining.

        Raises:
            ValueError: If *model* has no validated fields, so no validation list table is
                produced, or if a resolved column has an unexpected data type.
        """
        log_table = get_validation_list_table(model)
        if log_table is None:
            raise ValueError(
                "Cannot add a log table: the model has no validated fields, so no "
                "validation list table was produced."
            )

        severity = log_table.get_field(TYPE_FIELD)
        message = log_table.get_field(MESSAGE_FIELD)
        sheet = log_table.get_field(SUBGROUP_FIELD)
        row = log_table.get_field(ROW_FIELD)
        column = log_table.get_field(FIELD_NAME_FIELD)
        value = log_table.get_field(VALUE_FIELD)

        _require_column(severity, log_table, DataType.STRING)
        _require_column(message, log_table, DataType.STRING)
        _require_column(sheet, log_table, DataType.STRING)
        _require_column(row, log_table, DataType.INTEGER)
        _require_column(column, log_table, DataType.INTEGER, DataType.STRING)
        _require_column(value, log_table, DataType.STRING)

        self.log_table = log_table.id
        self.log_table_columns = _LogTableColumns(
            severity=severity.id,
            message=message.id,
            sheet=sheet.id,
            row=row.id,
            column=column.id,
            value=value.id,
        )
        return self

    def set_failure_named_value(
        self, named_value: Calculation | Parameter
    ) -> "ModelTransformConfig":
        """Flag a model named value when the transform logs a blocking entry.

        Args:
            named_value: A model named value that evaluates to true when the transform should fail.
        """
        if named_value.to_data_type() != DataType.BOOLEAN:
            raise ValueError(
                f"failure_named_value must be BOOLEAN, got {named_value.to_data_type()}"
            )
        self.failure_named_value = named_value.id
        return self

    @property
    def type(self) -> DataSourceType:
        return DataSourceType.MODEL_TRANSFORM
