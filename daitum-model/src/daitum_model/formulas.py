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
This module provides various functions that generate formulas used in Daitum models.
"""

from typing import Any, cast

from typeguard import typechecked

from daitum_model import (
    DataType,
    Formula,
    MapDataType,
    ObjectDataType,
    Table,
)
from daitum_model._base_formulas import (
    _ABS,
    _AND,
    _ARRAY,
    _ARRAYMAX,
    _ARRAYMIN,
    _AVERAGE,
    _BITAND,
    _BITMASK,
    _BITMASKSTRING,
    _BITOR,
    _BLANK,
    _CEILING,
    _CHAR,
    _CHOOSE,
    _CONTAINS,
    _COUNT,
    _COUNTBLANKS,
    _COUNTDUPLICATES,
    _DATE,
    _DATETIME,
    _DAY,
    _DAYSBETWEEN,
    _DISTINCT,
    _DISTRIBUTE,
    _EOMONTH,
    _EXP,
    _FILTER,
    _FIND,
    _FINDDUPLICATES,
    _FLOOR,
    _FROMTIMEZONE,
    _GET,
    _HOUR,
    _HOURSBETWEEN,
    _IF,
    _IFBLANK,
    _IFERROR,
    _INDEX,
    _INTEGER,
    _INTERSECTION,
    _ISBLANK,
    _ISERROR,
    _LEFT,
    _LEN,
    _LOOKUP,
    _LOOKUPARRAY,
    _LOWER,
    _MATCH,
    _MAX,
    _MEDIAN,
    _MIN,
    _MINUTE,
    _MOD,
    _MONTH,
    _MONTHSBETWEEN,
    _NEXT,
    _NOT,
    _OR,
    _PLUSDAYS,
    _PLUSMINUTES,
    _POWER,
    _PREV,
    _RANK,
    _RIGHT,
    _ROUND,
    _ROWS,
    _ROWVECTOR,
    _SECOND,
    _SETTIME,
    _SIZE,
    _STDEV,
    _SUM,
    _TEXT,
    _TEXTJOIN,
    _TIME,
    _TOMAP,
    _TOTIMEZONE,
    _TRIM,
    _UNION,
    _UPPER,
    _VALUES,
    _WEEKDAY,
    _WEIBULL,
    _YEAR,
)
from daitum_model.formula import CONST, Operand

# This applies type checking to all the functions in the file
typechecked()

NUMERIC_AND_ARRAY_TYPES = {
    DataType.INTEGER,
    DataType.DECIMAL,
    DataType.INTEGER_ARRAY,
    DataType.DECIMAL_ARRAY,
}

BOOLEANISH_AND_ARRAY_TYPES = {
    DataType.BOOLEAN,
    DataType.BOOLEAN_ARRAY,
    DataType.DECIMAL,
    DataType.DECIMAL_ARRAY,
    DataType.INTEGER,
    DataType.INTEGER_ARRAY,
}

DATE_AND_ARRAY_TYPES = {
    DataType.DATE,
    DataType.DATETIME,
    DataType.DATE_ARRAY,
    DataType.DATETIME_ARRAY,
}

TIME_AND_ARRAY_TYPES = {
    DataType.TIME,
    DataType.DATETIME,
    DataType.TIME_ARRAY,
    DataType.DATETIME_ARRAY,
}

STRING_AND_ARRAY_TYPES = {DataType.STRING, DataType.STRING_ARRAY}


def _is_object_array(x: Table | Operand) -> bool:
    if isinstance(x, Table):
        return True

    data_type = x.to_data_type()

    return data_type.is_array() if isinstance(data_type, ObjectDataType) else False


def LOOKUP(
    table: Table | Operand,
    field_name: Operand | str,
    condition: Operand | int | float | str | bool,
    reverse_search: bool | Operand = False,
) -> Formula:
    """
    The LOOKUP function searches for a row in a table or object array where a specified field
    matches a given condition and returns the corresponding row. If no matching row is found, the
    formula evaluates to an error. An optional `reverse_search` argument can be provided; if True,
    the search begins from the end of the table and moves backwards. Only exact matches are
    considered. If any argument is blank or in an error state, the formula evaluates to an error.

    Arguments:
        table:
            The table or OBJECT_ARRAY in which to perform the lookup. If the input is blank or in an
            error state, the formula evaluates to an error.

            *Supported types*:

            .. container:: supported-types

                - TABLE
                - OBJECT_ARRAY
        field_name:
            The field name of the column to match against the condition. Must exist in `table`.
            If the field does not exist, the formula evaluates to an error. If a raw string is
            provided (rather than a formula), the method verifies that the field exists in the
            table, and raises a ValueError otherwise.

            *Supported types*:

            .. container:: supported-types

                - STRING
        condition:
            The condition value to search for within the specified column. Must be compatible with
            the column's data type. If the value is not found the formula evaluates to an error.

            *Supported types*:

            .. container:: supported-types

                - ANY
        reverse_search:
            Optional. If True, the search starts from the last row and moves backward toward the
            first row. Defaults to False. Only BOOLEAN values are accepted; otherwise, a ValueError
            is raised.

            *Supported types*:

            .. container:: supported-types

                - BOOLEAN

    Returns:
        The row in the table where the specified field equals the condition. If no row matches,
        the formula evaluates to an error.

        *Supported types*:

        .. container:: supported-types

            - OBJECT

    Raises:
        ValueError: if the specified field does not exist in the table.
        ValueError: if the data type of `condition` is incompatible with the field's data type.
        ValueError: if `table` is not a valid TABLE or OBJECT_ARRAY.
        ValueError: if `reverse_search` is not BOOLEAN.

    Examples:
        Basic usage:

        .. code-block:: python

            LOOKUP(my_table, "status", "active")
            # Returns the first row where status == "active"

        Using reverse search:

        .. code-block:: python

            LOOKUP(my_table, "status", "active", reverse_search=True)
            # Returns the last row where status == "active"
    """
    if not _is_object_array(table):
        raise ValueError("LOOKUP can only be called on a table or OBJECT_ARRAY")

    if isinstance(condition, int | float | str | bool):
        return LOOKUP(table, field_name, CONST(condition), reverse_search)

    if isinstance(reverse_search, bool):
        return LOOKUP(table, field_name, condition, CONST(reverse_search))

    table_data_type = None if isinstance(table, Table) else table.to_data_type()

    source_table = (
        table
        if isinstance(table, Table)
        else (
            cast(Table, table_data_type._source_table)
            if isinstance(table_data_type, ObjectDataType)
            else None
        )
    )
    assert source_table

    # This will be the default way to use it (with field_name as string),
    # but must also support a formula being passed in. For this latter case,
    # we cannot perform most type checks
    if isinstance(field_name, str):
        field = source_table.get_field(field_name)
        if not field:
            raise ValueError(f"Field '{field_name}' does not exist in the table")
        field_data_type = field.to_data_type()
        condition_data_type = condition.to_data_type()

        if condition_data_type != field_data_type:
            raise ValueError(
                f"Cannot compare field of type {field_data_type} with condition of type "
                f"{condition_data_type}"
            )
        return LOOKUP(table, CONST(field_name), condition, reverse_search)

    if reverse_search.to_data_type() != DataType.BOOLEAN:
        raise ValueError(f"Reverse search data type {reverse_search.to_data_type()} is invalid")

    table_string = table.id if isinstance(table, Table) else table.to_string()

    return _LOOKUP(
        ObjectDataType(source_table),
        table_string,
        field_name.to_string(),
        condition.to_string(),
        reverse_search.to_string(),
    )


def MATCH(
    lookup_value: Operand | int | float | str | bool,
    lookup_array: Operand,
    reverse_search: bool | Operand = False,
) -> Formula:
    """
    The MATCH function searches for a specified value within an array and returns its 1-based index.
    If the value is not found, the formula evaluates to an error value. An optional argument
    `reverse_search`  can be provided; if set to True, the search begins at the end of the array and
    moves backwards. If the array contains duplicates, MATCH returns the first occurrence. If any
    argument is blank or in an error state, the formula evaluates to an error.

    Arguments:
        lookup_value:
            The value to search for in `lookup_array`. Must be compatible with the array elements.
            If `lookup_value` is blank or in an error state, or the value is not found, the returned
            formula will evaluate to an error.

            *Supported types*:

            .. container:: supported-types

                - INTEGER
                - DECIMAL
                - STRING
                - BOOLEAN
                - DATE
                - DATETIME
                - TIME
                - OBJECT
        lookup_array:
            The array in which to search for `lookup_value`. Must be a valid array type and
            compatible with the data type of `lookup_value`. If the array is blank or in an error
            state, the formula will evaluate to an error.

            *Supported types*:

            .. container:: supported-types

                - INTEGER_ARRAY
                - DECIMAL_ARRAY
                - STRING_ARRAY
                - BOOLEAN_ARRAY
                - DATE_ARRAY
                - DATETIME_ARRAY
                - TIME_ARRAY
                - OBJECT_ARRAY
        reverse_search:
             Optional. If True, the search starts from the end of the array and moves backward.
             Defaults to False. Only BOOLEAN values are accepted; otherwise, a ValueError is raised.

             *Supported types*:

             .. container:: supported-types

                 - BOOLEAN

    Returns:
        The 1-based index of the array where the match is found. If the value is not found, the
        formula will evaluate to an error.

        *Supported types*:

        .. container:: supported-types

            - INTEGER

    Raises:
        ValueError: if the data type of `lookup_value` is not a singular version of the data type of
            `lookup_array`.

    Examples:
        Basic usage:

        .. code-block:: python

            MATCH(5, [1, 3, 5, 7])
            # Returns 3

        Using reverse search:

        .. code-block:: python

            MATCH(5, [1, 3, 5, 7], reverse_search=True)
            # Returns 2
    """

    array_data_type = lookup_array.to_data_type()
    if not array_data_type.is_array():
        raise ValueError("MATCH can only be called on an array type")

    if isinstance(lookup_value, int | float | str | bool):
        return MATCH(CONST(lookup_value), lookup_array, reverse_search)

    if (
        isinstance(lookup_value, Operand)
        and array_data_type.from_array() != lookup_value.to_data_type()
    ):
        raise ValueError(
            f"Cannot search for {lookup_value.to_data_type()} in " f"{array_data_type}"
        )

    if isinstance(reverse_search, bool):
        return MATCH(lookup_value, lookup_array, CONST(reverse_search))

    if reverse_search.to_data_type() != DataType.BOOLEAN:
        raise ValueError(f"Reverse search data type {reverse_search.to_data_type()} is invalid")

    return _MATCH(
        lookup_value.to_string(),
        lookup_array.to_string(),
        reverse_search.to_string(),
    )


def ROWS(array: Table | Operand) -> Formula:
    """
    The ROWS function returns the number of rows in a specified table or array. If the input is
    blank or in an error state, the formula evaluates to an error. Only valid tables or array types
    are accepted.

    Arguments:
        array:
            The table or array for which to count the number of rows. Must be a valid table or array
            type. If the input is blank or in an error state, the formula evaluates to an error.

            *Supported types*:

            .. container:: supported-types

                - INTEGER_ARRAY
                - DECIMAL_ARRAY
                - STRING_ARRAY
                - BOOLEAN_ARRAY
                - DATE_ARRAY
                - DATETIME_ARRAY
                - TIME_ARRAY
                - OBJECT_ARRAY

    Returns:
        The total number of rows in the specified table or array. If the input is invalid, blank, or
        in an error state, the formula evaluates to an error.

        *Supported types*:

        .. container:: supported-types

            - INTEGER

    Raises:
        ValueError: if the input is not a valid table or array type.

    Examples:
        .. code-block:: python

            ROWS(my_table)
            # Returns the number of rows in my_table
    """
    if isinstance(array, Table):
        return _ROWS(array.id)

    array_data_type = array.to_data_type()

    if not array_data_type.is_array():
        raise ValueError("ROWS can only be called on an array type")

    return _ROWS(array.to_string())


def SUM(*values: Operand | int | float) -> Formula:
    """
    Calculates the sum of one or more numeric values.

    This formula computes the total of the specified values. Each input must be an int, float,
    or a Operand whose data type is numeric (INTEGER, INTEGER_ARRAY, DECIMAL, DECIMAL_ARRAY).
    If any input is blank or in an error state, the formula evaluates to an error.

    Arguments:
        *values:
            One or more arguments to be summed.

            *Supported types*:

            .. container:: supported-types

                - INTEGER
                - INTEGER_ARRAY
                - DECIMAL
                - DECIMAL_ARRAY

    Returns:
        The total sum of the specified values. If all inputs are integers, the result is INTEGER.
        If any input is DECIMAL or DECIMAL_ARRAY, the result is DECIMAL.

        *Supported types*:

        .. container:: supported-types

            - INTEGER
            - DECIMAL

    Raises:
        ValueError: if no arguments are provided.
        ValueError: if any argument is not a numeric type.

    Examples:
        Summing scalars:

        .. code-block:: python

            SUM(1, 2, 3)
            # Returns 6

        Summing arrays:

        .. code-block:: python

            SUM(my_table["amount"], my_table["tax"])
            # Returns the sum of the two columns amount and tax
    """

    if not values:
        raise ValueError("At least one input is required")

    # Convert all inputs to `Operand` if necessary
    converted_fields = [field if isinstance(field, Operand) else CONST(field) for field in values]

    ret_data_type = DataType.INTEGER
    for value in converted_fields:
        data_type = value.to_data_type()
        if data_type not in NUMERIC_AND_ARRAY_TYPES:
            raise ValueError(f"Datatype {data_type} is not a valid input for this method")
        if data_type in {DataType.DECIMAL, DataType.DECIMAL_ARRAY}:
            ret_data_type = DataType.DECIMAL

    string_values = [value.to_string() for value in converted_fields]

    return _SUM(ret_data_type, *string_values)


def POWER(
    mantissa: Operand | int | float,
    exponent: Operand | int | float,
) -> Formula:
    """
    Raises a number to the power of another number.

    Computes the result of raising the mantissa to the specified exponent. Inputs
    can be fields, parameters, calculations, or numeric constants.

    Arguments:
        mantissa:
            The base number to raise to a power.

            *Supported types*:

            .. container:: supported-types

                - INTEGER
                - DECIMAL
                - INTEGER_ARRAY
                - DECIMAL_ARRAY

        exponent:
            The exponent to which the mantissa is raised.

            *Supported types*:

            .. container:: supported-types

                - INTEGER
                - DECIMAL
                - INTEGER_ARRAY
                - DECIMAL_ARRAY

    Returns:
        The result of the exponentiation.

        *Supported types*:

        .. container:: supported-types

            - INTEGER (if both inputs are integer types)
            - DECIMAL (otherwise)
            - INTEGER_ARRAY or DECIMAL_ARRAY (if either input is an array)
    """

    if isinstance(mantissa, (int, float)):
        return POWER(CONST(mantissa), exponent)
    if isinstance(exponent, (int, float)):
        return POWER(mantissa, CONST(exponent))

    mantissa_data_type = mantissa.to_data_type()
    exponent_data_type = exponent.to_data_type()

    if not isinstance(mantissa_data_type, DataType) or not isinstance(exponent_data_type, DataType):
        raise ValueError(
            f"Incompatible data types for method POWER: {mantissa_data_type}, {exponent_data_type}"
        )

    if mantissa_data_type not in {
        DataType.DECIMAL,
        DataType.DECIMAL_ARRAY,
        DataType.INTEGER,
        DataType.INTEGER_ARRAY,
    }:
        raise ValueError(f"POWER does not support mantissa with data type: {mantissa_data_type}")

    if exponent_data_type not in {
        DataType.DECIMAL,
        DataType.DECIMAL_ARRAY,
        DataType.INTEGER,
        DataType.INTEGER_ARRAY,
    }:
        raise ValueError(f"POWER does not support exponent with data type: {exponent_data_type}")

    integer_types = {DataType.INTEGER, DataType.INTEGER_ARRAY}
    non_array_ret_data_type = (
        DataType.INTEGER
        if mantissa_data_type in integer_types and exponent_data_type in integer_types
        else DataType.DECIMAL
    )
    ret_is_array = mantissa_data_type.is_array() or exponent_data_type.is_array()
    ret_data_type = non_array_ret_data_type.to_array() if ret_is_array else non_array_ret_data_type

    return _POWER(ret_data_type, mantissa.to_string(), exponent.to_string())


def ROW() -> Formula:
    """
    Returns the row number of the current table row.

    The ROW function mimics the behavior of Excel's ROW function. It returns the 1-based index of
    the current row when evaluated in a table. If no table context is available (for example, when
    used in a named value), the formula evaluates to an error.

    Arguments:
        None.

    Returns:
        The 1-based row index of the current table.

        *Supported types*:

        .. container:: supported-types

            - INTEGER

    Examples:
        Basic usage within a table:

        .. code-block:: python

            ROW()
            # Returns 1 for the first row, 2 for the second, etc.

        Used outside a table context:

        .. code-block:: python

            ROW()
            # Evaluates to an error
    """
    return Formula(DataType.INTEGER, "ROW()")


def IF(
    condition: Operand | bool | int,
    true_branch: Operand | bool | int | float | str,
    false_branch: Operand | bool | int | float | str,
) -> Formula:
    """
    Returns one of two values depending on the evaluation of a condition.

    This function mimics the behavior of the Excel IF function. It evaluates the condition, and if
    true, returns the value of `true_branch`; otherwise, it returns the value of `false_branch`. If
    any input is blank or in an error state, the formula evaluates to an error.

    Arguments:
        condition:
            The condition to evaluate.

            *Supported types*:

            .. container:: supported-types

                - BOOLEAN
                - INTEGER (treats 0 as False, non-zero as True)

        true_branch:
            The value to return if the condition is true. Must be the same data type as
            `false_branch`, or NULL.

            *Supported types*:

            .. container:: supported-types

                - ANY

        false_branch:
            The value to return if the condition is false. Must be the same data type as
            `true_branch`, or NULL.

            *Supported types*:

            .. container:: supported-types

                - ANY

    Returns:
        Either `true_branch` or `false_branch`, depending on the condition.

        *Supported types*:

        .. container:: supported-types

            - ANY

    Raises:
        ValueError: If `condition` is not BOOLEAN or INTEGER.
        ValueError: If `true_branch` and `false_branch` have incompatible types (unless one is
            NULL).
        ValueError: If both `true_branch` and `false_branch` are NULL.

    Examples:
        Basic usage with literals:

        .. code-block:: python

            result = IF(True, "Yes", "No")

        Using fields and formulas:

        .. code-block:: python

            result = IF(customer["age"] > 18, "Adult", "Minor")

        Nested IF statements:

        .. code-block:: python

            result = IF(score > 90, "A", IF(score > 80, "B", IF(score > 70, "C", "F")))
    """

    if isinstance(condition, (int, bool)):
        return IF(CONST(condition), true_branch, false_branch)
    if isinstance(true_branch, (int, float, str, bool)):
        return IF(condition, CONST(true_branch), false_branch)
    if isinstance(false_branch, (int, float, str, bool)):
        return IF(condition, true_branch, CONST(false_branch))

    condition_data_type = condition.to_data_type()
    true_branch_data_type = true_branch.to_data_type()
    false_branch_data_type = false_branch.to_data_type()

    if not isinstance(condition_data_type, DataType) or condition_data_type not in {
        DataType.BOOLEAN,
        DataType.INTEGER,
    }:
        raise ValueError("An IF condition must be either a BOOLEAN or INTEGER")

    if (
        true_branch_data_type != false_branch_data_type
        and true_branch.to_data_type() != DataType.NULL
        and false_branch.to_data_type() != DataType.NULL
    ):
        raise ValueError(
            f"Both branches of IF statement must have the same data type. True branch: "
            f"{true_branch_data_type}. False branch: {false_branch_data_type}."
        )

    if true_branch.to_data_type() == DataType.NULL and false_branch.to_data_type() == DataType.NULL:
        raise ValueError("Both branches of IF statement cannot be blank.")
    ret_data_type = (
        true_branch_data_type if true_branch_data_type != DataType.NULL else false_branch_data_type
    )
    return _IF(
        ret_data_type,
        condition.to_string(),
        true_branch.to_string(),
        false_branch.to_string(),
    )


def FIND(
    match_string: Operand | str,
    search_string: Operand | str,
    start_index: Operand | int | None = None,
) -> Formula:
    """
    Returns the starting position of a substring within a string.

    This function mimics the behavior of the Excel FIND function. It searches for the first
    occurrence of `match_string` within `search_string` and returns the 1-based starting position.
    An optional `start_index` argument can be provided to begin the search from a specific position
    in the string.  If any argument is blank or in an error state, the formula evaluates to an
    error.

    FIND does have array support, meaning any of the arguments can be arrays and the output will
    also be an array. If multiple arguments are arrays, they must be of the same length,
    else the formula will evaluate to an error.

    Arguments:
        match_string:
            The substring to search for within `search_string`. If blank or in an error state, the
            formula evaluates to an error.

            *Supported types*:

            .. container:: supported-types

                - STRING
                - STRING_ARRAY

        search_string:
            The string within which to search for `match_string`. Must be a valid string or string
            array. If blank or in an error state, the formula evaluates to an error.

            *Supported types*:

            .. container:: supported-types

                - STRING
                - STRING_ARRAY

        start_index:
            Optional. The 1-based position to start searching from. Defaults to 1 if not provided.

            *Supported types*:

            .. container:: supported-types

                - INTEGER
                - INTEGER_ARRAY

    Returns:
        Returns the index within this string of the first occurrence of the specified substring,
        starting at `start_index` if specified, otherwise 1. If the substring is not found, the
        formula evaluates to 0.

        *Supported types*:

        .. container:: supported-types

            - INTEGER
            - INTEGER_ARRAY

    Raises:
        ValueError: if `match_string` or `search_string` is not of type STRING or STRING_ARRAY.
        ValueError: if `start_index` is not of type INTEGER or INTEGER_ARRAY.

    Examples:
        Basic usage:

        .. code-block:: python

            FIND("apple", "apple pie")
            # Returns 1

        Starting from a specific index:

        .. code-block:: python

            FIND("apple", "banana apple pie", start_index=5)
            # Returns 8
    """
    if isinstance(match_string, str):
        return FIND(CONST(match_string), search_string, start_index)
    if isinstance(search_string, str):
        return FIND(match_string, CONST(search_string), start_index)
    if start_index:
        if isinstance(start_index, int):
            return FIND(match_string, search_string, CONST(start_index))

    match_string_data_type = match_string.to_data_type()
    search_string_data_type = search_string.to_data_type()
    start_index_data_type = start_index.to_data_type() if start_index else None

    data_type_exception = ValueError(
        f"FIND is only supported for strings with type {DataType.STRING} or {DataType.STRING_ARRAY}"
    )

    if not isinstance(match_string_data_type, DataType) or not isinstance(
        search_string_data_type, DataType
    ):
        raise data_type_exception

    if search_string_data_type not in STRING_AND_ARRAY_TYPES:
        raise data_type_exception
    if match_string_data_type not in STRING_AND_ARRAY_TYPES:
        raise data_type_exception

    if start_index:
        if start_index_data_type not in {DataType.INTEGER, DataType.INTEGER_ARRAY}:
            raise ValueError(
                f"FIND's third argument must be of type {DataType.INTEGER} or "
                f"{DataType.INTEGER_ARRAY}"
            )

    ret_is_array = search_string_data_type.is_array() or match_string_data_type.is_array()
    ret_data_type = DataType.INTEGER_ARRAY if ret_is_array else DataType.INTEGER

    if start_index:
        ret_data_type = (
            DataType.INTEGER_ARRAY if start_index.to_data_type().is_array() else ret_data_type
        )
        return _FIND(
            ret_data_type,
            match_string.to_string(),
            search_string.to_string(),
            start_index.to_string(),
        )
    return _FIND(ret_data_type, match_string.to_string(), search_string.to_string())


def LEFT(
    input_string: Operand | str,
    length: Operand | int,
) -> Formula:
    """
    Returns a substring consisting of the leftmost characters from a string.

    This function mimics the behavior of Excel's LEFT function. It extracts a substring
    from the start of `input_string`, up to the number of characters specified by `length`.
    Both singular values and arrays are supported. If any argument is blank or in an error
    state, the formula evaluates to an error.

    Arguments:
        input_string:
            The string from which characters will be extracted. Can be a literal string,
            a field, formula, calculation, or parameter.

            *Supported types*:

            .. container:: supported-types

                - STRING
                - STRING_ARRAY

        length:
            The number of characters to extract from the left of `input_string`. If negative, the
            formula evaluates to an error.

            *Supported types*:

            .. container:: supported-types

                - INTEGER
                - INTEGER_ARRAY

    Returns:
        The substring consisting of the leftmost characters of `input_string` up to `index`.
        If either input is an array, an array of substrings is returned.

        *Supported types*:

        .. container:: supported-types

            - STRING
            - STRING_ARRAY

    Raises:
        ValueError: if `input_string` is not of type STRING or STRING_ARRAY.
        ValueError: if `index` is not of type INTEGER or INTEGER_ARRAY.

    Examples:
        Basic usage:

        .. code-block:: python

            LEFT("Hello World", 5)
            # Returns "Hello"

        Using a Field or Formula:

        .. code-block:: python

            LEFT(customer["name"], 3)
            # Returns first three characters of the customer's name

        With array input:

        .. code-block:: python

            LEFT(["Apple", "Banana", "Cherry"], 2)
            # Returns ["Ap", "Ba", "Ch"]
    """
    if isinstance(input_string, str):
        return LEFT(CONST(input_string), length)
    if isinstance(length, int):
        return LEFT(input_string, CONST(length))

    input_string_data_type = input_string.to_data_type()
    length_data_type = length.to_data_type()

    data_type_exception = ValueError(
        f"LEFT is only supported with input string data type {DataType.STRING} or "
        f"{DataType.STRING_ARRAY}"
    )

    if not isinstance(input_string_data_type, DataType) or not isinstance(
        length_data_type, DataType
    ):
        raise data_type_exception

    if input_string_data_type not in STRING_AND_ARRAY_TYPES:
        raise data_type_exception

    if length_data_type not in {DataType.INTEGER, DataType.INTEGER_ARRAY}:
        raise data_type_exception

    ret_is_array = input_string_data_type.is_array() or length_data_type.is_array()
    ret_data_type = DataType.STRING_ARRAY if ret_is_array else DataType.STRING

    return _LEFT(ret_data_type, input_string.to_string(), length.to_string())


def RIGHT(
    input_string: Operand | str,
    length: Operand | int,
) -> Formula:
    """
    Returns a substring consisting of the rightmost characters from a string.

    This function mimics the behavior of Excel's RIGHT function. It extracts a substring
    from the end of `input_string`, searching backwards up to the number of characters specified by
    `length`. Both singular values and arrays are supported. If any argument is blank or in an error
    state, the formula evaluates to an error.

    Arguments:
        input_string:
            The string from which characters will be extracted. Can be a literal string,
            a field, formula, calculation, or parameter.

            *Supported types*:

            .. container:: supported-types

                - STRING
                - STRING_ARRAY

        length:
            The number of characters to extract from the right of `input_string`. If negative, the
            formula evaluates to an error.

            *Supported types*:

            .. container:: supported-types

                - INTEGER
                - INTEGER_ARRAY

    Returns:
        The substring consisting of the rightmost characters of `input_string` up to `index`.
        If either input is an array, an array of substrings is returned.

        *Supported types*:

        .. container:: supported-types

            - STRING
            - STRING_ARRAY

    Raises:
        ValueError: if `input_string` is not of type STRING or STRING_ARRAY.
        ValueError: if `index` is not of type INTEGER or INTEGER_ARRAY.

    Examples:
        Basic usage:

        .. code-block:: python

            RIGHT("Hello World", 5)
            # Returns "World"

        Using a Field or Formula:

        .. code-block:: python

            RIGHT(customer["name"], 3)
            # Returns last three characters of the customer's name

        With array input:

        .. code-block:: python

            RIGHT(["Apple", "Banana", "Cherry"], 2)
            # Returns ["ue", "le", "ry"]
    """
    if isinstance(input_string, str):
        return RIGHT(CONST(input_string), length)
    if isinstance(length, int):
        return RIGHT(input_string, CONST(length))

    input_string_data_type = input_string.to_data_type()
    length_data_type = length.to_data_type()

    data_type_exception = ValueError(
        f"LEFT is only supported with input string data type {DataType.STRING} or "
        f"{DataType.STRING_ARRAY}"
    )

    if not isinstance(input_string_data_type, DataType) or not isinstance(
        length_data_type, DataType
    ):
        raise data_type_exception

    if input_string_data_type not in STRING_AND_ARRAY_TYPES:
        raise data_type_exception

    if length_data_type not in {DataType.INTEGER, DataType.INTEGER_ARRAY}:
        raise data_type_exception

    ret_is_array = input_string_data_type.is_array() or length_data_type.is_array()
    ret_data_type = DataType.STRING_ARRAY if ret_is_array else DataType.STRING

    return _RIGHT(ret_data_type, input_string.to_string(), length.to_string())


def PREV(field: Operand) -> Formula:
    """
    Returns the previous value of a field within a table.

    When used in a table, it retrieves the value of `field` from the previous row. If used
    outside a table context or if there is no previous row, the formula evaluates to an error.

    Arguments:
        field:
            The field whose previous value is to be retrieved. If a formula is provided, PREV will
            evaluate it for the previous row.

            *Supported types*:

            .. container:: supported-types

                - ANY

    Returns:
        The value of `field` from the preceding row in the table.

        *Supported types*:

        .. container:: supported-types

            - ANY
    """
    return _PREV(field.to_data_type(), field.to_string())


def NEXT(field: Operand) -> Formula:
    """
    Returns the next value of a field within a table.

    When used in a table, it retrieves the value of `field` from the next row. If used
    outside a table context or if there is no next row, the formula evaluates to an error.

    Arguments:
        field:
            The field whose next value is to be retrieved. If a formula is provided, PREV will
            evaluate it for the next row.

            *Supported types*:

            .. container:: supported-types

                - ANY

    Returns:
        The value of `field` from the next row in the table.

        *Supported types*:

        .. container:: supported-types

            - ANY
    """
    return _NEXT(field.to_data_type(), field.to_string())


def TEXT(value: Operand, formatting: Operand | str | None = None) -> Formula:
    """
    Converts a field or value to its text representation with optional formatting.

    This function mimics the behavior of Excel's TEXT function. It converts `value` to a string,
    optionally applying a formatting pattern. Both singular values and arrays are supported. If any
    argument is blank or in an error state, the formula evaluates to an error.

    Arguments:
        value:
            The value or field to convert to text.

            *Supported types*:

            .. container:: supported-types

                - ANY

        formatting:
            Optional. A string or field that specifies the text format to apply to `value`.
            If provided, must be a string or string array. Defaults to no formatting.

            *Supported types*:

            .. container:: supported-types

                - STRING
                - STRING_ARRAY

    Returns:
        The text representation of `value`, optionally formatted. Returns an array if `value` or
        `formatting` is an array.

        *Supported types*:

        .. container:: supported-types

            - STRING
            - STRING_ARRAY

    Raises:
        ValueError: If `formatting` is not STRING or STRING_ARRAY.

    Examples:
        Basic usage with literals:

        .. code-block:: python

            TEXT(123)
            # Returns "123"

        Using formatting:

        .. code-block:: python

            TEXT(0.75, "0.00%")
            # Returns "75.00%"

        With field references:

        .. code-block:: python

            TEXT(customer["balance"], "$0.00")
            # Returns formatted balance as text in dollar format

        With array input:

        .. code-block:: python

            TEXT([1, 2, 3], "00")
            # Returns ["01", "02", "03"]
    """

    ret_data_type = DataType.STRING_ARRAY if value.to_data_type().is_array() else DataType.STRING

    if formatting:
        if isinstance(formatting, str):
            return TEXT(value, CONST(formatting))

        if formatting.to_data_type() not in STRING_AND_ARRAY_TYPES:
            raise ValueError(
                f"TEXT is only supported with a formatting with type {DataType.STRING} or "
                f"{DataType.STRING_ARRAY}"
            )
        ret_data_type = (
            DataType.STRING_ARRAY if formatting.to_data_type().is_array() else ret_data_type
        )
        return _TEXT(ret_data_type, value.to_string(), formatting.to_string())

    return _TEXT(ret_data_type, value.to_string())


def BLANK(
    data_type: DataType | ObjectDataType | MapDataType | None = None,
) -> Formula:
    """
    Returns a blank value of the specified data type.

    This function creates a blank entry in a model or formula. By default, the blank value has type
    NULL, but a specific data type can be provided. Useful for setting default values or error
    cases.

    Arguments:
        data_type (DataType | ObjectDataType | MapDataType):
            Optional. The data type of the blank value. Defaults to NULL if not specified.

    Returns:
        A blank value of the specified data type.

        *Supported types*:

        .. container:: supported-types

            - ANY

    Examples:
        Creating a generic blank:

        .. code-block:: python

            BLANK()
            # Returns a NULL blank. Cannot be directly assigned to fields,
            # but can be used in other formulas.

        Creating a blank of a specific type:

        .. code-block:: python

            BLANK(DataType.STRING)
            # Returns a blank of type STRING. Can be assigned to a field or named value
    """
    return _BLANK(data_type if data_type else DataType.NULL)


def ISBLANK(value: Operand) -> Formula:
    """
    Returns True if the input value is blank, otherwise False.

    This function checks whether `value` is blank (empty or NULL). It evaluates to
    a boolean formula, making it useful for conditional logic and null-checking
    within models. Both singular values and arrays are supported.

    Arguments:
        value:
            The value to check if blank.

            *Supported types*:

            .. container:: supported-types

                - ANY

    Returns:
        True if `value` is blank, False otherwise. Returns an array of boolean values if `value` is
        an array.

        *Supported types*:

        .. container:: supported-types

            - BOOLEAN
            - BOOLEAN_ARRAY

    Examples:
        .. code-block:: python

            ISBLANK(customer["email"])
            # Returns True if email is blank, else False
    """
    return _ISBLANK(value.to_string())


def IFBLANK(
    value: Operand,
    blank_branch: Operand | int | str | float | bool,
) -> Formula:
    """
    Returns a specified value if the input value is blank, otherwise returns the `value`.

    This function checks whether `value` is blank (empty or null). If it is blank, the function
    returns `blank_branch`; otherwise, it returns the value of `value`. Both singular values and
    arrays are supported. This is useful for providing default values when data may be missing.

    Arguments:
        value:
            The value to check if blank.

            *Supported types*:

            .. container:: supported-types

                - ANY

        blank_branch:
            The value to return if `value` is blank. Must be compatible with the data type
            of `value` (or NULL).

            *Supported types*:

            .. container:: supported-types

                - ANY

    Returns:
        Either `blank_branch` if `value` is blank, or the original `value` otherwise.

        *Supported types*:

        .. container:: supported-types

            - ANY

    Raises:
        ValueError: If `value` and `blank_branch` have incompatible data types.
        ValueError: If both `value` and `blank_branch` have data type NULL.

    Examples:
        .. code-block:: python

            IFBLANK(order["discount"], order["default_discount"])
            # Returns the discount if present, else default_discount
    """
    if isinstance(blank_branch, (int, float, str, bool)):
        return IFBLANK(value, CONST(blank_branch))

    value_data_type = value.to_data_type()
    blank_branch_data_type = blank_branch.to_data_type()

    array_types_match = False
    if isinstance(value_data_type, DataType):
        array_types_match = (
            value_data_type.is_array() and value_data_type.from_array() == blank_branch_data_type
        )
    elif isinstance(value_data_type, ObjectDataType) and isinstance(
        blank_branch_data_type, ObjectDataType
    ):
        array_types_match = (
            value_data_type.is_array()
            and value_data_type._source_table == blank_branch_data_type._source_table
        )

    if (
        value_data_type != blank_branch_data_type
        and DataType.NULL not in (value_data_type, blank_branch_data_type)
        and not array_types_match
    ):
        raise ValueError(
            f"IFBLANK incompatible with data types {value_data_type} "
            f"and {blank_branch_data_type}"
        )

    if value_data_type == DataType.NULL and blank_branch_data_type == DataType.NULL:
        raise ValueError("Both branches of IFBLANK cannot be blank.")
    ret_data_type = value_data_type if value_data_type != DataType.NULL else blank_branch_data_type

    return _IFBLANK(ret_data_type, value.to_string(), blank_branch.to_string())


def FILTER(
    array: Table | Operand,
    filter_condition: Operand,
) -> Formula:
    """
    Returns a filtered subset of an array based on a specified condition.

    This function evaluates `array` and applies `filter_condition` to determine which
    elements or rows should be included in the result. The `filter_condition` must
    be an array of booleans, integers, or decimals representing the inclusion criteria.
    Both singular arrays and table objects are supported. If the condition or array
    is blank or in an error state, or if `array` and `filter_condition` are not arrays of the same
    size, the formula evaluates to an error.

    Arguments:
        array:
            The array or table to filter. The return will be a filtered array of the same type.

            *Supported types*:

            .. container:: supported-types

                - INTEGER_ARRAY
                - DECIMAL_ARRAY
                - STRING_ARRAY
                - BOOLEAN_ARRAY
                - DATE_ARRAY
                - DATETIME_ARRAY
                - TIME_ARRAY
                - OBJECT_ARRAY

        filter_condition:
            An array representing which elements or rows to include. Must be of type
            BOOLEAN_ARRAY, INTEGER_ARRAY, or DECIMAL_ARRAY. If a non-boolean type is used, the
            value is treated as True if non-zero, False if zero.

            *Supported types*:

            .. container:: supported-types

                - BOOLEAN_ARRAY
                - INTEGER_ARRAY
                - DECIMAL_ARRAY

    Returns:
        A filtered array containing only elements or rows that meet the `filter_condition`.
        Returns an array of the same type as `array` or an object array for tables.

        *Supported types*:

        .. container:: supported-types

            - INTEGER_ARRAY
            - DECIMAL_ARRAY
            - STRING_ARRAY
            - BOOLEAN_ARRAY
            - DATE_ARRAY
            - DATETIME_ARRAY
            - TIME_ARRAY
            - OBJECT_ARRAY

    Raises:
        ValueError: If `filter_condition` is not BOOLEAN_ARRAY, INTEGER_ARRAY, or DECIMAL_ARRAY.
        ValueError: If `array` is not an array or table type.

    Examples:
        Filtering an array of numbers:

        .. code-block:: python

            FILTER([1, 2, 3, 4, 5], [True, False, True, False, True])
            # Returns [1, 3, 5]

        Filtering a table:

        .. code-block:: python

            FILTER(customers_table, customers_table["active"])
            # Returns all rows where 'active' is True
    """
    filter_condition_data_type = filter_condition.to_data_type()

    if filter_condition_data_type not in {
        DataType.BOOLEAN_ARRAY,
        DataType.DECIMAL_ARRAY,
        DataType.INTEGER_ARRAY,
    }:
        raise ValueError(
            f"Filter condition must have a data type of either "
            f"{DataType.BOOLEAN_ARRAY, DataType.DECIMAL_ARRAY, DataType.INTEGER_ARRAY}."
        )

    if isinstance(array, Table):
        return _FILTER(ObjectDataType(array, True), array.id, filter_condition.to_string())

    array_data_type = array.to_data_type()

    if not array_data_type.is_array():
        raise ValueError("FILTER can only be called on an array type")

    return _FILTER(array_data_type, array.to_string(), filter_condition.to_string())


def MIN(*values: Operand | int | float) -> Formula:
    """
    Returns the minimum value among the provided inputs.

    This function evaluates the given inputs, which can be numeric literals, fields,
    formulas, calculations, or parameters, and returns the smallest value. It supports
    scalar and array-compatible numeric, date, time, and datetime types.

    Arguments:
        *values:
            An arbitrary number of values or fields to compare. All inputs must be of
            compatible types (numeric, date, time, or datetime).

            *Supported types*:

            .. container:: supported-types

                - INTEGER
                - DECIMAL
                - DATE
                - DATETIME
                - TIME
                - INTEGER_ARRAY
                - DECIMAL_ARRAY
                - DATE_ARRAY
                - DATETIME_ARRAY
                - TIME_ARRAY

    Returns:
        The minimum value among the inputs.

        *Supported types*:

        .. container:: supported-types

            - INTEGER
            - DECIMAL
            - DATE
            - DATETIME
            - TIME

    Raises:
        ValueError: If no inputs are provided.
        ValueError: If any input is of an unsupported type.
        ValueError: If inputs are of incompatible types.

    Examples:
        Minimum of numeric literals:

        .. code-block:: python

            MIN(3, 7, 1, 9)
            # Returns 1

        Minimum of multiple table columns:

        .. code-block:: python

            MIN(order_table["quantity"], order_table["min_quantity"])
            # Returns the smallest value between both columns

        Minimum of date values:

        .. code-block:: python

            MIN(DATE(2025, 1, 1), DATE(2024, 12, 31))
            # Returns DATE(2024, 12, 31)

    Note:
        This formula only returns a scalar value. For array-wise minimums, use the `ARRAYMIN`
        formula instead.
    """
    if not values:
        raise ValueError("At least one input is required")

    # Convert all inputs to `Operand` if necessary
    converted_value = [value if isinstance(value, Operand) else CONST(value) for value in values]

    ret_data_type = DataType.INTEGER
    # Check that all inputs are either numeric, date, time or datetime
    first_value_type = converted_value[0].to_data_type()
    for value in converted_value:
        data_type = value.to_data_type()

        if (
            data_type not in NUMERIC_AND_ARRAY_TYPES
            and data_type not in DATE_AND_ARRAY_TYPES
            and data_type not in {DataType.TIME, DataType.TIME_ARRAY}
        ):
            raise ValueError(f"Datatype {data_type} is not a valid input for this method")

        if first_value_type in NUMERIC_AND_ARRAY_TYPES and data_type not in NUMERIC_AND_ARRAY_TYPES:
            raise ValueError(f"Datatype {data_type} is not compatible with other inputs")

        if first_value_type in {DataType.TIME, DataType.TIME_ARRAY}:
            ret_data_type = DataType.TIME
            if data_type not in {DataType.TIME, DataType.TIME_ARRAY}:
                raise ValueError(f"Datatype {data_type} is not compatible with other inputs")

        if first_value_type in {DataType.DATE, DataType.DATE_ARRAY}:
            ret_data_type = DataType.DATE
            if data_type not in {DataType.DATE, DataType.DATE_ARRAY}:
                raise ValueError(f"Datatype {data_type} is not compatible with other inputs")

        if first_value_type in {DataType.DATETIME, DataType.DATETIME_ARRAY}:
            ret_data_type = DataType.DATETIME
            if data_type not in {DataType.DATETIME, DataType.DATETIME_ARRAY}:
                raise ValueError(f"Datatype {data_type} is not compatible with other inputs")

        if data_type in {DataType.DECIMAL, DataType.DECIMAL_ARRAY}:
            ret_data_type = DataType.DECIMAL

    value_strings = [value.to_string() for value in converted_value]
    return _MIN(ret_data_type, *value_strings)


def MAX(*values: Operand | int | float) -> Formula:
    """
    Returns the maximum value among the provided inputs.

    This function evaluates the given inputs, which can be numeric literals, fields,
    formulas, calculations, or parameters, and returns the smallest value. It supports
    scalar and array-compatible numeric, date, time, and datetime types.

    Arguments:
        *values:
            An arbitrary number of values or fields to compare. All inputs must be of
            compatible types (numeric, date, time, or datetime).

            *Supported types*:

            .. container:: supported-types

                - INTEGER
                - DECIMAL
                - DATE
                - DATETIME
                - TIME
                - INTEGER_ARRAY
                - DECIMAL_ARRAY
                - DATE_ARRAY
                - DATETIME_ARRAY
                - TIME_ARRAY

    Returns:
        The maximum value among the inputs.

        *Supported types*:

        .. container:: supported-types

            - INTEGER
            - DECIMAL
            - DATE
            - DATETIME
            - TIME

    Raises:
        ValueError: If no inputs are provided.
        ValueError: If any input is of an unsupported type.
        ValueError: If inputs are of incompatible types.

    Examples:
        Maximum of numeric literals:

        .. code-block:: python

            MAX(3, 7, 1, 9)
            # Returns 9

        Maximum of multiple table columns:

        .. code-block:: python

            MAX(order_table["quantity"], order_table["min_quantity"])
            # Returns the largest value between both columns

        Maximum of date values:

        .. code-block:: python

            MAX(DATE(2025, 1, 1), DATE(2024, 12, 31))
            # Returns DATE(2025, 1, 1)

    Note:
        This formula only returns a scalar value. For array-wise maximums, use the `ARRAYMAX`
        formula instead.
    """
    if not values:
        raise ValueError("At least one input is required")

    # Convert all inputs to `Operand` if necessary
    converted_value = [value if isinstance(value, Operand) else CONST(value) for value in values]

    ret_data_type = DataType.INTEGER
    # Check that all inputs are either numeric, date, time or datetime
    first_value_type = converted_value[0].to_data_type()
    for value in converted_value:
        data_type = value.to_data_type()

        if (
            data_type not in NUMERIC_AND_ARRAY_TYPES
            and data_type not in DATE_AND_ARRAY_TYPES
            and data_type not in {DataType.TIME, DataType.TIME_ARRAY}
        ):
            raise ValueError(f"Datatype {data_type} is not a valid input for this method")

        if first_value_type in NUMERIC_AND_ARRAY_TYPES and data_type not in NUMERIC_AND_ARRAY_TYPES:
            raise ValueError(f"Datatype {data_type} is not compatible with other inputs")

        if first_value_type in {DataType.TIME, DataType.TIME_ARRAY}:
            ret_data_type = DataType.TIME
            if data_type not in {DataType.TIME, DataType.TIME_ARRAY}:
                raise ValueError(f"Datatype {data_type} is not compatible with other inputs")

        if first_value_type in {DataType.DATE, DataType.DATE_ARRAY}:
            ret_data_type = DataType.DATE
            if data_type not in {DataType.DATE, DataType.DATE_ARRAY}:
                raise ValueError(f"Datatype {data_type} is not compatible with other inputs")

        if first_value_type in {DataType.DATETIME, DataType.DATETIME_ARRAY}:
            ret_data_type = DataType.DATETIME
            if data_type not in {DataType.DATETIME, DataType.DATETIME_ARRAY}:
                raise ValueError(f"Datatype {data_type} is not compatible with other inputs")

        if data_type in {DataType.DECIMAL, DataType.DECIMAL_ARRAY}:
            ret_data_type = DataType.DECIMAL

    value_strings = [value.to_string() for value in converted_value]
    return _MAX(ret_data_type, *value_strings)


def OR(*values: Operand | bool) -> Formula:
    """
    Returns True if any input evaluates to True.

    This function performs a logical disjunction (OR) over the provided inputs.
    If at least one value is True, the result is True; otherwise, the result
    is False. The inputs may be boolean literals, fields, formulas,
    calculations, or parameters.

    Arguments:
        *values:
            An arbitrary number of boolean or boolean-compatible inputs. At least
            one input is required. If the input is non-boolean, it is treated as True if non-zero,
            else False.

            *Supported types*:

            .. container:: supported-types

                - BOOLEAN
                - BOOLEAN_ARRAY
                - INTEGER
                - INTEGER_ARRAY
                - DECIMAL
                - DECIMAL_ARRAY

    Returns:
        True if any input is True, False otherwise. Evaluates to an error value if any input is null
        or in an error state. If a single array input is provided, returns scalar value representing
        the OR across all elements in the array. If multiple arrays are provided, returns an array
        where each element is the OR of the corresponding elements across all input arrays.

        *Supported types*:

        .. container:: supported-types

            - BOOLEAN
            - BOOLEAN_ARRAY

    Raises:
        ValueError: If no inputs are provided.
        ValueError: If any input is not boolean-compatible.

    Examples:
        Basic usage with literals:

        .. code-block:: python

            OR(True, False, False)
            # Returns True

        Usage with table column:

        .. code-block:: python

            OR(order_table["is_urgent"])
            # Returns True if any row in the column 'is_urgent' is True
    """
    if not values:
        raise ValueError("At least one input is required")

    # Convert all inputs to `Operand` if necessary
    converted_values = [value if isinstance(value, Operand) else CONST(value) for value in values]

    # Check that all inputs are boolean-compatible
    for field in converted_values:
        data_type = field.to_data_type()
        if data_type not in BOOLEANISH_AND_ARRAY_TYPES:
            raise ValueError(f"OR is not compatible with data type {data_type}")

    ret_data_type = (
        DataType.BOOLEAN
        if all(f.to_data_type() == DataType.BOOLEAN for f in converted_values)
        or (len(converted_values) == 1 and converted_values[0].to_data_type().is_array())
        else DataType.BOOLEAN_ARRAY
    )

    value_strings = [value.to_string() for value in converted_values]
    return _OR(ret_data_type, *value_strings)


def AND(*values: Operand | bool) -> Formula:
    """
    Returns False if any input evaluates to False.

    This function performs a logical disjunction (AND) over the provided inputs. If at least one
    value is False, the result is False; otherwise, the result is True. The inputs may be boolean
    literals, fields, formulas,  calculations, or parameters.

    Arguments:
        *values:
            An arbitrary number of boolean or boolean-compatible inputs. At least
            one input is required. If the input is non-boolean, it is treated as True if non-zero,
            else False.

            *Supported types*:

            .. container:: supported-types

                - BOOLEAN
                - BOOLEAN_ARRAY
                - INTEGER
                - INTEGER_ARRAY
                - DECIMAL
                - DECIMAL_ARRAY

    Returns:
        False if any input is False, True otherwise. Evaluates to an error value if any input is
        null or in an error state. If a single array input is provided, returns scalar value
        representing the AND across all elements in the array. If multiple arrays are provided,
        returns an array where each element is the AND of the corresponding elements across all
        input arrays.

        *Supported types*:

        .. container:: supported-types

            - BOOLEAN
            - BOOLEAN_ARRAY

    Raises:
        ValueError: If no inputs are provided.
        ValueError: If any input is not boolean-compatible.

    Examples:
        Basic usage with literals:

        .. code-block:: python

            AND(True, False, False)
            # Returns True

        Usage with table column:

        .. code-block:: python

            AND(order_table["is_urgent"])
            # Returns False if any row in the column 'is_urgent' is False, otherwise True
    """
    if not values:
        raise ValueError("At least one input is required")

    # Convert all inputs to `Operand` if necessary
    converted_values = [value if isinstance(value, Operand) else CONST(value) for value in values]

    # Check that all inputs are boolean-compatible
    for field in converted_values:
        data_type = field.to_data_type()
        if data_type not in BOOLEANISH_AND_ARRAY_TYPES:
            raise ValueError(f"AND is not compatible with data type {data_type}")

    ret_data_type = (
        DataType.BOOLEAN
        if all(f.to_data_type() == DataType.BOOLEAN for f in converted_values)
        or (len(converted_values) == 1 and converted_values[0].to_data_type().is_array())
        else DataType.BOOLEAN_ARRAY
    )

    value_strings = [value.to_string() for value in converted_values]
    return _AND(ret_data_type, *value_strings)


def NOT(value: Operand | bool) -> Formula:
    """
    Returns True if the input is False, and False if the input is True.

    This function performs a logical negation (NOT) on the provided input.
    If the value is True, the result is False; if the value is False, the result
    is True. The input may be a boolean literal, field, formula, calculation,
    or parameter. When the input is an array, the result is an array of boolean values computed
    element-wise.

    Arguments:
        value:
            A boolean or boolean-compatible input to negate.

            *Supported types*:

            .. container:: supported-types

                - BOOLEAN
                - BOOLEAN_ARRAY
                - INTEGER
                - INTEGER_ARRAY
                - DECIMAL
                - DECIMAL_ARRAY

    Returns:
        The logical negation of the input. Returns an array if the input is an array.

        *Supported types*:

        .. container:: supported-types

            - BOOLEAN
            - BOOLEAN_ARRAY

    Raises:
        ValueError: If the input is not boolean-compatible.

    Examples:
        Basic usage with literals:

        .. code-block:: python

            NOT(True)
            # Returns False

        Usage with a field:

        .. code-block:: python

            NOT(order["is_cancelled"])
            # Returns True if the order is not cancelled

        Element-wise operation with arrays:

        .. code-block:: python

            NOT([True, False])
            # Returns [False, True]
    """
    if isinstance(value, bool):
        return NOT(CONST(value))

    data_type = value.to_data_type()

    if data_type not in BOOLEANISH_AND_ARRAY_TYPES:
        raise ValueError(f"NOT is not compatible with data type {data_type}")

    ret_data_type = DataType.BOOLEAN_ARRAY if data_type.is_array() else DataType.BOOLEAN

    return _NOT(ret_data_type, value.to_string())


def BITMASK(value: Operand) -> Formula:
    """
    Converts an array of booleans into a single integer bitmask.

    A bitmask is an integer that compactly encodes an array of boolean values. Each element in the
    array is mapped to a bit (True as 1, False as 0) with the first element representing the least
    significant bit. For example, [True, False, True, True] becomes binary 1101, which equals the
    integer value 13. This representation is efficient for storage, comparison, and bitwise
    operations.

    Arguments:
        value:
            A model component representing a boolean array to convert into a bitmask.

            *Supported types*:

            .. container:: supported-types

                - BOOLEAN_ARRAY

    Returns:
        An integer whose binary representation encodes the boolean array.

        *Supported types*:

        .. container:: supported-types

            - INTEGER

    Raises:
        ValueError: If the input is not of type BOOLEAN_ARRAY.

    Examples:
        Basic usage:

        .. code-block:: python

            BITMASK([True, False, True, True])
            # Returns 13 (binary 1101)

        Using a field:

        .. code-block:: python

            BITMASK(order["flags"])
            # Converts the boolean flags array into an integer bitmask

    Note:
        The platform supports up to 32 bits in a bitmask. Therefore, if the input boolean array
        has a size greater than 32, information will be lost. For such cases, consider using
        `BITMASKSTRING` instead, which returns a hexadecimal string representation of the bitmask.
    """
    data_type = value.to_data_type()

    if data_type != DataType.BOOLEAN_ARRAY:
        raise ValueError(f"BITMASK is not compatible with data type {data_type}")

    return _BITMASK(value.to_string())


def VALUES(value: Operand) -> Formula:
    """
    Extracts the values from a map and returns them as an array.

    The VALUES function takes a model component with a map data type and converts its values into
    an array.

    Arguments:
        value:
            A model component of type `MapDataType` whose values will be extracted.

            *Supported types*:

            .. container:: supported-types

                - INTEGER_MAP
                - DECIMAL_MAP
                - STRING_MAP
                - BOOLEAN_MAP
                - DATE_MAP
                - DATETIME_MAP
                - TIME_MAP

    Returns:
        An array containing the values of the map.

        *Supported types*:

        .. container:: supported-types

            - INTEGER_ARRAY
            - DECIMAL_ARRAY
            - STRING_ARRAY
            - BOOLEAN_ARRAY
            - DATE_ARRAY
            - DATETIME_ARRAY
            - TIME_ARRAY

    Raises:
        ValueError: if the input is not of type `MapDataType`.

    Examples:
        Extracting values from a map:

        .. code-block:: python

            VALUES(my_map)
            # Returns ["a", "b", "c"] for a map {0: "a", 1: "b", 2: "c"}
    """
    data_type = value.to_data_type()

    if not isinstance(data_type, MapDataType):
        raise ValueError(f"VALUES is not compatible with data type {data_type}")

    ret_data_type = data_type._data_type.to_array()

    return _VALUES(ret_data_type, value.to_string())


def CONTAINS(search_array: Operand, search_value: Operand | bool | str | float | int) -> Formula:
    """
    Checks whether a specified value exists within an array.

    The CONTAINS function determines whether a given value or model component is present in
    the specified array. It returns a boolean result (`True` if the value is found, `False`
    otherwise). If either input is blank or in an error state, the formula evaluates to an error.

    Arguments:
        search_array:
            The array to search through. Must be an array type and compatible with the type of
            `search_value`.

            *Supported types*:

            .. container:: supported-types

                - BOOLEAN_ARRAY
                - INTEGER_ARRAY
                - DECIMAL_ARRAY
                - STRING_ARRAY
                - DATE_ARRAY
                - DATETIME_ARRAY
                - TIME_ARRAY
                - OBJECT_ARRAY

        search_value:
            The value to search for within the array. Must be the singular type corresponding to the
            `search_array` element type (for example, INTEGER for INTEGER_ARRAY).
            Cannot itself be an array type. A ValueError is raised if the type does not match.

            *Supported types*:

            .. container:: supported-types

                - BOOLEAN
                - INTEGER
                - DECIMAL
                - STRING
                - DATE
                - DATETIME
                - TIME
                - OBJECT

    Returns:
        A boolean value indicating whether the specified `search_value` is found in the
        `search_array`.

        *Supported types*:

        .. container:: supported-types

            - BOOLEAN

    Raises:
        ValueError: If `search_array` is not an array type.
        ValueError: If `search_value` is an array type.
        ValueError: If the singular type of `search_array` does not match the type of
            `search_value`.

    Examples:
        Basic usage:

        .. code-block:: python

            CONTAINS([1, 2, 3], 2)
            # Returns True

        Using a model component:

        .. code-block:: python

            CONTAINS(my_array_field, my_value_field)
            # Returns True if my_value_field exists in my_array_field
    """
    if isinstance(search_value, (bool, str, float, int)):
        return CONTAINS(search_array, CONST(search_value))

    search_array_data_type = search_array.to_data_type()
    search_value_data_type = search_value.to_data_type()

    exception = ValueError(
        f"CONTAINS not valid with data types {search_array_data_type} and "
        f"{search_value_data_type}."
    )

    if not search_array_data_type.is_array():
        raise exception

    if search_value_data_type.is_array():
        raise exception

    if isinstance(search_array_data_type, DataType) and isinstance(
        search_value_data_type, DataType
    ):
        if search_array_data_type.from_array() != search_value_data_type:
            raise exception
    elif isinstance(search_array_data_type, ObjectDataType) and isinstance(
        search_value_data_type, ObjectDataType
    ):
        if search_array_data_type._source_table != search_value_data_type._source_table:
            raise exception
    else:
        raise exception

    return _CONTAINS(search_array.to_string(), search_value.to_string())


def INDEX(array: Table | Operand, index: Operand | int) -> Formula:
    """
    Retrieves the element or row at a specified index from an array or table.

    The INDEX function returns the item at the given 1-based index within an array or table. If the
    input is a Table or OBJECT_ARRAY, it returns the row corresponding to the index. If the input is
    a primitive ARRAY type (e.g. INTEGER_ARRAY, BOOLEAN_ARRAY), it returns the array element at that
    position. If the index argument is an array type, an array of indices is returned. A ValueError
    is raised if `index` is not an INTEGER or INTEGER_ARRAY type or if `array` is not a valid array
    type.

    Arguments:
        array:
            The array or table from which to retrieve an element. Must be an array type or a Table.
            If the type is invalid, a ValueError is raised.

            *Supported types*:

            .. container:: supported-types

                - BOOLEAN_ARRAY
                - INTEGER_ARRAY
                - DECIMAL_ARRAY
                - STRING_ARRAY
                - DATE_ARRAY
                - DATETIME_ARRAY
                - TIME_ARRAY
                - OBJECT_ARRAY

        index:
            The 1-based index of the element or row to retrieve. Must be an INTEGER or INTEGER_ARRAY
            value. If the index is not INTEGER or INTEGER_ARRAY, a ValueError is raised. If the
            index is less than 1 or greater than the size of the array, the formula evaluates to an
            error.

            *Supported types*:

            .. container:: supported-types

                - INTEGER
                - INTEGER_ARRAY

    Returns:
        The element or row at the specified index. If the array is OBJECT_ARRAY or Table, the result
        is an object type. If the array is a primitive ARRAY, the result is the corresponding
        singular type.

        *Supported types*:

        .. container:: supported-types

            - BOOLEAN
            - INTEGER
            - DECIMAL
            - STRING
            - DATE
            - DATETIME
            - TIME
            - OBJECT
            - BOOLEAN_ARRAY
            - INTEGER_ARRAY
            - DECIMAL_ARRAY
            - STRING_ARRAY
            - DATE_ARRAY
            - DATETIME_ARRAY
            - TIME_ARRAY
            - OBJECT_ARRAY

    Raises:
        ValueError: If `index` is not of type INTEGER or INTEGER_ARRAY.
        ValueError: If `array` is not a valid array or Table type.

    Examples:
        Retrieving an element from an array:

        .. code-block:: python

            INDEX([10, 20, 30], 2)
            # Returns 20

        Retrieving multiple elements from an array:

        .. code-block:: python

            INDEX([10, 20, 30], [1, 2])
            # Returns [10, 20]

        Retrieving a row from a table:

        .. code-block:: python

            INDEX(my_table, 1)
            # Returns the first row of the table
    """
    if isinstance(index, int):
        return INDEX(array, CONST(index))

    index_data_type = index.to_data_type()
    if index_data_type not in [DataType.INTEGER, DataType.INTEGER_ARRAY]:
        raise ValueError(f"INDEX not valid with index data type {index_data_type}")

    is_array = index_data_type.is_array()

    if isinstance(array, Table):
        return _INDEX(ObjectDataType(array, is_array), array.id, index.to_string())

    array_data_type = array.to_data_type()
    data_type_exception = ValueError(
        f"INDEX invalid with data types {array_data_type} and {index_data_type}"
    )
    if isinstance(array_data_type, MapDataType):
        raise data_type_exception
    if isinstance(array_data_type, ObjectDataType):
        if not array_data_type.is_array():
            raise data_type_exception
        return _INDEX(
            ObjectDataType(array_data_type._source_table, False),
            array.to_string(),
            index.to_string(),
        )

    if not array_data_type.is_array():
        raise data_type_exception

    ret_data_type = array_data_type if is_array else array_data_type.from_array()
    return _INDEX(ret_data_type, array.to_string(), index.to_string())


def SIZE(array: Operand) -> Formula:
    """
    Returns the number of elements in an array or table.

    The SIZE function calculates the size of an array-like model component and returns it as a
    Formula object of type INTEGER. It is useful for determining the number of elements in an array
    or the size of a table. If the input is a primitive array (e.g. BOOLEAN_ARRAY, INTEGER_ARRAY),
    this formula has the same behaviour as the formula `ROWS`. However, if the input is a table or
    OBJECT_ARRAY, then the formula will evaluate to the number of rows multiplied by the number of
    columns. A ValueError is raised if the input is not an array type.

    Arguments:
        array:
            The arra or table whose size will be evaluated. Must be a valid array type.
            If the input is not an array, a ValueError is raised.

            *Supported types*:

            .. container:: supported-types

                - BOOLEAN_ARRAY
                - INTEGER_ARRAY
                - DECIMAL_ARRAY
                - STRING_ARRAY
                - DATE_ARRAY
                - DATETIME_ARRAY
                - TIME_ARRAY
                - OBJECT_ARRAY

    Returns:
        The total number of elements in the input array, returned as an INTEGER Formula.

        *Supported types*:

        .. container:: supported-types

            - INTEGER

    Raises:
        ValueError: If `array` is not a valid array type.

    Examples:
        Getting the size of a primitive array:

        .. code-block:: python

            SIZE([10, 20, 30])
            # Returns 3

        Getting the size of a table:

        .. code-block:: python

            SIZE(my_table)
            # Returns the size (rows * columns) of the table
    """
    array_data_type = array.to_data_type()
    data_type_exception = ValueError(f"SIZE invalid with data type {array_data_type}")

    if not array_data_type.is_array():
        raise data_type_exception

    return _SIZE(array.to_string())


def PLUSDAYS(date: Operand, days: Operand | int) -> Formula:
    """
    Returns a new date by adding a specified number of days to a given date.

    The PLUSDAYS function calculates a new date by adding `days` to the input `date`.
    Both single dates and arrays of dates are supported, and the number of days can
    be a single integer or an array of integers. If any input is blank or in an error
    state, the formula evaluates to an error.

    Arguments:
        date:
            The starting date to which days will be added.

            *Supported types*:

            .. container:: supported-types

                - DATE
                - DATETIME
                - DATE_ARRAY
                - DATETIME_ARRAY

        days:
            The number of days to add to `date`. Can be a single integer or an array of integers.

            *Supported types*:

            .. container:: supported-types

                - INTEGER
                - INTEGER_ARRAY

    Returns:
        The resulting date after adding the specified number of days. The type of the result
        matches the input `date`, unless `days` is an array, in which case the result will be the
        array version of the `date` type.

        *Supported types*:

        .. container:: supported-types

            - DATE
            - DATETIME
            - DATE_ARRAY
            - DATETIME_ARRAY

    Raises:
        ValueError: If `date` is not of type DATE, DATETIME, DATE_ARRAY, or DATETIME_ARRAY.
        ValueError: If `days` is not of type INTEGER or INTEGER_ARRAY.

    Examples:
        Adding days to a single date:

        .. code-block:: python

            PLUSDAYS(DATE(2025, 9, 3), 5)
            # Returns DATE(2025, 9, 8)

        Adding an array of days to a single date:

        .. code-block:: python

            PLUSDAYS(DATE(2025, 9, 3), [1, 2, 3])
            # Returns [DATE(2025, 9, 4), DATE(2025, 9, 5), DATE(2025, 9, 6)]
    """
    if isinstance(days, int):
        return PLUSDAYS(date, CONST(days))
    date_data_type = date.to_data_type()
    days_data_type = days.to_data_type()
    data_type_exception = ValueError(
        f"PLUSDAYS invalid with data types {date_data_type} and {days_data_type}"
    )
    if not isinstance(date_data_type, DataType) or not isinstance(days_data_type, DataType):
        raise data_type_exception
    if date_data_type not in DATE_AND_ARRAY_TYPES:
        raise data_type_exception
    if days_data_type not in {DataType.INTEGER, DataType.INTEGER_ARRAY}:
        raise data_type_exception

    ret_data_type = (
        date_data_type if days_data_type == DataType.INTEGER else date_data_type.to_array()
    )
    return _PLUSDAYS(ret_data_type, date.to_string(), days.to_string())


def ROUND(value: Operand | float) -> Formula:
    """
    Rounds a number or array of numbers to the nearest integer.

    The ROUND function evaluates the input `value` and returns the closest integer.
    If an array of numbers is provided, each element is rounded individually.
    If the input is blank or in an error state, the formula evaluates to an error.

    Arguments:
        value:
            The number or array of numbers to round. If blank or in an error state, the formula
            will evaluate to an error.

            *Supported types*:

            .. container:: supported-types

                - DECIMAL
                - DECIMAL_ARRAY

    Returns:
        The rounded integer value(s). The result matches the input type: scalar input
        returns a single integer, array input returns an integer array.

        *Supported types*:

        .. container:: supported-types

            - INTEGER
            - INTEGER_ARRAY

    Raises:
        ValueError: If `value` is not of type DECIMAL or DECIMAL_ARRAY.

    Examples:
        Rounding a single value:

        .. code-block:: python

            ROUND(3.6)
            # Returns 4

        Rounding an array of values:

        .. code-block:: python

            ROUND([1.2, 3.7, 4.5])
            # Returns [1, 4, 5]
    """
    if isinstance(value, float):
        return ROUND(CONST(value))

    data_type = value.to_data_type()
    data_type_exception = ValueError(f"ROUND invalid with data type {data_type}")
    if not isinstance(data_type, DataType):
        raise data_type_exception
    if data_type not in {DataType.DECIMAL, DataType.DECIMAL_ARRAY}:
        raise data_type_exception

    ret_data_type = DataType.INTEGER_ARRAY if data_type.is_array() else DataType.INTEGER
    return _ROUND(ret_data_type, value.to_string())


def FLOOR(value: Operand | float) -> Formula:
    """
    Rounds a number or array of numbers down to the nearest integer.

    The FLOOR function evaluates the input `value` and returns the largest integer less than or
    equal to it. If an array of numbers is provided, each element is rounded down individually.
    If the input is blank or in an error state, the formula evaluates to an error.

    Arguments:
        value:
            The number or array of numbers to compute the floor of. If blank or in an error state,
            the formula will evaluate to an error.

            *Supported types*:

            .. container:: supported-types

                - DECIMAL
                - DECIMAL_ARRAY

    Returns:
        The integer value(s) representing the floor of the input. The result matches the input
        type: scalar input returns a single integer, array input returns an integer array.

        *Supported types*:

        .. container:: supported-types

            - INTEGER
            - INTEGER_ARRAY

    Raises:
        ValueError: If `value` is not of type DECIMAL or DECIMAL_ARRAY.

    Examples:
        Rounding a single value:

        .. code-block:: python

            ROUND(3.6)
            # Returns 3

        Rounding an array of values:

        .. code-block:: python

            ROUND([1.2, 3.0, 4.5])
            # Returns [1, 3, 4]
    """
    if isinstance(value, float):
        return FLOOR(CONST(value))

    data_type = value.to_data_type()
    data_type_exception = ValueError(f"FLOOR invalid with data type {data_type}")
    if not isinstance(data_type, DataType):
        raise data_type_exception
    if data_type not in {DataType.DECIMAL, DataType.DECIMAL_ARRAY}:
        raise data_type_exception

    ret_data_type = DataType.INTEGER_ARRAY if data_type.is_array() else DataType.INTEGER
    return _FLOOR(ret_data_type, value.to_string())


def CEILING(value: Operand | float) -> Formula:
    """
    Rounds a number or array of numbers up to the nearest integer.

    The CEILING function evaluates the input `value` and returns the smallest integer greater than
    or equal to it. If an array of numbers is provided, each element is rounded up individually.
    If the input is blank or in an error state, the formula evaluates to an error.

    Arguments:
        value:
            The number or array of numbers to compute the ceiling of. If blank or in an error state,
            the formula will evaluate to an error.

            *Supported types*:

            .. container:: supported-types

                - DECIMAL
                - DECIMAL_ARRAY

    Returns:
        The integer value(s) representing the ceiling of the input. The result matches the input
        type: scalar input returns a single integer, array input returns an integer array.

        *Supported types*:

        .. container:: supported-types

            - INTEGER
            - INTEGER_ARRAY

    Raises:
        ValueError: If `value` is not of type DECIMAL or DECIMAL_ARRAY.

    Examples:
        Rounding a single value:

        .. code-block:: python

            ROUND(3.6)
            # Returns 4

        Rounding an array of values:

        .. code-block:: python

            ROUND([1.2, 3.0, 4.5])
            # Returns [2, 3, 5]
    """
    if isinstance(value, float):
        return FLOOR(CONST(value))

    data_type = value.to_data_type()
    data_type_exception = ValueError(f"CEILING invalid with data type {data_type}")
    if not isinstance(data_type, DataType):
        raise data_type_exception
    if data_type not in {DataType.DECIMAL, DataType.DECIMAL_ARRAY}:
        raise data_type_exception

    ret_data_type = DataType.INTEGER_ARRAY if data_type.is_array() else DataType.INTEGER
    return _CEILING(ret_data_type, value.to_string())


def MOD(
    number: Operand | int | float,
    divisor: Operand | int | float,
) -> Formula:
    """
    Returns the remainder after dividing `number` by `divisor`.

    The MOD function calculates the modulus of a number with respect to a divisor,
    returning the remainder of the division. For example, if 5 is divided by 3, the remainder is 2.
    Therefore, MOD(5, 3) = 2. If any input is blank or in an error state, the formula evaluates to
    an error. If either input is an array, the operation is performed element-wise and an array type
    is returned.

    Arguments:
        number:
            The value to divide.

            *Supported types*:

            .. container:: supported-types

                - INTEGER
                - DECIMAL
                - INTEGER_ARRAY
                - DECIMAL_ARRAY

        divisor:
            The value to divide by.

            *Supported types*:

            .. container:: supported-types

                - INTEGER
                - DECIMAL
                - INTEGER_ARRAY
                - DECIMAL_ARRAY

    Returns:
        The remainder of the division `number % divisor`.

        *Supported types*:

        .. container:: supported-types

            - INTEGER
            - DECIMAL
            - INTEGER_ARRAY
            - DECIMAL_ARRAY

    Raises:
        ValueError: If either `number` or `divisor` is not numeric.

    Examples:
        Basic usage:

        .. code-block:: python

            MOD(10, 3)
            # Returns 1

        With arrays:

        .. code-block:: python

            MOD([10, 20, 30], 7)
            # Returns [3, 6, 2]
    """
    if isinstance(number, (int, float)):
        return MOD(CONST(number), divisor)
    if isinstance(divisor, (int, float)):
        return MOD(number, CONST(divisor))

    number_data_type = number.to_data_type()
    divisor_data_type = divisor.to_data_type()

    if number_data_type not in {
        DataType.INTEGER,
        DataType.DECIMAL,
    } or divisor_data_type not in {DataType.INTEGER, DataType.DECIMAL}:
        raise ValueError("MOD can only be called with numerical inputs")

    ret_data_type = (
        DataType.INTEGER
        if number_data_type == DataType.INTEGER and divisor_data_type == DataType.INTEGER
        else DataType.DECIMAL
    )

    return _MOD(ret_data_type, number.to_string(), divisor.to_string())


def IFERROR(
    formula: Operand,
    error_branch: Operand | int | float | str | bool,
) -> Formula:
    """
    Returns the result of a formula, or a specified alternative value if an error occurs.

    The IFERROR function evaluates the given `formula`. If the formula executes successfully,
    its result is returned. If an error occurs during evaluation, the value provided in
    `error_branch` is returned instead. This allows graceful handling of errors in model
    calculations without breaking the workflow.

    Arguments:
        formula:
            The formula or model component to evaluate, which may produce an error.

            *Supported types*:

            .. container:: supported-types

                - ANY

        error_branch:
            The value to return if the formula evaluates to an error. If not of the same data type
            as `formula`, or `NULL`, a ValueError is raised.

            *Supported types*:

            .. container:: supported-types

                - ANY

    Returns:
        The result of the formula if no error occurs, otherwise the `error_branch` value.

        *Supported types*:

        .. container:: supported-types

            - ANY

    Raises:
        ValueError: If `formula` and `error_branch` have incompatible data types (unless one
            is NULL).
        ValueError: If both `formula` and `error_branch` are NULL.

    Examples:
        Basic usage with literals:

        .. code-block:: python

            IFERROR(1 / 0, 0)
            # Returns 0

        Using formulas:

        .. code-block:: python

            IFERROR(LOOKUP(my_table, "customer", "bob"), BLANK())
            # Returns the customer record for "bob", or blank if not found
    """

    if isinstance(error_branch, int | float | str | bool):
        return IFERROR(formula, CONST(error_branch))

    formula_data_type = formula.to_data_type()
    error_branch_data_type = error_branch.to_data_type()

    array_types_match = False
    if isinstance(formula_data_type, DataType):
        array_types_match = (
            formula_data_type.is_array()
            and formula_data_type.from_array() == error_branch_data_type
        )
    elif isinstance(formula_data_type, ObjectDataType) and isinstance(
        error_branch_data_type, ObjectDataType
    ):
        array_types_match = (
            formula_data_type.is_array()
            and formula_data_type._source_table == error_branch_data_type._source_table
        )

    if (
        formula_data_type != error_branch_data_type
        and DataType.NULL not in (formula_data_type, error_branch_data_type)
        and not array_types_match
    ):
        raise ValueError(
            f"IFERROR incompatible with data types {formula_data_type} "
            f"and {error_branch_data_type}"
        )

    if formula_data_type == DataType.NULL and error_branch_data_type == DataType.NULL:
        raise ValueError("Both branches of IFERROR cannot be blank")

    return _IFERROR(
        (formula_data_type if formula_data_type != DataType.NULL else error_branch_data_type),
        formula.to_string(),
        error_branch.to_string(),
    )


def DAYSBETWEEN(
    first_date: Operand,
    second_date: Operand,
) -> Formula:
    """
    Returns the number of days between two dates.

    The DAYSBETWEEN function calculates the difference in days between `first_date` and
    `second_date`. The result is positive if `second_date` occurs after `first_date` and
    negative if it occurs before. This function supports both single dates and arrays of dates.

    Arguments:
        first_date:
            The starting date or array of dates.

            *Supported types*:

            .. container:: supported-types

                - DATE
                - DATETIME
                - DATE_ARRAY
                - DATETIME_ARRAY

        second_date:
            The ending date or array of dates.

            *Supported types*:

            .. container:: supported-types

                - DATE
                - DATETIME
                - DATE_ARRAY
                - DATETIME_ARRAY

    Returns:
        The number of days between the two dates. If input arrays have unequal lengths the returned
        formula will evaluate to an error.

        *Supported types*:

        .. container:: supported-types

            - INTEGER
            - INTEGER_ARRAY

    Raises:
        ValueError: If either input is not a date or datetime type.

    Examples:
        .. code-block:: python

            DAYSBETWEEN(DATE(2025, 1, 1), DATE(2025, 1, 10))
            # Returns 9
    """

    first_date_data_type = first_date.to_data_type()
    second_date_data_type = second_date.to_data_type()

    if (
        first_date_data_type not in DATE_AND_ARRAY_TYPES
        or second_date_data_type not in DATE_AND_ARRAY_TYPES
    ):
        raise ValueError(
            f"DAYSBETWEEN invalid with arguments {first_date_data_type} and {second_date_data_type}"
        )
    ret_data_type = DataType.INTEGER
    if first_date_data_type.is_array() or second_date_data_type.is_array():
        ret_data_type = DataType.INTEGER_ARRAY

    return _DAYSBETWEEN(ret_data_type, first_date.to_string(), second_date.to_string())


def YEAR(
    date: Operand,
) -> Formula:
    """
    Extracts the year component from a date or array of dates.

    The YEAR function returns the year (e.g., 2024) from the provided `date`. It supports both
    single dates and arrays of dates, returning an integer or an integer array accordingly.

    Arguments:
        date:
            The date or array of dates from which to extract the year.

            *Supported types*:

            .. container:: supported-types

                - DATE
                - DATETIME
                - DATE_ARRAY
                - DATETIME_ARRAY

    Returns:
        The year as an integer or array of integers.

        *Supported types*:

        .. container:: supported-types

            - INTEGER
            - INTEGER_ARRAY

    Raises:
        ValueError: If the input is not a date or datetime type.

    Examples:
        .. code-block:: python

            YEAR(DATE(2025, 9, 3))
            # Returns 2025
    """
    date_data_type = date.to_data_type()
    if date_data_type not in DATE_AND_ARRAY_TYPES:
        raise ValueError(f"YEAR invalid with the argument {date.to_data_type()}")

    ret_data_type = DataType.INTEGER
    if date_data_type.is_array():
        ret_data_type = DataType.INTEGER_ARRAY

    return _YEAR(ret_data_type, date.to_string())


def MONTH(
    date: Operand,
) -> Formula:
    """
    Extracts the month component from a date or array of dates.

    The MONTH function returns the month from the provided `date`. It supports both
    single dates and arrays of dates, returning an integer or an integer array accordingly.

    Arguments:
        date:
            The date or array of dates from which to extract the month.

            *Supported types*:

            .. container:: supported-types

                - DATE
                - DATETIME
                - DATE_ARRAY
                - DATETIME_ARRAY

    Returns:
        The month as an integer or array of integers.

        *Supported types*:

        .. container:: supported-types

            - INTEGER
            - INTEGER_ARRAY

    Raises:
        ValueError: If the input is not a date or datetime type.

    Examples:
        .. code-block:: python

            MONTH(DATE(2025, 9, 3))
            # Returns 9
    """
    date_data_type = date.to_data_type()
    if date_data_type not in DATE_AND_ARRAY_TYPES:
        raise ValueError(f"MONTH invalid with the argument {date.to_data_type()}")

    ret_data_type = DataType.INTEGER
    if date_data_type.is_array():
        ret_data_type = DataType.INTEGER_ARRAY

    return _MONTH(ret_data_type, date.to_string())


def DAY(
    date: Operand,
) -> Formula:
    """
    Extracts the day component from a date or array of dates.

    The DAY function returns the day from the provided `date`. It supports both
    single dates and arrays of dates, returning an integer or an integer array accordingly.

    Arguments:
        date:
            The date or array of dates from which to extract the day.

            *Supported types*:

            .. container:: supported-types

                - DATE
                - DATETIME
                - DATE_ARRAY
                - DATETIME_ARRAY

    Returns:
        The day as an integer or array of integers.

        *Supported types*:

        .. container:: supported-types

            - INTEGER
            - INTEGER_ARRAY

    Raises:
        ValueError: If the input is not a date or datetime type.

    Examples:
        .. code-block:: python

            DAY(DATE(2025, 9, 3))
            # Returns 3
    """
    date_data_type = date.to_data_type()
    if date_data_type not in DATE_AND_ARRAY_TYPES:
        raise ValueError(f"DAY invalid with the argument {date.to_data_type()}")

    ret_data_type = DataType.INTEGER
    if date_data_type.is_array():
        ret_data_type = DataType.INTEGER_ARRAY

    return _DAY(ret_data_type, date.to_string())


def DATE(
    year: Operand | int,
    month: Operand | int,
    day: Operand | int,
) -> Formula:
    """
    Constructs a date from the given year, month, and day components.

    The DATE function returns a valid date using the specified `year`, `month`, and `day`.
    It supports both single values and arrays; if arrays are provided, they must all have
    the same length, otherwise the formula will evaluate to an error.

    Arguments:
        year:
            The year component of the date.

            *Supported types*:

            .. container:: supported-types

                - INTEGER
                - INTEGER_ARRAY
        month:
            The month component of the date (1–12).

            *Supported types*:

            .. container:: supported-types

                - INTEGER
                - INTEGER_ARRAY
        day:
            The day component of the date.

            *Supported types*:

            .. container:: supported-types

                - INTEGER
                - INTEGER_ARRAY

    Returns:
        A `Formula` object representing the constructed date. If the inputs do not form a valid
        date, the formula will evaluate to an error.

        *Supported types*:

        .. container:: supported-types

            - DATE
            - DATE_ARRAY

    Raises:
        ValueError: If any input is not numeric or an array of numeric values.
    """
    if isinstance(year, int):
        return DATE(CONST(year), month, day)
    if isinstance(month, int):
        return DATE(year, CONST(month), day)
    if isinstance(day, int):
        return DATE(year, month, CONST(day))

    year_date_type = year.to_data_type()
    month_date_type = month.to_data_type()
    day_date_type = day.to_data_type()

    if (
        year_date_type not in NUMERIC_AND_ARRAY_TYPES
        or month_date_type not in NUMERIC_AND_ARRAY_TYPES
        or day_date_type not in NUMERIC_AND_ARRAY_TYPES
    ):
        raise ValueError(
            f"DATE invalid with data types {year_date_type}, {month_date_type}, {day_date_type}"
        )

    ret_data_type = DataType.DATE
    if year_date_type.is_array() or month_date_type.is_array() or day_date_type.is_array():
        ret_data_type = DataType.DATE_ARRAY

    return _DATE(ret_data_type, year.to_string(), month.to_string(), day.to_string())


def DATETIME(  # noqa: PLR0913
    year: Operand | int,
    month: Operand | int,
    day: Operand | int,
    hours: Operand | int,
    minutes: Operand | int,
    seconds: Operand | int,
) -> Formula:
    """
    Constructs a datetime from the given year, month, day, hour, minute, and second components.

    The DATETIME function returns a valid datetime using the specified components. It supports
    both single values and arrays; if arrays are provided, they must all have the same length,
    otherwise the returned formula will evaluate to an error.

    Arguments:
        year:
            The year component.

            *Supported types*:

            .. container:: supported-types

                - INTEGER
                - INTEGER_ARRAY
        month:
            The month component (1–12).

            *Supported types*:

            .. container:: supported-types

                - INTEGER
                - INTEGER_ARRAY
        day:
            The day component.

            *Supported types*:

            .. container:: supported-types

                - INTEGER
                - INTEGER_ARRAY
        hours:
            The hour component (0–23).

            *Supported types*:

            .. container:: supported-types

                - INTEGER
                - INTEGER_ARRAY
        minutes:
            The minute component (0–59).

            *Supported types*:

            .. container:: supported-types

                - INTEGER
                - INTEGER_ARRAY
        seconds:
            The second component (0–59).

            *Supported types*:

            .. container:: supported-types

                - INTEGER
                - INTEGER_ARRAY

    Returns:
        A `Formula` object representing the constructed datetime. If the inputs do not form a valid
        date/time, the formula will evaluate to an error.

        *Supported types*:

        .. container:: supported-types

            - DATETIME
            - DATETIME_ARRAY

    Raises:
        ValueError: If any input is not numeric or an array of numeric values.
    """
    components = {
        "year": year,
        "month": month,
        "day": day,
        "hours": hours,
        "minutes": minutes,
        "seconds": seconds,
    }

    converted_components = {
        key: CONST(value) if isinstance(value, int) else value for key, value in components.items()
    }

    data_types = [value.to_data_type() for _, value in converted_components.items()]

    for dt in data_types:
        if dt not in NUMERIC_AND_ARRAY_TYPES:
            raise ValueError(f"DATETIME invalid with the argument {dt}")

    ret_data_type = (
        DataType.DATETIME_ARRAY if any(dt.is_array() for dt in data_types) else DataType.DATETIME
    )

    return _DATETIME(
        ret_data_type,
        (
            converted_components["year"].to_string(),
            converted_components["month"].to_string(),
            converted_components["day"].to_string(),
        ),
        (
            converted_components["hours"].to_string(),
            converted_components["minutes"].to_string(),
            converted_components["seconds"].to_string(),
        ),
    )


def EOMONTH(
    date: Operand,
    months: Operand | int = 0,
) -> Formula:
    """
    Returns the last day of the month for a given date, optionally offset by a number of months.

    The EOMONTH function calculates the end-of-month date based on the input `date`. You can
    shift the resulting date forward or backward using the `months` parameter. If `months` is
    positive, the end-of-month moves forward; if negative, it moves backward. If either input
    is an array, the function operates element-wise.

    Arguments:
        date:
            The starting date from which the end-of-month is calculated.

            *Supported types*:

            .. container:: supported-types

                - DATE
                - DATETIME
                - DATE_ARRAY
                - DATETIME_ARRAY
        months:
            Optional. The number of months to offset from the month of `date`. Can be a scalar or
            array. Defaults to 0.

            *Supported types*:

            .. container:: supported-types

                - INTEGER
                - DECIMAL
                - INTEGER_ARRAY
                - DECIMAL_ARRAY

    Returns:
        The end-of-month date after applying the month offset. The result has the same shape
        (scalar or array) as the inputs.

        *Supported types*:

        .. container:: supported-types

            - DATE
            - DATE_ARRAY

    Raises:
        ValueError: If `date` is not a date/datetime type, or if `months` is not numeric.

    Examples:
        Basic usage:

        .. code-block:: python

            EOMONTH(DATE(2024, 1, 15))
            # Returns DATE(2024, 1, 31)

        Offset by 2 months:

        .. code-block:: python

            EOMONTH(DATE(2024, 1, 15), 2)
            # Returns DATE(2024, 3, 31)

        Negative offset:

        .. code-block:: python

            EOMONTH(DATE(2024, 1, 15), -1)
            # Returns DATE(2023, 12, 31)
    """
    if isinstance(months, int):
        return EOMONTH(date, CONST(months))

    date_data_type = date.to_data_type()
    months_data_type = months.to_data_type()

    if (
        date_data_type not in DATE_AND_ARRAY_TYPES
        or months_data_type not in NUMERIC_AND_ARRAY_TYPES
    ):
        raise ValueError(
            f"EOMONTH called with invalid data types: {date_data_type}, " f"{months_data_type}"
        )

    ret_data_type = DataType.DATE
    if date_data_type.is_array() or months_data_type.is_array():
        ret_data_type = DataType.DATE_ARRAY

    return _EOMONTH(ret_data_type, date.to_string(), months.to_string())


def BITAND(field_1: Operand | int | str, field_2: Operand | int | str) -> Formula:
    """
    Performs a bitwise AND operation between two numeric or hexadecimal inputs.

    The bitwise AND operation compares each bit of the inputs and returns 1 if both bits at a given
    position are 1; otherwise, it returns 0. This function supports both integers and hexadecimal
    strings (interpreted as binary values) and will return a corresponding result in the same
    format.

    If a string is provided as an input, it is interpreted as a hexadecimal number. This allows
    support for values larger than 32 bits, which are not representable using standard integers. Any
    non-hexadecimal character in a string is treated as '0'.

    If both inputs are strings, the result is returned as a hexadecimal string; otherwise, the
    result is an integer. Array inputs are supported, but if both inputs are arrays, they must have
    the same length, else the formula will evaluate to an error.

    Arguments:
        field_1:
            The first value in the BITAND operation. Interpreted as a string of bits (either the
            binary representation of the integer value or hexadecimal string). If an array type, the
            operation is performed element-wise and the return will also be an array type.

            *Supported types*:

            .. container:: supported-types

                - INTEGER
                - STRING
                - INTEGER_ARRAY
                - STRING_ARRAY
        field_2:
            The second value in the BITAND operation. Interpreted as a string of bits (either the
            binary representation of the integer value or hexadecimal string). If an array type, the
            operation is performed element-wise and the return will also be an array type.

            *Supported types*:

            .. container:: supported-types

                - INTEGER
                - STRING
                - INTEGER_ARRAY
                - STRING_ARRAY

    Returns:
        A `Formula` object representing the bitwise AND result of the two inputs. If either input
        is an array type, the return will also be an array type. If both inputs are strings, the
        return type will also be a string; otherwise, it will be an integer. If either input is
        blank or in an error state, the formula evaluates to an error.

        *Supported types*:

        .. container:: supported-types

            - INTEGER
            - STRING
            - INTEGER_ARRAY
            - STRING_ARRAY

    Raises:
        ValueError: If the input data types are incompatible, unsupported, or if array lengths
                    mismatch when both inputs are arrays.

    Examples:
        With integer inputs:

        .. code-block:: python

            BITAND(7, 3)
            # Returns 3. (Binary: 0111 & 0011 = 0011)

        With hexadecimal inputs:

        .. code-block:: python

            BITAND("9", "A")
            # Returns "08". (Binary: 1001 & 1010 = 1000)
    """
    if isinstance(field_1, int | str):
        return BITAND(CONST(field_1), field_2)

    if isinstance(field_2, int | str):
        return BITAND(field_1, CONST(field_2))

    field_1_data_type = field_1.to_data_type()
    field_2_data_type = field_2.to_data_type()

    incompatible_data_types_message = (
        f"BITAND incompatible with data types " f"{field_1_data_type} and {field_2_data_type}"
    )

    if not (isinstance(field_1_data_type, DataType) and isinstance(field_2_data_type, DataType)):
        raise ValueError(incompatible_data_types_message)

    field_1_base_data_type = (
        field_1_data_type.from_array() if field_1_data_type.is_array() else field_1_data_type
    )
    field_2_base_data_type = (
        field_2_data_type.from_array() if field_2_data_type.is_array() else field_2_data_type
    )

    if field_1_base_data_type not in {
        DataType.INTEGER,
        DataType.STRING,
    } or field_2_base_data_type not in {DataType.INTEGER, DataType.STRING}:
        raise ValueError(incompatible_data_types_message)

    if field_1_base_data_type != field_2_base_data_type:
        raise ValueError(incompatible_data_types_message)

    ret_data_type = field_1_data_type if field_1_data_type.is_array() else field_2_data_type

    return _BITAND(ret_data_type, field_1.to_string(), field_2.to_string())


def BITOR(field_1: Operand | int | str, field_2: Operand | int | str) -> Formula:
    """
    Performs a bitwise OR operation between two numeric or hexadecimal inputs.

    The bitwise OR operation compares each bit of the inputs and returns 1 if either bit at a given
    position are 1; otherwise, it returns 0. This function supports both integers and hexadecimal
    strings (interpreted as binary values) and will return a corresponding result in the same
    format.

    If a string is provided as an input, it is interpreted as a hexadecimal number. This allows
    support for values larger than 32 bits, which are not representable using standard integers. Any
    non-hexadecimal character in a string is treated as '0'.

    If both inputs are strings, the result is returned as a hexadecimal string; otherwise, the
    result is an integer. Array inputs are supported, but if both inputs are arrays, they must have
    the same length, else the formula will evaluate to an error.

    Arguments:
        field_1:
            The first value in the BITOR operation. Interpreted as a string of bits (either the
            binary representation of the integer value or hexadecimal string). If an array type, the
            operation is performed element-wise and the return will also be an array type.

            *Supported types*:

            .. container:: supported-types

                - INTEGER
                - STRING
                - INTEGER_ARRAY
                - STRING_ARRAY
        field_2:
            The second value in the BITOR operation. Interpreted as a string of bits (either the
            binary representation of the integer value or hexadecimal string). If an array type, the
            operation is performed element-wise and the return will also be an array type.

            *Supported types*:

            .. container:: supported-types

                - INTEGER
                - STRING
                - INTEGER_ARRAY
                - STRING_ARRAY

    Returns:
        A `Formula` object representing the bitwise OR result of the two inputs. If either input
        is an array type, the return will also be an array type. If both inputs are strings, the
        return type will also be a string; otherwise, it will be an integer. If either input is
        blank or in an error state, the formula evaluates to an error.

        *Supported types*:

        .. container:: supported-types

            - INTEGER
            - STRING
            - INTEGER_ARRAY
            - STRING_ARRAY

    Raises:
        ValueError: If the input data types are incompatible, unsupported, or if array lengths
                    mismatch when both inputs are arrays.

    Examples:
        With integer inputs:

        .. code-block:: python

            BITOR(7, 3)
            # Returns 7. (Binary: 0111 | 0011 = 0111)

        With hexadecimal inputs:

        .. code-block:: python

            BITOR("9", "A")
            # Returns "0B". (Binary: 1001 | 1010 = 1011)
    """

    if isinstance(field_1, int | str):
        return BITOR(CONST(field_1), field_2)

    if isinstance(field_2, int | str):
        return BITOR(field_1, CONST(field_2))

    field_1_data_type = field_1.to_data_type()
    field_2_data_type = field_2.to_data_type()

    incompatible_data_types_message = (
        f"BITOR incompatible with data types " f"{field_1_data_type} and {field_2_data_type}"
    )

    if not (isinstance(field_1_data_type, DataType) and isinstance(field_2_data_type, DataType)):
        raise ValueError(incompatible_data_types_message)

    field_1_base_data_type = (
        field_1_data_type.from_array() if field_1_data_type.is_array() else field_1_data_type
    )
    field_2_base_data_type = (
        field_2_data_type.from_array() if field_2_data_type.is_array() else field_2_data_type
    )

    if field_1_base_data_type not in {
        DataType.INTEGER,
        DataType.STRING,
    } or field_2_base_data_type not in {DataType.INTEGER, DataType.STRING}:
        raise ValueError(incompatible_data_types_message)

    if field_1_base_data_type != field_2_base_data_type:
        raise ValueError(incompatible_data_types_message)

    ret_data_type = field_1_data_type if field_1_data_type.is_array() else field_2_data_type

    return _BITOR(ret_data_type, field_1.to_string(), field_2.to_string())


def TIME(
    hours: Operand | int,
    minutes: Operand | int,
    seconds: Operand | int,
) -> Formula:
    """
    Constructs a time value from hour, minute, and second components.

    The TIME function creates a valid time based on the provided `hours`, `minutes`, and `seconds`.
    It can operate element-wise if any of the inputs are arrays, producing a corresponding array
    of time values.

    Arguments:
        hours:
            The hours component of the time (0–23).

            *Supported types*:

            .. container:: supported-types

                - INTEGER
                - INTEGER_ARRAY
        minutes:
            The minutes component of the time (0–59).

            *Supported types*:

            .. container:: supported-types

                - INTEGER
                - INTEGER_ARRAY
        seconds:
            The seconds component of the time (0–59).

            *Supported types*:

            .. container:: supported-types

                - INTEGER
                - INTEGER_ARRAY

    Returns:
        A `Formula` object representing the constructed time. The result is an array if any input
        is an array; otherwise, it is a scalar. If the inputs do not form a valid time, the formula
        will evaluate to an error.

        *Supported types*:

        .. container:: supported-types

            - TIME
            - TIME_ARRAY

    Raises:
        ValueError: If any of the inputs are not integers or integer arrays.

    Examples:
        Basic usage:

        .. code-block:: python

            TIME(14, 30, 0)
            # Returns a time representing 14:30:00

        Using arrays:

        .. code-block:: python

            TIME([9, 12, 15], [0, 30, 45], [0, 0, 30])
            # Returns TIME_ARRAY with [09:00:00, 12:30:00, 15:45:30]
    """
    if isinstance(hours, int):
        return TIME(CONST(hours), minutes, seconds)
    if isinstance(minutes, int):
        return TIME(hours, CONST(minutes), seconds)
    if isinstance(seconds, int):
        return TIME(hours, minutes, CONST(seconds))

    hours_date_type = hours.to_data_type()
    minutes_date_type = minutes.to_data_type()
    seconds_date_type = seconds.to_data_type()

    if (
        hours_date_type not in {DataType.INTEGER, DataType.INTEGER_ARRAY}
        or minutes_date_type not in {DataType.INTEGER, DataType.INTEGER_ARRAY}
        or seconds_date_type not in {DataType.INTEGER, DataType.INTEGER_ARRAY}
    ):
        raise ValueError(
            f"TIME invalid with data types {hours_date_type}, {minutes_date_type}, "
            f"{seconds_date_type}"
        )

    ret_data_type = (
        DataType.TIME_ARRAY
        if hours_date_type.is_array()
        or minutes_date_type.is_array()
        or seconds_date_type.is_array()
        else DataType.TIME
    )

    return _TIME(ret_data_type, hours.to_string(), minutes.to_string(), seconds.to_string())


def SETTIME(date: Operand, time: Operand) -> Formula:
    """
    Combines a date and a time into a single datetime value.

    The SETTIME function constructs a DATETIME formula by combining the provided `date`
    with the specified `time`. If any input is an array, the function will operate element-wise
    and produce a DATETIME_ARRAY.

    Arguments:
        date:
            The date component. Can be a scalar date or DATE_ARRAY.

            *Supported types*:

            .. container:: supported-types

                - DATE
                - DATE_ARRAY
                - DATETIME
                - DATETIME_ARRAY
        time:
            The time component.

            *Supported types*:

            .. container:: supported-types

                - TIME
                - DATETIME
                - TIME_ARRAY
                - DATETIME_ARRAY

    Returns:
        A `Formula` object representing the combined date and time. Returns an array if any
        input is an array; otherwise, a scalar DATETIME.

        *Supported types*:

        .. container:: supported-types

            - DATETIME
            - DATETIME_ARRAY

    Raises:
        ValueError: If the `date` is not of type DATE/DATE_ARRAY/DATETIME/DATETIME_ARRAY or
        `time` is not of type TIME/TIME_ARRAY.

    Examples:
        .. code-block:: python

            SETTIME(DATE(2025, 9, 3), TIME(14, 30, 0))
            # Returns a DATETIME representing 2025-09-03 14:30:00
    """

    date_date_type = date.to_data_type()
    time_date_type = time.to_data_type()

    if date_date_type not in DATE_AND_ARRAY_TYPES or time_date_type not in TIME_AND_ARRAY_TYPES:
        raise ValueError(f"SETTIME invalid with data types {date_date_type}, {time_date_type}")

    ret_data_type = DataType.DATETIME
    if date_date_type.is_array() or time_date_type.is_array():
        ret_data_type = DataType.DATETIME_ARRAY

    return _SETTIME(ret_data_type, date.to_string(), time.to_string())


def PLUSMINUTES(time: Operand, minutes: Operand | int) -> Formula:
    """
    Adds a specified number of minutes to a given time or datetime.

    The PLUSMINUTES function returns a DATETIME or TIME value that is offset by the given
    number of `minutes`. If either input is an array, the function operates element-wise
    and returns a TIME_ARRAY or DATETIME_ARRAY. If negative minutes are provided, the function
    subtracts that number of minutes from the original time or datetime.

    Arguments:
        time:
            The starting time or datetime to which minutes will be added. Can be a scalar
            or an array.

            *Supported types*:

            .. container:: supported-types

                - DATE
                - DATE_ARRAY
                - TIME
                - TIME_ARRAY
                - DATETIME
                - DATETIME_ARRAY
        minutes:
            The number of minutes to add. Can be a scalar integer or INTEGER_ARRAY. If negative, the
            minutes are subtracted.

            *Supported types*:

            .. container:: supported-types

                - INTEGER
                - INTEGER_ARRAY

    Returns:
        A `Formula` object representing the time or datetime after adding the specified
        minutes. Returns an array if any input is an array; otherwise, a scalar DATE, TIME or
        DATETIME.

        *Supported types*:

        .. container:: supported-types

            - DATE
            - DATE_ARRAY
            - TIME
            - TIME_ARRAY
            - DATETIME
            - DATETIME_ARRAY

    Raises:
        ValueError: If the `time` input is not a valid DATE/TIME/DATETIME type or if `minutes`
        is not an integer type.

    Examples:
        .. code-block:: python

            PLUSMINUTES(TIME(14, 30, 0), 45)
            # Returns a TIME representing 15:15:00
    """
    if isinstance(minutes, int):
        return PLUSMINUTES(time, CONST(minutes))

    time_date_type = time.to_data_type()
    minutes_date_type = minutes.to_data_type()

    if (
        time_date_type not in TIME_AND_ARRAY_TYPES and time_date_type not in DATE_AND_ARRAY_TYPES
    ) or minutes_date_type not in {
        DataType.INTEGER,
        DataType.INTEGER_ARRAY,
    }:
        raise ValueError(
            f"PLUSMINUTES invalid with data types {time_date_type}, {minutes_date_type}"
        )

    if isinstance(time_date_type, DataType):
        ret_data_type = (
            time_date_type if minutes_date_type == DataType.INTEGER else time_date_type.to_array()
        )
    else:
        raise ValueError(f"PLUSMINUTES invalid with data types {time_date_type}")

    return _PLUSMINUTES(ret_data_type, time.to_string(), minutes.to_string())


def CHOOSE(index: Operand | int, *values: Operand | str | int | float | bool) -> Formula:
    """
    Returns the value at a specified index from a list of inputs.

    The CHOOSE function selects a value from the provided `values` based on the 1-based
    `index`. If the index is out of range, the formula will evaluate to an error.
    All input values must be of the same data type.

    Arguments:
        index:
            The position of the value to select. Indexing starts at 1.

            *Supported types*:

            .. container:: supported-types

                - INTEGER

        *values:
            An arbitrary number of values to choose from. All values must share the same
            data type.

            *Supported types*:

            .. container:: supported-types

                - ANY

    Returns:
        A `Formula` object representing the selected value.

        *Supported types*:

        .. container:: supported-types

            - ANY

    Raises:
        ValueError:
            - If no values are provided.
            - If the index is not an integer.
            - If the data types of the input values are inconsistent.

    Examples:
        .. code-block:: python

            CHOOSE(2, "apple", "banana", "cherry")
            # Returns "banana"

        .. code-block:: python

            CHOOSE(4, "apple", "banana", "cherry")
            # Returns an error value since index 4 is out of range.
    """
    if not values:
        raise ValueError("At least one input is required")

    if isinstance(index, int):
        return CHOOSE(CONST(index), *values)

    converted_values = [value if isinstance(value, Operand) else CONST(value) for value in values]

    data_type = converted_values[0].to_data_type()
    for field in converted_values:
        if field.to_data_type() != data_type:
            raise ValueError("All provided fields of CHOOSE must have the same data type")

    value_strings = [value.to_string() for value in converted_values]
    return _CHOOSE(data_type, index.to_string(), *value_strings)


def ARRAY(ignore_null: Operand | bool, *fields: Operand | str | int | float | bool) -> Formula:
    """
    Creates a `Formula` representing an array from the provided fields.

    The ARRAY function constructs an array from the input values or model components.
    Optionally, fields with blank values can be excluded if `ignore_null` is True.
    All input fields must have the same data type and cannot themselves be arrays or maps.

    Arguments:
        ignore_null:
            Boolean or model component indicating whether to exclude BLANK values from the
            resulting array.

            *Supported types*:

            .. container:: supported-types

                - BOOLEAN

        *fields:
            An arbitrary number of scalar values, model components, or BLANK() values to include
            in the array. All non-BLANK fields must share the same data type and cannot be
            MapDataTypes. At least one non-BLANK field must be provided to determine the array
            data type.

            *Supported types*:

            .. container:: supported-types

                - STRING
                - INTEGER
                - DECIMAL
                - BOOLEAN
                - DATE
                - TIME
                - DATETIME
                - OBJECT
                - STRING_ARRAY
                - INTEGER_ARRAY
                - DECIMAL_ARRAY
                - BOOLEAN_ARRAY
                - DATE_ARRAY
                - TIME_ARRAY
                - DATETIME_ARRAY
                - OBJECT_ARRAY
                - NULL (BLANK)

    Returns:
        A `Formula` object representing the constructed array.

        *Supported types*:

        .. container:: supported-types

            - STRING_ARRAY
            - INTEGER_ARRAY
            - DECIMAL_ARRAY
            - BOOLEAN_ARRAY
            - DATE_ARRAY
            - TIME_ARRAY
            - DATETIME_ARRAY
            - OBJECT_ARRAY

    Raises:
        ValueError: If no fields are provided.
        ValueError: If all fields are BLANK (cannot determine data type).
        ValueError: If non-BLANK field types are inconsistent.
        ValueError: If any non-BLANK field is a MapDataType.
        ValueError: If `ignore_null` is not a BOOLEAN type.

    Examples:
        Creating an array from primitive values:

        .. code-block:: python

            ARRAY(False, 1, 2, 3)
            # Returns [1, 2, 3]

        Creating an array excluding blank values:

        .. code-block:: python

            ARRAY(True, CONST(1), BLANK(), CONST(3))
            # Returns [1, 3]

        Creating an array that includes BLANK values:

        .. code-block:: python

            ARRAY(False, CONST(1), BLANK(), CONST(3))
            # Returns [1, BLANK(), 3]

        Combining arrays where some elements are BLANK:

        .. code-block:: python

            ARRAY(False, ARRAY(False, 1, 2), ARRAY(False, 3, BLANK()))
            # Returns [1, 2, 3, BLANK()]
    """
    if not fields:
        raise ValueError("At least one input is required")

    if isinstance(ignore_null, bool):
        return ARRAY(CONST(ignore_null), *fields)

    converted_fields = [field if isinstance(field, Operand) else CONST(field) for field in fields]

    ignore_null_data_type = ignore_null.to_data_type()
    if ignore_null_data_type != DataType.BOOLEAN:
        raise ValueError(f"ARRAY invalid with data type {ignore_null_data_type}")

    first_non_blank = next((f for f in converted_fields if f.to_data_type() != DataType.NULL), None)
    if first_non_blank is None:
        raise ValueError("ARRAY requires at least one non-BLANK field to determine data type")

    data_type = first_non_blank.to_data_type()
    base_data_type = data_type.from_array() if data_type.is_array() else data_type
    for field in converted_fields:
        field_data_type = field.to_data_type()
        if field_data_type == DataType.NULL:
            continue
        base_field_data_type = (
            field_data_type.from_array() if field_data_type.is_array() else field_data_type
        )
        if base_field_data_type != base_data_type:
            raise ValueError("All provided fields of ARRAY must have the same data type")

    ret_data_type: DataType | ObjectDataType
    if isinstance(base_data_type, ObjectDataType):
        ret_data_type = ObjectDataType(base_data_type._source_table, is_array=True)
    elif isinstance(base_data_type, DataType):
        ret_data_type = base_data_type.to_array()
    else:
        raise ValueError(f"ARRAY invalid with data type {base_data_type}")

    field_strings = [field.to_string() for field in converted_fields]
    return _ARRAY(ret_data_type, ignore_null.to_string(), *field_strings)


def ABS(value: int | float | Operand) -> Formula:
    """
    Returns the absolute value of a number or numeric array.

    The ABS function computes the absolute value of the input. For scalar numbers, it returns
    the positive equivalent. For array inputs the absolute value is computed element-wise and an
    array type is returned.

    Arguments:
        value: The numeric input whose absolute value is to be computed.

            *Supported types*:

            .. container:: supported-types

                - INTEGER
                - DECIMAL
                - INTEGER_ARRAY
                - DECIMAL_ARRAY

    Returns:
        A `Formula` object representing the absolute value of the input. For arrays,
        the absolute value is computed element-wise.

        *Supported types*:

        .. container:: supported-types

            - INTEGER
            - DECIMAL
            - INTEGER_ARRAY
            - DECIMAL_ARRAY

    Raises:
        ValueError: If the input is not a numeric type.

    Examples:
        Absolute value of a scalar:

        .. code-block:: python

            ABS(-5)
            # Returns 5

        Absolute value of a decimal:

        .. code-block:: python

            ABS(-3.7)
            # Returns 3.7

        Absolute value of a numeric array:

        .. code-block:: python

            ABS([-1, -2, 3])
            # Returns [1, 2, 3]
    """
    if isinstance(value, int | float):
        return ABS(CONST(value))

    data_type = value.to_data_type()

    if data_type not in NUMERIC_AND_ARRAY_TYPES or not isinstance(data_type, DataType):
        raise ValueError(f"ABS invalid with data type {data_type}")

    return _ABS(data_type, value.to_string())


def GET(map_object: Operand, key: Operand) -> Formula:
    """
    Retrieves the value associated with a specified key from a map field.

    The GET function looks up a key in a MAP-type `Operand` and returns the corresponding
    value. The key must be a singular OBJECT reference to the same source table as the map.

    Arguments:
        map_object:
            The MAP-type model component containing key-value pairs.

            *Supported types*:

            .. container:: supported-types

                - STRING_MAP
                - INTEGER_MAP
                - DECIMAL_MAP
                - BOOLEAN_MAP
                - DATE_MAP
                - TIME_MAP
                - DATETIME_MAP
        key:
            The OBJECT-type key whose associated value is to be retrieved. Must reference the same
            table as the map and cannot be an array.

            *Supported types*:

            .. container:: supported-types

                - OBJECT

    Returns:
        A `Formula` object representing the value associated with the specified key. The data type
        will match the underlying data type of the map's values. If the key does not exist in the,
        the formula will evaluate to an error.

        *Supported types*:

        .. container:: supported-types

            - STRING
            - INTEGER
            - DECIMAL
            - BOOLEAN
            - DATE
            - TIME
            - DATETIME

    Raises:
        ValueError: If `map_object` is not a MAP type.
        ValueError: If `key` is not a singular OBJECT referencing the map's source table.

    Examples:
        Basic usage:

        .. code-block:: python

            GET(my_map, some_object_key)
            # Returns the value associated with `some_object_key` in `my_map`

        Invalid key:

        .. code-block:: python

            GET(my_map, another_table_object)
            # Raises `ValueError` because the key references a different table
    """

    value_data_type = map_object.to_data_type()
    if not isinstance(value_data_type, MapDataType):
        raise ValueError("GET operation requires a MAP type as the first argument.")

    key_data_type = key.to_data_type()
    if not isinstance(key_data_type, ObjectDataType):
        raise ValueError("Key must be an OBJECT type referencing the same table as the map.")

    if key_data_type.is_array() or key_data_type._source_table != value_data_type._source_table:
        raise ValueError("Key must be a singular OBJECT reference to the same table as the map.")

    ret_data_type = value_data_type._data_type

    return _GET(ret_data_type, map_object.to_string(), key.to_string())


def EXP(value: int | float | Operand) -> Formula:
    """
    Computes the exponential (e^x) of a given number or numeric array.

    This function calculates the natural exponential of a given number or array of numbers. If an
    array of numbers is provided, the exponential is calculated for each element individually. If
    the input is blank or in an error state, the formula will evaluate to an error.

    Arguments:
        value:
            The numeric input to exponentiate.

            *Supported types*:

            .. container:: supported-types

                - INTEGER
                - DECIMAL
                - INTEGER_ARRAY
                - DECIMAL_ARRAY

    Returns:
        A `Formula` object representing the computed exponential.

        *Supported types*:

        .. container:: supported-types

            - DECIMAL
            - DECIMAL_ARRAY

    Raises:
        ValueError: If `value` is not a numeric type or a numeric array.

    Examples:
        Basic usage with a scalar:

        .. code-block:: python

            EXP(1)
            # Returns 2.718281828459045 (approximately)

        Usage with a model object:

        .. code-block:: python

            EXP(my_numeric_field)
            # Returns a formula representing the natural exponentation of `my_numeric_field`)`

        Usage with an array:

        .. code-block:: python

            EXP([1, 2, 3])
            # Returns [2.718, 7.389, 20.085] approximately
    """
    if isinstance(value, int | float):
        return EXP(CONST(value))

    data_type = value.to_data_type()

    if data_type not in NUMERIC_AND_ARRAY_TYPES or not isinstance(data_type, DataType):
        raise ValueError(f"EXP invalid with data type {data_type}")

    return _EXP(data_type, value.to_string())


def INTERSECTION(ignore_blanks: Operand | bool, *arrays: Operand) -> Formula:
    """
    Returns the intersection of one or more arrays, optionally ignoring blank values.

    This function performs a set intersection operation across all input arrays.
    Only elements present in every array are included in the result. Duplicates
    are removed automatically, and order is not guaranteed. Blank values can be
    optionally ignored using the `ignore_blanks` flag.

    Arguments:
        ignore_blanks:
            A boolean specifying whether blank values should be ignored in the input arrays.

            *Supported types*:

            .. container:: supported-types

                - BOOLEAN

        *arrays:
            One or more array objects to intersect. All arrays must have the same base data type.

            *Supported types*:

            .. container:: supported-types

                - INTEGER_ARRAY
                - DECIMAL_ARRAY
                - STRING_ARRAY
                - BOOLEAN_ARRAY
                - DATE_ARRAY
                - DATETIME_ARRAY
                - OBJECT_ARRAY

    Returns:
        A formula object representing the intersection of all input arrays. The output array
        contains only elements present in every input array, with duplicates removed.

        *Supported types*:

        .. container:: supported-types

            - INTEGER_ARRAY
            - DECIMAL_ARRAY
            - STRING_ARRAY
            - BOOLEAN_ARRAY
            - DATE_ARRAY
            - DATETIME_ARRAY
            - OBJECT_ARRAY

    Raises:
        ValueError: If `ignore_blanks` is not BOOLEAN.
        ValueError: If no arrays are provided.
        ValueError: If any input is not an array type.
        ValueError: If arrays do not all share the same base data type.

    Examples:
        Basic usage with integers:

        .. code-block:: python

            INTERSECTION(True, [1, 2, 3], [2, 3, 4])
            # Returns [2, 3]

        Strings with blanks ignored:

        .. code-block:: python

            INTERSECTION(True, ["A", null, "B"], ["B", "A", null])
            # Returns ["A", "B"]

        Single array de-duplication:

        .. code-block:: python

            INTERSECTION(False, [1, 2, 2, 3])
            # Returns [1, 2, 3]
    """
    if isinstance(ignore_blanks, bool):
        return INTERSECTION(CONST(ignore_blanks), *arrays)

    ignore_blanks_data_type = ignore_blanks.to_data_type()
    if ignore_blanks_data_type != DataType.BOOLEAN:
        raise ValueError(
            f"The 'ignore_blanks' argument must be of BOOLEAN type, but got "
            f"{ignore_blanks_data_type}."
        )

    if len(arrays) < 1:
        raise ValueError("At least one array is required. No arrays were provided.")

    data_type = arrays[0].to_data_type()
    if not data_type.is_array():
        raise ValueError(
            f"The UNION function only supports ARRAY types, but the provided input is of "
            f"type {data_type}."
        )

    array_strings = []
    for array in arrays:
        if array.to_data_type() != data_type:
            raise ValueError(
                f"All input arrays must have the same data type. The first array has type "
                f"{data_type}, but the provided array has type {array.to_data_type()}."
            )
        array_strings.append(array.to_string())

    return _INTERSECTION(data_type, ignore_blanks.to_string(), *array_strings)


def UNION(ignore_blanks: Operand | bool, *arrays: Operand) -> Formula:
    """
    Returns the union of one or more arrays, optionally ignoring blank values.

    This function performs a set union operation across all input arrays.
    Elements present in *any* array are included in the result. Duplicates
    are removed automatically, and order is not guaranteed. Blank values can be
    optionally ignored using the `ignore_blanks` flag.

    Arguments:
        ignore_blanks:
            A boolean specifying whether blank values should be ignored in the input arrays.

            *Supported types*:

            .. container:: supported-types

                - BOOLEAN

        *arrays:
            One or more array objects to union. All arrays must have the same base data type.

            *Supported types*:

            .. container:: supported-types

                - INTEGER_ARRAY
                - DECIMAL_ARRAY
                - STRING_ARRAY
                - BOOLEAN_ARRAY
                - DATE_ARRAY
                - DATETIME_ARRAY
                - OBJECT_ARRAY

    Returns:
        A formula object representing the union of all input arrays. The output array
        contains only elements present in every input array, with duplicates removed.

        *Supported types*:

        .. container:: supported-types

            - INTEGER_ARRAY
            - DECIMAL_ARRAY
            - STRING_ARRAY
            - BOOLEAN_ARRAY
            - DATE_ARRAY
            - DATETIME_ARRAY
            - OBJECT_ARRAY

    Raises:
        ValueError: If `ignore_blanks` is not BOOLEAN.
        ValueError: If no arrays are provided.
        ValueError: If any input is not an array type.
        ValueError: If arrays do not all share the same base data type.

    Examples:
        Basic usage with integers:

        .. code-block:: python

            UNION(True, [1, 2, 3], [2, 3, 4])
            # Returns [1, 2, 3, 4]

        Strings with blanks ignored:

        .. code-block:: python

            UNION(True, ["A", null, "B"], ["B", "A", null])
            # Returns ["A", "B"]

        Single array de-duplication:

        .. code-block:: python

            UNION(False, [1, 2, 2, 3])
            # Returns [1, 2, 3]
    """
    if isinstance(ignore_blanks, bool):
        return UNION(CONST(ignore_blanks), *arrays)

    ignore_blanks_data_type = ignore_blanks.to_data_type()
    if ignore_blanks_data_type != DataType.BOOLEAN:
        raise ValueError(
            f"The 'ignore_blanks' argument must be of BOOLEAN type, but got "
            f"{ignore_blanks_data_type}."
        )

    if len(arrays) < 1:
        raise ValueError("At least one array is required. No arrays were provided.")

    data_type = arrays[0].to_data_type()
    if not data_type.is_array():
        raise ValueError(
            f"The UNION function only supports ARRAY types, but the provided input is of type "
            f"{data_type}."
        )

    array_strings = []
    for array in arrays:
        if array.to_data_type() != data_type:
            raise ValueError(
                f"All input arrays must have the same data type. The first array has type "
                f"{data_type}, but the provided array has type {array.to_data_type()}."
            )
        array_strings.append(array.to_string())

    return _UNION(data_type, ignore_blanks.to_string(), *array_strings)


def AVERAGE(*values: Operand | int | float) -> Formula:
    """
    Computes the average of one or more numeric values or arrays.

    This function calculates the arithmetic mean of the provided inputs. If array arguments
    are provided, their elements are aggregated to compute the average. If any input is blank or
    in an error state, the formula will evaluate to an error.

    Arguments:
        *values:
            One or more numeric values or arrays to include in the average calculation.

            *Supported types*:

            .. container:: supported-types

                - INTEGER
                - DECIMAL
                - INTEGER_ARRAY
                - DECIMAL_ARRAY

    Returns:
        A formula object representing the computed average. If all inputs are arrays,
        the result is a single aggregated numeric value.

        *Supported types*:

        .. container:: supported-types

            - DECIMAL

    Raises:
        ValueError: If no inputs are provided.
        ValueError: If any input is not a numeric type or array of numeric type.

    Examples:
        Single values:

        .. code-block:: python

            AVERAGE(1, 2, 3)
            # Returns 2.0

        Array input:

        .. code-block:: python

            AVERAGE([1, 2, 3], [4, 5, 6])
            # Returns 3.5
    """

    if not values:
        raise ValueError("At least one input is required")

    # Convert all inputs to `Operand` if necessary
    converted_fields = [field if isinstance(field, Operand) else CONST(field) for field in values]

    for value in converted_fields:
        data_type = value.to_data_type()
        if data_type not in NUMERIC_AND_ARRAY_TYPES:
            raise ValueError(f"Datatype {data_type} is not a valid input for this method")

    string_values = [value.to_string() for value in converted_fields]
    return _AVERAGE(*string_values)


def CHAR(value: Operand | int) -> Formula:
    """
    Converts an integer or array of integers to corresponding ASCII characters.

    This function returns the character represented by an integer value. If an array of integers
    is provided, it returns an array of corresponding characters. The valid input range is 0–255.
    If the input is outside this range, blank, or in an error state, the formula will evaluate to
    an error.

    Arguments:
        value:
            The integer to convert to a character.

            *Supported types*:

            .. container:: supported-types

                - INTEGER
                - INTEGER_ARRAY

    Returns:
        A formula object that evaluates to the ASCII character.

        *Supported types*:

        .. container:: supported-types

            - STRING
            - STRING_ARRAY

    Raises:
        ValueError: If the input is not an integer type or array of integers.

    Examples:
        Single value:

        .. code-block:: python

            CHAR(65)
            # Returns "A"

        Array input:

        .. code-block:: python

            CHAR([65, 66, 67])
            # Returns ["A", "B", "C"]
    """

    if isinstance(value, int):
        if value not in range(0, 256):
            raise ValueError(f"Input value: {value} is not in a valid ASCII range.")

    if isinstance(value, int):
        return CHAR(CONST(value))

    value_data_type = value.to_data_type()
    if value_data_type not in {DataType.INTEGER, DataType.INTEGER_ARRAY} or not isinstance(
        value_data_type, DataType
    ):
        raise ValueError(f"CHAR is not compatible with data type {value_data_type}")

    ret_data_type = DataType.STRING_ARRAY if value_data_type.is_array() else DataType.STRING
    return _CHAR(ret_data_type, value.to_string())


def DISTINCT(array: Operand) -> Formula:
    """
    Returns an array containing only the distinct values from the input array.

    This function removes duplicates from the provided array, preserving the order of
    first occurrences. It works on any scalar or object array type.

    Arguments:
        array:
            The array from which duplicates will be removed.

            *Supported types*:

            .. container:: supported-types

                - INTEGER_ARRAY
                - DECIMAL_ARRAY
                - STRING_ARRAY
                - BOOLEAN_ARRAY
                - DATE_ARRAY
                - TIME_ARRAY
                - DATETIME_ARRAY
                - OBJECT_ARRAY

    Returns:
        A formula object representing the array of distinct values.

        *Supported types*:

        .. container:: supported-types

            - INTEGER_ARRAY
            - DECIMAL_ARRAY
            - STRING_ARRAY
            - BOOLEAN_ARRAY
            - DATE_ARRAY
            - TIME_ARRAY
            - DATETIME_ARRAY
            - OBJECT_ARRAY

    Raises:
        ValueError: If the input is not an array type or is a MAP type.

    Examples:
        Removing duplicates from numbers:

        .. code-block:: python

            DISTINCT([1, 2, 2, 3, 1])
            # Returns [1, 2, 3]

        Removing duplicates from strings:

        .. code-block:: python

            DISTINCT(["apple", "banana", "apple", "cherry"])
            # Returns ["apple", "banana", "cherry"]
    """

    array_data_type = array.to_data_type()
    if isinstance(array_data_type, MapDataType):
        raise ValueError(f"DISTINCT is not compatible with data type {array_data_type}")
    if not array_data_type.is_array():
        raise ValueError(f"DISTINCT is not compatible with data type {array_data_type}")

    return _DISTINCT(array_data_type, array.to_string())


def HOUR(
    time: Operand,
) -> Formula:
    """
    Extracts the hour component from a time or array of times.

    The HOUR function returns the hour from the provided `time`. It supports both
    single times and arrays of times, returning an integer or an integer array accordingly.

    Arguments:
        time:
            The time or array of times from which to extract the hour.

            *Supported types*:

            .. container:: supported-types

                - TIME
                - DATETIME
                - TIME_ARRAY
                - DATETIME_ARRAY

    Returns:
        The hour as an integer or array of integers.

        *Supported types*:

        .. container:: supported-types

            - INTEGER
            - INTEGER_ARRAY

    Raises:
        ValueError: If the input is not a time type.

    Examples:
        .. code-block:: python

            HOUR(TIME(14, 32, 53))
            # Returns 14
    """
    time_data_type = time.to_data_type()
    if time_data_type not in TIME_AND_ARRAY_TYPES:
        raise ValueError(f"HOUR invalid with the argument {time_data_type}")

    ret_data_type = DataType.INTEGER_ARRAY if time_data_type.is_array() else DataType.INTEGER

    return _HOUR(ret_data_type, time.to_string())


def HOURSBETWEEN(
    first_time: Operand,
    second_time: Operand,
) -> Formula:
    """
    Returns the number of hours between two times or arrays of times.

    The HOURSBETWEEN function calculates the difference in hours between `first_time` and
    `second_time`. The result is positive if `second_time` occurs after `first_time` and
    negative if it occurs before. This function supports both single times and arrays of times.
    The return value is a decimal or decimal array representing the hour difference.

    Arguments:
        first_time:
            The starting time or date time.

            *Supported types*:

            .. container:: supported-types

                - TIME
                - DATETIME
                - TIME_ARRAY
                - DATETIME_ARRAY

        second_time:
            The ending time or date time.

            *Supported types*:

            .. container:: supported-types

                - TIME
                - DATETIME
                - TIME_ARRAY
                - DATETIME_ARRAY

    Returns:
        The number of hours between the two times. If input arrays have unequal lengths the returned
        formula will evaluate to an error.

        *Supported types*:

        .. container:: supported-types

            - DECIMAL
            - DECIMAL_ARRAY

    Raises:
        ValueError: If either input is not a valid type.

    Examples:
        .. code-block:: python

            HOURSBETWEEN(TIME(14, 30, 0), DATE(16, 0, 0))
            # Returns 1.5
    """

    first_time_data_type = first_time.to_data_type()
    second_time_data_type = second_time.to_data_type()

    if (
        first_time_data_type not in TIME_AND_ARRAY_TYPES
        and first_time_data_type not in {DataType.DATE, DataType.DATE_ARRAY}
    ) or (
        second_time_data_type not in TIME_AND_ARRAY_TYPES
        and second_time_data_type not in {DataType.DATE, DataType.DATE_ARRAY}
    ):
        raise ValueError(
            f"HOURSBETWEEN invalid with arguments {first_time_data_type} and "
            f"{second_time_data_type}"
        )

    if not isinstance(first_time_data_type, DataType) or not isinstance(
        second_time_data_type, DataType
    ):
        raise ValueError(
            f"HOURSBETWEEN invalid with arguments {first_time_data_type} and "
            f"{second_time_data_type}"
        )

    singular_first_time_type = first_time_data_type
    if first_time_data_type.is_array():
        singular_first_time_type = first_time_data_type.from_array()

    singular_second_time_type = second_time_data_type
    if second_time_data_type.is_array():
        singular_second_time_type = second_time_data_type.from_array()

    if singular_first_time_type != singular_second_time_type:
        raise ValueError(
            f"Inputs are in different singular types {first_time_data_type} and "
            f"{second_time_data_type}"
        )

    ret_data_type = DataType.DECIMAL
    if first_time_data_type.is_array() or second_time_data_type.is_array():
        ret_data_type = DataType.DECIMAL_ARRAY

    return _HOURSBETWEEN(ret_data_type, first_time.to_string(), second_time.to_string())


def INTEGER(
    value: Operand | bool | float | str,
) -> Formula:
    """
    Converts a value or expression to an INTEGER or INTEGER_ARRAY.

    This function converts the provided input to an integer type.

    Arguments:
        value:
            The input to convert. Can be a scalar or a model object.

            *Supported types*:

            .. container:: supported-types

                - BOOLEAN,
                - BOOLEAN_ARRAY,
                - DECIMAL,
                - DECIMAL_ARRAY,
                - STRING,
                - STRING_ARRAY,

    Returns:
        A formula object of type INTEGER or INTEGER_ARRAY representing the converted value.

        *Supported types*:

        .. container:: supported-types

            - INTEGER
            - INTEGER_ARRAY

    Raises:
        ValueError: If the input value is not a supported type or model object.

    Examples:
        .. code-block:: python

            INTEGER(3.7)
            # Returns 3

            INTEGER(True)
            # Returns 1
    """
    allow_data_types = {
        DataType.BOOLEAN,
        DataType.BOOLEAN_ARRAY,
        DataType.DECIMAL,
        DataType.DECIMAL_ARRAY,
        DataType.STRING,
        DataType.STRING_ARRAY,
    }

    if isinstance(value, bool | float | str):
        return INTEGER(CONST(value))

    value_data_type = value.to_data_type()

    if value_data_type not in allow_data_types:
        raise ValueError(f"INTEGER invalid with the argument {value_data_type}")

    ret_data_type = DataType.INTEGER_ARRAY if value_data_type.is_array() else DataType.INTEGER

    return _INTEGER(ret_data_type, value.to_string())


def LEN(value: Operand | str | int | float) -> Formula:
    """
    Returns the length of a string or the number of digits in a numeric value.

    - For strings: returns the number of characters.
    - For numbers: returns the number of digits in the integer representation.
    - For arrays: returns an array of lengths for each element.

    Arguments:
        value:
            The value to measure.

            *Supported types*:

            .. container:: supported-types

                - INTEGER
                - DECIMAL
                - STRING
                - INTEGER_ARRAY
                - DECIMAL_ARRAY
                - STRING_ARRAY

    Returns:
        A formula representing the length(s) of the input value(s).

        *Supported types*:

        .. container:: supported-types

            - INTEGER
            - INTEGER_ARRAY

    Raises:
        ValueError: If the input value's data type is not one of the supported types.

    Examples:
        Single string:

        .. code-block:: python

            LEN("Hello")
            # Returns 5

        Single number:

        .. code-block:: python

            LEN(12345)
            # Returns 5

        Array of strings:

        .. code-block:: python

            LEN(["Hi", "Test", "A"])
            # Returns [2, 4, 1]

        Array of numbers:

        .. code-block:: python

            LEN([12, 345, 6])
            # Returns [2, 3, 1]
    """

    if isinstance(value, str | int | float):
        return LEN(CONST(value))

    value_data_type = value.to_data_type()

    if value_data_type not in NUMERIC_AND_ARRAY_TYPES and value_data_type not in {
        DataType.STRING,
        DataType.STRING_ARRAY,
    }:
        raise ValueError(f"LEN invalid with the argument {value_data_type}")

    ret_data_type = DataType.INTEGER_ARRAY if value_data_type.is_array() else DataType.INTEGER
    return _LEN(ret_data_type, value.to_string())


def ISERROR(value: Operand | Any) -> Formula:
    """
    Checks whether a value or array contains an error.

    - Returns True for elements that represent an error.
    - Returns False for elements that are valid values.
    - Works for both scalar values and arrays.

    Arguments:
        value:
            The value to check for errors.

            *Supported types*:

            .. container:: supported-types

                - ANY

    Returns:
        A formula indicating error status.

        *Supported types*:

        .. container:: supported-types

            - BOOLEAN
            - BOOLEAN_ARRAY

    Examples:
        Scalar value:

        .. code-block:: python

            ISERROR(123)
            # Returns False

        Array of values:

        .. code-block:: python

            ISERROR([123, "abc", ERROR_VALUE])
            # Returns [False, False, True]
    """

    if not isinstance(value, Operand):
        return ISERROR(CONST(value))

    value_data_type = value.to_data_type()

    ret_data_type = DataType.BOOLEAN_ARRAY if value_data_type.is_array() else DataType.BOOLEAN

    return _ISERROR(ret_data_type, value.to_string())


def LOOKUPARRAY(source_array: Operand, match_array: Operand, result_array: Operand) -> Formula:
    """
    Performs a vectorised mapping on `source_array` defined by `match_array` and `result_array`.

    Each element in `source_array` is searched for in `match_array`. If a match is found, the
    corresponding element from `result_array` is returned. If no match exists, the result is null.

    The `match_array` and `result_array` arguments must be of equal length, defining
    a mapping from match → result. The first argument (`source_array`) can be a different length;
    the output will have the same length as `source_array` and the same data type as `result_array`.

    This function is similar to a vectorised `VLOOKUP` in Excel or dictionary mapping: it applies
    the mapping to every element in the source array in one operation.

    Arguments:
        source_array:
            The array containing values to look up. Must be an array type of the same type as
            `match_array`. Each element will be searched for in `match_array`.

            *Supported types*:

            .. container:: supported-types

                - INTEGER_ARRAY
                - DECIMAL_ARRAY
                - STRING_ARRAY
                - BOOLEAN_ARRAY
                - DATE_ARRAY
                - DATETIME_ARRAY
                - OBJECT_ARRAY

        match_array:
            The array containing reference values. Each element in `source_array` is
            compared to this array to find a match. Must be the same type as `source_array`
            and the same length as `result_array`.

            *Supported types*:

            .. container:: supported-types

                - INTEGER_ARRAY
                - DECIMAL_ARRAY
                - STRING_ARRAY
                - BOOLEAN_ARRAY
                - DATE_ARRAY
                - DATETIME_ARRAY
                - OBJECT_ARRAY

        result_array:
            The array containing values to return when matches are found in `match_array`.
            Must have the same length as `match_array`.

            *Supported types*:

            .. container:: supported-types

                - INTEGER_ARRAY
                - DECIMAL_ARRAY
                - STRING_ARRAY
                - BOOLEAN_ARRAY
                - DATE_ARRAY
                - DATETIME_ARRAY
                - OBJECT_ARRAY

    Returns:
        A formula object representing the lookup operation. The resulting array has
        the same length as `source_array`, with each element computed as follows:

            - If `source_array[i]` is found in `match_array`, return `result_array[j]`,
              where `match_array[j] == source_array[i]`.
            - If `source_array[i]` is not found in `match_array`, return null.

        *Supported types*:

        .. container:: supported-types

            - INTEGER_ARRAY
            - DECIMAL_ARRAY
            - STRING_ARRAY
            - BOOLEAN_ARRAY
            - DATE_ARRAY
            - DATETIME_ARRAY
            - OBJECT_ARRAY

    Raises:
        ValueError: If any input is not an array type, if `source_array` and `match_array`
                    have different types, or if `match_array` and `result_array` have
                    different lengths.

    Examples:
        Basic usage with strings:

        .. code-block:: python

            LOOKUPARRAY(["A", "B", "C"], ["X", "B", "Y"], ["X_val", "B_val", "Y_val"])
            # Returns [null, "B_val", null]
            # Explanation:
            # - "A" is not in match_array → null
            # - "B" is found at index 2 → return "B_val"
            # - "C" is not in match_array → null

        Numbers with exact matches:

        .. code-block:: python

            LOOKUPARRAY([1, 2, 3], [3, 1, 2], [30, 10, 20])
            # Returns [10, 20, 30]
            # Explanation:
            # - 1 is found at index 2 → 10
            # - 2 is found at index 3 → 20
            # - 3 is found at index 1 → 30

        Partial matches:

        .. code-block:: python

            LOOKUPARRAY([5, 7, 9], [7, 5], [70, 50])
            # Returns [50, 70, null]
            # Explanation:
            # - 5 is found at index 2 → 50
            # - 7 is found at index 1 → 70
            # - 9 is not found → null

        Boolean arrays:

        .. code-block:: python

            LOOKUPARRAY([True, False, True], [False, True], ["No", "Yes"])
            # Returns ["Yes", "No", "Yes"]
            # Explanation:
            # - True is found at index 2 → "Yes"
            # - False is found at index 1 → "No"
            # - True again → "Yes"
            Basic usage:
    """
    source_array_data_type = source_array.to_data_type()
    match_array_data_type = match_array.to_data_type()
    result_array_data_type = result_array.to_data_type()

    if (
        isinstance(source_array_data_type, MapDataType)
        or isinstance(match_array_data_type, MapDataType)
        or isinstance(result_array_data_type, MapDataType)
    ):
        raise ValueError(
            f"LOOKUPARRAY invalid with the arguments {source_array_data_type}, "
            f"{match_array_data_type} and {result_array_data_type}"
        )

    if (
        not source_array_data_type.is_array()
        or not match_array_data_type.is_array()
        or not result_array_data_type.is_array()
    ):
        raise ValueError(
            f"LOOKUPARRAY invalid with the arguments {source_array_data_type}, "
            f"{match_array_data_type} and {result_array_data_type}"
        )

    if source_array_data_type != match_array_data_type:
        raise ValueError(
            f"Source array and match array are in different types of "
            f"{source_array_data_type}, {match_array_data_type}"
        )

    return _LOOKUPARRAY(
        result_array_data_type,
        source_array.to_string(),
        match_array.to_string(),
        result_array.to_string(),
    )


def LOWER(value: Operand | str) -> Formula:
    """
    Converts a string or string array to lowercase.

    - For scalar strings: Returns the lowercase version.
    - For string arrays: Returns a new array where each element is converted to lowercase.

    Arguments:
        value:
            The string or string array to convert.

            *Supported types*:

            .. container:: supported-types

                - STRING
                - STRING_ARRAY

    Returns:
        A formula containing the lowercase transformation.

        *Supported types*:

        .. container:: supported-types

            - STRING
            - STRING_ARRAY

    Raises:
        ValueError: If the input is not of type STRING or STRING_ARRAY.

    Examples:
        Single string:

        .. code-block:: python

            LOWER("HELLO")
            # Returns "hello"

        String array:

        .. code-block:: python

            LOWER(["Hello", "WORLD"])
            # Returns ["hello", "world"]
    """
    if isinstance(value, str):
        return LOWER(CONST(value))

    value_data_type = value.to_data_type()
    if value_data_type not in STRING_AND_ARRAY_TYPES:
        raise ValueError(f"LOWER invalid with the argument {value_data_type}")

    ret_data_type = DataType.STRING_ARRAY if value_data_type.is_array() else DataType.STRING

    return _LOWER(ret_data_type, value.to_string())


def MEDIAN(*values: Operand | int | float) -> Formula:
    """
    Computes the median of one or more numeric values or arrays.

    This function calculates the median of the provided inputs. If array arguments
    are provided, their elements are aggregated to compute the median. If any input is blank or
    in an error state, the formula will evaluate to an error.

    Arguments:
        *values:
            One or more numeric values or arrays to include in the median calculation.

            *Supported types*:

            .. container:: supported-types

                - INTEGER
                - DECIMAL
                - INTEGER_ARRAY
                - DECIMAL_ARRAY

    Returns:
        A formula object representing the computed median. If all inputs are arrays,
        the result is a single aggregated numeric value.

        *Supported types*:

        .. container:: supported-types

            - DECIMAL

    Raises:
        ValueError: If no inputs are provided.
        ValueError: If any input is not a numeric type or array of numeric type.

    Examples:
        Single values:

        .. code-block:: python

            MEDIAN(1, 2, 5)
            # Returns 2.0

        Array input:

        .. code-block:: python

            MEDIAN([0, 2, 3], [4, 5, 8])
            # Returns 3.5
    """
    if not values:
        raise ValueError("At least one input is required")

        # Convert all inputs to `Operand` if necessary
    converted_fields = [field if isinstance(field, Operand) else CONST(field) for field in values]

    for value in converted_fields:
        data_type = value.to_data_type()
        if data_type not in NUMERIC_AND_ARRAY_TYPES:
            raise ValueError(f"Datatype {data_type} is not a valid input for this method")

    string_values = [value.to_string() for value in converted_fields]
    return _MEDIAN(*string_values)


def MINUTE(
    time: Operand,
) -> Formula:
    """
    Extracts the minute component from a time or array of times.

    The MINUTE function returns the minute from the provided `time`. It supports both
    single times and arrays of times, returning an integer or an integer array accordingly.

    Arguments:
        time:
            The time or array of times from which to extract the hour.

            *Supported types*:

            .. container:: supported-types

                - TIME
                - DATETIME
                - TIME_ARRAY
                - DATETIME_ARRAY

    Returns:
        The minute as an integer or array of integers.

        *Supported types*:

        .. container:: supported-types

            - INTEGER
            - INTEGER_ARRAY

    Raises:
        ValueError: If the input is not a time type.

    Examples:
        .. code-block:: python

            MINUTE(TIME(14, 32, 53))
            # Returns 32
    """
    time_data_type = time.to_data_type()
    if time_data_type not in TIME_AND_ARRAY_TYPES:
        raise ValueError(f"MINUTE invalid with the argument {time_data_type}")

    ret_data_type = DataType.INTEGER
    if time_data_type.is_array():
        ret_data_type = DataType.INTEGER_ARRAY

    return _MINUTE(ret_data_type, time.to_string())


def MONTHSBETWEEN(
    first_date: Operand,
    second_date: Operand,
) -> Formula:
    """
    Returns the number of months between two dates.

    The MONTHSBETWEEN function calculates the difference in months between `first_date` and
    `second_date`. The result is positive if `second_date` occurs after `first_date` and
    negative if it occurs before. This function supports both single dates and arrays of dates.

    Arguments:
        first_date:
            The starting date or array of dates.

            *Supported types*:

            .. container:: supported-types

                - DATE
                - DATETIME
                - DATE_ARRAY
                - DATETIME_ARRAY

        second_date:
            The ending date or array of dates.

            *Supported types*:

            .. container:: supported-types

                - DATE
                - DATETIME
                - DATE_ARRAY
                - DATETIME_ARRAY

    Returns:
        The number of months between the two dates. If input arrays have unequal lengths the
        returned formula will evaluate to an error.

        *Supported types*:

        .. container:: supported-types

            - INTEGER
            - INTEGER_ARRAY

    Raises:
        ValueError: If either input is not a date or datetime type.

    Examples:
        .. code-block:: python

            MONTHSBETWEEN(DATE(2025, 1, 1), DATE(2025, 3, 10))
            # Returns 2
    """

    first_date_data_type = first_date.to_data_type()
    second_date_data_type = second_date.to_data_type()

    if (
        first_date_data_type not in DATE_AND_ARRAY_TYPES
        or second_date_data_type not in DATE_AND_ARRAY_TYPES
    ):
        raise ValueError(
            f"MONTHSBETWEEN invalid with arguments {first_date_data_type} "
            f"and {second_date_data_type}"
        )
    ret_data_type = DataType.INTEGER
    if first_date_data_type.is_array() or second_date_data_type.is_array():
        ret_data_type = DataType.INTEGER_ARRAY

    return _MONTHSBETWEEN(ret_data_type, first_date.to_string(), second_date.to_string())


def SECOND(
    time: Operand,
) -> Formula:
    """
    Extracts the second component from a time or array of times.

    The SECOND function returns the second from the provided `time`. It supports both
    single times and arrays of times, returning an integer or an integer array accordingly.

    Arguments:
        time:
            The time or array of times from which to extract the hour.

            *Supported types*:

            .. container:: supported-types

                - TIME
                - DATETIME
                - TIME_ARRAY
                - DATETIME_ARRAY

    Returns:
        The second as an integer or array of integers.

        *Supported types*:

        .. container:: supported-types

            - INTEGER
            - INTEGER_ARRAY

    Raises:
        ValueError: If the input is not a time type.

    Examples:
        .. code-block:: python

            SECOND(TIME(14, 32, 53))
            # Returns 53
    """
    time_data_type = time.to_data_type()
    if time_data_type not in TIME_AND_ARRAY_TYPES:
        raise ValueError(f"SECOND invalid with the argument {time_data_type}")

    ret_data_type = DataType.INTEGER
    if time_data_type.is_array():
        ret_data_type = DataType.INTEGER_ARRAY

    return _SECOND(ret_data_type, time.to_string())


def STDEV(*values: Operand | int | float) -> Formula:
    """
    Computes the standard deviation of one or more numeric values or arrays.

    This function calculates the standard deviation (sample) for all provided inputs.
    Inputs can be scalar numbers or arrays of numbers. If arrays are provided, they must
    be of numeric type and the function will compute the standard deviation over all values.

    Arguments:
        *values:
            One or more numeric values or arrays to compute the standard deviation.

            *Supported types*:

            .. container:: supported-types

                - INTEGER
                - INTEGER_ARRAY
                - DECIMAL
                - DECIMAL_ARRAY

    Returns:
        A formula representing the standard deviation of the input values.

        *Supported types*:

        .. container:: supported-types

            - DECIMAL
            - DECIMAL_ARRAY

    Raises:
        ValueError: If any input value is not numeric.

    Examples:
        Scalar numbers:

        .. code-block:: python

            STDEV(2, 4, 4, 4, 5, 5, 7, 9)
            # Returns 2.0

        Numeric arrays:

        .. code-block:: python

            STDEV([2, 4, 4], [4, 5, 5], [7, 9])
            # Returns 2.0
    """
    if not values:
        raise ValueError("At least one input is required")

    converted_fields = [value if isinstance(value, Operand) else CONST(value) for value in values]

    for value in converted_fields:
        data_type = value.to_data_type()
        if data_type not in NUMERIC_AND_ARRAY_TYPES:
            raise ValueError(f"Datatype {data_type} is not a valid input for this method")

    string_values = [value.to_string() for value in converted_fields]
    return _STDEV(*string_values)


def TEXTJOIN(
    delimiter: Operand | str,
    ignore_empty: Operand | bool,
    *string_arrays: Operand | str,
) -> Formula:
    """
    Joins text strings or string arrays with a specified delimiter, optionally ignoring empty
    values.

    This function concatenates multiple strings or string arrays into a single text string.
    Delimiters can be a single string or an array of strings; if multiple delimiters are provided,
    they are applied cyclically across the inputs. If `ignore_empty` is True, empty strings are
    skipped in the concatenation.

    Arguments:
        delimiter:
            The string or string array to use as the delimiter between elements.

            *Supported types*:

            .. container:: supported-types

                - STRING
                - STRING_ARRAY

        ignore_empty:
            Boolean flag indicating whether empty strings should be ignored.

            *Supported types*:

            .. container:: supported-types

                - BOOLEAN

        *string_arrays:
            One or more strings or string arrays to concatenate.

            *Supported types*:

            .. container:: supported-types

                - STRING
                - STRING_ARRAY

    Returns:
        A formula representing the concatenated string.

        *Supported types*:

        .. container:: supported-types

            - STRING
            - STRING_ARRAY

    Raises:
        ValueError: If no input strings are provided.
        ValueError: If `delimiter` or any input string is not a valid string/string array.
        ValueError: If `ignore_empty` is not BOOLEAN.

    Examples:
        Simple join:

        .. code-block:: python

            TEXTJOIN(",", True, "a", "b", "c")
            # Returns "a,b,c"

        Join with empty strings ignored:

        .. code-block:: python

            TEXTJOIN("-", True, "x", "", "y")
            # Returns "x-y"
    """

    if not string_arrays:
        raise ValueError("At least one input is required")

    if isinstance(delimiter, str):
        return TEXTJOIN(CONST(delimiter), ignore_empty, *string_arrays)
    if isinstance(ignore_empty, bool):
        return TEXTJOIN(delimiter, CONST(ignore_empty), *string_arrays)

    converted_string_arrays = [
        string if isinstance(string, Operand) else CONST(string) for string in string_arrays
    ]

    delimiter_data_type = delimiter.to_data_type()
    ignore_empty_data_type = ignore_empty.to_data_type()

    if (
        delimiter_data_type not in STRING_AND_ARRAY_TYPES
        or ignore_empty_data_type != DataType.BOOLEAN
    ):
        raise ValueError(
            f"TEXTJOIN invalid with the arguments {delimiter_data_type} "
            f"and {ignore_empty_data_type}"
        )

    for string_array in converted_string_arrays:
        string_array_data_type = string_array.to_data_type()
        if string_array_data_type not in STRING_AND_ARRAY_TYPES:
            raise ValueError(f"TEXTJOIN invalid with the argument {string_array_data_type}")

    string_values = [value.to_string() for value in converted_string_arrays]
    return _TEXTJOIN(delimiter.to_string(), ignore_empty.to_string(), *string_values)


def TRIM(value: Operand | str) -> Formula:
    """
    Removes leading and trailing whitespace from a string or string array.

    This function trims whitespace from each element if the input is a string array,
    or from the single string if the input is scalar.

    Arguments:
        value:
            The string or string array to trim.

            *Supported types*:

            .. container:: supported-types

                - STRING
                - STRING_ARRAY

    Returns:
        A formula representing the trimmed string(s).

        *Supported types*:

        .. container:: supported-types

            - STRING
            - STRING_ARRAY (if the input was an array)

    Raises:
        ValueError: If the input value is not STRING or STRING_ARRAY.

    Examples:
        Trim a single string:

        .. code-block:: python

            TRIM("  hello world  ")
            # Returns "hello world"

        Trim a string array:

        .. code-block:: python

            TRIM(["  foo  ", " bar "])
            # Returns ["foo", "bar"]
    """

    if isinstance(value, str):
        return TRIM(CONST(value))

    value_data_type = value.to_data_type()

    if value_data_type not in STRING_AND_ARRAY_TYPES:
        raise ValueError(f"TRIM invalid with the argument {value_data_type}")

    ret_data_type = DataType.STRING_ARRAY if value_data_type.is_array() else DataType.STRING

    return _TRIM(ret_data_type, value.to_string())


def UPPER(value: Operand | str) -> Formula:
    """
    Converts a string or string array to uppercase.

    - For scalar strings: Returns the uppercase version.
    - For string arrays: Returns a new array where each element is converted to uppercase.

    Arguments:
        value:
            The string or string array to convert.

            *Supported types*:

            .. container:: supported-types

                - STRING
                - STRING_ARRAY

    Returns:
        A formula containing the uppercase transformation.

        *Supported types*:

        .. container:: supported-types

            - STRING
            - STRING_ARRAY

    Raises:
        ValueError: If the input is not of type STRING or STRING_ARRAY.

    Examples:
        Single string:

        .. code-block:: python

            UPPER("hello")
            # Returns "HELLO"

        String array:

        .. code-block:: python

            UPPER(["Hello", "WorLD"])
            # Returns ["HELLO", "WORLD"]
    """
    if isinstance(value, str):
        return UPPER(CONST(value))

    value_data_type = value.to_data_type()
    if value_data_type not in STRING_AND_ARRAY_TYPES:
        raise ValueError(f"UPPER invalid with the argument {value_data_type}")

    ret_data_type = DataType.STRING_ARRAY if value_data_type.is_array() else DataType.STRING

    return _UPPER(ret_data_type, value.to_string())


def WEEKDAY(date: Operand, return_type: Operand | int | None = None) -> Formula:
    """
    Returns the day of the week for a given date, using a customizable numbering scheme.

    This function calculates the weekday for each date in `date` or a single date.
    The numbering of the days is determined by `return_type`, following conventions similar
    to Excel's WEEKDAY function.

    Arguments:
        date:
            The date or date array to evaluate.

            *Supported types*:

            .. container:: supported-types

                - DATE
                - DATE_ARRAY

        return_type:
            Optional parameter specifying the day numbering scheme. Can be a scalar integer
            (1-3 or 11-17) or a numeric model object. Defaults to 1 (Sunday=1 through Saturday=7).

            *Supported types*:

            .. container:: supported-types

                - INTEGER
                - INTEGER_ARRAY

    Returns:
        A formula representing the weekday(s).

        *Supported types*:

        .. container:: supported-types

            - INTEGER
            - INTEGER_ARRAY

    Raises:
        ValueError: If `date` is not DATE or DATE_ARRAY, or if `return_type` is outside the
                    allowed range or of invalid type and is determinable at compile time.

    Examples:
        Default numbering (Sunday=1 through Saturday=7):

        .. code-block:: python

            WEEKDAY(DATE("2025-09-03"))
            # Returns 4 (Wednesday)

        Monday=1 through Sunday=7:

        .. code-block:: python

            WEEKDAY(DATE("2025-09-03"), 2)
            # Returns 3 (Wednesday)

        Monday=0 through Sunday=6:

        .. code-block:: python

            WEEKDAY(DATE("2025-09-03"), 3)
            # Returns 2 (Wednesday)

    Note:
        - The return type follows the same format as Excel's WEEKDAY function.
          For details see: <https://support.microsoft.com/en-us/office/\
                    weekday-function-60e44483-2ed1-439f-8bd0-e404c190949a>
    """

    if return_type:
        if isinstance(return_type, int):
            if return_type not in range(1, 4) and return_type not in range(11, 18):
                raise ValueError(f"Return type: {return_type} is out of range.")

    if return_type:
        if isinstance(return_type, int):
            return WEEKDAY(date, CONST(return_type))

    date_data_type = date.to_data_type()
    if date_data_type not in DATE_AND_ARRAY_TYPES:
        raise ValueError(f"WEEKDAY invalid with the argument {date_data_type}")

    ret_data_type = DataType.INTEGER_ARRAY if date_data_type.is_array() else DataType.INTEGER

    if return_type:
        return_type_data_type = return_type.to_data_type()

        if return_type_data_type not in NUMERIC_AND_ARRAY_TYPES:
            raise ValueError(f"WEEKDAY invalid with the argument {return_type_data_type}")

        ret_data_type = (
            DataType.INTEGER
            if not return_type_data_type.is_array() and ret_data_type == DataType.INTEGER
            else DataType.INTEGER_ARRAY
        )
        return _WEEKDAY(ret_data_type, date.to_string(), return_type.to_string())

    return _WEEKDAY(ret_data_type, date.to_string())


def WEIBULL(x: Operand, shape: Operand, scale: Operand, cumulative: Operand) -> Formula:
    """
    Calculates the Weibull distribution probability density (PDF) or cumulative distribution (CDF).

    WEIBULL evaluates either the probability density function (PDF) or the cumulative
    distribution function (CDF) of the Weibull distribution for the given input(s).

    Arguments:
        x:
            The input value(s) at which to evaluate the distribution. Must be ≥ 0.

            *Supported types*:

            .. container:: supported-types

                - INTEGER
                - DECIMAL
                - INTEGER_ARRAY
                - DECIMAL_ARRAY

        shape:
            The shape parameter α (must be > 0). Determines the distribution shape:

            - α < 1: Decreasing failure rate
            - α = 1: Exponential distribution
            - α > 1: Increasing failure rate

            *Supported types*:

            .. container:: supported-types

                - INTEGER
                - DECIMAL
                - INTEGER_ARRAY
                - DECIMAL_ARRAY

        scale:
            The scale parameter β (must be > 0). Characteristic life parameter.

            *Supported types*:

            .. container:: supported-types

                - INTEGER
                - DECIMAL
                - INTEGER_ARRAY
                - DECIMAL_ARRAY

        cumulative:
            Boolean flag (or numeric 0/1) to determine calculation type:

            - False / 0: PDF
            - True / 1: CDF

            *Supported types*:

            .. container:: supported-types

                - BOOLEAN
                - BOOLEAN_ARRAY

    Returns:
        A formula object evaluating to the Weibull distribution value(s).

        - Returns DECIMAL if all inputs are scalar
        - Returns DECIMAL_ARRAY if any input is an array

        *Supported types*:

        .. container:: supported-types

            - DECIMAL
            - DECIMAL_ARRAY

    Raises:
        ValueError: If `x`, `shape`, or `scale` are not numeric types
        ValueError: If `cumulative` is not boolean-compatible

    Examples:
        Probability density function (PDF):

        .. code-block:: python

            WEIBULL(2, 1.5, 3, False)
            # Returns the PDF at x=2

        Cumulative distribution function (CDF):

        .. code-block:: python

            WEIBULL(2, 1.5, 3, True)
            # Returns the CDF at x=2

        Array inputs:

        .. code-block:: python

            WEIBULL([1, 2, 3], 1.5, 3, True)
            # Returns an array of CDF values at x=1,2,3
    """

    x_data_type = x.to_data_type()
    shape_data_type = shape.to_data_type()
    scale_data_type = scale.to_data_type()
    cumulative_data_type = cumulative.to_data_type()

    if (
        x_data_type not in NUMERIC_AND_ARRAY_TYPES
        or shape_data_type not in NUMERIC_AND_ARRAY_TYPES
        or scale_data_type not in NUMERIC_AND_ARRAY_TYPES
    ):
        raise ValueError(
            f"WEIBULL invalid with the argument {x_data_type}, "
            f"{shape_data_type} and {scale_data_type}"
        )

    if cumulative_data_type not in BOOLEANISH_AND_ARRAY_TYPES:
        raise ValueError(f"WEIBULL invalid with the argument {cumulative_data_type}")

    ret_data_type = DataType.DECIMAL
    if (
        x_data_type.is_array()
        or shape_data_type.is_array()
        or scale_data_type.is_array()
        or cumulative_data_type.is_array()
    ):
        ret_data_type = DataType.DECIMAL_ARRAY

    return _WEIBULL(
        ret_data_type, x.to_string(), shape.to_string(), scale.to_string(), cumulative.to_string()
    )


def COUNT(array: Operand, value: Operand | int | float | str | bool) -> Formula:
    """
    Counts the number of occurrences of a specified value in an array.

    COUNT evaluates the input array and returns the total number of times `value` appears.
    The value must be compatible with the data type of the array elements.

    Arguments:
        array:
            The array to search for occurrences of `value`. Must be a valid array type
            or object array.

            *Supported types*:

            .. container:: supported-types

                - BOOLEAN_ARRAY
                - INTEGER_ARRAY
                - DECIMAL_ARRAY
                - STRING_ARRAY
                - DATE_ARRAY
                - TIME_ARRAY
                - DATETIME_ARRAY
                - OBJECT_ARRAY

        value:
            The value to count in the array. Must have the same data type as the array elements.

            *Supported types*:

            .. container:: supported-types

                - BOOLEAN
                - INTEGER
                - DECIMAL
                - STRING
                - DATE
                - TIME
                - DATETIME
                - OBJECT

    Returns:
        A formula object evaluating to an INTEGER representing the count of `value` in `array`.

        *Supported types*:

        .. container:: supported-types

            - INTEGER

    Raises:
        ValueError: If `array` is not an array type
        ValueError: If `value` does not match the array element type

    Examples:
        Counting numeric occurrences:

        .. code-block:: python

            COUNT([1, 2, 1, 3, 1], 1)
            # Returns 3
            # Explanation: The value 1 occurs three times

        Counting string occurrences:

        .. code-block:: python

            COUNT(["A", "B", "A", "C"], "A")
            # Returns 2
            # Explanation: "A" appears twice in the array

        Counting boolean occurrences:

        .. code-block:: python

            COUNT([True, False, True, True], True)
            # Returns 3
    """

    if isinstance(value, int | float | str | bool):
        return COUNT(array, CONST(value))

    array_data_type = array.to_data_type()
    value_data_type = value.to_data_type()

    if isinstance(array_data_type, MapDataType) or isinstance(value_data_type, MapDataType):
        raise ValueError("COUNT is not supported with MapDataType")

    if not array_data_type.is_array():
        raise ValueError("'array' must be an array type in this method")

    if not isinstance(array_data_type, ObjectDataType):
        if array_data_type.from_array() != value_data_type:
            raise ValueError(
                f"COUNT is not supported with the datatypes {array_data_type}"
                f" and {value_data_type}"
            )
    elif not isinstance(value_data_type, ObjectDataType):
        raise ValueError(
            f"COUNT is not supported with the datatypes {array_data_type}" f" and {value_data_type}"
        )

    return _COUNT(array.to_string(), value.to_string())


def COUNTBLANKS(array: Operand) -> Formula:
    """
    Counts the number of blank elements in an array.

    COUNTBLANKS evaluates the input array and returns the total number of blank elements.
    A blank element is defined as either:

    1. A null value for any data type
    2. An empty string ("") for string arrays

    Arguments:
        array: The array to evaluate for blank elements. Must be a valid array type or object array.

            *Supported types*:

            .. container:: supported-types

                - BOOLEAN_ARRAY
                - INTEGER_ARRAY
                - DECIMAL_ARRAY
                - STRING_ARRAY
                - DATE_ARRAY
                - TIME_ARRAY
                - DATETIME_ARRAY
                - OBJECT_ARRAY

    Returns:
        A formula object evaluating to an INTEGER representing the number of blank elements
        in the array.

        *Supported types*:

        .. container:: supported-types

            - INTEGER

    Raises:
        ValueError: If `array` is not an array type

    Examples:
        Counting blanks in a numeric array:

        .. code-block:: python

            COUNTBLANKS([1, null, 3, null])
            # Returns 2
            # Explanation: Two null values are counted as blanks

        Counting blanks in a string array:

        .. code-block:: python

            COUNTBLANKS(["A", "", "B", null])
            # Returns 2
            # Explanation: Empty string and null are counted as blanks
    """
    array_data_type = array.to_data_type()

    if not array_data_type.is_array():
        raise ValueError(f"COUNTBLANKS is not compatible with data type {array_data_type}")

    return _COUNTBLANKS(array.to_string())


def COUNTDUPLICATES(
    array: Operand,
    include_first_instance: Operand | bool,
    ignore_blanks: Operand | bool,
) -> Formula:
    """
    Counts the number of duplicate elements in an array according to configurable rules.

    COUNTDUPLICATES evaluates an array and returns the total count of duplicates. The behaviour
    can be customised using `include_first_instance` and `ignore_blanks`.

    Arguments:
        array: The array to check for duplicates. Must be a valid array type or object array.

            *Supported types*:

            .. container:: supported-types

                - BOOLEAN_ARRAY
                - INTEGER_ARRAY
                - DECIMAL_ARRAY
                - STRING_ARRAY
                - DATE_ARRAY
                - TIME_ARRAY
                - DATETIME_ARRAY
                - OBJECT_ARRAY

        include_first_instance:  Determines whether the first occurrence of each duplicate should be
            included in the count. If True, first occurrence and duplicates are counted; if False,
            only subsequent duplicates are counted

            *Supported types*:

            .. container:: supported-types

                - BOOLEAN

        ignore_blanks:
            Determines whether blank values (null or empty strings) should be ignored in duplicate
                counting.

            *Supported types*:

            .. container:: supported-types

                - BOOLEAN

    Returns:
        A formula object evaluating to an INTEGER representing the count of duplicate elements
        according to the specified rules.

        *Supported types*:

        .. container:: supported-types

            - INTEGER

    Raises:
        ValueError: If `array` is not an array type
        ValueError: If `include_first_instance` or `ignore_blanks` is not BOOLEAN

    Examples:
        Counting duplicates including the first instance:

        .. code-block:: python

            COUNTDUPLICATES(
                ["A", "B", "A", "C"],
                include_first_instance=True,
                ignore_blanks=False
            )
            # Returns 2
            # Explanation:
            # - "A" occurs twice → both counted
            # - "B" and "C" occur once → not duplicates

        Counting duplicates excluding the first instance and ignoring blanks:

        .. code-block:: python

            COUNTDUPLICATES(
                ["A", "", "A"],
                include_first_instance=False,
                ignore_blanks=True
            )
            # Returns 1
            # Explanation:
            # - "A" occurs twice → only the second counted
            # - Blank ignored
    """

    if isinstance(include_first_instance, bool):
        return COUNTDUPLICATES(array, CONST(include_first_instance), ignore_blanks)
    if isinstance(ignore_blanks, bool):
        return COUNTDUPLICATES(array, include_first_instance, CONST(ignore_blanks))

    array_data_type = array.to_data_type()
    include_first_instance_type = include_first_instance.to_data_type()
    ignore_blanks_type = ignore_blanks.to_data_type()

    if not array_data_type.is_array():
        raise ValueError(f"'array' is not compatible with data type {array_data_type}")

    if include_first_instance_type != DataType.BOOLEAN or ignore_blanks_type != DataType.BOOLEAN:
        raise ValueError(
            f"'include_first_instance' and 'ignore_blanks' are not compatible with data types "
            f"{include_first_instance_type} and {ignore_blanks_type}"
        )

    return _COUNTDUPLICATES(
        array.to_string(), include_first_instance.to_string(), ignore_blanks.to_string()
    )


def BITMASKSTRING(array: Operand) -> Formula:
    """
    Converts a boolean array into a compact hexadecimal mask string representation.

    BITMASKSTRING encodes a BOOLEAN_ARRAY as a hexadecimal string, where each character
    represents 4 boolean values (bits). If the array length is not a multiple of 4, the last
    group is padded with zeros.

    Arguments:
        array:
            The boolean array to convert into a hexadecimal mask string.

            *Supported types*:

            .. container:: supported-types

                - BOOLEAN_ARRAY

    Returns:
        A formula object that evaluates to a hexadecimal string representing the boolean array.

        Characteristics:

        - Each character encodes 4 boolean values (0-9, A-F)
        - String length is ceil(array_length / 4)

        *Supported types*:

        .. container:: supported-types

            - STRING

    Raises:
        ValueError: If `array` is not a BOOLEAN_ARRAY

    Examples:
        Basic 4-bit conversion:

        .. code-block:: python

            BITMASKSTRING([True, False, True, False])
            # Returns "0A"
            # Explanation: Binary 1010 → Hex 0A

        Fewer than 4 bits (padded with zeros):

        .. code-block:: python

            BITMASKSTRING([True, True, True])
            # Returns "0E"
            # Explanation: Binary 1110 (last bit padded with 0) → Hex 0E
    """
    array_data_type = array.to_data_type()

    if array_data_type != DataType.BOOLEAN_ARRAY:
        raise ValueError(f"BITMASKSTRING is not supported with the data type {array_data_type}")

    return _BITMASKSTRING(array.to_string())


def DISTRIBUTE(value: Operand | int, array: Operand) -> Formula:
    """
    Distributes an integer value across a series of buckets with defined capacities.

    DISTRIBUTE allocates the input `value` to the buckets in a left-to-right manner,
    filling each bucket up to its specified capacity before moving to the next.

    Arguments:
        value:
            The total value to distribute. Can be an integer constant or a model object
            of type INTEGER.

            *Supported types*:

            .. container:: supported-types

                - INTEGER

        array:
            The bucket capacities. Must be an integer array where each element represents
            a bucket's maximum capacity.

            *Supported types*:

            .. container:: supported-types

                - INTEGER_ARRAY

    Returns:
        A formula object evaluating to an integer array where each element indicates
        the portion of `value` allocated to the corresponding bucket. The array length
        matches the input bucket array length.

        *Supported types*:

        .. container:: supported-types

            - INTEGER_ARRAY

    Raises:
        ValueError: If `value` is not an INTEGER
        ValueError: If `array` is not an INTEGER_ARRAY

    Examples:
        Basic full distribution:

        .. code-block:: python

            DISTRIBUTE(10, [5, 3, 2])
            # Returns [5, 3, 2]
            # Explanation:
            # 5 goes to first bucket (capacity 5)
            # 3 goes to second bucket (capacity 3)
            # 2 goes to third bucket (capacity 2)

        Partial filling:

        .. code-block:: python

            DISTRIBUTE(7, [5, 3, 2])
            # Returns [5, 2, 0]
            # Explanation:
            # 5 goes to first bucket
            # 2 goes to second bucket (capacity 3, only 2 remaining)
            # third bucket remains empty
    """
    if isinstance(value, int):
        return DISTRIBUTE(CONST(value), array)

    value_data_type = value.to_data_type()
    array_data_type = array.to_data_type()

    if value_data_type != DataType.INTEGER or array_data_type != DataType.INTEGER_ARRAY:
        raise ValueError(
            f"DISTRIBUTE is not supported with the data type {value_data_type}"
            f" and {array_data_type}"
        )

    return _DISTRIBUTE(value.to_string(), array.to_string())


def FINDDUPLICATES(
    array: Operand,
    include_first_instance: Operand | bool,
    ignore_blanks: Operand | bool,
) -> Formula:
    """
    Identifies duplicate elements in an array and returns a boolean array.

    FINDDUPLICATES scans `array` and returns a boolean array of the same length, where True
    indicates that the corresponding element is considered a duplicate. Behavior can be
    customised using `include_first_instance` and `ignore_blanks`.

    Arguments:
        array:
            The array to check for duplicates. Must be a valid array type or object array.

            *Supported types*:

            .. container:: supported-types

                - BOOLEAN_ARRAY
                - INTEGER_ARRAY
                - DECIMAL_ARRAY
                - STRING_ARRAY
                - DATE_ARRAY
                - TIME_ARRAY
                - DATETIME_ARRAY
                - OBJECT_ARRAY

        include_first_instance:
            Determines whether the first occurrence of a duplicate should be marked as True.
            If True, the first occurrence is included; if False, only subsequent duplicates are
            marked.

            *Supported types*:

            .. container:: supported-types

                - BOOLEAN

        ignore_blanks:
            Determines whether blank values (null or empty strings) should be ignored in duplicate
            detection.

            *Supported types*:

            .. container:: supported-types

                - BOOLEAN

    Returns:
        A formula object that evaluates to a boolean array of the same length as `array`, where
        True indicates a duplicate element according to the specified rules.

        *Supported types*:

        .. container:: supported-types

            - BOOLEAN_ARRAY

    Raises:
        ValueError:
            - If `array` is not an array type
            - If `include_first_instance` or `ignore_blanks` is not BOOLEAN

    Examples:
        Basic usage including first instance:

        .. code-block:: python

            FINDDUPLICATES(
                ["A", "B", "A", "C"],
                include_first_instance=True,
                ignore_blanks=False
            )
            # Returns [True, False, True, False]

        Excluding first instance:

        .. code-block:: python

            FINDDUPLICATES(
                ["A", "B", "A"],
                include_first_instance=False,
                ignore_blanks=False
            )
            # Returns [False, False, True]
    """
    if isinstance(include_first_instance, bool):
        return FINDDUPLICATES(array, CONST(include_first_instance), ignore_blanks)
    if isinstance(ignore_blanks, bool):
        return FINDDUPLICATES(array, include_first_instance, CONST(ignore_blanks))

    array_data_type = array.to_data_type()
    include_first_instance_type = include_first_instance.to_data_type()
    ignore_blanks_type = ignore_blanks.to_data_type()

    if not array_data_type.is_array():
        raise ValueError(f"'array' is not compatible with data type {array_data_type}")

    if include_first_instance_type != DataType.BOOLEAN or ignore_blanks_type != DataType.BOOLEAN:
        raise ValueError(
            f"'include_first_instance' and 'ignore_blanks' are not compatible with data types "
            f"{include_first_instance_type} and {ignore_blanks_type}"
        )

    return _FINDDUPLICATES(
        array.to_string(), include_first_instance.to_string(), ignore_blanks.to_string()
    )


def ROWVECTOR() -> Formula:
    """
    Generates a row position indicator vector for the current table context.

    ROWVECTOR creates a sparse integer array where a single element is set to 1 at the
    current row index, and all other elements are 0. If no table context is available,
    it returns an empty array.

    Returns:
        A formula object representing an integer array with the following behavior:

        - Length matches the number of rows in the current table context
        - Element at the current row index is 1
        - All other elements are 0
        - Returns an empty array if no table context is available

        *Supported types*:

        .. container:: supported-types

            - INTEGER_ARRAY

    Examples:
        Basic usage within a table context:

        .. code-block:: python

            # In a 4-row table, evaluating on row 2
            ROWVECTOR()
            # Returns [0, 1, 0, 0]

        No table context:

        .. code-block:: python

            ROWVECTOR()
            # Returns []
    """
    return _ROWVECTOR()


def ARRAYMAX(*values: Operand | int | float) -> Formula:
    """
    Returns the maximum value(s) across one or more numeric inputs or arrays.

    ARRAYMAX performs either a scalar maximum operation or an element-wise maximum operation
    depending on the input types:

    - *Scalar operation:* If all inputs are single values, returns the largest value.
    - *Element-wise array operation:* If any input is an array, performs a position-wise
      maximum across all inputs, broadcasting scalar values to match array lengths.

    Arguments:
        *values: One or more numeric values or arrays to compare. Each value must be one of the
            supported types. Mixed inputs (scalars and arrays) are allowed.

            *Supported types*:

            .. container:: supported-types

                - INTEGER
                - DECIMAL
                - INTEGER_ARRAY
                - DECIMAL_ARRAY

    Returns:
        A formula object representing the maximum scalar if all inputs are scalar values, an array
        of element-wise maximums if any input is an array. The return type is DECIMAL if any decimal
        input is present; otherwise INTEGER. Array outputs match the length of input arrays. All
        arrays must have equal length else an error value is returned.

        *Supported types*:

        .. container:: supported-types

            - INTEGER
            - DECIMAL
            - INTEGER_ARRAY
            - DECIMAL_ARRAY

    Raises:
        ValueError: If no input is provided.
        ValueError: If any input is not a supported numeric type.

    Examples:
        Basic scalar usage:

        .. code-block:: python

            ARRAYMAX(1, 5, 3)
            # Returns 5

        Element-wise array comparison:

        .. code-block:: python

            ARRAYMAX(
                [1, 2, 3],
                [4, 1, 2]
            )
            # Returns [4, 2, 3]

        Mixed scalar and array:

        .. code-block:: python

            ARRAYMAX(
                5,
                [2, 7, 4]
            )
            # Returns [5, 7, 5]
    """

    if not values:
        raise ValueError("At least one input is required")

    # Convert all inputs to `Operand` if necessary
    converted_fields = [field if isinstance(field, Operand) else CONST(field) for field in values]

    ret_data_type = DataType.INTEGER
    is_array = False
    for value in converted_fields:
        data_type = value.to_data_type()
        if data_type not in NUMERIC_AND_ARRAY_TYPES:
            raise ValueError(f"Datatype {data_type} is not a valid input for this method")
        if data_type in {DataType.DECIMAL, DataType.DECIMAL_ARRAY}:
            ret_data_type = DataType.DECIMAL
        if data_type.is_array():
            is_array = True

    ret_data_type = ret_data_type.to_array() if is_array else ret_data_type

    string_values = [value.to_string() for value in converted_fields]

    return _ARRAYMAX(ret_data_type, *string_values)


def ARRAYMIN(*values: Operand | int | float) -> Formula:
    """
    Returns the minimum value(s) across one or more numeric inputs or arrays.

    ARRAYMIN performs either a scalar minimum operation or an element-wise minimum operation
    depending on the input types:

    - *Scalar operation:* If all inputs are single values, returns the smallest value.
    - *Element-wise array operation:* If any input is an array, performs a position-wise
      minimum across all inputs, broadcasting scalar values to match array lengths.

    Arguments:
        *values:
            One or more numeric values or arrays to compare. Each value must be one of the
            supported types. Mixed inputs (scalars and arrays) are allowed.

            *Supported types*:

            .. container:: supported-types

                - INTEGER
                - DECIMAL
                - INTEGER_ARRAY
                - DECIMAL_ARRAY

    Returns:
        A formula object representing the minimum scalar if all inputs are scalar values, an array
        of element-wise minimums if any input is an array. The return type is DECIMAL if any decimal
        input is present; otherwise INTEGER. Array outputs match the length of input arrays. All
        arrays must have equal length else an error value is returned.

        *Supported types*:

        .. container:: supported-types

            - INTEGER
            - DECIMAL
            - INTEGER_ARRAY
            - DECIMAL_ARRAY

    Raises:
        ValueError: If no input is provided.
        ValueError: If any input is not a supported numeric type.

    Examples:
        Basic scalar usage:

        .. code-block:: python

            ARRAYMIN(1, 5, 3)
            # Returns 1

        Element-wise array comparison:

        .. code-block:: python

            ARRAYMIN(
                [1, 2, 3],
                [4, 1, 2]
            )
            # Returns [1, 1, 2]

        Mixed scalar and array:

        .. code-block:: python

            ARRAYMIN(
                5,
                [2, 7, 4]
            )
            # Returns [2, 5, 4]
    """
    if not values:
        raise ValueError("At least one input is required")

    # Convert all inputs to `Operand` if necessary
    converted_fields = [field if isinstance(field, Operand) else CONST(field) for field in values]

    ret_data_type = DataType.INTEGER
    is_array = False
    for value in converted_fields:
        data_type = value.to_data_type()
        if data_type not in NUMERIC_AND_ARRAY_TYPES:
            raise ValueError(f"Datatype {data_type} is not a valid input for this method")
        if data_type in {DataType.DECIMAL, DataType.DECIMAL_ARRAY}:
            ret_data_type = DataType.DECIMAL
        if data_type.is_array():
            is_array = True

    ret_data_type = ret_data_type.to_array() if is_array else ret_data_type

    string_values = [value.to_string() for value in converted_fields]

    return _ARRAYMIN(ret_data_type, *string_values)


def RANK(
    comparison_value: Operand | bool | int | float | str,
    array: Operand,
    ascending: bool | Operand = False,
) -> Formula:
    """
    Determines the rank of a value within an array, with support for ascending or descending order.

    The RANK function searches for `comparison_value` within `array` and returns its rank as a
    1-based integer. By default, ranks are assigned in descending order (largest value → rank 1).
    If `ascending` is True, ranks are assigned in ascending order (smallest value → rank 1).

    Null values in the array are treated as positive infinity (i.e., larger than any non-null
    value). If `comparison_value` is not found in the array, the formula evaluates to an error
    value.

    Arguments:
        comparison_value:
            The value to rank within the array. Must be a primitive (non-array) type compatible
            with the elements of `array`.

            *Supported types*:

            .. container:: supported-types

                - BOOLEAN
                - INTEGER
                - DECIMAL
                - STRING
                - DATE
                - TIME
                - DATETIME

        array:
            The array to search within. Must be an array of the same type as `comparison_value`.

            *Supported types*:

            .. container:: supported-types

                - BOOLEAN_ARRAY
                - INTEGER_ARRAY
                - DECIMAL_ARRAY
                - STRING_ARRAY
                - DATE_ARRAY
                - TIME_ARRAY
                - DATETIME_ARRAY

        ascending:
            Optional boolean indicating whether to rank in ascending order (True) or descending
            order (False). Defaults to False. Only BOOLEAN values are accepted; otherwise, a
            ValueError is raised.

            *Supported types*:

            .. container:: supported-types

                - BOOLEAN

    Returns:
        A formula object that evaluates to an INTEGER representing the 1-based rank of
        `comparison_value` within `array`.

        If `comparison_value` is not found, the formula evaluates to an error value.

        *Supported types*:

        .. container:: supported-types

            - INTEGER

    Raises:
        ValueError: If `array` is not an array type
        ValueError: If `comparison_value` type does not match the element type of `array`
        ValueError: If `ascending` is not a BOOLEAN

    Examples:
        Basic usage in descending order:

        .. code-block:: python

            RANK(3, [1, 4, 3, 3, 2])
            # Returns 2
            # Explanation: In descending order → [4, 3, 3, 2, 1]
            # The first 3 appears at position 2 → rank = 2

        Ranking a value not at the extremes:

        .. code-block:: python

            RANK(2, [1, 4, 3, 3, 2])
            # Returns 4
            # Explanation: In descending order → [4, 3, 3, 2, 1]
            # 2 appears at position 4 → rank = 4

        Using ascending order:

        .. code-block:: python

            RANK("B", ["A", "D", "B", "C"], ascending=True)
            # Returns 2
            # Explanation: In ascending order → ["A", "B", "C", "D"]
            # "B" appears at position 2 → rank = 2

        With boolean values:

        .. code-block:: python

            RANK(True, [False, True, True])
            # Returns 1
            # Explanation: In descending order → [True, True, False]
            # True is ranked highest → rank = 1

        Value not found in array:

        .. code-block:: python

            RANK(10, [1, 2, 3])
            # Evaluates to #ERROR
    """

    if isinstance(comparison_value, bool | int | float | str):
        return RANK(CONST(comparison_value), array, ascending)

    if isinstance(ascending, bool):
        return RANK(comparison_value, array, CONST(ascending))

    comparison_value_data_type = comparison_value.to_data_type()
    array_data_type = array.to_data_type()

    error_message = (
        f"RANK is not supported with the data types {comparison_value_data_type} "
        f"and {array_data_type}"
    )

    if isinstance(array_data_type, MapDataType | ObjectDataType) or isinstance(
        comparison_value_data_type, MapDataType | ObjectDataType
    ):
        raise ValueError(error_message)

    if comparison_value_data_type.is_array() or not array_data_type.is_array():
        raise ValueError(error_message)

    if comparison_value_data_type.to_array() != array_data_type:
        raise ValueError(error_message)

    if ascending.to_data_type() != DataType.BOOLEAN:
        raise ValueError(f"'ascending' is not compatible with data type {ascending.to_data_type()}")

    return _RANK(comparison_value.to_string(), array.to_string(), ascending.to_string())


def TOTIMEZONE(date_time: Operand, time_zone: Operand | str) -> Formula:
    """
    Converts a UTC datetime value (or array of datetimes) into a specified time zone.

    This formula assumes the input datetime(s) are expressed in Coordinated Universal Time (UTC)
    and shifts them into the specified local time zone. The time zone must be a valid IANA time
    zone identifier (see https://en.wikipedia.org/wiki/List_of_tz_database_time_zones). If the
    provided time zone is invalid (i.e., not in the tz database), the resulting formula will
    evaluate to an error value.

    Arguments:
        date_time:
            The datetime or array of datetimes expressed in UTC.

            *Supported types*:

            .. container:: supported-types

                - DATETIME
                - DATETIME_ARRAY

        time_zone:
            The time zone or array of time zones to convert the UTC datetime(s) into.

            *Supported types*:

            .. container:: supported-types

                - STRING
                - STRING_ARRAY

    Returns:
        A formula object that evaluates to the datetime (or array of datetimes if either input is
        an array type) converted from UTC into the specified time zone.

        *Supported types*:

        .. container:: supported-types

            - DATETIME
            - DATETIME_ARRAY

    Raises:
        ValueError: If either input is not a valid type.

    Examples:
        Basic usage with a single datetime:

        .. code-block:: python

            TOTIMEZONE(DATETIME(2024, 3, 10, 19, 0, 0), "America/New_York")
            # Returns 2024-03-10 15:00:00

        Using an array of datetimes with a single timezone:

        .. code-block:: python

            TOTIMEZONE(
                [
                    DATETIME(2024, 3, 10, 19, 0, 0),
                    DATETIME(2024, 6, 1, 13, 30, 0)
                ],
                "America/New_York"
            )
            # Returns [2024-03-10 15:00:00, 2024-06-01 09:30:00]

        Using a datetime with an array of time zones:

        .. code-block:: python

            TOTIMEZONE(
                DATETIME(2024, 3, 10, 19, 0, 0),
                ["America/New_York", "Europe/London"]
            )
            # Returns [2024-03-10 15:00:00, 2024-03-10 19:00:00]

        Invalid timezone:

        .. code-block:: python

            TOTIMEZONE(DATETIME(2024, 3, 10, 19, 0, 0), "Invalid/Zone")
            # Evaluates to #ERROR
    """
    if isinstance(time_zone, str):
        return TOTIMEZONE(date_time, CONST(time_zone))

    date_time_type = date_time.to_data_type()
    time_zone_type = time_zone.to_data_type()

    error_message = (
        f"TOTIMEZONE is not supported with the data types " f"{date_time_type} and {time_zone_type}"
    )

    if date_time_type not in [DataType.DATETIME, DataType.DATETIME_ARRAY]:
        raise ValueError(error_message)
    if time_zone_type not in [DataType.STRING, DataType.STRING_ARRAY]:
        raise ValueError(error_message)

    is_array = date_time_type.is_array() or time_zone_type.is_array()

    return _TOTIMEZONE(is_array, date_time.to_string(), time_zone.to_string())


def FROMTIMEZONE(date_time: Operand, time_zone: Operand | str) -> Formula:
    """
    Converts a datetime value (or array of datetimes) in a specified time zone into UTC time.

    This formula assumes the input datetime(s) are expressed in the specified local time of the
    given IANA time zone identifier (see
    https://en.wikipedia.org/wiki/List_of_tz_database_time_zones) and shifts them to UTC time.
    If the provided time zone is invalid (i.e., not in the tz database), the resulting
    Formula will evaluate to an error value.

    Arguments:
        date_time: The datetime or array of datetimes in the specified time zone.

            *Supported types*:

            .. container:: supported-types

                - DATETIME
                - DATETIME_ARRAY

        time_zone: The timezone or array of timezones the specified datetimes are in.

            *Supported types*:

            .. container:: supported-types

                - STRING
                - STRING_ARRAY

    Returns:
        A formula object that evaluates to the datetime (or array of datetimes if either input is
        an array type) converted to UTC time.

        *Supported types*:

        .. container:: supported-types

            - DATETIME
            - DATETIME_ARRAY

    Raises:
        ValueError: If either input is not a valid type

    Examples:
        Basic usage with a single datetime:

        .. code-block:: python

            FROMTIMEZONE(DATETIME(2024, 3, 10, 15, 0, 0), "America/New_York")
            # Returns 2024-03-10 19:00:00 UTC

        Using an array of datetimes with a single timezone:

        .. code-block:: python

            FROMTIMEZONE(
                [
                    DATETIME(2024, 3, 10, 15, 0, 0),
                    DATETIME(2024, 6, 1, 9, 30, 0)
                ],
                "America/New_York"
            )
            # Returns [2024-03-10 19:00:00 UTC, 2024-06-01 13:30:00 UTC]

        Using a datetime with an array of time zones:

        .. code-block:: python

            FROMTIMEZONE(
                DATETIME(2024, 3, 10, 15, 0, 0),
                ["America/New_York", "Europe/London"]
            )
            # Returns [2024-03-10 19:00:00 UTC, 2024-03-10 15:00:00 UTC]

        Invalid timezone:

        .. code-block:: python

            FROMTIMEZONE(DATETIME(2024, 3, 10, 15, 0, 0), "Invalid/Zone")
            # Evaluates to #ERROR
    """
    if isinstance(time_zone, str):
        return FROMTIMEZONE(date_time, CONST(time_zone))

    date_time_type = date_time.to_data_type()
    time_zone_type = time_zone.to_data_type()

    error_message = (
        f"FROMTIMEZONE is not supported with the data types "
        f"{date_time_type} and {time_zone_type}"
    )

    if date_time_type not in [DataType.DATETIME, DataType.DATETIME_ARRAY]:
        raise ValueError(error_message)
    if time_zone_type not in [DataType.STRING, DataType.STRING_ARRAY]:
        raise ValueError(error_message)

    is_array = date_time_type.is_array() or time_zone_type.is_array()

    return _FROMTIMEZONE(is_array, date_time.to_string(), time_zone.to_string())


def TOMAP(array: Operand, table: Table) -> Formula:
    """
    Converts an array of values into a map keyed by table rows.

    This formula takes an array object and a table, and constructs a map where
    each row of the table is used as a key and the corresponding element of the
    array is used as the value. The array must have the same length as the number
    of rows in the table. If the lengths do not match, the formula evaluates to
    an error value.

    Arguments:
        array: The array of values to convert to a map.

            *Supported types*:

            .. container:: supported-types

                - BOOLEAN_ARRAY
                - INTEGER_ARRAY
                - DECIMAL_ARRAY
                - STRING_ARRAY
                - DATE_ARRAY
                - TIME_ARRAY
                - DATETIME_ARRAY

        table: The table whose rows will be used as keys.

            *Supported types*:

            .. container:: supported-types

                - TABLE

    Returns:
        A formula object that evaluates to a map whose keys are the rows of the
        given table and whose values come from the provided array.

        *Supported types*:

        .. container:: supported-types

            - BOOLEAN_MAP
            - INTEGER_MAP
            - DECIMAL_MAP
            - STRING_MAP
            - DATE_MAP
            - TIME_MAP
            - DATETIME_MAP

    Raises:
        ValueError: If either input is not a valid type.

    Examples:
        Using a string array:

        .. code-block:: python

            TOMAP(["A", "B", "C"], MyTable)
            # Returns a map from table rows to strings

        Mismatched array and table sizes:

        .. code-block:: python

            TOMAP([1, 2], MyTable)
            # Evaluates to #ERROR
    """
    array_data_type = array.to_data_type()

    if not array_data_type.is_array():
        raise ValueError(f"'array' is not compatible with data type {array.to_data_type()}")

    ret_data_type = MapDataType(cast(DataType, array_data_type.from_array()), table)

    return _TOMAP(ret_data_type, array.to_string(), table.id)
