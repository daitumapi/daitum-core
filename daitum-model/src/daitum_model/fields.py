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
Field hierarchy: :class:`Field` base + the three concrete field types
(:class:`DataField`, :class:`CalculatedField`, :class:`ComboField`).

A field is a column on a :class:`~daitum_model.Table`. Each field carries an id,
a data type, and an optional set of :class:`~daitum_model.validator.Validator`
instances. Concrete field types differ in where the value comes from — imported
data, a formula, or a hybrid that switches between the two.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from typeguard import typechecked

from daitum_model.serialisation import Buildable, json_type_info

from .data_types import BaseDataType, DataType, _FieldBase
from .formula import Formula, Operand
from .tracking import normalise_tracking_groups

if TYPE_CHECKING:
    from .tables import Table
    from .tracking import TrackingGroup
    from .validator import Severity, Validator


_NON_NULLABLE_DATA_TYPES: frozenset[DataType] = frozenset(
    {
        DataType.INTEGER,
        DataType.DECIMAL,
        DataType.STRING,
        DataType.BOOLEAN,
    }
)

#: The complete camelCase key vocabulary a field's ``build()`` can emit, across all three concrete
#: field types. Co-located with the field classes so it is the single source of truth for both the
#: serialiser (the generic :class:`~daitum_model.serialisation.Buildable` walk over these attrs)
#: and the field decoder's unmapped-key guard, which imports it as ``_KNOWN_KEYS``. Fields build via
#: the generic walk rather than a custom ``build``; this set is pinned to that walk's actual output
#: by ``test_guard_key_sets`` so it cannot drift. ``@type`` is the discriminator emitted by
#: :func:`~daitum_model.serialisation.json_type_info`; the rest are the camelised public attributes
#: set across :class:`DataField`, :class:`CalculatedField` and :class:`ComboField`.
FIELD_BUILD_KEYS: frozenset[str] = frozenset(
    {
        "@type",
        "id",
        "tableId",
        "dataType",
        "formula",
        "calculateInOptimiser",
        "orderIndex",
        "description",
        "defaultValue",
        "importFormat",
        "unique",
        "nullable",
        "trackingGroups",
    }
)


@dataclass
@typechecked
class ValidationFieldsContainer:
    """The synthetic calculated fields produced by one validator on a parent field."""

    #: Severity of the associated validator.
    severity: Severity
    #: Boolean calculated field; ``True`` when the parent field's value is invalid.
    invalid_field: Field
    #: String calculated field carrying the error message when invalid; blank otherwise.
    message_field: Field
    #: Summary message describing the validation failure.
    summary_message: str


# pylint: disable=too-many-instance-attributes
@typechecked
class Field(Buildable, _FieldBase, Operand):
    """
    Abstract base for a column on a :class:`~daitum_model.Table`.

    Use the concrete subclasses :class:`DataField`, :class:`CalculatedField`,
    and :class:`ComboField` rather than constructing :class:`Field` directly.
    Every field has an ``id``, an owning ``table``, and a ``data_type``;
    optionally an ``order_index``, a ``description``, and zero or more
    :class:`~daitum_model.validator.Validator` instances (at most one per
    :class:`~daitum_model.validator.Severity`).
    """

    def __init__(
        self,
        id: str,
        table: Table,
        data_type: BaseDataType,
    ):
        super().__init__(id)
        #: The owning table's id.
        self.table_id = table.id
        self._table = table
        #: The :class:`~daitum_model.data_types.BaseDataType` of this field.
        self.data_type = data_type
        #: Order in which this field appears in the table (lower comes first).
        self.order_index: int | None = None
        #: Free-text description shown in the UI.
        self.description: str | None = None
        #: Names of the tracking groups this field belongs to (``None`` when untracked).
        self.tracking_groups: list[str] | None = None

        self._validators: list[Validator] = []
        self._combined_message_field: Field | None = None

    @property
    def table(self) -> Table:
        """The :class:`~daitum_model.Table` that owns this field."""
        return self._table

    def set_tracking_groups(self, groups: list[str | TrackingGroup]) -> Field:
        """
        Assign this field to one or more change-tracking groups.

        A tracked field requires its table to declare an ``id_field``. Passing an
        empty list clears tracking.

        Args:
            groups: Tracking groups (or their names) this field belongs to.

        Returns:
            This field, for chaining.
        """
        normalised = normalise_tracking_groups(groups)
        self.tracking_groups = normalised or None
        return self

    def set_order_index(self, idx: int | None) -> Field:
        """Set the field's position within its table (lower values come first)."""
        self.order_index = idx
        return self

    def set_description(self, desc: str | None) -> Field:
        """Set the field's free-text description."""
        self.description = desc
        return self

    def to_string(self) -> str:
        return f"[{self.id}]"

    def to_data_type(self) -> BaseDataType:
        return self.data_type

    def add_validator(self, validator: Validator) -> None:
        """Attach a :class:`~daitum_model.validator.Validator` to this field.

        Each field may carry at most one validator per
        :class:`~daitum_model.validator.Severity`.

        Raises:
            ValueError: If a validator with the same severity is already attached.
        """

        if validator.severity in [val.severity for val in self._validators]:
            raise ValueError(f"Duplicate severity validator detected for field: {self.id}")

        self._validators.append(validator)
        validator._attach_to_field(self, self._table)  # pylint: disable=protected-access

    def get_validation_fields(
        self, severity: Severity | None = None
    ) -> list[ValidationFieldsContainer] | ValidationFieldsContainer | None:
        """Return the synthetic validation fields generated for this field's validators.

        Args:
            severity: When given, return only the validation fields for that
                severity. When ``None``, return one
                :class:`ValidationFieldsContainer` per attached validator,
                sorted by ascending severity rank.

        Returns:
            A single :class:`ValidationFieldsContainer`, a list of them, or
            ``None`` if no validator matches.
        """
        from .validator import SEVERITY_RANK  # pylint: disable=import-outside-toplevel

        if not self._validators:
            return None

        # return all validations' fields in a list
        if not severity:
            validation_fields = []
            for validator in self._validators:
                validation_fields.append(
                    ValidationFieldsContainer(
                        validator.severity,
                        self._table.get_field(f"{self.id}__invalid__{validator.severity.value}"),
                        self._table.get_field(f"{self.id}__message__{validator.severity.value}"),
                        validator.summary_message,
                    )
                )

            return sorted(validation_fields, key=lambda v: SEVERITY_RANK.get(v.severity, 0))

        # return the corresponding validation fields
        for validator in self._validators:
            if validator.severity == severity:
                return ValidationFieldsContainer(
                    validator.severity,
                    self._table.get_field(f"{self.id}__invalid__{severity.value}"),
                    self._table.get_field(f"{self.id}__message__{severity.value}"),
                    validator.summary_message,
                )
        return None

    def get_combined_message_field(self) -> Field | None:
        """Return a single calculated field combining all per-severity messages.

        The combined field is a STRING_ARRAY ordered from highest to lowest
        severity (CRITICAL → ERROR → WARNING → INFO); blank messages are
        excluded. The field is registered on the table as
        ``{id}__message__combined`` on first call and cached for subsequent
        calls.

        Returns:
            The combined-message field, or ``None`` if this field has no
            validators. When exactly one validator is attached, that
            validator's existing message field is returned directly.
        """
        # to avoid circular import
        from daitum_model import formulas  # pylint: disable=import-outside-toplevel

        from .validator import SEVERITY_RANK  # pylint: disable=import-outside-toplevel

        if not self._validators:
            return None

        if self._combined_message_field is not None:
            return self._combined_message_field

        if len(self._validators) == 1:
            single_validator = self._validators[0]
            return self._table.get_field(f"{self.id}__message__{single_validator.severity.value}")

        # Sort highest severity first so the combined array is ordered
        sorted_validators = sorted(
            self._validators, key=lambda v: SEVERITY_RANK.get(v.severity, 0), reverse=True
        )
        msg_fields = [
            self._table.get_field(f"{self.id}__message__{v.severity.value}")
            for v in sorted_validators
        ]

        # ignore_null=True so blank messages are excluded from the array
        formula = formulas.ARRAY(True, *msg_fields)

        combined_id = f"{self.id}__message__combined"
        self._combined_message_field = self._table.add_calculated_field(combined_id, formula)
        return self._combined_message_field


@json_type_info("calculated")
@typechecked
class CalculatedField(Field):
    """A field whose value is computed by a :class:`~daitum_model.Formula`.

    The field's data type is taken from the formula. Calculated fields are
    read-only — their value is recomputed whenever inputs change.
    """

    def __init__(
        self,
        id: str,
        table: Table,
        formula: Formula,
    ):
        super().__init__(id, table, formula.data_type)
        #: The formula evaluated to produce this field's value.
        self.formula = formula

    def dependencies(self) -> set[Operand]:
        """The reference leaves (fields / calculations / parameters / tables) this field's formula
        uses. Empty when the formula is a literal constant."""
        return self.formula.dependencies()


@json_type_info("data")
@typechecked
class DataField(Field):
    """A field populated from imported data or an optional default value."""

    def __init__(
        self,
        id: str,
        table: Table,
        data_type: BaseDataType,
    ):
        super().__init__(id, table, data_type)
        #: Default value applied when no imported value is present.
        self.default_value: Any = None
        #: Import format hint (e.g. a date pattern) applied when parsing input rows.
        self.import_format: str | None = None
        #: Whether values in this column must be unique within the table.
        self.unique: bool = False
        #: Whether this field accepts null/blank values. Integer, decimal, string and boolean
        #: fields default to not nullable; every other type (dates/times, arrays, object
        #: references, maps) defaults to nullable.
        self.nullable: bool = data_type not in _NON_NULLABLE_DATA_TYPES

    def set_default_value(self, value: Any) -> DataField:
        """Set the default value used when no imported value is present."""
        self.default_value = value
        return self

    def set_import_format(self, fmt: str | None) -> DataField:
        """Set the import format hint applied when parsing this field on import."""
        self.import_format = fmt
        return self

    def set_unique(self, unique: bool) -> DataField:
        """Require values in this column to be unique within the table."""
        self.unique = unique
        return self

    def set_nullable(self, nullable: bool) -> DataField:
        """Allow null/blank values in this column."""
        self.nullable = nullable
        return self


@json_type_info("combo")
@typechecked
class ComboField(Field):
    """A field that switches between data and calculated behaviour.

    Combo fields carry a :class:`~daitum_model.Formula` *and* an underlying
    stored value. The :attr:`calculate_in_optimiser` flag chooses which one
    the optimiser sees:

    - ``calculate_in_optimiser=True``: the optimiser evaluates the formula
      (treating the field as a :class:`CalculatedField`), while outside
      optimisation the stored data value is used.
    - ``calculate_in_optimiser=False``: the optimiser uses the stored data
      value (treating the field as a :class:`DataField`), while outside
      optimisation — for example when the field is rendered in the UI — the
      formula is evaluated (treating the field as a :class:`CalculatedField`).
    """

    def __init__(
        self,
        id: str,
        table: Table,
        formula: Formula,
        calculate_in_optimiser: bool,
    ):
        super().__init__(id, table, formula.data_type)
        #: Formula evaluated when the field is treated as calculated.
        self.formula = formula
        #: Selects whether the optimiser evaluates the formula or reads the stored value.
        #: See the class docstring for the full behaviour.
        self.calculate_in_optimiser = calculate_in_optimiser
        #: Default value applied when no imported value is present.
        self.default_value: Any = None
        #: Import format hint applied when parsing input rows.
        self.import_format: str | None = None

    def dependencies(self) -> set[Operand]:
        """The reference leaves this field's formula uses (empty for a string-only formula)."""
        return self.formula.dependencies()

    def set_default_value(self, value: Any) -> ComboField:
        """Set the default value used when no imported value is present."""
        self.default_value = value
        return self

    def set_import_format(self, fmt: str | None) -> ComboField:
        """Set the import format hint applied when parsing this field on import."""
        self.import_format = fmt
        return self
