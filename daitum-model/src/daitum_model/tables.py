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
Module for defining and managing different types of tables used in the model, including data tables,
derived tables, joined tables, and union tables. Each table type has specific attributes and methods
to facilitate field addition, sorting, grouping, filtering, and joining operations.

Tables:
    - DataTable: Represents a data table that can hold plain data fields and calculated fields.
        This table type is used for holding raw data and decision variables for optimisation.
    - DerivedTable: Represents a table derived from another source table, with support for grouping,
        sorting, filtering, and additional field calculations.
    - JoinedTable: Represents a table resulting from a join operation on two or more tables,
        based on defined join conditions.
    - UnionTable: Represents a table resulting from a union operation on multiple source tables,
        stacking rows from different tables into one unified result.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

from typeguard import typechecked

from ._buildable import Buildable
from ._helpers import _validate_name
from .data_types import MapDataType, ObjectDataType, _TableBase
from .enums import (
    PRIMITIVE_DATA_TYPES,
    SEVERITY_RANK,
    AggregationMethod,
    DataType,
    JoinType,
    SortDirection,
)
from .fields import (
    CalculatedField,
    ComboField,
    DataField,
    Field,
)
from .formula import CONST, Formula, Operand


@typechecked
class Table(Buildable, _TableBase):  # pylint: disable=too-many-instance-attributes
    """
    The base class for all table types.

    This class defines the core structure and behavior of a table, including field management
    and relationships with derived tables.

    Attributes:
        id (str): The unique identifier for the table.
        id_field (Optional[str]): The ID field of the table, which uniquely identifies records.
        key_column_field (Optional[str]): The key column field, used for lookup or indexing
            purposes.
        model_level (bool): Indicates whether the table is at the model level (True) or scenario
            level (False).
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
        return self.key_column_field

    @property
    def validation_group(self) -> str | None:
        return self._validation_group

    @property
    def display_name(self) -> str:
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

    def set_export_as_key_column(self, export_as_key=True):
        """
        Configures the table to export its key column instead of the row number when generating
            reports.

        Args:
            export_as_key (bool, optional): If True, the table's key column is exported.
            If False, the row number is exported instead. Defaults to True.
        """
        self.export_as_key_column = export_as_key

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
        data_type: DataType | ObjectDataType | MapDataType,
    ) -> DataField:
        """
        Registers a placeholder field with the given ID and data type.

        Use this when a field must exist before its final definition is known — for example,
        when using PREV or NEXT, or to resolve circular dependencies in combo fields.
        The placeholder will be automatically replaced when add_calculated_field or
        add_combo_field is later called with the same id.

        Args:
            id (str): The unique ID of the field.
            data_type (DataType | ObjectDataType | MapDataType): The data type of the field.

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
        data_type: DataType | ObjectDataType | MapDataType,
        tracking_group: str | None = None,
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
        tracking_group: str | None = None,
    ) -> DataField:
        """
        Adds an object reference field to the table.

        Args:
            id (str): The ID of the new field.
            table (Table): The table being referenced.
            is_array (bool, optional): Whether the object reference is an array.
            tracking_group (str, optional): Group identifier for change tracking.

        Returns:
            DataField: The created object reference field.
        """
        object_reference_field = DataField(id, self, ObjectDataType(table, is_array))
        if tracking_group is not None:
            object_reference_field.set_tracking_group(tracking_group)
        self._add_field(object_reference_field)

        if tracking_group is not None:
            self.add_object_reference_field(
                object_reference_field.tracking_id,
                table,
                is_array,
            )

        return object_reference_field

    def add_map_field(
        self,
        id: str,
        data_type: DataType,
        table: Table,
        tracking_group: str | None = None,
    ) -> DataField:
        """
        Adds a map field to the table.

        Args:
            id (str): The ID of the new field.
            data_type (DataType): The underlying data type of the map values.
            table (Table): The table field maps into.
            tracking_group (str, optional): Group identifier for change tracking.

        Returns:
            DataField: The created map field.
        """
        map_data_type = MapDataType(data_type, table)
        map_field = DataField(id, self, map_data_type)
        if tracking_group is not None:
            map_field.set_tracking_group(tracking_group)
        self._add_field(map_field)

        if tracking_group is not None:
            self.add_map_field(map_field.tracking_id, data_type, table)

        return map_field

    def add_calculated_field(
        self,
        id: str,
        formula: Operand | float | int | bool | str,
        order_index: int | None = None,
        description: str | None = None,
        tracking_group: str | None = None,
    ) -> CalculatedField:
        """
        Adds a `CalculatedField` to the table.

        Args:
            id (str): The ID of the calculated field.
            formula (Formula): The formula used to compute the field value.
            order_index (Optional[int]): The order index of the field.
            description (Optional[str]): Description of the field.
            tracking_group (Optional[str]): Group identifier for change tracking.

        Returns:
            CalculatedField: The created `CalculatedField` object.
        """
        if not isinstance(formula, Formula):
            return self.add_calculated_field(
                id,
                CONST(formula),
                order_index,
                description,
                tracking_group,
            )
        calculated_field = CalculatedField(id, self, formula)
        if order_index is not None:
            calculated_field.set_order_index(order_index)
        if description is not None:
            calculated_field.set_description(description)
        if tracking_group is not None:
            calculated_field.set_tracking_group(tracking_group)
        self._add_field(calculated_field)

        if tracking_group is not None:
            self.add_calculated_field(
                calculated_field.tracking_id,
                formula,
                order_index,
                description,
            )
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
            raise ValueError(f"The field {id} does not exist in the table")
        return self.field_definitions[id]

    def get_fields(self) -> Sequence[Field]:
        """
        Retrieves all fields in the table.

        Returns:
            Sequence[Field]: A sequence of fields contained in the table.
        """
        return list(self.field_definitions.values())

    def create_derived_table(
        self,
        id: str,
        group_by: list[Field] | None = None,
        filter_field: Field | None = None,
    ) -> DerivedTable:
        """
        Creates a `DerivedTable` based on the current table.

        Args:
            id (str): The unique ID of the new derived table.
            group_by (list[Field], optional): Fields to group by.
            filter_field (Field, optional): A BOOLEAN field to filter rows by.

        Returns:
            DerivedTable: The created `DerivedTable` object.
        """
        return DerivedTable(id, self, group_by=group_by, filter_field=filter_field)

    def __getitem__(self, id: str) -> Formula:
        field = self.field_definitions.get(id)
        if not field:
            raise ValueError(f"The field with ID {id} does not exist in this table")

        field_data_type = field.data_type
        if isinstance(field_data_type, DataType):
            if field_data_type.is_array():
                raise ValueError("Cannot call __getitem__ on table with an array field")
            return Formula(field_data_type.to_array(), f"{self.id}[{id}]")
        if isinstance(field_data_type, ObjectDataType):
            if field_data_type.is_array():
                raise ValueError("Cannot call __getitem__ on table with an array field")
            return Formula(
                ObjectDataType(field_data_type._source_table, is_array=True),
                f"{self.id}[{id}]",
            )
        raise ValueError("Cannot call __getitem__ on table with a map field")

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
    capture a significant portion of the model's logic. For instance, in the ElectraNet 18-month
    planner, the `Work_Orders` table handles most of the model's logic.

    Attributes:
        id (str): The id of the table.
        key_column_field: (Optional[str]): The key used for object references to the derived table.
        id_field (Optional[str]): The ID field for the derived table.
        model_level (bool): A boolean indicating whether the `Table` is a model level or scenario
            level object.
    """

    def add_data_field(
        self,
        id: str,
        data_type: DataType | ObjectDataType | MapDataType,
        tracking_group: str | None = None,
    ) -> DataField:
        """
        Adds a `DataField` to the table.

        Args:
            id (str): The id of the data field.
            data_type (DataType): The data type of the field.
            tracking_group (str, optional): Group identifier for change tracking.

        Returns:
            DataField: The created `DataField` object.
        """
        data_field = DataField(id, self, data_type)
        if tracking_group is not None:
            data_field.set_tracking_group(tracking_group)

        if tracking_group is not None:
            self.add_data_field(data_field.tracking_id, data_type)

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
        if not isinstance(formula, Formula):
            return self.add_combo_field(id, CONST(formula), calculate_in_optimiser)
        combo_field = ComboField(id, self, formula, calculate_in_optimiser)
        self._add_field(combo_field)
        return combo_field


def _is_valid_aggregation(
    data_type: DataType | ObjectDataType | MapDataType,
    aggregation_method: AggregationMethod,
) -> bool:

    match aggregation_method:
        case (
            AggregationMethod.BLANK
            | AggregationMethod.COUNT
            | AggregationMethod.FIRST
            | AggregationMethod.LAST
            | AggregationMethod.EQUAL
            | AggregationMethod.REFERENCE
        ):
            result = True
        case AggregationMethod.SUM:
            result = data_type in [
                DataType.INTEGER,
                DataType.DECIMAL,
                DataType.INTEGER_ARRAY,
                DataType.DECIMAL_ARRAY,
            ]
        case AggregationMethod.MIN | AggregationMethod.MAX:
            result = data_type in PRIMITIVE_DATA_TYPES
        case AggregationMethod.AVERAGE:
            result = data_type in [DataType.INTEGER, DataType.DECIMAL]
        case AggregationMethod.AND | AggregationMethod.OR:
            result = data_type == DataType.BOOLEAN
        case AggregationMethod.ARRAY:
            result = data_type in PRIMITIVE_DATA_TYPES or (
                isinstance(data_type, ObjectDataType) and not data_type.is_array()
            )
        case AggregationMethod.INTERSECTION | AggregationMethod.UNION:
            result = not isinstance(data_type, MapDataType)
        case _:
            result = False
    return result


def _get_aggregated_data_type(
    source_field: Field,
    aggregation_method: AggregationMethod,
) -> DataType | ObjectDataType | MapDataType:

    data_type: DataType | ObjectDataType | MapDataType = source_field.data_type

    if not _is_valid_aggregation(data_type, aggregation_method):
        raise ValueError(
            f"Aggregation method {aggregation_method.name} is not valid for data type "
            f"{data_type}"
        )
    match aggregation_method:
        case AggregationMethod.COUNT:
            return DataType.INTEGER
        case AggregationMethod.AVERAGE:
            return DataType.DECIMAL
        case AggregationMethod.ARRAY:
            if not isinstance(data_type, MapDataType):
                return data_type.to_array()
        case AggregationMethod.REFERENCE:
            return ObjectDataType(source_field.table, is_array=True)
        case AggregationMethod.INTERSECTION | AggregationMethod.UNION:
            if not isinstance(data_type, MapDataType):
                return data_type if data_type.is_array() else data_type.to_array()
    return data_type


@typechecked
class DerivedTable(Table):
    """
    Represents a derived table that is based on another source table and supports grouping,
    sorting, and filtering.
    """

    def __init__(
        self,
        id: str,
        source_table: Table,
        group_by: list[Field] | None = None,
        filter_field: Field | None = None,
    ):
        super().__init__(id)
        self._source_table = source_table
        self.source_table_id: str = source_table.id
        self.grouping_configuration: DerivedTable._GroupingConfiguration | None = None
        self.filter_field: str | None = None
        self._filter_field_ref: Field | None = None
        self.sort_keys: list[DerivedTable._SortKey] = []

        if group_by is not None:
            for field in group_by:
                if field.tracking_group is not None:
                    raise ValueError("Currently do not support grouping by tracked fields")
            self.grouping_configuration = DerivedTable._GroupingConfiguration(group_by)

        if filter_field is not None:
            if filter_field.data_type != DataType.BOOLEAN:
                raise ValueError(f"Cannot filter on field with data type: {filter_field.data_type}")
            self._filter_field_ref = filter_field
            self.filter_field = filter_field.id

    def add_source_fields(  # noqa: PLR0912
        self, source_fields: list[Field] | None = None, include_validators: bool = False
    ):
        """
        Adds fields to the current object from the source table or grouping configuration.

        This method checks whether the `source_fields` parameter is provided. If `source_fields` is
        `None`, it adds all fields from the source table or grouped fields (depending on whether
        the grouping configuration is present). If `source_fields` is provided, it validates that
        each field is present in the available fields before adding it.

        Args:
            source_fields (list[Field]): A list of `Field` objects to be added. Defaults to `None`,
                for which case all available fields will be added.
            include_validators (bool): Whether to propagate validators from source fields to the
                derived table. Defaults to `False`.

        Raises:
            ValueError: If Any field in `source_fields` is not found in the available fields.

        Note:
            If `_grouping_configuration` is `None`, fields are taken from
            `self.source_table._fields`.
            If `_grouping_configuration` is not `None`, fields are taken from
            `self.grouping_configuration.group_by_fields`.
        """
        fields = (
            self.grouping_configuration._raw_fields
            if self.grouping_configuration
            else list(self._source_table.field_definitions.values())
        )

        field_list = list(source_fields or fields)

        if source_fields is not None:
            for field in source_fields:
                if field not in fields:
                    context = "grouped fields." if self.grouping_configuration else "source table."
                    raise ValueError(f"The field {field.id} does not appear in the {context}")

                if field.tracking_group is not None:
                    tracked_field = self._source_table.get_field(field.tracking_id)
                    if tracked_field not in field_list:
                        field_list.append(tracked_field)

        if include_validators and source_fields is not None:
            self._append_validator_fields(field_list)

        for field in field_list:
            is_validator_field = "__invalid__" in field.id or "__message__" in field.id
            if not include_validators and is_validator_field:
                continue

            data_field = DataField(field.id, self, field.data_type)
            if field.order_index is not None:
                data_field.set_order_index(field.order_index)
            if field.description is not None:
                data_field.set_description(field.description)
            if field.tracking_group is not None:
                data_field.set_tracking_group(field.tracking_group)
            self._add_field(data_field)

            if include_validators:
                for validator in field._validators:  # pylint: disable=protected-access
                    data_field._validators.append(validator)  # pylint: disable=protected-access

    def _append_validator_fields(self, field_list: list) -> None:
        existing_ids = {f.id for f in field_list}
        base_ids = {
            fid for fid in existing_ids if "__invalid__" not in fid and "__message__" not in fid
        }
        for (
            source_field
        ) in self._source_table.field_definitions.values():  # pylint: disable=protected-access
            fid = source_field.id
            if fid in existing_ids:
                continue
            if "__invalid__" not in fid and "__message__" not in fid:
                continue
            base_id = fid.split("__invalid__")[0].split("__message__")[0]
            if base_id in base_ids:
                field_list.append(source_field)

    def add_sort_key(self, field: Field, direction: SortDirection):
        """
        Adds a sort key to the derived table.

        Args:
            field (Field): The field to sort by.
            direction (SortDirection): The direction in which to sort.
        """
        self.sort_keys.append(DerivedTable._SortKey(field, direction))

    def add_aggregated_field(
        self,
        id: str,
        source_field: Field,
        aggregation_method: AggregationMethod,
        tracking_group: str | None = None,
    ) -> DataField:
        """
        Adds an aggregated field to the table.

        Args:
            id (str): The unique identifier for the aggregated field.
            source_field (Field): The source field that will be aggregated.
            aggregation_method (AggregationMethod): The method used to aggregate the `source_field`.
            tracking_group (str, optional): Group identifier for change tracking.

        Raises:
            ValueError: If no grouped fields are present in the table.
            ValueError: If the aggregation method is not valid for the source field's data type.
        """
        if self.grouping_configuration is None:
            raise ValueError(
                "Cannot add an aggregated field to a DerivedTable with no grouped fields"
            )
        data_type = _get_aggregated_data_type(source_field, aggregation_method)
        self.grouping_configuration.add_aggregated_field(id, source_field, aggregation_method)
        data_field = DataField(id, self, data_type)
        if tracking_group is not None:
            data_field.set_tracking_group(tracking_group)
        self._add_field(data_field)

        if tracking_group is not None:
            self.add_aggregated_field(
                data_field.tracking_id,
                self._source_table.get_field(source_field.tracking_id),
                aggregation_method,
            )

        return data_field

    class _SortKey(Buildable):
        def __init__(self, field: Field, direction: SortDirection):
            self.field = field.id
            self.direction = direction

    class _GroupingConfiguration(Buildable):
        def __init__(self, group_by_fields: list[Field]):
            self.group_by_fields = [f.id for f in group_by_fields]
            self.aggregated_fields: list[DerivedTable._GroupingConfiguration._AggregatedField] = []
            self._raw_fields = group_by_fields

        # pylint: disable=missing-function-docstring
        def add_aggregated_field(
            self, id: str, source_field: Field, aggregation_method: AggregationMethod
        ):
            self.aggregated_fields.append(
                DerivedTable._GroupingConfiguration._AggregatedField(
                    id, source_field, aggregation_method
                )
            )

        class _AggregatedField(Buildable):
            def __init__(self, id: str, source_field: Field, aggregation_method: AggregationMethod):
                self.aggregated_field_id = id
                self.source_field_id = source_field.id
                self.aggregation_method = aggregation_method.name


@typechecked
class JoinCondition(Buildable):
    """
    Represents a condition for joining two tables.
    """

    def __init__(
        self,
        left_table: Table,
        left_field: Field,
        right_table: Table,
        right_field: Field,
        join_type: JoinType,
    ):
        self._left_table = left_table
        self._left_field = left_field
        self._right_table = right_table
        self._right_field = right_field

        self.left_table_id = left_table.id
        self.left_table_field = left_field.id
        self.right_table_id = right_table.id
        self.right_table_field = right_field.id
        self.join_type = join_type

    @property
    def left_table(self) -> Table:
        return self._left_table

    @property
    def left_field(self) -> Field:
        return self._left_field

    @property
    def right_table(self) -> Table:
        return self._right_table

    @property
    def right_field(self) -> Field:
        return self._right_field


@typechecked
class JoinedTable(Table):
    """
    Represents a table resulting from a join operation.

    A `JoinedTable` is a table that is constructed by joining two or more other tables based on
    specific join conditions. A join operation combines rows from different tables based on a
    related field (column) between them. The `join_conditions` list defines how these tables are
    connected and which fields from the tables are used for the join.

    Joins can be of different types, such as `INNER`, `LEFT`, `RIGHT`, and `FULL`, and they dictate
    how the rows from the tables are combined and which rows are included in the final result.

    A `JoinCondition` consists of the following:
        - `left_table`: The left table involved in the join.
        - `left_field`: The field in the left table that is used to match with the right table.
        - `right_table`: The right table involved in the join.
        - `right_field`: The field in the right table that is used to match with the left table.
        - `join_type`: The type of join (e.g., INNER, LEFT, RIGHT, FULL).

    Multiple `JoinCondition` objects can be specified to represent more complex join scenarios. Each
    condition defines how a pair of tables are joined, and having multiple conditions allows for
    joining more than two tables at once, with each pair of tables joined based on the specific
    conditions defined. When there are multiple `JoinCondition` objects, the joins are performed in
    sequence, and the resulting table combines the results of all the joins.
    """

    def __init__(
        self,
        id: str,
        join_conditions: list[JoinCondition],
    ):
        super().__init__(id)
        self.join_conditions = join_conditions

    def add_table_reference(self, source_table: Table) -> Field:
        """
        Adds a reference to a table in the `JoinedTable`.

        This method allows for adding a reference field for a source table that is part of the join
        conditions. If the source table is not part of the join conditions, a `ValueError` will be
        raised.

        Args:
            source_table (Table): The table to be referenced.

        Returns:
            Field: The reference field for the source table.

        Raises:
            ValueError: If the source table is not present in any of the join conditions.
        """
        all_tables = list(
            {jc.left_table for jc in self.join_conditions}
            | {jc.right_table for jc in self.join_conditions}
        )

        if source_table not in all_tables:
            raise ValueError(
                f"The provided source table with id {source_table.id} is not present in the "
                f"JoinedTable"
            )

        table_object_reference = self.add_object_reference_field(source_table.id, source_table)

        return table_object_reference


@typechecked
class UnionSource(Buildable):
    """
    A source table in a union

    Attributes:
        source_table: The source table, multiple UnionSources in a UnionTable may reference the same
            table
        mapping_key: The key to identify this particular source in the union table. Must be unique
            in the union table.
    """

    def __init__(self, source_table: Table, mapping_key: str):
        self._source_table = source_table
        self.source_table_id = source_table.id
        self.mapping_key = mapping_key

    @property
    def source_table(self) -> Table:
        return self._source_table


@typechecked
class UnionTable(Table):
    """
    Represents a table that is derived by performing a union operation on multiple source tables.

    A union operation combines rows from multiple tables into a single table. Unlike joins,
     a union does not merge columns based on key relationships but instead stacks rows from
     different tables on top of each other.

    Attributes:
        source_tables: The list of tables being combined into the `UnionTable`.
        filter_field: An optional field ID that acts as a filter for selecting specific rows
                      across the source tables.
    """

    def __init__(
        self,
        id: str,
        source_tables: list[Table | UnionSource],
    ):
        super().__init__(id)
        self.filter_field: str | None = None
        self.source_tables = [
            (s if isinstance(s, UnionSource) else UnionSource(s, s.id)) for s in source_tables
        ]

        self.field_mappings: dict[str, UnionTable.FieldMapping] = {}

    def set_filter_field(self, field: Field) -> UnionTable:
        """Sets the filter field for this union table. Returns self."""
        self.filter_field = field.id
        return self

    def add_field(
        self,
        id: str,
        data_type: DataType | ObjectDataType | MapDataType,
        order_index: int | None = None,
        description: str | None = None,
    ) -> DataField:
        """
        Adds a new field to the `UnionTable`.

        Args:
            id: A unique identifier for the field.
            data_type: The data type of the field.
            order_index: (Optional) The order in which the field appears.

        Returns:
            DataField: The newly created `DataField` instance.
        """
        # tracking??
        data_field = DataField(id, self, data_type)
        if order_index is not None:
            data_field.set_order_index(order_index)
        if description is not None:
            data_field.set_description(description)
        self._add_field(data_field)
        return data_field

    def add_field_mapping(
        self, source_table: Table | UnionSource, field_name: str, source_field: Field
    ):
        """
        Maps a field from a source table to a field in the `UnionTable`.

        Field mappings allow fields with different names in different tables to be treated as
        equivalent in the `UnionTable`.

        Args:
            source_table: The source table containing the field, or a UnionSource describing the
                source table and the key to identify it if the same source is reused.
            field_name: The name of the field in the `UnionTable`.
            source_field: The corresponding field in the source table.

        Raises:
            ValueError: If the source table is not part of the `UnionTable`.
        """
        union_source = (
            source_table
            if isinstance(source_table, UnionSource)
            else UnionSource(source_table, source_table.id)
        )
        if union_source not in self.source_tables:
            raise ValueError("The provided source table does not appear in the UnionTable")

        if union_source.mapping_key not in self.field_mappings:
            self.field_mappings[union_source.mapping_key] = UnionTable.FieldMapping(union_source)
        self.field_mappings[union_source.mapping_key].add_map(field_name, source_field)

    def direct_field_mapping(self, source_tables: list[Table | UnionSource] | None = None):
        """
        Automatically maps fields from the source tables that have matching field IDs.

        If `source_tables` is not provided, it defaults to all source tables in the `UnionTable`.

        Args:
            source_tables: (Optional) A list of source tables to perform direct field mapping on.

        Raises:
            ValueError: If a provided source table is not part of the `UnionTable`.
        """
        tables = (
            [(s if isinstance(s, UnionSource) else UnionSource(s, s.id)) for s in source_tables]
            if source_tables
            else self.source_tables
        )

        for table in tables:
            if table not in self.source_tables:
                raise ValueError(
                    f"The provided source table with id {table.source_table_id} is not present in "
                    "the UnionTable"
                )
            for field in self.field_definitions.values():
                if (
                    isinstance(field, DataField)
                    and field.id in table.source_table.field_definitions
                ):
                    self.add_field_mapping(table, field.id, field)

    class FieldMapping(Buildable):
        def __init__(self, union_source: UnionSource):
            self.union_source = union_source
            self.mapping: dict[str, str] = {}

        @property
        def source_table(self) -> Table:
            """
            Returns: the source table for this field mapping.
            """
            return self.union_source.source_table

        @property
        def mapping_key(self) -> str:
            """
            Returns: mapping_key for this field mapping.
            """
            return self.union_source.mapping_key

        # pylint: disable=missing-function-docstring
        def add_map(self, field_name: str, source_field: Field):
            if source_field.id not in (field.id for field in self.source_table.get_fields()):
                raise ValueError(
                    f"The provided source field with id {source_field.id} does not appear in"
                    f" the source table"
                )

            self.mapping[field_name] = source_field.id

        def build(self) -> dict[str, Any]:
            return self.mapping
