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
This module defines various enumerations used within the model generator framework.

Enumerations in this module provide a structured way to represent essential concepts such as
data types, sorting directions, aggregation methods, and SQL join types. These enumerations
help enforce consistency and clarity in model definitions and data processing.

## Enumerations Defined:

- **DataType**: Represents various data types, including primitive types (INTEGER, STRING, etc.)
  and their array counterparts.
- **SortDirection**: Defines sorting directions (ASCENDING or DESCENDING) for ordered operations.
- **AggregationMethod**: Lists possible aggregation methods, such as SUM, COUNT, AVERAGE, and more.
- **JoinType**: Specifies different types of SQL JOIN operations, including LEFT, RIGHT, INNER,
  and FULL.
"""

from enum import Enum


class DataType(Enum):
    """
    Enumeration representing various data types.

    This enumeration is used to specify different data types that can be used in calculations,
    parameters, or tables within a model.
    """

    INTEGER = "INTEGER"
    """Integer data type."""

    DECIMAL = "DECIMAL"
    """Decimal data type."""

    STRING = "STRING"
    """String data type."""

    BOOLEAN = "BOOLEAN"
    """Boolean data type."""

    DATE = "DATE"
    """Date data type."""

    DATETIME = "DATETIME"
    """Datetime data type."""

    TIME = "TIME"
    """Time data type."""

    INTEGER_ARRAY = "INTEGER_ARRAY"
    """Array of `INTEGER` data type."""

    DECIMAL_ARRAY = "DECIMAL_ARRAY"
    """Array of `DECIMAL` data type."""

    STRING_ARRAY = "STRING_ARRAY"
    """Array of `STRING` data type."""

    BOOLEAN_ARRAY = "BOOLEAN_ARRAY"
    """Array of `BOOLEAN` data type."""

    DATE_ARRAY = "DATE_ARRAY"
    """Array of `DATE` data type."""

    DATETIME_ARRAY = "DATETIME_ARRAY"
    """Array of `DATETIME` data type."""

    TIME_ARRAY = "TIME_ARRAY"
    """Array of `TIME` data type."""

    NULL = "NULL"
    """ Used to identify BLANK() formulae. **Should never be used** explicitly in models """

    def to_array(self) -> "DataType":
        """
        Converts the data type to its corresponding array type.

        Returns:
            DataType: The array type corresponding to the current data type.

        Raises:
            ValueError: If the data type cannot be converted to an array.
        """
        result = _TO_ARRAY_MAP.get(self)
        if result is None:
            raise ValueError(f"Cannot convert {self.name} to an array type")
        return result

    def from_array(self) -> "DataType":
        """
        Converts the array data type back to its primitive type.

        Returns:
            DataType: The primitive type corresponding to the current array data type.

        Raises:
            ValueError: If the array data type cannot be converted to a primitive type.
        """
        result = _FROM_ARRAY_MAP.get(self)
        if result is None:
            raise ValueError(f"Cannot convert {self.name} from an array type")
        return result

    def is_array(self) -> bool:
        """
        Checks if the data type is an array type.

        Returns:
            bool: `True` if the data type is an array, `False` otherwise.
        """
        return self in {
            DataType.INTEGER_ARRAY,
            DataType.DECIMAL_ARRAY,
            DataType.STRING_ARRAY,
            DataType.BOOLEAN_ARRAY,
            DataType.DATE_ARRAY,
            DataType.DATETIME_ARRAY,
            DataType.TIME_ARRAY,
        }


_TO_ARRAY_MAP: dict["DataType", "DataType"] = {
    DataType.INTEGER: DataType.INTEGER_ARRAY,
    DataType.DECIMAL: DataType.DECIMAL_ARRAY,
    DataType.STRING: DataType.STRING_ARRAY,
    DataType.BOOLEAN: DataType.BOOLEAN_ARRAY,
    DataType.DATE: DataType.DATE_ARRAY,
    DataType.DATETIME: DataType.DATETIME_ARRAY,
    DataType.TIME: DataType.TIME_ARRAY,
}

_FROM_ARRAY_MAP: dict["DataType", "DataType"] = {v: k for k, v in _TO_ARRAY_MAP.items()}

PRIMITIVE_DATA_TYPES = {
    DataType.INTEGER,
    DataType.DECIMAL,
    DataType.STRING,
    DataType.BOOLEAN,
    DataType.DATE,
    DataType.DATETIME,
    DataType.TIME,
}


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


class JoinType(Enum):
    """
    Enumeration for the various types of SQL JOIN operations.
    """

    LEFT = "LEFT"
    """A LEFT join returns all records from the left table, and the matched records from the right
     table."""

    RIGHT = "RIGHT"
    """A RIGHT join returns all records from the right table, and the matched records from the left
     table."""

    INNER = "INNER"
    """An INNER join returns only the rows where there is a match between the two tables based on
     the join condition. If no match is found, the row is excluded from the result."""

    FULL = "FULL"
    """A FULL join returns all rows from both tables—whether or not there's a match between them. It
     combines the behavior of both the LEFT join and RIGHT join, keeping every row from both the
     left and right tables."""


class BoundType(Enum):
    """Whether a range bound is inclusive or exclusive."""

    INCLUSIVE = "Inclusive"
    EXCLUSIVE = "Exclusive"


class Severity(Enum):
    """Enumeration of validation severity levels."""

    INFO = "Info"
    WARNING = "Warning"
    ERROR = "Error"
    CRITICAL = "Critical"


SEVERITY_RANK = {
    Severity.INFO: 1,
    Severity.WARNING: 2,
    Severity.ERROR: 3,
    Severity.CRITICAL: 4,
}
