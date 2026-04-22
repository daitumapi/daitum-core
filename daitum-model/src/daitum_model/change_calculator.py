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
Provides a utility class for generating formulas to calculate changes in fields,
parameters, or calculations in a model.
"""

from typing import cast

from typeguard import typechecked

from daitum_model import (
    Calculation,
    DataType,
    Field,
    Formula,
    MapDataType,
    ModelBuilder,
    Parameter,
    Table,
)
from daitum_model.formulas import COUNT, IF, SUM, VALUES

TRACKING_GROUP_MISSING = ValueError("ERROR - changes are not tracked for this field or named value")
TABLE_MISSING = ValueError("ERROR - table context must be provided when computing field changes")
MODEL_MISSING = ValueError(
    "ERROR - model context must be provided when computing named value changes"
)


@typechecked
def _get_tracked_object(
    model_object: Field | Parameter | Calculation, context: Table | ModelBuilder
) -> Field | Parameter | Calculation:
    if not model_object.tracking_group:
        raise TRACKING_GROUP_MISSING

    if isinstance(model_object, Field):
        if not isinstance(context, Table):
            raise TABLE_MISSING

        return context.get_field(model_object.tracking_id)

    if not isinstance(context, ModelBuilder):
        raise MODEL_MISSING

    return context.get_named_value(model_object.tracking_id)


def difference(
    model_object: Field | Parameter | Calculation, context: Table | ModelBuilder
) -> Formula:
    """
    Returns a formula representing the difference between the current and tracked value.

    Args:
        model_object: The model object to compare (Field, Parameter, or Calculation).
        context: The Table or Model context.

    Returns:
        A formula representing the numeric difference.
    """
    return model_object - _get_tracked_object(model_object, context)


def percent_increase(
    model_object: Field | Parameter | Calculation, context: Table | ModelBuilder
) -> Formula:
    """
    Returns a formula representing the percentage increase between the tracked and current
    value.

    Args:
        model_object: The model object to compare (Field, Parameter, or Calculation).
        context: The Table or Model context.

    Returns:
        A formula representing the numeric ratio.
    """
    return model_object / _get_tracked_object(model_object, context)


def total_difference(field: Field, table: Table) -> Formula:
    """
    Returns the total difference (aggregated across the table) between tracked and current
    field values.

    Args:
        field: A numeric field with tracking enabled.
        table: The table containing the field.

    Returns:
        A SUM formula representing the total change across the table.
    """
    data_type = field.data_type
    if data_type not in [DataType.INTEGER, DataType.DECIMAL]:
        raise ValueError(
            f"Can only compute total difference for INTEGER and DECIMAL types. "
            f"Received: {data_type}"
        )

    tracked_field = cast(Field, _get_tracked_object(field, table))

    return SUM(table[field.id]) - SUM(table[tracked_field.id])


def number_of_field_changes(field: Field, table: Table) -> Formula:
    """
    Counts the number of row-level changes for a specific field. If the field is not an array
    or map type, the returned value can only be 1 or 0.

    Args:
        field: The field to evaluate.
        table: The table containing the field.

    Returns:
        A COUNT formula representing the number of changes in the field.
    """
    data_type = field.data_type
    if data_type.is_array():
        return COUNT(_get_tracked_object(field, table).not_equal_to(field), True)
    if isinstance(data_type, MapDataType):
        return COUNT(
            VALUES(_get_tracked_object(field, table)).not_equal_to(VALUES(field)),
            True,
        )

    return IF(_get_tracked_object(field, table).not_equal_to(field), 1, 0)


def number_of_total_changes(field: Field, table: Table) -> Formula:
    """
    Returns the total number of changed rows in the table for a scalar field.

    Args:
        field: The field to evaluate.
        table: The table containing the field.

    Returns:
        A COUNT formula for the number of changes in the entire table.

    Raises:
        ValueError: If the field is an array or map type.
    """
    data_type = field.data_type
    if data_type.is_array() or isinstance(data_type, MapDataType):
        raise ValueError(
            "Cannot compute total table changes for array or map types. "
            "Use number_of_field_changes instead"
        )

    tracked_field = cast(Field, _get_tracked_object(field, table))

    return COUNT(table[tracked_field.id].not_equal_to(table[field.id]), True)


def has_changed(
    model_object: Field | Parameter | Calculation, context: Table | ModelBuilder
) -> Formula:
    """
    Returns a boolean formula indicating whether the object has changed.

    Args:
        model_object: The model object to evaluate.
        context: The Table or Model context.

    Returns:
        A boolean formula representing whether the object has changed.
    """
    data_type = model_object.to_data_type()
    if data_type.is_array():
        return (
            COUNT(_get_tracked_object(model_object, context).not_equal_to(model_object), True) > 0
        )
    if isinstance(data_type, MapDataType):
        return (
            COUNT(
                VALUES(_get_tracked_object(model_object, context)).not_equal_to(
                    VALUES(model_object)
                ),
                True,
            )
            > 0
        )

    return _get_tracked_object(model_object, context).not_equal_to(model_object)
