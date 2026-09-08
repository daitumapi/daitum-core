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

""":class:`ModelTransform` — a sub-model plus the output maps that expose its results.

A transform pairs a self-contained :class:`~daitum_model.ModelBuilder` sub-model with two
declaration-ordered output maps: table outputs and parameter outputs. The same built file serves
two roles depending on where it is attached, and only the *meaning* of the outputs differs — so
each role has its own pair of methods, phrased in its own terms:

* **Data-source transform** — attached to a :class:`ModelTransformConfig`. The sub-model is fed
  input data, and each output routes back into the *parent* model: a table into a parent table
  (:meth:`ModelTransform.add_data_source_table`), a value into a parent named value
  (:meth:`ModelTransform.add_data_source_named_value`).
* **Report transform** — attached to a report via
  :meth:`~daitum_configuration.ReportProperty.set_transform_file`. Each output becomes report
  content: a table becomes a sheet (XLSX) or file (CSV) named by a string
  (:meth:`ModelTransform.add_report_sheet`), and every named value collapses into a single
  ``Named Values`` sheet (:meth:`ModelTransform.add_report_named_value`).

Both pairs write the same underlying maps, so a single transform *could* declare either — but a
given transform is attached in one role, and mixing the two on one object is not meaningful.

The transform is stored out-of-band; both attachment points reference it by a storage key, not by
this object. Use :meth:`build` to obtain the JSON to upload.
"""

import warnings
from typing import Any

from daitum_model import Calculation, Field, ModelBuilder, Parameter, Table
from daitum_model.fields import ComboField, DataField
from daitum_model.serialisation import Buildable


class ModelTransform(Buildable):
    """
    A sub-model together with the maps that expose its tables and named values as outputs.

    Build the sub-model as an ordinary :class:`~daitum_model.ModelBuilder`, declare what it
    produces with the role-specific ``add_*`` methods, then :meth:`build` it to JSON. See the
    module docstring for the data-source and report roles.

    Output maps preserve declaration order: table outputs become sheets/files in the order added,
    and columns in the order they are mapped. Whatever tables and named values the sub-model
    declares as plain inputs are populated from same-named data on the host; anything else is
    derived inside the sub-model.

    Args:
        model_builder: The self-contained sub-model whose results the output maps expose.
    """

    def __init__(self, model_builder: ModelBuilder):
        self._model_definition: ModelBuilder = model_builder
        self._parameter_outputs: dict[str, str] = {}
        self._table_outputs: dict[str, dict] = {}

    # -- Report role -------------------------------------------------------------------

    def add_report_sheet(
        self,
        name: str,
        source: Table,
        columns: dict[str, Field],
    ) -> "ModelTransform":
        """Declare a report output sheet/file reading rows from ``source``.

        Args:
            name: The output name — the XLSX sheet name, the CSV file name, and the name a
                template sheet targets. Must be non-blank, unique across the transform's
                outputs, at most 31 characters, and free of ``[]:*?/\\`` (these become Excel
                sheet names and zip entry names). When named values are also declared, no sheet
                may be named ``Named Values``.
            source: The sub-model table whose rows populate the sheet.
            columns: Map of column header to the sub-model :class:`~daitum_model.Field`
                supplying it. Column headers must be non-blank and unique within the sheet;
                iteration order sets the column order.
        """
        self._table_outputs[name] = {
            "sourceName": source.id,
            "fieldMapping": {header: field.id for header, field in columns.items()},
        }
        return self

    def add_report_named_value(
        self, name: str, source: Parameter | Calculation
    ) -> "ModelTransform":
        """Expose a sub-model named value as a column of the report's ``Named Values`` sheet.

        Every named value declared this way collapses into a single sheet named ``Named
        Values`` — one column per name in declaration order, with a single row.

        Args:
            name: The column header. Must be non-blank.
            source: The sub-model parameter or calculation supplying the value.
        """
        self._parameter_outputs[name] = source.id
        return self

    # -- Data-source role --------------------------------------------------------------

    def add_data_source_table(
        self,
        sub_model_table: Table,
        parent_table: Table,
        field_mapping: dict[Field, Field] | None = None,
    ) -> "ModelTransform":
        """Route a sub-model table's rows back into a table of the *parent* model.

        Args:
            sub_model_table: Source table inside the sub-model.
            parent_table: The parent-model table the rows are written into.
            field_mapping: Map of parent-model :class:`~daitum_model.Field` to the sub-model
                :class:`~daitum_model.Field` supplying it. When omitted, fields with matching
                ids are auto-paired (data and combo fields only).
        """
        if field_mapping is not None:
            resolved = {dest.id: src.id for dest, src in field_mapping.items()}
        else:
            resolved = {}
            sub_model_fields = [field.id for field in sub_model_table.get_fields()]
            for field in parent_table.get_fields():
                if field.id in sub_model_fields and isinstance(field, (DataField, ComboField)):
                    resolved[field.id] = field.id

        self._table_outputs[parent_table.id] = {
            "sourceName": sub_model_table.id,
            "fieldMapping": resolved,
        }
        return self

    def add_data_source_named_value(
        self,
        parent_value: Parameter | Calculation,
        source: Parameter | Calculation,
    ) -> "ModelTransform":
        """Route a sub-model named value into a named value of the *parent* model.

        Args:
            parent_value: The parent-model parameter or calculation to set.
            source: The sub-model parameter or calculation supplying the value.
        """
        self._parameter_outputs[parent_value.id] = source.id
        return self

    # -- Deprecated ---------------------------------------------------------------------

    def add_output_table(
        self,
        sub_model_table: Table,
        model_table: Table,
        field_mapping: dict[str, str] | None = None,
    ) -> "ModelTransform":
        """Declare a table output. Deprecated — use the role-specific methods instead.

        .. deprecated::
            Superseded by :meth:`add_report_sheet` (report role) and
            :meth:`add_data_source_table` (data-source role), which take arguments in each
            role's own terms. This method keeps the original combined signature — where
            ``model_table`` supplies only its id and ``field_mapping`` maps destination id to
            sub-model field id as strings — for backwards compatibility.
        """
        warnings.warn(
            "ModelTransform.add_output_table is deprecated; use add_report_sheet (report role) "
            "or add_data_source_table (data-source role).",
            DeprecationWarning,
            stacklevel=2,
        )
        if field_mapping is not None:
            resolved = dict(field_mapping)
        else:
            resolved = {}
            sub_model_fields = [field.id for field in sub_model_table.get_fields()]
            for field in model_table.get_fields():
                if field.id in sub_model_fields and isinstance(field, (DataField, ComboField)):
                    resolved[field.id] = field.id

        self._table_outputs[model_table.id] = {
            "sourceName": sub_model_table.id,
            "fieldMapping": resolved,
        }
        return self

    def add_output_parameter(self, name: str, source: Parameter | Calculation) -> "ModelTransform":
        """Expose a named value as a scalar output. Deprecated.

        .. deprecated::
            Superseded by :meth:`add_report_named_value` (report role) and
            :meth:`add_data_source_named_value` (data-source role).
        """
        warnings.warn(
            "ModelTransform.add_output_parameter is deprecated; use add_report_named_value "
            "(report role) or add_data_source_named_value (data-source role).",
            DeprecationWarning,
            stacklevel=2,
        )
        self._parameter_outputs[name] = source.id
        return self

    def build(self) -> dict[str, Any]:
        """Serialise to the JSON-compatible transform dict.

        Emits ``parameterOutputs`` and ``tableOutputs`` (both empty when nothing was declared)
        alongside the embedded sub-model under ``modelDefinition``. This is the payload uploaded
        and referenced by storage key from a data source or a report.
        """
        return {
            "parameterOutputs": self._parameter_outputs,
            "tableOutputs": self._table_outputs,
            "modelDefinition": self._model_definition.build(),
        }
