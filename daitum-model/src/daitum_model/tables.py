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
The ``Table`` base class and the concrete ``DataTable``.

Other table types live in their own modules:

- :mod:`daitum_model.derived_table` -- ``DerivedTable``
- :mod:`daitum_model.joined_table` -- ``JoinedTable``, ``JoinCondition``
- :mod:`daitum_model.union_table` -- ``UnionTable``, ``UnionSource``
"""

from __future__ import annotations

from collections.abc import Sequence

from typeguard import typechecked

from daitum_model.serialisation import Buildable

from ._helpers import _validate_name
from .data_types import BaseDataType, DataType, MapDataType, ObjectDataType, _TableBase
from .fields import CalculatedField, ComboField, DataField, Field
from .formula import Formula, Operand, to_formula


@typechecked
class Table(Buildable, _TableBase, Operand):  # pylint: disable=too-many-instance-attributes
    """
    The base class for all table types.

    This class defines the core structure and behaviour of a table, including field management
    and relationships with derived tables.

    A table also satisfies the :class:`~daitum_model.formula.Operand` contract: passed *into* a
    formula function it behaves as an ``OBJECT_ARRAY`` operand whose rendered string is its id
    (so ``LOOKUP``/``ROWS``/``FILTER``/``INDEX`` accept a bare table with no special-casing).
    Note that ``table[field]`` (column access) is a *distinct* operator from
    :meth:`Operand.__getitem__` (member access) — it renders ``table[field]`` with brackets, never
    the dot form — so :meth:`__getitem__` is overridden below rather than inherited.
    """

    def __init__(
        self,
        id: str,
    ):
        _validate_name(id, "table id")
        super().__init__(id)
        self.key_column_field: str | None = None
        self.id_field: str | None = None
        self.model_level: bool = False
        self._validation_group: str | None = None
        self._display_name: str = id
        self.field_definitions: dict[str, Field] = {}
        self._initialised_ids: set[str] = set()

        self.export_as_key_column: bool = False

    @property
    def key_column(self) -> str | None:
        """The key column field ID used for object references, or ``None`` if not set."""
        return self.key_column_field

    @property
    def validation_group(self) -> str | None:
        """The validation group identifier, or ``None`` if not assigned to a group."""
        return self._validation_group

    @property
    def display_name(self) -> str:
        """The human-readable display name for this table. Defaults to the table ID."""
        return self._display_name

    def set_key_column(self, key_column: str) -> Table:
        """Sets the key column for this table. Returns self."""
        self.key_column_field = key_column
        return self

    def set_id_field(self, id_field: str) -> Table:
        """Sets the id field for this table. Returns self."""
        self.id_field = id_field
        return self

    def set_model_level(self, model_level: bool) -> Table:
        """Sets whether this table is model-level. Returns self."""
        self.model_level = model_level
        return self

    def set_validation_group(self, group: str) -> Table:
        """Sets the validation group for this table. Returns self."""
        self._validation_group = group
        return self

    def set_display_name(self, name: str) -> Table:
        """Sets the display name for this table. Returns self."""
        self._display_name = name
        return self

    def set_export_as_key_column(self, export_as_key: bool = True) -> Table:
        """
        Configures the table to export its key column instead of the row number when generating
            reports. Returns self.

        Args:
            export_as_key (bool, optional): If True, the table's key column is exported.
            If False, the row number is exported instead. Defaults to True.
        """
        self.export_as_key_column = export_as_key
        return self

    def _add_field(self, field: Field):
        if field.id in self.field_definitions:
            if field.id in self._initialised_ids:
                del self.field_definitions[field.id]
                self._initialised_ids.discard(field.id)
            else:
                raise ValueError(f"A field with id {field.id} already exists in the table")
        self.field_definitions[field.id] = field

    def initialise_field(
        self,
        id: str,
        data_type: BaseDataType,
    ) -> DataField:
        """
        Registers a placeholder field with the given ID and data type.

        Use this when a field must exist before its final definition is known — for example,
        when using PREV or NEXT, or to resolve circular dependencies in combo fields.
        The placeholder will be automatically replaced when add_calculated_field or
        add_combo_field is later called with the same id.

        Args:
            id (str): The unique ID of the field.
            data_type (BaseDataType): The data type of the field.

        Returns:
            DataField: The placeholder field, which can be referenced in formulas.
        """
        placeholder = DataField(id, self, data_type)
        self._initialised_ids.add(id)
        self.field_definitions[id] = placeholder
        return placeholder

    def add_data_field(
        self,
        id: str,
        data_type: BaseDataType,
    ) -> DataField:
        """
        Adds a data field to the table.

        This method should be implemented by subclasses and is not valid for the base Table class.

        Raises:
            NotImplementedError: Always raised since this method is not applicable to `Table`.
        """
        raise NotImplementedError("ERROR - add_data_field is not valid for this type of table")

    def add_object_reference_field(
        self,
        id: str,
        table: Table,
        is_array: bool = False,
    ) -> DataField:
        """
        Adds an object reference field to the table.

        Args:
            id (str): The ID of the new field.
            table (Table): The table being referenced.
            is_array (bool, optional): Whether the object reference is an array.

        Returns:
            DataField: The created object reference field.
        """
        object_reference_field = DataField(id, self, ObjectDataType(table, is_array))
        self._add_field(object_reference_field)
        return object_reference_field

    def add_map_field(
        self,
        id: str,
        data_type: DataType,
        table: Table,
    ) -> DataField:
        """
        Adds a map field to the table.

        Args:
            id (str): The ID of the new field.
            data_type (DataType): The underlying data type of the map values.
            table (Table): The table field maps into.

        Returns:
            DataField: The created map field.
        """
        map_data_type = MapDataType(data_type, table)
        map_field = DataField(id, self, map_data_type)
        self._add_field(map_field)
        return map_field

    def add_calculated_field(
        self,
        id: str,
        formula: Operand | float | int | bool | str,
        order_index: int | None = None,
        description: str | None = None,
    ) -> CalculatedField:
        """
        Adds a `CalculatedField` to the table.

        Args:
            id (str): The ID of the calculated field.
            formula (Formula): The formula used to compute the field value.
            order_index (int | None): The order index of the field.
            description (str | None): Description of the field.

        Returns:
            CalculatedField: The created `CalculatedField` object.
        """
        formula = to_formula(formula)
        calculated_field = CalculatedField(id, self, formula)
        if order_index is not None:
            calculated_field.set_order_index(order_index)
        if description is not None:
            calculated_field.set_description(description)
        self._add_field(calculated_field)
        return calculated_field

    def get_field(self, id: str) -> Field:
        """
        Retrieves a field from the table.

        Args:
            id (str): The ID of the field to retrieve.

        Returns:
            Field: The field object matching the given ID.

        Raises:
            ValueError: If the field does not exist in the table.
        """
        if id not in self.field_definitions:
            available = ", ".join(self.field_definitions) or "<none>"
            raise ValueError(
                f"The field {id!r} does not exist in table {self.id!r} "
                f"(available fields: {available})"
            )
        return self.field_definitions[id]

    def get_fields(self) -> Sequence[Field]:
        """
        Retrieves all fields in the table.

        Returns:
            Sequence[Field]: A sequence of fields contained in the table.
        """
        return list(self.field_definitions.values())

    def to_string(self) -> str:
        """Render this table as a formula operand — its id (an ``OBJECT_ARRAY`` reference)."""
        return self.id

    def to_data_type(self) -> BaseDataType:
        """The data type of this table used as an operand: an ``OBJECT_ARRAY`` over itself."""
        return ObjectDataType(self, is_array=True)

    def __getitem__(self, id: str) -> Formula:
        """
        Return an array-typed formula referencing the entire column *id* of this table.

        This is *column access* — a distinct operator from member access
        (:meth:`Operand.__getitem__`): it renders ``table_id[field_id]`` with brackets, which the
        platform requires for a raw-table column (the dot form is invalid there).

        Args:
            id: The field ID to look up.

        Returns:
            A ``Formula`` whose expression is ``table_id[field_id]`` and whose data type is
            the array variant of the field's data type.

        Raises:
            ValueError: If *id* does not exist, is already an array type, or is a map type.
        """
        from daitum_model import expression as _expr

        return _expr.ColumnAccess(self, id)

    def get_validation_state(self) -> Field | CalculatedField:
        """
        Build a calculated field representing the maximum severity rank among all
        currently-invalid fields in this table.

        For each field with validators, ``COUNT(table[field__invalid__severity], True) > 0``
        is used to check whether any row is invalid at that severity level.  The result
        is a scalar formula — all rows will carry the same value — evaluating to the highest
        ``SEVERITY_RANK`` among failing fields, or ``0`` when nothing is invalid.

        The result is registered in the table as a calculated field named
        ``__validation_state__``.  Subsequent calls return the already-registered
        field without rebuilding it.

        Returns:
            CalculatedField: A calculated field whose value is the highest severity rank
            of any currently-invalid field in this table.
        """
        from daitum_model import formulas  # pylint: disable=import-outside-toplevel

        from .validator import SEVERITY_RANK  # pylint: disable=import-outside-toplevel

        if "__validation_state__" in [field.id for field in self.get_fields()]:
            return self.get_field("__validation_state__")

        # Collect invalid fields' severity rank
        field_severity = []
        for field in self.get_fields():
            for validator in field._validators:  # pylint: disable=protected-access
                invalid_field_name = f"{field.id}__invalid__{validator.severity.value}"
                bool_formula = self[invalid_field_name]  # BOOLEAN_ARRAY
                any_invalid = formulas.OR(bool_formula)
                field_severity.append(
                    formulas.IF(any_invalid, SEVERITY_RANK[validator.severity], 0)
                )

        if not field_severity:
            return self.add_calculated_field("__validation_state__", 0)

        return self.add_calculated_field("__validation_state__", formulas.MAX(*field_severity))


@typechecked
class DataTable(Table):
    """
    Data Tables are used wherever plain data is required, including all input tables. Notably,
    optimiser decision variables can only appear in Data Tables, as these cells contain plain
    data that the optimiser writes.

    In addition to holding data fields, Data Tables often include calculated fields, which can
    capture a significant portion of the model's logic.
    """

    def add_data_field(
        self,
        id: str,
        data_type: BaseDataType,
    ) -> DataField:
        """
        Adds a `DataField` to the table.

        Args:
            id (str): The id of the data field.
            data_type (DataType): The data type of the field.

        Returns:
            DataField: The created `DataField` object.
        """
        data_field = DataField(id, self, data_type)
        self._add_field(data_field)
        return data_field

    def add_combo_field(
        self,
        id: str,
        formula: Operand | float | int | bool | str,
        calculate_in_optimiser: bool,
    ) -> ComboField:
        """
        Adds a `ComboField` to the table.

        Args:
            id (str): The id of the calculated field.
            formula (Formula): The formula used to calculate the field.
            calculate_in_optimiser (bool): Specifies whether the formula is evaluated during
                optimisation.

        Returns:
            ComboField: The created `ComboField` object.
        """
        formula = to_formula(formula)
        combo_field = ComboField(id, self, formula, calculate_in_optimiser)
        self._add_field(combo_field)
        return combo_field
