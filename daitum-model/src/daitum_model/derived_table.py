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
``DerivedTable`` and its supporting enums and helpers.

A derived table is built from another source table with optional grouping,
filtering, sorting and aggregation. The aggregation helpers in this module
validate which ``AggregationMethod`` values are legal for each
``DataType``/``ObjectDataType``/``MapDataType`` and compute the resulting
data type.
"""

from __future__ import annotations

from enum import Enum

from typeguard import typechecked

from ._buildable import Buildable
from .data_types import (
    PRIMITIVE_DATA_TYPES,
    BaseDataType,
    DataType,
    MapDataType,
    ObjectDataType,
)
from .fields import DataField, Field
from .tables import Table


class SortDirection(Enum):
    """
    Enumeration representing the possible sorting options for a `SortKey` in a `DerivedTable`.
    """

    ASCENDING = "ASCENDING"
    """Ascending sort direction."""

    DESCENDING = "DESCENDING"
    """Descending sort direction."""


class AggregationMethod(Enum):
    """
    Enumeration listing the possible aggregation methods for aggregated fields.
    """

    BLANK = "BLANK"
    """ Returns a typed null for the target field without aggregating values.
     Allowed DataTypes: any type.
     Return DataTypes: same as the allowed type. """

    COUNT = "COUNT"
    """ Counts the number of non-null input items and returns that count. Result type is
     INTEGER irrespective of the source item type.
     Allowed DataTypes: any type.
     Return DataTypes: INTEGER. """

    SUM = "SUM"
    """ Sums numeric inputs. For array targets, performs element-wise sum across arrays.
     Allowed DataTypes: INTEGER, DECIMAL, INTEGER_ARRAY, DECIMAL_ARRAY.
     Return DataTypes: same as the allowed type. """

    MIN = "MIN"
    """ Returns the minimum (by natural ordering) of the inputs.
     Allowed DataTypes: any comparable scalar type (INTEGER, DECIMAL, STRING, BOOLEAN,
     DATE, TIME, DATETIME) and other comparable values. Not intended for arrays.
     Return DataTypes: same as the allowed type. """

    MAX = "MAX"
    """ Returns the maximum (by natural ordering) of the inputs.
     Allowed DataTypes: any comparable scalar type (INTEGER, DECIMAL, STRING, BOOLEAN,
     DATE, TIME, DATETIME) and other comparable values. Not intended for arrays.
     Return DataTypes: same as the allowed type. """

    AVERAGE = "AVERAGE"
    """ Calculates the arithmetic mean of numeric inputs and returns a DECIMAL value.
     Allowed DataTypes: INTEGER, DECIMAL.
     Return DataTypes: DECIMAL. """

    FIRST = "FIRST"
    """ Returns the first input value encountered (typed), or null if none.
     Allowed DataTypes: any type.
     Return DataTypes: same as the allowed type. """

    LAST = "LAST"
    """ Returns the last input value encountered (typed), or null if none.
     Allowed DataTypes: any type.
     Return DataTypes: same as the allowed type. """

    EQUAL = "EQUAL"
    """ If all input values are equal, returns that value; otherwise returns typed null.
     Allowed DataTypes: any type.
     Return DataTypes: same as the allowed type. """

    AND = "AND"
    """ Logical AND over boolean inputs. Nulls are treated as false by booleanValue() conversion.
     Allowed DataTypes: BOOLEAN.
     Return DataTypes: same as the allowed type. """

    OR = "OR"
    """ Logical OR over boolean inputs. Nulls are treated as false by booleanValue() conversion.
     Allowed DataTypes: BOOLEAN.
     Return DataTypes: same as the allowed type. """

    ARRAY = "ARRAY"
    """ Collects input items into an array of the target element type, preserving order.
     Allowed DataTypes: any non-array types except MapDataType (e.g., INTEGER, DECIMAL,
     STRING, BOOLEAN, DATE, TIME, DATETIME, OBJECT)
     Return DataTypes: the corresponding array type of the allowed type. (e.g., INTEGER_ARRAY,
     DECIMAL_ARRAY, STRING_ARRAY, BOOLEAN_ARRAY, DATE_ARRAY, TIME_ARRAY, DATETIME_ARRAY,
     OBJECT_ARRAY) """

    REFERENCE = "REFERENCE"
    """ Creates an OBJECT_ARRAY of references from row ids provided by the evaluation engine.
     Allowed DataTypes: any type.
     Return DataTypes: OBJECT_ARRAY for a specific table. """

    INTERSECTION = "INTERSECTION"
    """ Computes the set intersection across array inputs and returns an array result.
     Allowed DataTypes: any scalar or array type.
     Return DataTypes: the array of the scalar type when scalar target is provided, or the
     same array type when the target is already an array. """

    UNION = "UNION"
    """ Computes the set union of inputs. If inputs are arrays, unions their elements; if inputs
     are scalars, unions individual values..
     Allowed DataTypes: any scalar or array type.
     Return DataTypes: the array of the scalar type when scalar target is provided, or the same
     array type when the target is already an array. """


def _is_valid_aggregation(
    data_type: BaseDataType,
    aggregation_method: AggregationMethod,
) -> bool:
    """
    Return ``True`` if *aggregation_method* is valid for the given *data_type*.

    Args:
        data_type: The data type of the source field.
        aggregation_method: The proposed aggregation method.

    Returns:
        ``True`` if the combination is supported, ``False`` otherwise.
    """
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
) -> BaseDataType:
    """
    Determine the result data type after applying *aggregation_method* to *source_field*.

    Args:
        source_field: The field being aggregated.
        aggregation_method: The aggregation method to apply.

    Returns:
        The resulting data type.

    Raises:
        ValueError: If *aggregation_method* is not valid for the source field's data type.
    """
    data_type: BaseDataType = source_field.data_type

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
