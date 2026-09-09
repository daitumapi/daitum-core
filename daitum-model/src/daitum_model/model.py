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
Top-level :class:`ModelBuilder` for assembling a Daitum model definition.

A model is composed of tables (data, derived, joined, union) and named values
(:class:`~daitum_model.Calculation` and :class:`~daitum_model.Parameter`).
:meth:`ModelBuilder.write_to_file` serialises the model into the canonical
JSON layout consumed by the Daitum platform.
"""

import json
import os
import pathlib
import warnings
from typing import TYPE_CHECKING, Any

from typeguard import typechecked

from .data_types import BaseDataType, DataType
from .derived_table import DerivedTable
from .fields import Field
from .formula import Operand, to_formula
from .joined_table import JoinCondition, JoinedTable
from .named_values import Calculation, Parameter
from .tables import DataTable, Table
from .tracking import AutoCapture, Baseline, TrackingGroup
from .union_table import FoldedTable, UnionSource, UnionTable

if TYPE_CHECKING:
    from .validation import ValidationReport

#: Top-level keys :meth:`ModelBuilder.build` always emits.
_ALWAYS_MODEL_KEYS: tuple[str, ...] = (
    "calculationDefinitions",
    "parameterDefinitions",
    "tableDefinitions",
    "optimisationCheckNamedValue",
    "partialEvaluationAllowed",
)

#: Top-level keys :meth:`ModelBuilder.build` emits only when at least one tracking group or
#: baseline is declared.
_TRACKING_MODEL_KEYS: tuple[str, ...] = (
    "trackingGroupDefinitions",
    "baselineDefinitions",
)

#: The complete top-level key vocabulary of a built model definition — the single source of truth
#: shared by :meth:`ModelBuilder.build` (which emits from it) and the model decoder (which accepts
#: exactly these). Keeping both sides bound to this set makes drift impossible: a new top-level key
#: must be added here, so ``build`` and the decoder learn about it together.
MODEL_DEFINITION_KEYS: frozenset[str] = frozenset(_ALWAYS_MODEL_KEYS + _TRACKING_MODEL_KEYS)


@typechecked
class ModelBuilder:
    """
    Top-level entry point for building a Daitum model.

    A model holds tables and named values (calculations and parameters). Build
    one incrementally with the ``add_*`` factory methods, then call
    :meth:`write_to_file` to emit the JSON output.
    """

    def __init__(self):
        """Initialise an empty model with no tables, calculations, or parameters."""
        self._calculations: list[Calculation] = list[Calculation]()
        self._parameters: list[Parameter] = list[Parameter]()
        self._tables: list[Table] = list[Table]()

        self._validation_named_val: Parameter | Calculation | None = None
        self._partial_evaluation_allowed: bool = True

        # Populated by ``read_from_file`` so a loaded model exposes its symbol table.
        self._load_context: Any = None

        self._tracking_groups: list[TrackingGroup] = []
        self._baselines: list[Baseline] = []

    def add_calculation(
        self,
        id: str,
        formula: Operand | float | int | bool | str,
        model_level: bool = False,
    ) -> Calculation:
        """
        Add a :class:`~daitum_model.Calculation` to the model.

        Args:
            id: Unique identifier for the calculation. Must not collide with any
                existing calculation or parameter id.
            formula: The expression. A :class:`~daitum_model.Formula` or any value
                accepted by :func:`~daitum_model.formula.CONST` (number, bool, or
                string), which is wrapped automatically.
            model_level: If ``True``, the calculation is evaluated once for the
                whole model. If ``False`` (the default) it is scenario-level.

        Returns:
            The newly added :class:`~daitum_model.Calculation`.

        Raises:
            ValueError: If a calculation or parameter with the same ``id``
                already exists in the model.
        """
        formula = to_formula(formula)
        if any(calculation.id == id for calculation in self._calculations) or any(
            parameter.id == id for parameter in self._parameters
        ):
            raise ValueError(f"A named value with id {id} already exists in the model")
        calc = Calculation(id, formula, model_level=model_level, model=self)
        self._calculations.append(calc)
        return calc

    def add_parameter(
        self,
        id: str,
        data_type: BaseDataType,
        value: Any,
        model_level: bool = False,
    ) -> Parameter:
        """
        Add a :class:`~daitum_model.Parameter` to the model.

        Args:
            id: Unique identifier for the parameter.
            data_type: Data type of the parameter — a :class:`~daitum_model.DataType`,
                :class:`~daitum_model.ObjectDataType`, or :class:`~daitum_model.MapDataType`.
            value: Initial value. Must be compatible with ``data_type``.
            model_level: If ``True``, the parameter is shared across all
                scenarios. If ``False`` (the default) it is scenario-level.

        Returns:
            The newly added :class:`~daitum_model.Parameter`.
        """
        param = Parameter(id, data_type, value, model_level)
        param.set_model(self)
        self._parameters.append(param)
        return param

    def add_tracking_group(self, name: str) -> TrackingGroup:
        """
        Declare a change-tracking group.

        Tag fields, parameters, and calculations with the returned group (via
        ``set_tracking_groups``) to include them in baselines that capture it.

        Args:
            name: Unique identifier for the tracking group.

        Returns:
            The newly declared :class:`~daitum_model.tracking.TrackingGroup`.

        Raises:
            ValueError: If a tracking group with the same ``name`` already exists.
        """
        if any(group.name == name for group in self._tracking_groups):
            raise ValueError(f"A tracking group named '{name}' already exists in the model")
        group = TrackingGroup(name)
        self._tracking_groups.append(group)
        return group

    def add_baseline(
        self,
        name: str,
        tracking_groups: list[str | TrackingGroup],
        auto_capture: AutoCapture = AutoCapture.NONE,
    ) -> Baseline:
        """
        Declare a baseline — a named point in time that snapshots tracking groups.

        Args:
            name: Unique identifier for the baseline.
            tracking_groups: The tracking groups (or their names) this baseline
                captures.
            auto_capture: Platform milestone that triggers an automatic capture,
                or :attr:`~daitum_model.tracking.AutoCapture.NONE` (the default)
                for manual capture only.

        Returns:
            The newly declared :class:`~daitum_model.tracking.Baseline`.

        Raises:
            ValueError: If a baseline with the same ``name`` already exists.
        """
        if any(baseline.name == name for baseline in self._baselines):
            raise ValueError(f"A baseline named '{name}' already exists in the model")
        baseline = Baseline(name, tracking_groups, auto_capture)
        self._baselines.append(baseline)
        return baseline

    def add_data_table(self, id: str) -> DataTable:
        """
        Add a :class:`~daitum_model.tables.DataTable` to the model.

        A data table holds raw imported rows and is the only table type that
        supports decision variables.

        Args:
            id: Unique identifier for the table. Must not collide with any
                existing table id.

        Returns:
            The newly added :class:`~daitum_model.tables.DataTable`. Use its
            ``add_data_field`` / ``add_calculated_field`` / ``set_key_column``
            methods to populate it.

        Raises:
            ValueError: If a table with the same ``id`` already exists.
        """
        table = DataTable(id)
        self._add_table(table)
        return table

    def add_derived_table(
        self,
        id: str,
        source_table: Table,
        group_by: list[Field] | None = None,
        filter_field: Field | None = None,
    ) -> DerivedTable:
        """
        Add a :class:`~daitum_model.derived_table.DerivedTable` to the model.

        A derived table is a grouped, filtered, and/or sorted view of an
        existing source table.

        Args:
            id: Unique identifier for the derived table.
            source_table: The table whose rows the derived table draws from.
            group_by: Deprecated. Call :meth:`DerivedTable.group_by` on the returned
                table instead.
            filter_field: Deprecated. Call :meth:`DerivedTable.set_filter_field` on the
                returned table instead.

        Returns:
            The newly added :class:`~daitum_model.derived_table.DerivedTable`.

        Raises:
            ValueError: If a table with the same ``id`` already exists.
        """
        table = DerivedTable(id, source_table, group_by=group_by, filter_field=filter_field)
        self._add_table(table)
        return table

    def add_joined_table(self, id: str, join_conditions: list[JoinCondition]) -> JoinedTable:
        """
        Add a :class:`~daitum_model.joined_table.JoinedTable` to the model.

        A joined table is the result of joining two or more tables on a list
        of :class:`~daitum_model.joined_table.JoinCondition` rows.

        Args:
            id: Unique identifier for the joined table.
            join_conditions: One condition per joined table pairing. The
                :class:`~daitum_model.JoinType` of each condition controls how
                unmatched rows are handled. A :attr:`~daitum_model.JoinType.CROSS`
                condition pairs every left row with every right row and takes no
                match fields.

        Returns:
            The newly added :class:`~daitum_model.joined_table.JoinedTable`.

        Raises:
            ValueError: If a table with the same ``id`` already exists.
        """
        table = JoinedTable(id, join_conditions)
        self._add_table(table)
        return table

    def add_union_table(self, id: str, source_tables: list[Table | UnionSource]) -> UnionTable:
        """
        Add a :class:`~daitum_model.union_table.UnionTable` to the model.

        A union table stacks rows from multiple source tables. Pass a
        :class:`~daitum_model.union_table.UnionSource` instead of a bare
        :class:`~daitum_model.Table` when the source schema does not line up
        with the union table's fields.

        Args:
            id: Unique identifier for the union table.
            source_tables: The tables (or wrapped ``UnionSource`` instances)
                whose rows are stacked.

        Returns:
            The newly added :class:`~daitum_model.union_table.UnionTable`.

        Raises:
            ValueError: If a table with the same ``id`` already exists.
        """
        table = UnionTable(id, source_tables)
        self._add_table(table)
        return table

    def add_folded_table(self, id: str, source_table: Table) -> FoldedTable:
        """
        Add a folded table — the "columns to rows" transform — to the model.

        A folded table turns wide columns of ``source_table`` into rows. Declare the output
        columns with :meth:`~daitum_model.union_table.FoldedTable.add_column`, pass-through
        columns with :meth:`~daitum_model.union_table.FoldedTable.carry`, then call
        :meth:`~daitum_model.union_table.FoldedTable.fold` once per column group to collapse.

        For example, folding ``(Employee, Day1Wages, Day2Wages)`` into
        ``(Employee, Day, Wages)``::

            folded = model.add_folded_table("Roster_Long", roster)
            folded.add_column("Day", DataType.INTEGER)
            folded.add_column("Wages", DataType.DECIMAL)
            folded.carry(roster["Employee"])
            folded.fold(Day=1, Wages=roster["Day1Wages"])
            folded.fold(Day=2, Wages=roster["Day2Wages"])

        The builder wraps a :class:`~daitum_model.union_table.UnionTable`, which is registered
        on the model and available as :attr:`~daitum_model.union_table.FoldedTable.table`.

        Args:
            id: Unique identifier for the folded table.
            source_table: The wide table whose columns are folded into rows.

        Returns:
            A :class:`~daitum_model.union_table.FoldedTable` builder.

        Raises:
            ValueError: If a table with the same ``id`` already exists.
        """
        folded = FoldedTable(id, source_table)
        self._add_table(folded.table)
        return folded

    def set_partial_evaluation_allowed(self, partial_evaluation_allowed: bool = True):
        """
        Toggle partial evaluation for this model.

        When enabled (the default), the platform re-evaluates only the
        calculations affected by a change rather than the whole model, which
        speeds up UI rendering. Disable only if a model has dependencies that
        the partial evaluator cannot track correctly.

        Args:
            partial_evaluation_allowed: ``True`` to allow partial evaluation.
        """
        self._partial_evaluation_allowed = partial_evaluation_allowed

    def set_data_validation_rule(self, named_value: Parameter | Calculation):
        """
        Gate optimisation on a boolean named value.

        Optimisation is allowed only while ``named_value`` evaluates to
        ``True``. When it is ``False`` and the UI definition specifies a
        validation screen, the user is redirected there on attempting to start
        optimisation.

        Args:
            named_value: A :class:`~daitum_model.Parameter` or
                :class:`~daitum_model.Calculation` of type
                :attr:`~daitum_model.DataType.BOOLEAN`.

        Raises:
            ValueError: If ``named_value`` is not of boolean data type.
        """
        if named_value.to_data_type() != DataType.BOOLEAN:
            raise ValueError(f"Invalid data validation rule with type {named_value.to_data_type()}")
        self._validation_named_val = named_value

    def get_tables(self) -> list[Table]:
        """
        Return every table that has been added to the model, in insertion order.
        """
        return self._tables

    def get_table(self, id: str) -> Table:
        """
        Return the table with the given id.

        Args:
            id: Identifier of the table to look up.

        Returns:
            The matching :class:`~daitum_model.Table`.

        Raises:
            ValueError: If no table with that id exists in the model.
        """
        if not any(table.id == id for table in self._tables):
            raise ValueError(f"The table {id} does not exist in the model")
        return next(table for table in self._tables if table.id == id)

    def get_named_value(self, id: str) -> Parameter | Calculation:
        """
        Return the named value (parameter or calculation) with the given id.

        Args:
            id: Identifier of the named value to look up.

        Returns:
            The matching :class:`~daitum_model.Parameter` or
            :class:`~daitum_model.Calculation`. Parameters are searched first,
            so a parameter is returned if both exist with the same id (which
            ``add_parameter`` / ``add_calculation`` would normally prevent).

        Raises:
            ValueError: If no named value with that id exists in the model.
        """
        if any(parameter.id == id for parameter in self._parameters):
            return next(parameter for parameter in self._parameters if parameter.id == id)
        if any(calculation.id == id for calculation in self._calculations):
            return next(calculation for calculation in self._calculations if calculation.id == id)
        raise ValueError(f"The named value {id} does not exist in the model")

    def get_validation_state(self) -> Calculation | Parameter:
        """
        Return (and lazily build) a calculation summarising current validity.

        The calculation evaluates to the highest
        :data:`~daitum_model.validator.SEVERITY_RANK` among every field, parameter,
        and calculation whose ``__invalid__`` formula is currently ``True``, or
        ``0`` when nothing is invalid. Useful as the gating value for
        :meth:`set_data_validation_rule`.

        The result is registered in the model under the id
        ``__validation_state__``. Subsequent calls return the already-registered
        calculation without rebuilding it, so call this only after every
        validator has been attached.

        Returns:
            A model-level :class:`~daitum_model.Calculation` whose integer
            value is the highest severity rank of any currently-invalid entity.
        """
        from daitum_model import formulas  # pylint: disable=import-outside-toplevel

        from .validator import SEVERITY_RANK  # pylint: disable=import-outside-toplevel

        if "__validation_state__" in [cal.id for cal in self._calculations]:
            return self.get_named_value("__validation_state__")

        # Collect invalid fields' severity rank
        field_severity = []
        named_values = self._parameters + self._calculations
        for named_value in named_values:
            for validator in named_value._validators:  # pylint: disable=protected-access
                invalid_value = self.get_named_value(
                    f"{named_value.id}__invalid__{validator.severity.value}"
                )
                field_severity.append(
                    formulas.IF(invalid_value, SEVERITY_RANK[validator.severity], 0)
                )

        # Use table[column] to get a BOOLEAN_ARRAY, then COUNT(array, True) > 0
        # to produce a scalar boolean indicating whether any row is invalid
        for table in self._tables:
            for field in table.get_fields():
                for validator in field._validators:  # pylint: disable=protected-access
                    invalid_field_name = f"{field.id}__invalid__{validator.severity.value}"
                    bool_formula = table[invalid_field_name]  # BOOLEAN_ARRAY
                    any_invalid = formulas.OR(bool_formula)
                    field_severity.append(
                        formulas.IF(any_invalid, SEVERITY_RANK[validator.severity], 0)
                    )

        if not field_severity:
            return self.add_calculation("__validation_state__", 0)

        return self.add_calculation("__validation_state__", formulas.MAX(*field_severity))

    def _add_table(self, table: Table):
        """
        Append ``table`` to the model after checking its id is unique.

        Raises:
            ValueError: If a table with the same id already exists.
        """
        if any(_table.id == table.id for _table in self._tables):
            raise ValueError(f"A table with id {table.id} already exists in the model")
        self._tables.append(table)

    @classmethod
    def read_from_file(cls, model_directory: str | os.PathLike[str]) -> "ModelBuilder":
        """
        Reconstruct a live :class:`ModelBuilder` from the canonical Daitum directory layout.

        The inverse of :meth:`write_to_file`. Reads ``model-definition.json`` and the
        scenario- and model-level ``named-values.json`` files from disk, then delegates to
        :meth:`read_from_dict` to do the actual decoding.

        Args:
            model_directory: The directory previously written by :meth:`write_to_file`.

        Returns:
            A :class:`ModelBuilder` equivalent to the one that produced the files.
        """
        root = pathlib.Path(model_directory)
        with (root / "model-definition.json").open(encoding="utf-8") as fp:
            definition = json.load(fp)

        named_values: list[dict[str, Any]] = []
        for relative in ("model-data/named-values.json", "scenarios/Initial/named-values.json"):
            path = root / relative
            if path.exists():
                with path.open(encoding="utf-8") as fp:
                    named_values.append(json.load(fp))

        return cls.read_from_dict(definition, named_values)

    @classmethod
    def read_from_dict(
        cls,
        definition: dict[str, Any],
        named_values: list[dict[str, Any]] | None = None,
    ) -> "ModelBuilder":
        """
        Reconstruct a live :class:`ModelBuilder` from already-parsed JSON dicts.

        The dict-level inverse of :meth:`build`. Rebuilds the tables, calculations, and
        parameters from ``definition``, then restores each parameter's value from the
        ``named_values`` payloads. The returned builder is fully re-editable (decoding
        routes through the ``add_*`` factories) and exposes the populated
        :class:`~daitum_model.decoding.LoadContext` via :attr:`load_context` for a
        configuration or UI load to consume.

        Args:
            definition: The dict produced by :meth:`build` (``model-definition.json``).
            named_values: Parsed ``named-values.json`` payloads (each a ``{"values": {...}}``
                dict) supplying parameter values. May be omitted when no values are needed.

        Returns:
            A :class:`ModelBuilder` equivalent to the one that produced the dict.
        """
        from ._decoders.model import decode_model  # pylint: disable=import-outside-toplevel
        from .decoding import LoadContext  # pylint: disable=import-outside-toplevel

        ctx = LoadContext()
        model = decode_model(definition, ctx)

        for payload in named_values or []:
            for param_id, value_dict in payload.get("values", {}).items():
                param = ctx.symbols.get(param_id)
                if isinstance(param, Parameter):
                    param._value = value_dict.get("value")  # pylint: disable=protected-access

        model._load_context = ctx  # pylint: disable=protected-access
        return model

    @property
    def load_context(self):
        """The :class:`~daitum_model.decoding.LoadContext` populated by :meth:`read_from_file`.

        ``None`` on a builder that was constructed directly rather than loaded.
        """
        return getattr(self, "_load_context", None)

    def write_to_file(self, model_directory: str | os.PathLike[str]) -> None:
        """
        Serialise the model into the canonical Daitum directory layout.

        Writes three files under ``model_directory``, creating it if it does
        not exist:

        - ``model-definition.json`` — the full model definition from :meth:`build`.
        - ``scenarios/Initial/named-values.json`` — scenario-level named values
          (those added with ``model_level=False``).
        - ``model-data/named-values.json`` — model-level named values
          (those added with ``model_level=True``).

        Args:
            model_directory: Destination directory. Parents are created as needed.

        Raises:
            ModelValidationError: If the model is structurally invalid. Validation runs
                (via :meth:`build`) before any file is written, so an invalid model
                produces no output.
        """
        root = pathlib.Path(model_directory)
        targets = [
            (root / "model-definition.json", self.build()),
            (root / "scenarios/Initial/named-values.json", self.to_named_value_dict(False)),
            (root / "model-data/named-values.json", self.to_named_value_dict(True)),
        ]
        for path, payload in targets:
            path.parent.mkdir(parents=True, exist_ok=True)
            with path.open("w", encoding="utf-8") as fp:
                json.dump(payload, fp, indent=2, sort_keys=True)

    def validate(self) -> "ValidationReport":
        """
        Run the structural validation pass over this model without raising.

        Detects circular dependencies, references to fields or tables that do not exist,
        and missing source fields, returning every problem in a
        :class:`~daitum_model.validation.ValidationReport`. :meth:`build` (and therefore
        :meth:`write_to_file`) calls this and raises
        :class:`~daitum_model.validation.ModelValidationError` when the report is not
        empty; call this directly to inspect problems programmatically.

        Returns:
            The validation report (``report.ok`` is ``True`` when the model is valid).
        """
        from daitum_model.validation import validate_model  # noqa: PLC0415

        return validate_model(self)

    def build(self) -> dict[str, Any]:
        """
        Build the JSON-compatible dict representation of the model.

        Change-tracking declarations are validated here (see
        :meth:`_validate_tracking`). The ``trackingGroupDefinitions`` and
        ``baselineDefinitions`` keys are only emitted when at least one tracking
        group or baseline has been declared, so untracked models are unaffected.

        Returns:
            A dict suitable for ``json.dump`` containing
            ``calculationDefinitions``, ``parameterDefinitions``,
            ``tableDefinitions``, ``optimisationCheckNamedValue``,
            ``partialEvaluationAllowed`` and, when present, the change-tracking
            definition maps.

        Raises:
            ValueError: If a change-tracking declaration is invalid.
            ModelValidationError: If the model is structurally invalid (circular
                dependencies, references to fields or tables that do not exist, or missing
                source fields). Every problem found is reported at once.
        """
        self._validate_tracking()
        self.validate().raise_if_errors()

        # Keyed by the shared ``MODEL_DEFINITION_KEYS`` vocabulary (via its always/conditional
        # split) so ``build`` and the decoder can never disagree on the top-level key set.
        emitters: dict[str, Any] = {
            "calculationDefinitions": lambda: {c.id: c.build() for c in self._calculations},
            "parameterDefinitions": lambda: {p.id: p.build() for p in self._parameters},
            "tableDefinitions": lambda: {t.id: t.build() for t in self._tables},
            "optimisationCheckNamedValue": lambda: (
                self._validation_named_val.id if self._validation_named_val else None
            ),
            "partialEvaluationAllowed": lambda: self._partial_evaluation_allowed,
            "trackingGroupDefinitions": lambda: {g.name: g.build() for g in self._tracking_groups},
            "baselineDefinitions": lambda: {b.name: b.build() for b in self._baselines},
        }

        definition: dict[str, Any] = {key: emitters[key]() for key in _ALWAYS_MODEL_KEYS}
        if self._tracking_groups:
            definition["trackingGroupDefinitions"] = emitters["trackingGroupDefinitions"]()
        if self._baselines:
            definition["baselineDefinitions"] = emitters["baselineDefinitions"]()

        return definition

    def _validate_tracking(self) -> None:
        """
        Validate change-tracking declarations.

        Raises:
            ValueError: If an element or baseline references an undeclared
                tracking group, or a table has a tracked field but no
                ``id_field``.
        """
        declared_groups = {group.name for group in self._tracking_groups}

        def check_element(kind: str, name: str, groups: list[str] | None) -> set[str]:
            used = set(groups or [])
            unknown = used - declared_groups
            if unknown:
                raise ValueError(
                    f"{kind} '{name}' references undeclared tracking group(s): "
                    f"{', '.join(sorted(unknown))}"
                )
            return used

        captured_groups: set[str] = set()

        for named_value in self._calculations:
            check_element("Calculation", named_value.id, named_value.tracking_groups)
        for param in self._parameters:
            check_element("Parameter", param.id, param.tracking_groups)

        for table in self._tables:
            table_has_tracked_field = False
            for field in table.get_fields():
                used = check_element("Field", field.id, field.tracking_groups)
                if used:
                    table_has_tracked_field = True
            if table_has_tracked_field and table.id_field is None:
                raise ValueError(
                    f"Table '{table.id}' has tracked fields but does not declare an id_field; "
                    "baseline row values are matched by identity, so a stable id_field is required"
                )

        for baseline in self._baselines:
            unknown = set(baseline.tracking_groups) - declared_groups
            if unknown:
                raise ValueError(
                    f"Baseline '{baseline.name}' references undeclared tracking group(s): "
                    f"{', '.join(sorted(unknown))}"
                )
            captured_groups.update(baseline.tracking_groups)

        for group_name in sorted(declared_groups - captured_groups):
            warnings.warn(
                f"Tracking group '{group_name}' is not captured by any baseline; "
                "tagging is inert.",
                stacklevel=2,
            )

    def to_named_value_dict(self, model_level: bool) -> dict[str, Any]:
        """
        Build the JSON-compatible dict of parameter values for one scope.

        Args:
            model_level: When ``True``, include only model-level parameters
                (written to ``model-data/named-values.json``). When ``False``,
                include only scenario-level parameters (written to
                ``scenarios/Initial/named-values.json``).

        Returns:
            ``{"values": {parameter_id: value_dict, ...}}``.
        """
        return {
            "values": {
                param.id: param.to_named_value_dict()
                for param in self._parameters
                if (param.model_level == model_level)
            }
        }
