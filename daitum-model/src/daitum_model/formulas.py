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

from typing import Any

from typeguard import typechecked

from daitum_model import (
    BaseDataType,
    Baseline,
    Calculation,
    DataType,
    Field,
    Formula,
    ObjectDataType,
    Parameter,
    Table,
    _functions,
)

# ``CONST`` is part of the public ``daitum_model.formulas`` surface (an uppercase formula function
# recognised by the docs reflector and imported by callers), so it is re-exported here.
from daitum_model.formula import CONST, Constant, Operand  # noqa: F401

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


def _is_object_array(x: Operand) -> bool:
    """Whether *x* is an ``OBJECT_ARRAY`` operand.

    A bare :class:`~daitum_model.Table` qualifies because, as an operand, its data type is an
    ``OBJECT_ARRAY`` over itself (see :meth:`Table.to_data_type`) — so tables and object-array
    fields flow through the same path with no special-casing.
    """
    data_type = x.to_data_type()
    return data_type.is_array() if isinstance(data_type, ObjectDataType) else False


def LOOKUP(
    table: Operand,
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

        field_name:
            The field name of the column to match against the condition. Must exist in `table`.
            If the field does not exist, the formula evaluates to an error. If a raw string is
            provided (rather than a formula), the method verifies that the field exists in the
            table, and raises a ValueError otherwise.

        condition:
            The condition value to search for within the specified column. Must be compatible with
            the column's data type. If the value is not found the formula evaluates to an error.

        reverse_search:
            Optional. If True, the search starts from the last row and moves backward toward the
            first row. Defaults to False. Only BOOLEAN values are accepted; otherwise, a ValueError
            is raised.


    Returns:
        The row in the table where the specified field equals the condition. If no row matches,
        the formula evaluates to an error.


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
    return _functions.Lookup(table, field_name, condition, reverse_search)


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

        lookup_array:
            The array in which to search for `lookup_value`. Must be a valid array type and
            compatible with the data type of `lookup_value`. If the array is blank or in an error
            state, the formula will evaluate to an error.

        reverse_search:
             Optional. If True, the search starts from the end of the array and moves backward.
             Defaults to False. Only BOOLEAN values are accepted; otherwise, a ValueError is raised.


    Returns:
        The 1-based index of the array where the match is found. If the value is not found, the
        formula will evaluate to an error.


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
    return _functions.Match(lookup_value, lookup_array, reverse_search)


def ROWS(array: Operand) -> Formula:
    """
    The ROWS function returns the number of rows in a specified table or array. If the input is
    blank or in an error state, the formula evaluates to an error. Only valid tables or array types
    are accepted.

    Arguments:
        array:
            The table or array for which to count the number of rows. Must be a valid table or array
            type. If the input is blank or in an error state, the formula evaluates to an error.


    Returns:
        The total number of rows in the specified table or array. If the input is invalid, blank, or
        in an error state, the formula evaluates to an error.


    Raises:
        ValueError: if the input is not a valid table or array type.

    Examples:
        .. code-block:: python

            ROWS(my_table)
            # Returns the number of rows in my_table
    """
    return _functions.Rows(array)


def SUM(*values: Operand | int | float) -> Formula:
    """
    Calculates the sum of one or more numeric values.

    This formula computes the total of the specified values. Each input must be an int, float,
    or a Operand whose data type is numeric (INTEGER, INTEGER_ARRAY, DECIMAL, DECIMAL_ARRAY).
    If any input is blank or in an error state, the formula evaluates to an error.

    Arguments:
        *values:
            One or more arguments to be summed.


    Returns:
        The total sum of the specified values. If all inputs are integers, the result is INTEGER.
        If any input is DECIMAL or DECIMAL_ARRAY, the result is DECIMAL.


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

    return _functions.Sum(*values)


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


        exponent:
            The exponent to which the mantissa is raised.


    Returns:
        The result of the exponentiation.

    """
    return _functions.Power(mantissa, exponent)


def ROW() -> Formula:
    """
    Returns the row number of the current table row.

    The ROW function mimics the behaviour of Excel's ROW function. It returns the 1-based index of
    the current row when evaluated in a table. If no table context is available (for example, when
    used in a named value), the formula evaluates to an error.

    Arguments:
        None.

    Returns:
        The 1-based row index of the current table.


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
    return Constant(DataType.INTEGER, "ROW()")


def IF(
    condition: Operand | bool | int,
    true_branch: Operand | bool | int | float | str,
    false_branch: Operand | bool | int | float | str,
) -> Formula:
    """
    Returns one of two values depending on the evaluation of a condition.

    This function mimics the behaviour of the Excel IF function. It evaluates the condition, and if
    true, returns the value of `true_branch`; otherwise, it returns the value of `false_branch`. If
    any input is blank or in an error state, the formula evaluates to an error.

    Arguments:
        condition:
            The condition to evaluate.


        true_branch:
            The value to return if the condition is true. Must be the same data type as
            `false_branch`, or NULL.


        false_branch:
            The value to return if the condition is false. Must be the same data type as
            `true_branch`, or NULL.


    Returns:
        Either `true_branch` or `false_branch`, depending on the condition.


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
    return _functions.If(condition, true_branch, false_branch)


def FIND(
    match_string: Operand | str,
    search_string: Operand | str,
    start_index: Operand | int | None = None,
) -> Formula:
    """
    Returns the starting position of a substring within a string.

    This function mimics the behaviour of the Excel FIND function. It searches for the first
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


        search_string:
            The string within which to search for `match_string`. Must be a valid string or string
            array. If blank or in an error state, the formula evaluates to an error.


        start_index:
            Optional. The 1-based position to start searching from. Defaults to 1 if not provided.


    Returns:
        Returns the index within this string of the first occurrence of the specified substring,
        starting at `start_index` if specified, otherwise 1. If the substring is not found, the
        formula evaluates to 0.


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
    return _functions.Find(match_string, search_string, start_index)


def LEFT(
    input_string: Operand | str,
    length: Operand | int,
) -> Formula:
    """
    Returns a substring consisting of the leftmost characters from a string.

    This function mimics the behaviour of Excel's LEFT function. It extracts a substring
    from the start of `input_string`, up to the number of characters specified by `length`.
    Both singular values and arrays are supported. If any argument is blank or in an error
    state, the formula evaluates to an error.

    Arguments:
        input_string:
            The string from which characters will be extracted. Can be a literal string,
            a field, formula, calculation, or parameter.


        length:
            The number of characters to extract from the left of `input_string`. If negative, the
            formula evaluates to an error.


    Returns:
        The substring consisting of the leftmost characters of `input_string` up to `index`.
        If either input is an array, an array of substrings is returned.


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
    return _functions.Left(input_string, length)


def RIGHT(
    input_string: Operand | str,
    length: Operand | int,
) -> Formula:
    """
    Returns a substring consisting of the rightmost characters from a string.

    This function mimics the behaviour of Excel's RIGHT function. It extracts a substring
    from the end of `input_string`, searching backwards up to the number of characters specified by
    `length`. Both singular values and arrays are supported. If any argument is blank or in an error
    state, the formula evaluates to an error.

    Arguments:
        input_string:
            The string from which characters will be extracted. Can be a literal string,
            a field, formula, calculation, or parameter.


        length:
            The number of characters to extract from the right of `input_string`. If negative, the
            formula evaluates to an error.


    Returns:
        The substring consisting of the rightmost characters of `input_string` up to `index`.
        If either input is an array, an array of substrings is returned.


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
    return _functions.Right(input_string, length)


def PREV(field: Operand) -> Formula:
    """
    Returns the previous value of a field within a table.

    When used in a table, it retrieves the value of `field` from the previous row. If used
    outside a table context or if there is no previous row, the formula evaluates to an error.

    Arguments:
        field:
            The field whose previous value is to be retrieved. If a formula is provided, PREV will
            evaluate it for the previous row.


    Returns:
        The value of `field` from the preceding row in the table.

    """
    return _functions.Prev(field)


def NEXT(field: Operand) -> Formula:
    """
    Returns the next value of a field within a table.

    When used in a table, it retrieves the value of `field` from the next row. If used
    outside a table context or if there is no next row, the formula evaluates to an error.

    Arguments:
        field:
            The field whose next value is to be retrieved. If a formula is provided, PREV will
            evaluate it for the next row.


    Returns:
        The value of `field` from the next row in the table.

    """
    return _functions.Next(field)


def TEXT(value: Operand, formatting: Operand | str | None = None) -> Formula:
    """
    Converts a field or value to its text representation with optional formatting.

    This function mimics the behaviour of Excel's TEXT function. It converts `value` to a string,
    optionally applying a formatting pattern. Both singular values and arrays are supported. If any
    argument is blank or in an error state, the formula evaluates to an error.

    Arguments:
        value:
            The value or field to convert to text.


        formatting:
            Optional. A string or field that specifies the text format to apply to `value`.
            If provided, must be a string or string array. Defaults to no formatting.


    Returns:
        The text representation of `value`, optionally formatted. Returns an array if `value` or
        `formatting` is an array.


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
    return _functions.Text(value, formatting)


def BLANK(
    data_type: BaseDataType | None = None,
) -> Formula:
    """
    Returns a blank value of the specified data type.

    This function creates a blank entry in a model or formula. By default, the blank value has type
    NULL, but a specific data type can be provided. Useful for setting default values or error
    cases.

    Arguments:
        data_type (BaseDataType):
            Optional. The data type of the blank value. Defaults to NULL if not specified.

    Returns:
        A blank value of the specified data type.


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
    return _functions.Blank(data_type)


def ISBLANK(value: Operand) -> Formula:
    """
    Returns True if the input value is blank, otherwise False.

    This function checks whether `value` is blank (empty or NULL). It evaluates to
    a boolean formula, making it useful for conditional logic and null-checking
    within models. Both singular values and arrays are supported.

    Arguments:
        value:
            The value to check if blank.


    Returns:
        True if `value` is blank, False otherwise. Returns an array of boolean values if `value` is
        an array.


    Examples:
        .. code-block:: python

            ISBLANK(customer["email"])
            # Returns True if email is blank, else False
    """
    return _functions.IsBlank(value)


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


        blank_branch:
            The value to return if `value` is blank. Must be compatible with the data type
            of `value` (or NULL).


    Returns:
        Either `blank_branch` if `value` is blank, or the original `value` otherwise.


    Raises:
        ValueError: If `value` and `blank_branch` have incompatible data types.
        ValueError: If both `value` and `blank_branch` have data type NULL.

    Examples:
        .. code-block:: python

            IFBLANK(order["discount"], order["default_discount"])
            # Returns the discount if present, else default_discount
    """
    return _functions.IfBlank(value, blank_branch)


def FILTER(
    array: Operand,
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


        filter_condition:
            An array representing which elements or rows to include. Must be of type
            BOOLEAN_ARRAY, INTEGER_ARRAY, or DECIMAL_ARRAY. If a non-boolean type is used, the
            value is treated as True if non-zero, False if zero.


    Returns:
        A filtered array containing only elements or rows that meet the `filter_condition`.
        Returns an array of the same type as `array` or an object array for tables.


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
    return _functions.Filter(array, filter_condition)


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


    Returns:
        The minimum value among the inputs.


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
    return _functions.Min(*values)


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


    Returns:
        The maximum value among the inputs.


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
    return _functions.Max(*values)


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


    Returns:
        True if any input is True, False otherwise. Evaluates to an error value if any input is null
        or in an error state. If a single array input is provided, returns scalar value representing
        the OR across all elements in the array. If multiple arrays are provided, returns an array
        where each element is the OR of the corresponding elements across all input arrays.


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
    return _functions.Or(*values)


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


    Returns:
        False if any input is False, True otherwise. Evaluates to an error value if any input is
        null or in an error state. If a single array input is provided, returns scalar value
        representing the AND across all elements in the array. If multiple arrays are provided,
        returns an array where each element is the AND of the corresponding elements across all
        input arrays.


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
    return _functions.And(*values)


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


    Returns:
        The logical negation of the input. Returns an array if the input is an array.


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
    return _functions.Not(value)


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


    Returns:
        An integer whose binary representation encodes the boolean array.


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
    return _functions.Bitmask(value)


def VALUES(value: Operand) -> Formula:
    """
    Extracts the values from a map and returns them as an array.

    The VALUES function takes a model component with a map data type and converts its values into
    an array.

    Arguments:
        value:
            A model component of type `MapDataType` whose values will be extracted.


    Returns:
        An array containing the values of the map.


    Raises:
        ValueError: if the input is not of type `MapDataType`.

    Examples:
        Extracting values from a map:

        .. code-block:: python

            VALUES(my_map)
            # Returns ["a", "b", "c"] for a map {0: "a", 1: "b", 2: "c"}
    """
    return _functions.Values(value)


def CONTAINS(search_array: Operand, search_value: Operand | bool | str | float | int) -> Formula:
    """
    Checks whether one or more values exist within an array.

    The CONTAINS function determines whether a given value or model component is present in
    the specified array. When `search_value` is a single value it returns a boolean result
    (`True` if the value is found, `False` otherwise). When `search_value` is an array it returns
    a BOOLEAN_ARRAY, with one entry per element of `search_value` indicating whether that element
    is present in `search_array`. If either input is blank or in an error state, the formula
    evaluates to an error.

    Arguments:
        search_array:
            The array to search through. Must be an array type and compatible with the element
            type of `search_value`.


        search_value:
            The value or values to search for within the array. Either the singular type
            corresponding to the `search_array` element type (for example, INTEGER for
            INTEGER_ARRAY) or an array of that element type (for example, INTEGER_ARRAY).
            A ValueError is raised if the element type does not match.


    Returns:
        A BOOLEAN when `search_value` is a single value, or a BOOLEAN_ARRAY when `search_value`
        is an array, indicating for each searched value whether it is found in `search_array`.


    Raises:
        ValueError: If `search_array` is not an array type.
        ValueError: If the element type of `search_array` does not match the (element) type of
            `search_value`.

    Examples:
        Basic usage:

        .. code-block:: python

            CONTAINS([1, 2, 3], 2)
            # Returns True

        Searching for multiple values:

        .. code-block:: python

            CONTAINS([1, 2, 3], [2, 5])
            # Returns [True, False]

        Using a model component:

        .. code-block:: python

            CONTAINS(my_array_field, my_value_field)
            # Returns True if my_value_field exists in my_array_field
    """
    return _functions.Contains(search_array, search_value)


def INDEX(array: Operand, index: Operand | int) -> Formula:
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


        index:
            The 1-based index of the element or row to retrieve. Must be an INTEGER or INTEGER_ARRAY
            value. If the index is not INTEGER or INTEGER_ARRAY, a ValueError is raised. If the
            index is less than 1 or greater than the size of the array, the formula evaluates to an
            error.


    Returns:
        The element or row at the specified index. If the array is OBJECT_ARRAY or Table, the result
        is an object type. If the array is a primitive ARRAY, the result is the corresponding
        singular type.


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
    return _functions.Index(array, index)


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


    Returns:
        The total number of elements in the input array, returned as an INTEGER Formula.


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
    return _functions.Size(array)


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


        days:
            The number of days to add to `date`. Can be a single integer or an array of integers.


    Returns:
        The resulting date after adding the specified number of days. The type of the result
        matches the input `date`, unless `days` is an array, in which case the result will be the
        array version of the `date` type.


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
    return _functions.PlusDays(date, days)


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


    Returns:
        The rounded integer value(s). The result matches the input type: scalar input
        returns a single integer, array input returns an integer array.


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
    return _functions.Round(value)


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


    Returns:
        The integer value(s) representing the floor of the input. The result matches the input
        type: scalar input returns a single integer, array input returns an integer array.


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
    return _functions.Floor(value)


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


    Returns:
        The integer value(s) representing the ceiling of the input. The result matches the input
        type: scalar input returns a single integer, array input returns an integer array.


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
    return _functions.Ceiling(value)


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


        divisor:
            The value to divide by.


    Returns:
        The remainder of the division `number % divisor`.


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
    return _functions.Mod(number, divisor)


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


        error_branch:
            The value to return if the formula evaluates to an error. If not of the same data type
            as `formula`, or `NULL`, a ValueError is raised.


    Returns:
        The result of the formula if no error occurs, otherwise the `error_branch` value.


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
    return _functions.IfError(formula, error_branch)


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


        second_date:
            The ending date or array of dates.


    Returns:
        The number of days between the two dates. If input arrays have unequal lengths the returned
        formula will evaluate to an error.


    Raises:
        ValueError: If either input is not a date or datetime type.

    Examples:
        .. code-block:: python

            DAYSBETWEEN(DATE(2025, 1, 1), DATE(2025, 1, 10))
            # Returns 9
    """
    return _functions.DaysBetween(first_date, second_date)


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


    Returns:
        The year as an integer or array of integers.


    Raises:
        ValueError: If the input is not a date or datetime type.

    Examples:
        .. code-block:: python

            YEAR(DATE(2025, 9, 3))
            # Returns 2025
    """
    return _functions.Year(date)


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


    Returns:
        The month as an integer or array of integers.


    Raises:
        ValueError: If the input is not a date or datetime type.

    Examples:
        .. code-block:: python

            MONTH(DATE(2025, 9, 3))
            # Returns 9
    """
    return _functions.Month(date)


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


    Returns:
        The day as an integer or array of integers.


    Raises:
        ValueError: If the input is not a date or datetime type.

    Examples:
        .. code-block:: python

            DAY(DATE(2025, 9, 3))
            # Returns 3
    """
    return _functions.Day(date)


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

        month:
            The month component of the date (1–12).

        day:
            The day component of the date.


    Returns:
        A `Formula` object representing the constructed date. If the inputs do not form a valid
        date, the formula will evaluate to an error.


    Raises:
        ValueError: If any input is not numeric or an array of numeric values.
    """
    return _functions.Date(year, month, day)


def DATETIME(  # noqa: PLR0913, PLR0917
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

        month:
            The month component (1–12).

        day:
            The day component.

        hours:
            The hour component (0–23).

        minutes:
            The minute component (0–59).

        seconds:
            The second component (0–59).


    Returns:
        A `Formula` object representing the constructed datetime. If the inputs do not form a valid
        date/time, the formula will evaluate to an error.


    Raises:
        ValueError: If any input is not numeric or an array of numeric values.
    """
    return _functions.DateTime(year, month, day, hours, minutes, seconds)


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

        months:
            Optional. The number of months to offset from the month of `date`. Can be a scalar or
            array. Defaults to 0.


    Returns:
        The end-of-month date after applying the month offset. The result has the same shape
        (scalar or array) as the inputs.


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
    return _functions.EoMonth(date, months)


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

        field_2:
            The second value in the BITAND operation. Interpreted as a string of bits (either the
            binary representation of the integer value or hexadecimal string). If an array type, the
            operation is performed element-wise and the return will also be an array type.


    Returns:
        A `Formula` object representing the bitwise AND result of the two inputs. If either input
        is an array type, the return will also be an array type. If both inputs are strings, the
        return type will also be a string; otherwise, it will be an integer. If either input is
        blank or in an error state, the formula evaluates to an error.


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
    return _functions.BitAnd(field_1, field_2)


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

        field_2:
            The second value in the BITOR operation. Interpreted as a string of bits (either the
            binary representation of the integer value or hexadecimal string). If an array type, the
            operation is performed element-wise and the return will also be an array type.


    Returns:
        A `Formula` object representing the bitwise OR result of the two inputs. If either input
        is an array type, the return will also be an array type. If both inputs are strings, the
        return type will also be a string; otherwise, it will be an integer. If either input is
        blank or in an error state, the formula evaluates to an error.


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
    return _functions.BitOr(field_1, field_2)


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

        minutes:
            The minutes component of the time (0–59).

        seconds:
            The seconds component of the time (0–59).


    Returns:
        A `Formula` object representing the constructed time. The result is an array if any input
        is an array; otherwise, it is a scalar. If the inputs do not form a valid time, the formula
        will evaluate to an error.


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
    return _functions.Time(hours, minutes, seconds)


def SETTIME(date: Operand, time: Operand) -> Formula:
    """
    Combines a date and a time into a single datetime value.

    The SETTIME function constructs a DATETIME formula by combining the provided `date`
    with the specified `time`. If any input is an array, the function will operate element-wise
    and produce a DATETIME_ARRAY.

    Arguments:
        date:
            The date component. Can be a scalar date or DATE_ARRAY.

        time:
            The time component.


    Returns:
        A `Formula` object representing the combined date and time. Returns an array if any
        input is an array; otherwise, a scalar DATETIME.


    Raises:
        ValueError: If the `date` is not of type DATE/DATE_ARRAY/DATETIME/DATETIME_ARRAY or
        `time` is not of type TIME/TIME_ARRAY.

    Examples:
        .. code-block:: python

            SETTIME(DATE(2025, 9, 3), TIME(14, 30, 0))
            # Returns a DATETIME representing 2025-09-03 14:30:00
    """
    return _functions.SetTime(date, time)


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

        minutes:
            The number of minutes to add. Can be a scalar integer or INTEGER_ARRAY. If negative, the
            minutes are subtracted.


    Returns:
        A `Formula` object representing the time or datetime after adding the specified
        minutes. Returns an array if any input is an array; otherwise, a scalar DATE, TIME or
        DATETIME.


    Raises:
        ValueError: If the `time` input is not a valid DATE/TIME/DATETIME type or if `minutes`
        is not an integer type.

    Examples:
        .. code-block:: python

            PLUSMINUTES(TIME(14, 30, 0), 45)
            # Returns a TIME representing 15:15:00
    """
    return _functions.PlusMinutes(time, minutes)


def CHOOSE(index: Operand | int, *values: Operand | str | int | float | bool) -> Formula:
    """
    Returns the value at a specified index from a list of inputs.

    The CHOOSE function selects a value from the provided `values` based on the 1-based
    `index`. If the index is out of range, the formula will evaluate to an error.
    All input values must be of the same data type.

    Arguments:
        index:
            The position of the value to select. Indexing starts at 1.


        *values:
            An arbitrary number of values to choose from. All values must share the same
            data type.


    Returns:
        A `Formula` object representing the selected value.


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
    return _functions.Choose(index, *values)


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


        *fields:
            An arbitrary number of scalar values, model components, or BLANK() values to include
            in the array. All non-BLANK fields must share the same data type and cannot be
            MapDataTypes. At least one non-BLANK field must be provided to determine the array
            data type.


    Returns:
        A `Formula` object representing the constructed array.


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
    return _functions.Array(ignore_null, *fields)


def ABS(value: int | float | Operand) -> Formula:
    """
    Returns the absolute value of a number or numeric array.

    The ABS function computes the absolute value of the input. For scalar numbers, it returns
    the positive equivalent. For array inputs the absolute value is computed element-wise and an
    array type is returned.

    Arguments:
        value: The numeric input whose absolute value is to be computed.


    Returns:
        A `Formula` object representing the absolute value of the input. For arrays,
        the absolute value is computed element-wise.


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
    return _functions.Abs(value)


def GET(map_object: Operand, key: Operand) -> Formula:
    """
    Retrieves the value associated with a specified key from a map field.

    The GET function looks up a key in a MAP-type `Operand` and returns the corresponding
    value. The key must be a singular OBJECT reference to the same source table as the map.

    Arguments:
        map_object:
            The MAP-type model component containing key-value pairs.

        key:
            The OBJECT-type key whose associated value is to be retrieved. Must reference the same
            table as the map and cannot be an array.


    Returns:
        A `Formula` object representing the value associated with the specified key. The data type
        will match the underlying data type of the map's values. If the key does not exist in the,
        the formula will evaluate to an error.


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
    return _functions.Get(map_object, key)


def EXP(value: int | float | Operand) -> Formula:
    """
    Computes the exponential (e^x) of a given number or numeric array.

    This function calculates the natural exponential of a given number or array of numbers. If an
    array of numbers is provided, the exponential is calculated for each element individually. If
    the input is blank or in an error state, the formula will evaluate to an error.

    Arguments:
        value:
            The numeric input to exponentiate.


    Returns:
        A `Formula` object representing the computed exponential.


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
    return _functions.Exp(value)


def LOG(value: int | float | Operand) -> Formula:
    """
    Computes the natural logarithm (ln) of a given number or numeric array.

    This function calculates the natural logarithm (base e) of a given number or array of numbers.
    If an array of numbers is provided, the natural logarithm is calculated for each element
    individually. The input must be strictly positive; if the input is zero, negative, blank, or
    in an error state, the formula will evaluate to an error.

    Arguments:
        value:
            The numeric input whose natural logarithm is to be computed.


    Returns:
        A `Formula` object representing the computed natural logarithm.


    Raises:
        ValueError: If `value` is not a numeric type or a numeric array.

    Examples:
        Basic usage with a scalar:

        .. code-block:: python

            LOG(1)
            # Returns 0.0

        Usage with a model object:

        .. code-block:: python

            LOG(my_numeric_field)
            # Returns a formula representing the natural logarithm of `my_numeric_field`

        Usage with an array:

        .. code-block:: python

            LOG([1, 2.718281828, 7.389056099])
            # Returns [0.0, 1.0, 2.0] approximately
    """
    return _functions.Log(value)


def SIN(value: int | float | Operand) -> Formula:
    """
    Computes the sine of a given number or numeric array.

    This function calculates the trigonometric sine of a given number or array of numbers, where
    the input is interpreted in radians. If an array of numbers is provided, the sine is
    calculated for each element individually. If the input is blank or in an error state, the
    formula will evaluate to an error.

    Arguments:
        value:
            The numeric input, in radians, whose sine is to be computed.


    Returns:
        A `Formula` object representing the computed sine.


    Raises:
        ValueError: If `value` is not a numeric type or a numeric array.

    Examples:
        Basic usage with a scalar:

        .. code-block:: python

            SIN(0)
            # Returns 0.0

        Usage with a model object:

        .. code-block:: python

            SIN(my_numeric_field)
            # Returns a formula representing the sine of `my_numeric_field` (in radians)

        Usage with an array:

        .. code-block:: python

            SIN([0, 1.5707963, 3.1415927])
            # Returns [0.0, 1.0, 0.0] approximately
    """
    return _functions.Sin(value)


def COS(value: int | float | Operand) -> Formula:
    """
    Computes the cosine of a given number or numeric array.

    This function calculates the trigonometric cosine of a given number or array of numbers,
    where the input is interpreted in radians. If an array of numbers is provided, the cosine is
    calculated for each element individually. If the input is blank or in an error state, the
    formula will evaluate to an error.

    Arguments:
        value:
            The numeric input, in radians, whose cosine is to be computed.


    Returns:
        A `Formula` object representing the computed cosine.


    Raises:
        ValueError: If `value` is not a numeric type or a numeric array.

    Examples:
        Basic usage with a scalar:

        .. code-block:: python

            COS(0)
            # Returns 1.0

        Usage with a model object:

        .. code-block:: python

            COS(my_numeric_field)
            # Returns a formula representing the cosine of `my_numeric_field` (in radians)

        Usage with an array:

        .. code-block:: python

            COS([0, 1.5707963, 3.1415927])
            # Returns [1.0, 0.0, -1.0] approximately
    """
    return _functions.Cos(value)


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


        *arrays:
            One or more array objects to intersect. All arrays must have the same base data type.


    Returns:
        A formula object representing the intersection of all input arrays. The output array
        contains only elements present in every input array, with duplicates removed.


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
    return _functions.Intersection(ignore_blanks, *arrays)


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


        *arrays:
            One or more array objects to union. All arrays must have the same base data type.


    Returns:
        A formula object representing the union of all input arrays. The output array
        contains only elements present in every input array, with duplicates removed.


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
    return _functions.Union(ignore_blanks, *arrays)


def AVERAGE(*values: Operand | int | float) -> Formula:
    """
    Computes the average of one or more numeric values or arrays.

    This function calculates the arithmetic mean of the provided inputs. If array arguments
    are provided, their elements are aggregated to compute the average. If any input is blank or
    in an error state, the formula will evaluate to an error.

    Arguments:
        *values:
            One or more numeric values or arrays to include in the average calculation.


    Returns:
        A formula object representing the computed average. If all inputs are arrays,
        the result is a single aggregated numeric value.


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

    return _functions.Average(*values)


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


    Returns:
        A formula object that evaluates to the ASCII character.


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
    if isinstance(value, int) and value not in range(0, 256):
        raise ValueError(f"Input value: {value} is not in a valid ASCII range.")
    return _functions.Char(value)


def DISTINCT(array: Operand) -> Formula:
    """
    Returns an array containing only the distinct values from the input array.

    This function removes duplicates from the provided array, preserving the order of
    first occurrences. It works on any scalar or object array type.

    Arguments:
        array:
            The array from which duplicates will be removed.


    Returns:
        A formula object representing the array of distinct values.


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
    return _functions.Distinct(array)


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


    Returns:
        The hour as an integer or array of integers.


    Raises:
        ValueError: If the input is not a time type.

    Examples:
        .. code-block:: python

            HOUR(TIME(14, 32, 53))
            # Returns 14
    """
    return _functions.Hour(time)


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


        second_time:
            The ending time or date time.


    Returns:
        The number of hours between the two times. If input arrays have unequal lengths the returned
        formula will evaluate to an error.


    Raises:
        ValueError: If either input is not a valid type.

    Examples:
        .. code-block:: python

            HOURSBETWEEN(TIME(14, 30, 0), DATE(16, 0, 0))
            # Returns 1.5
    """
    return _functions.HoursBetween(first_time, second_time)


def INTEGER(
    value: Operand | bool | float | str,
) -> Formula:
    """
    Converts a value or expression to an INTEGER or INTEGER_ARRAY.

    This function converts the provided input to an integer type.

    Arguments:
        value:
            The input to convert. Can be a scalar or a model object.


    Returns:
        A formula object of type INTEGER or INTEGER_ARRAY representing the converted value.


    Raises:
        ValueError: If the input value is not a supported type or model object.

    Examples:
        .. code-block:: python

            INTEGER(3.7)
            # Returns 3

            INTEGER(True)
            # Returns 1
    """
    return _functions.Integer(value)


def LEN(value: Operand | str | int | float) -> Formula:
    """
    Returns the length of a string or the number of digits in a numeric value.

    - For strings: returns the number of characters.
    - For numbers: returns the number of digits in the integer representation.
    - For arrays: returns an array of lengths for each element.

    Arguments:
        value:
            The value to measure.


    Returns:
        A formula representing the length(s) of the input value(s).


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
    return _functions.Len(value)


def ISERROR(value: Operand | Any) -> Formula:
    """
    Checks whether a value or array contains an error.

    - Returns True for elements that represent an error.
    - Returns False for elements that are valid values.
    - Works for both scalar values and arrays.

    Arguments:
        value:
            The value to check for errors.


    Returns:
        A formula indicating error status.


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
    return _functions.IsError(value)


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


        match_array:
            The array containing reference values. Each element in `source_array` is
            compared to this array to find a match. Must be the same type as `source_array`
            and the same length as `result_array`.


        result_array:
            The array containing values to return when matches are found in `match_array`.
            Must have the same length as `match_array`.


    Returns:
        A formula object representing the lookup operation. The resulting array has
        the same length as `source_array`, with each element computed as follows:

            - If `source_array[i]` is found in `match_array`, return `result_array[j]`,
              where `match_array[j] == source_array[i]`.
            - If `source_array[i]` is not found in `match_array`, return null.


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
    return _functions.LookupArray(source_array, match_array, result_array)


def LOWER(value: Operand | str) -> Formula:
    """
    Converts a string or string array to lowercase.

    - For scalar strings: Returns the lowercase version.
    - For string arrays: Returns a new array where each element is converted to lowercase.

    Arguments:
        value:
            The string or string array to convert.


    Returns:
        A formula containing the lowercase transformation.


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
    return _functions.Lower(value)


def MEDIAN(*values: Operand | int | float) -> Formula:
    """
    Computes the median of one or more numeric values or arrays.

    This function calculates the median of the provided inputs. If array arguments
    are provided, their elements are aggregated to compute the median. If any input is blank or
    in an error state, the formula will evaluate to an error.

    Arguments:
        *values:
            One or more numeric values or arrays to include in the median calculation.


    Returns:
        A formula object representing the computed median. If all inputs are arrays,
        the result is a single aggregated numeric value.


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
    return _functions.Median(*values)


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


    Returns:
        The minute as an integer or array of integers.


    Raises:
        ValueError: If the input is not a time type.

    Examples:
        .. code-block:: python

            MINUTE(TIME(14, 32, 53))
            # Returns 32
    """
    return _functions.Minute(time)


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


        second_date:
            The ending date or array of dates.


    Returns:
        The number of months between the two dates. If input arrays have unequal lengths the
        returned formula will evaluate to an error.


    Raises:
        ValueError: If either input is not a date or datetime type.

    Examples:
        .. code-block:: python

            MONTHSBETWEEN(DATE(2025, 1, 1), DATE(2025, 3, 10))
            # Returns 2
    """
    return _functions.MonthsBetween(first_date, second_date)


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


    Returns:
        The second as an integer or array of integers.


    Raises:
        ValueError: If the input is not a time type.

    Examples:
        .. code-block:: python

            SECOND(TIME(14, 32, 53))
            # Returns 53
    """
    return _functions.Second(time)


def STDEV(*values: Operand | int | float) -> Formula:
    """
    Computes the standard deviation of one or more numeric values or arrays.

    This function calculates the standard deviation (sample) for all provided inputs.
    Inputs can be scalar numbers or arrays of numbers. If arrays are provided, they must
    be of numeric type and the function will compute the standard deviation over all values.

    Arguments:
        *values:
            One or more numeric values or arrays to compute the standard deviation.


    Returns:
        A formula representing the standard deviation of the input values.


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
    return _functions.Stdev(*values)


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


        ignore_empty:
            Boolean flag indicating whether empty strings should be ignored.


        *string_arrays:
            One or more strings or string arrays to concatenate.


    Returns:
        A formula representing the concatenated string.


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
    return _functions.TextJoin(delimiter, ignore_empty, *string_arrays)


def TRIM(value: Operand | str) -> Formula:
    """
    Removes leading and trailing whitespace from a string or string array.

    This function trims whitespace from each element if the input is a string array,
    or from the single string if the input is scalar.

    Arguments:
        value:
            The string or string array to trim.


    Returns:
        A formula representing the trimmed string(s).


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
    return _functions.Trim(value)


def UPPER(value: Operand | str) -> Formula:
    """
    Converts a string or string array to uppercase.

    - For scalar strings: Returns the uppercase version.
    - For string arrays: Returns a new array where each element is converted to uppercase.

    Arguments:
        value:
            The string or string array to convert.


    Returns:
        A formula containing the uppercase transformation.


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
    return _functions.Upper(value)


def WEEKDAY(date: Operand, return_type: Operand | int | None = None) -> Formula:
    """
    Returns the day of the week for a given date, using a customisable numbering scheme.

    This function calculates the weekday for each date in `date` or a single date.
    The numbering of the days is determined by `return_type`, following conventions similar
    to Excel's WEEKDAY function.

    Arguments:
        date:
            The date or date array to evaluate.


        return_type:
            Optional parameter specifying the day numbering scheme. Can be a scalar integer
            (1-3 or 11-17) or a numeric model object. Defaults to 1 (Sunday=1 through Saturday=7).


    Returns:
        A formula representing the weekday(s).


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
    if (
        isinstance(return_type, int)
        and return_type not in range(1, 4)
        and return_type not in range(11, 18)
    ):
        raise ValueError(f"Return type: {return_type} is out of range.")
    return _functions.Weekday(date, return_type)


def WEIBULL(x: Operand, shape: Operand, scale: Operand, cumulative: Operand) -> Formula:
    """
    Calculates the Weibull distribution probability density (PDF) or cumulative distribution (CDF).

    WEIBULL evaluates either the probability density function (PDF) or the cumulative
    distribution function (CDF) of the Weibull distribution for the given input(s).

    Arguments:
        x:
            The input value(s) at which to evaluate the distribution. Must be ≥ 0.


        shape:
            The shape parameter α (must be > 0). Determines the distribution shape:

            - α < 1: Decreasing failure rate
            - α = 1: Exponential distribution
            - α > 1: Increasing failure rate


        scale:
            The scale parameter β (must be > 0). Characteristic life parameter.


        cumulative:
            Boolean flag (or numeric 0/1) to determine calculation type:

            - False / 0: PDF
            - True / 1: CDF


    Returns:
        A formula object evaluating to the Weibull distribution value(s).

        - Returns DECIMAL if all inputs are scalar
        - Returns DECIMAL_ARRAY if any input is an array


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
    return _functions.Weibull(x, shape, scale, cumulative)


def NORMDIST(
    x: Operand | int | float,
    mean: Operand | int | float,
    standard_dev: Operand | int | float,
    cumulative: Operand | bool,
) -> Formula:
    """
    Calculates the normal distribution probability density (PDF) or cumulative distribution (CDF).

    NORMDIST evaluates either the probability density function (PDF) or the cumulative
    distribution function (CDF) of the normal distribution for the given input(s).

    Arguments:
        x:
            The input value(s) at which to evaluate the distribution.


        mean:
            The arithmetic mean of the distribution.


        standard_dev:
            The standard deviation of the distribution (must be > 0).


        cumulative:
            Boolean flag to determine calculation type:

            - False / 0: PDF
            - True / 1: CDF


    Returns:
        A formula object evaluating to the normal distribution value(s).

        - Returns DECIMAL if all inputs are scalar
        - Returns DECIMAL_ARRAY if any input is an array


    Raises:
        ValueError: If `x`, `mean`, or `standard_dev` are not numeric types
        ValueError: If `cumulative` is not boolean-compatible

    Examples:
        Probability density function (PDF):

        .. code-block:: python

            NORMDIST(1.0, 0.0, 1.0, False)
            # Returns the PDF at x=1 for a standard normal distribution

        Cumulative distribution function (CDF):

        .. code-block:: python

            NORMDIST(1.0, 0.0, 1.0, True)
            # Returns the CDF at x=1 for a standard normal distribution

        Array inputs:

        .. code-block:: python

            NORMDIST(my_table["value"], 0.0, 1.0, True)
            # Returns an array of CDF values for each row
    """
    return _functions.NormDist(x, mean, standard_dev, cumulative)


def NORMINV(
    probability: Operand | int | float,
    mean: Operand | int | float,
    standard_dev: Operand | int | float,
) -> Formula:
    """
    Calculates the inverse of the normal cumulative distribution.

    NORMINV returns the value x such that the normal CDF evaluated at x equals the given
    probability, for the specified mean and standard deviation.

    Arguments:
        probability:
            The probability value(s) for which to find the inverse (must be between 0 and 1).


        mean:
            The arithmetic mean of the distribution.


        standard_dev:
            The standard deviation of the distribution (must be > 0).


    Returns:
        A formula object evaluating to the inverse normal distribution value(s).

        - Returns DECIMAL if all inputs are scalar
        - Returns DECIMAL_ARRAY if any input is an array


    Raises:
        ValueError: If `probability`, `mean`, or `standard_dev` are not numeric types

    Examples:
        Scalar inverse:

        .. code-block:: python

            NORMINV(0.975, 0.0, 1.0)
            # Returns ~1.96 (the 97.5th percentile of the standard normal distribution)

        Array inputs:

        .. code-block:: python

            NORMINV(my_table["probability"], 0.0, 1.0)
            # Returns an array of inverse normal values for each row
    """
    return _functions.NormInv(probability, mean, standard_dev)


def BINOMDIST(
    number_s: Operand | int | float,
    trials: Operand | int | float,
    probability_s: Operand | int | float,
    cumulative: Operand | bool,
) -> Formula:
    """
    Calculates the binomial distribution probability mass (PMF) or cumulative distribution (CDF).

    BINOMDIST evaluates either the probability mass function (PMF) or the cumulative
    distribution function (CDF) of the binomial distribution for the given input(s).

    Arguments:
        number_s:
            The number of successes in the trials.


        trials:
            The number of independent trials.


        probability_s:
            The probability of success on each trial (must be between 0 and 1).


        cumulative:
            Boolean flag to determine calculation type:

            - False / 0: PMF
            - True / 1: CDF


    Returns:
        A formula object evaluating to the binomial distribution value(s).

        - Returns DECIMAL if all inputs are scalar
        - Returns DECIMAL_ARRAY if any input is an array


    Raises:
        ValueError: If `number_s`, `trials`, or `probability_s` are not numeric types
        ValueError: If `cumulative` is not boolean-compatible

    Examples:
        Probability mass function (PMF):

        .. code-block:: python

            BINOMDIST(3, 10, 0.5, False)
            # Returns the probability of exactly 3 successes in 10 trials

        Cumulative distribution function (CDF):

        .. code-block:: python

            BINOMDIST(3, 10, 0.5, True)
            # Returns the probability of at most 3 successes in 10 trials

        Array inputs:

        .. code-block:: python

            BINOMDIST(my_table["successes"], 10, 0.5, True)
            # Returns an array of CDF values for each row
    """
    return _functions.BinomDist(number_s, trials, probability_s, cumulative)


def BINOMINV(
    trials: Operand | int | float,
    probability_s: Operand | int | float,
    probability: Operand | int | float,
) -> Formula:
    """
    Calculates the inverse of the binomial cumulative distribution.

    BINOMINV returns the smallest integer k such that the binomial CDF evaluated at k is
    greater than or equal to the given criterion probability.

    Arguments:
        trials:
            The number of independent trials.


        probability_s:
            The probability of success on each trial (must be between 0 and 1).


        probability:
            The criterion probability (must be between 0 and 1).


    Returns:
        A formula object evaluating to the inverse binomial distribution value(s).

        - Returns INTEGER if all inputs are scalar
        - Returns INTEGER_ARRAY if any input is an array


    Raises:
        ValueError: If `trials`, `probability_s`, or `probability` are not numeric types

    Examples:
        Scalar inverse:

        .. code-block:: python

            BINOMINV(10, 0.5, 0.9)
            # Returns the smallest k where P(X <= k) >= 0.9 for X ~ Binomial(10, 0.5)

        Array inputs:

        .. code-block:: python

            BINOMINV(my_table["trials"], 0.5, 0.9)
            # Returns an array of inverse binomial values for each row
    """
    return _functions.BinomInv(trials, probability_s, probability)


def GAMMADIST(
    x: Operand | int | float,
    alpha: Operand | int | float,
    beta: Operand | int | float,
    cumulative: Operand | bool,
) -> Formula:
    """
    Calculates the gamma distribution probability density (PDF) or cumulative distribution (CDF).

    GAMMADIST evaluates either the probability density function (PDF) or the cumulative
    distribution function (CDF) of the gamma distribution for the given input(s).

    Arguments:
        x:
            The input value(s) at which to evaluate the distribution (must be ≥ 0).


        alpha:
            The shape parameter α of the distribution (must be > 0).


        beta:
            The scale parameter β of the distribution (must be > 0).


        cumulative:
            Boolean flag to determine calculation type:

            - False / 0: PDF
            - True / 1: CDF


    Returns:
        A formula object evaluating to the gamma distribution value(s).

        - Returns DECIMAL if all inputs are scalar
        - Returns DECIMAL_ARRAY if any input is an array


    Raises:
        ValueError: If `x`, `alpha`, or `beta` are not numeric types
        ValueError: If `cumulative` is not boolean-compatible

    Examples:
        Probability density function (PDF):

        .. code-block:: python

            GAMMADIST(2.0, 3.0, 1.0, False)
            # Returns the PDF at x=2 for a gamma distribution with shape=3, scale=1

        Cumulative distribution function (CDF):

        .. code-block:: python

            GAMMADIST(2.0, 3.0, 1.0, True)
            # Returns the CDF at x=2 for a gamma distribution with shape=3, scale=1

        Array inputs:

        .. code-block:: python

            GAMMADIST(my_table["value"], 3.0, 1.0, True)
            # Returns an array of CDF values for each row
    """
    return _functions.GammaDist(x, alpha, beta, cumulative)


def GAMMAINV(
    probability: Operand | int | float,
    alpha: Operand | int | float,
    beta: Operand | int | float,
) -> Formula:
    """
    Calculates the inverse of the gamma cumulative distribution.

    GAMMAINV returns the value x such that the gamma CDF evaluated at x equals the given
    probability, for the specified shape and scale parameters.

    Arguments:
        probability:
            The probability value(s) for which to find the inverse (must be between 0 and 1).


        alpha:
            The shape parameter α of the distribution (must be > 0).


        beta:
            The scale parameter β of the distribution (must be > 0).


    Returns:
        A formula object evaluating to the inverse gamma distribution value(s).

        - Returns DECIMAL if all inputs are scalar
        - Returns DECIMAL_ARRAY if any input is an array


    Raises:
        ValueError: If `probability`, `alpha`, or `beta` are not numeric types

    Examples:
        Scalar inverse:

        .. code-block:: python

            GAMMAINV(0.9, 3.0, 1.0)
            # Returns the 90th percentile of a gamma distribution with shape=3, scale=1

        Array inputs:

        .. code-block:: python

            GAMMAINV(my_table["probability"], 3.0, 1.0)
            # Returns an array of inverse gamma values for each row
    """
    return _functions.GammaInv(probability, alpha, beta)


def COUNT(array: Operand, value: Operand | int | float | str | bool) -> Formula:
    """
    Counts the number of occurrences of a specified value in an array.

    COUNT evaluates the input array and returns the total number of times `value` appears.
    The value must be compatible with the data type of the array elements.

    Arguments:
        array:
            The array to search for occurrences of `value`. Must be a valid array type
            or object array.


        value:
            The value to count in the array. Must have the same data type as the array elements.


    Returns:
        A formula object evaluating to an INTEGER representing the count of `value` in `array`.


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
    return _functions.Count(array, value)


def COUNTBLANKS(array: Operand) -> Formula:
    """
    Counts the number of blank elements in an array.

    COUNTBLANKS evaluates the input array and returns the total number of blank elements.
    A blank element is defined as either:

    1. A null value for any data type
    2. An empty string ("") for string arrays

    Arguments:
        array: The array to evaluate for blank elements. Must be a valid array type or object array.


    Returns:
        A formula object evaluating to an INTEGER representing the number of blank elements
        in the array.


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
    return _functions.CountBlanks(array)


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


        include_first_instance:  Determines whether the first occurrence of each duplicate should be
            included in the count. If True, first occurrence and duplicates are counted; if False,
            only subsequent duplicates are counted


        ignore_blanks:
            Determines whether blank values (null or empty strings) should be ignored in duplicate
                counting.


    Returns:
        A formula object evaluating to an INTEGER representing the count of duplicate elements
        according to the specified rules.


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
    return _functions.CountDuplicates(array, include_first_instance, ignore_blanks)


def BITMASKSTRING(array: Operand) -> Formula:
    """
    Converts a boolean array into a compact hexadecimal mask string representation.

    BITMASKSTRING encodes a BOOLEAN_ARRAY as a hexadecimal string, where each character
    represents 4 boolean values (bits). If the array length is not a multiple of 4, the last
    group is padded with zeros.

    Arguments:
        array:
            The boolean array to convert into a hexadecimal mask string.


    Returns:
        A formula object that evaluates to a hexadecimal string representing the boolean array.

        Characteristics:

        - Each character encodes 4 boolean values (0-9, A-F)
        - String length is ceil(array_length / 4)


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
    return _functions.BitmaskString(array)


def DISTRIBUTE(value: Operand | int, array: Operand) -> Formula:
    """
    Distributes an integer value across a series of buckets with defined capacities.

    DISTRIBUTE allocates the input `value` to the buckets in a left-to-right manner,
    filling each bucket up to its specified capacity before moving to the next.

    Arguments:
        value:
            The total value to distribute. Can be an integer constant or a model object
            of type INTEGER.


        array:
            The bucket capacities. Must be an integer array where each element represents
            a bucket's maximum capacity.


    Returns:
        A formula object evaluating to an integer array where each element indicates
        the portion of `value` allocated to the corresponding bucket. The array length
        matches the input bucket array length.


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
    return _functions.Distribute(value, array)


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


        include_first_instance:
            Determines whether the first occurrence of a duplicate should be marked as True.
            If True, the first occurrence is included; if False, only subsequent duplicates are
            marked.


        ignore_blanks:
            Determines whether blank values (null or empty strings) should be ignored in duplicate
            detection.


    Returns:
        A formula object that evaluates to a boolean array of the same length as `array`, where
        True indicates a duplicate element according to the specified rules.


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
    return _functions.FindDuplicates(array, include_first_instance, ignore_blanks)


def ROWVECTOR() -> Formula:
    """
    Generates a row position indicator vector for the current table context.

    ROWVECTOR creates a sparse integer array where a single element is set to 1 at the
    current row index, and all other elements are 0. If no table context is available,
    it returns an empty array.

    Returns:
        A formula object representing an integer array with the following behaviour:

        - Length matches the number of rows in the current table context
        - Element at the current row index is 1
        - All other elements are 0
        - Returns an empty array if no table context is available


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
    return _functions.RowVector()


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


    Returns:
        A formula object representing the maximum scalar if all inputs are scalar values, an array
        of element-wise maximums if any input is an array. The return type is DECIMAL if any decimal
        input is present; otherwise INTEGER. Array outputs match the length of input arrays. All
        arrays must have equal length else an error value is returned.


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

    return _functions.ArrayMax(*values)


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


    Returns:
        A formula object representing the minimum scalar if all inputs are scalar values, an array
        of element-wise minimums if any input is an array. The return type is DECIMAL if any decimal
        input is present; otherwise INTEGER. Array outputs match the length of input arrays. All
        arrays must have equal length else an error value is returned.


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
    return _functions.ArrayMin(*values)


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


        array:
            The array to search within. Must be an array of the same type as `comparison_value`.


        ascending:
            Optional boolean indicating whether to rank in ascending order (True) or descending
            order (False). Defaults to False. Only BOOLEAN values are accepted; otherwise, a
            ValueError is raised.


    Returns:
        A formula object that evaluates to an INTEGER representing the 1-based rank of
        `comparison_value` within `array`.

        If `comparison_value` is not found, the formula evaluates to an error value.


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
    return _functions.Rank(comparison_value, array, ascending)


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


        time_zone:
            The time zone or array of time zones to convert the UTC datetime(s) into.


    Returns:
        A formula object that evaluates to the datetime (or array of datetimes if either input is
        an array type) converted from UTC into the specified time zone.


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
    return _functions.ToTimezone(date_time, time_zone)


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


        time_zone: The timezone or array of timezones the specified datetimes are in.


    Returns:
        A formula object that evaluates to the datetime (or array of datetimes if either input is
        an array type) converted to UTC time.


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
    return _functions.FromTimezone(date_time, time_zone)


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


        table: The table whose rows will be used as keys.


    Returns:
        A formula object that evaluates to a map whose keys are the rows of the
        given table and whose values come from the provided array.


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
    return _functions.ToMap(array, table)


def BASELINE(
    baseline: Baseline | str,
    reference: Field | Calculation | Parameter,
    fallback: Field | Calculation | Parameter | None = None,
) -> Formula:
    """
    Returns the value of a tracked field or named value at a captured baseline.

    Until the baseline is captured at runtime, the function evaluates to blank (or to
    ``fallback`` if supplied). Use :func:`HASBASELINE` to guard against the
    not-yet-captured case. ``BASELINE`` does not create a dependency cycle with the
    live value, so a field may reference its own baseline.

    Arguments:
        baseline:
            The baseline to read from, or its name.

        reference:
            The tracked field or named value to read. Must be a single field or
            named-value reference — expressions are not supported (write
            ``BASELINE(b, [a]) + BASELINE(b, [c])`` instead of
            ``BASELINE(b, [a] + [c])``).

        fallback:
            Optional. A field or named value supplying the value to use before the
            baseline has been captured. Must share ``reference``'s data type.

    Returns:
        The baselined value of ``reference``, with the same data type.

    Raises:
        TypeError: If ``reference`` (or ``fallback``) is not a field or named value
            — a baseline can only read a single tracked element, not an expression.
        ValueError: If ``reference`` is not assigned to any tracking group, or if
            ``fallback`` has a different data type to ``reference``.

    Examples:
        Delta since optimisation:

        .. code-block:: python

            revenue - BASELINE("optimised", revenue)

        With a fallback to the live value:

        .. code-block:: python

            BASELINE("optimised", revenue, revenue)
    """
    if not isinstance(reference, (Field, Calculation, Parameter)):
        raise TypeError(
            "BASELINE reference must be a field, calculation, or parameter, "
            f"not {type(reference).__name__} — expressions are not supported "
            "(write BASELINE(b, [a]) + BASELINE(b, [c]) instead of BASELINE(b, [a] + [c]))"
        )
    if fallback is not None and not isinstance(fallback, (Field, Calculation, Parameter)):
        raise TypeError(
            "BASELINE fallback must be a field, calculation, or parameter, "
            f"not {type(fallback).__name__}"
        )

    if not reference.tracking_groups:
        raise ValueError(
            f"BASELINE reference {reference.to_string()} is not assigned to any tracking "
            "group — call set_tracking_groups([...]) on it before reading its baseline"
        )

    baseline_name = baseline.name if isinstance(baseline, Baseline) else baseline
    data_type = reference.to_data_type()

    if fallback is not None and fallback.to_data_type() != data_type:
        raise ValueError(
            f"BASELINE fallback type {fallback.to_data_type()} does not match "
            f"reference type {data_type}"
        )

    if fallback is None:
        return _functions.Baseline(CONST(baseline_name), reference)
    return _functions.Baseline(CONST(baseline_name), reference, fallback)


def HASBASELINE(baseline: Baseline | str) -> Formula:
    """
    Returns whether a baseline has been captured at runtime.

    Arguments:
        baseline:
            The baseline to test, or its name.

    Returns:
        A ``BOOLEAN`` formula that is true once the baseline has been captured.

    Examples:
        .. code-block:: python

            IF(HASBASELINE("optimised"), revenue - BASELINE("optimised", revenue), 0)
    """
    baseline_name = baseline.name if isinstance(baseline, Baseline) else baseline
    return _functions.HasBaseline(CONST(baseline_name))
