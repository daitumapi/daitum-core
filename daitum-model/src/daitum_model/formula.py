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
This module provides classes and functions to represent and manipulate formulas
used in calculations or data processing. The core components include `Formula`,
which encapsulates the logic for creating and managing formulas involving operations on various
data types.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from typeguard import typechecked

from ._buildable import Buildable
from .data_types import BaseDataType, DataType, MapDataType, ObjectDataType


def _numerical_operation(
    x: Operand,
    y: Operand,
    operator: str,
) -> Formula:
    """
    Build a ``Formula`` for a binary numeric or comparison operation between two operands.

    Validates that the data types of *x* and *y* are compatible with *operator*, infers the
    result data type (preserving array-ness), and returns the composed formula string.

    Args:
        x: The left-hand operand.
        y: The right-hand operand.
        operator: One of ``+``, ``-``, ``*``, ``/``, ``^``, ``<``, ``>``, ``<=``, ``>=``.

    Returns:
        A ``Formula`` with the appropriate result data type.

    Raises:
        ValueError: If *operator* is not one of the supported operators.
        TypeError: If the operand data types are incompatible with *operator*.
    """
    if operator not in {"+", "-", "*", "/", "^", "<", ">", "<=", ">="}:
        raise ValueError(f"Operator {operator} is not supported")

    x_data_type = x.to_data_type()
    y_data_type = y.to_data_type()

    data_type_exception = TypeError(
        f"Operator {operator} is not supported with data types {x_data_type} and {y_data_type}"
    )

    if not isinstance(x_data_type, DataType) or not isinstance(y_data_type, DataType):
        raise data_type_exception

    x_is_array = x_data_type.is_array()
    y_is_array = y_data_type.is_array()

    non_array_x_data_type = x_data_type.from_array() if x_is_array else x_data_type
    non_array_y_data_type = y_data_type.from_array() if y_is_array else y_data_type

    if operator in {"+", "-", "*", "/", "^"}:
        if non_array_x_data_type not in {
            DataType.INTEGER,
            DataType.DECIMAL,
        } or non_array_y_data_type not in {DataType.INTEGER, DataType.DECIMAL}:
            raise data_type_exception
        ret_data_type = (
            DataType.INTEGER
            if operator in {"+", "-", "*", "^"}
            and non_array_x_data_type == DataType.INTEGER
            and non_array_y_data_type == DataType.INTEGER
            else DataType.DECIMAL
        )
    else:
        if non_array_x_data_type not in {
            DataType.INTEGER,
            DataType.DECIMAL,
        } or non_array_y_data_type not in {DataType.INTEGER, DataType.DECIMAL}:
            if (
                non_array_x_data_type != non_array_y_data_type
                or non_array_x_data_type == DataType.STRING
            ):
                raise data_type_exception
        ret_data_type = DataType.BOOLEAN

    ret_data_type = ret_data_type.to_array() if (x_is_array or y_is_array) else ret_data_type

    return Formula(ret_data_type, f"({x.to_string()} {operator} {y.to_string()})")


# pylint: disable=invalid-name
def CONST(x: bool | float | int | str | Operand) -> Formula:
    """
    Creates a `Formula` object representing a constant value.

    The function determines the appropriate `DataType` based on the input type and returns a
    corresponding `Formula` instance.

    Args:
        x (bool | float | int | str | Operand): The constant value to be converted into a
            `Formula`.

    Returns:
        Formula: A `Formula` object representing the given constant.

    Raises:
        TypeError: If the input type is not supported.
    """
    if isinstance(x, bool):
        return Formula(DataType.BOOLEAN, "TRUE" if x else "FALSE")
    if isinstance(x, float):
        return Formula(DataType.DECIMAL, f"{x}")
    if isinstance(x, int):
        return Formula(DataType.INTEGER, f"{x}")
    if isinstance(x, str):
        return Formula(DataType.STRING, f'"{x}"')
    if isinstance(x, Operand):
        return Formula(x.to_data_type(), x.to_string())
    raise TypeError(f"CONST not supported for the input {x}")


@typechecked
class Operand(ABC):
    """
    Abstract base for objects that can participate in formula expressions.

    Concrete subclasses (``Formula``, ``Field``, ``Calculation``, ``Parameter``) implement
    ``to_string()`` and ``to_data_type()``, and inherit all Python operator overloads so
    that expressions like ``cost * qty`` or ``total > CONST(1000)`` compose naturally.
    """

    @abstractmethod
    def to_string(self) -> str:
        pass

    @abstractmethod
    def to_data_type(self) -> BaseDataType:
        pass

    def __add__(self, other: Operand | float | int | str) -> Formula:
        if isinstance(other, (float, int, str)):
            return self + CONST(other)
        other_data_type = other.to_data_type()
        self_data_type = self.to_data_type()

        string_concat = self_data_type in {
            DataType.STRING,
            DataType.STRING_ARRAY,
        } or other_data_type in {DataType.STRING, DataType.STRING_ARRAY}

        if string_concat:
            if not (isinstance(other_data_type, DataType) and isinstance(self_data_type, DataType)):
                raise TypeError(
                    f"Operator + is not supported with data types {self_data_type} and "
                    f"{other_data_type}"
                )
            ret_data_type = (
                DataType.STRING_ARRAY
                if self_data_type.is_array() or other_data_type.is_array()
                else DataType.STRING
            )
            return Formula(ret_data_type, f"({self.to_string()} & {other.to_string()})")

        return _numerical_operation(self, other, "+")

    def __radd__(self, other: Operand | float | int | str) -> Formula:
        if isinstance(other, (float, int, str)):
            return CONST(other) + self
        other_data_type = other.to_data_type()
        self_data_type = self.to_data_type()

        string_concat = self_data_type in {
            DataType.STRING,
            DataType.STRING_ARRAY,
        } or other_data_type in {DataType.STRING, DataType.STRING_ARRAY}

        if string_concat:
            if not (isinstance(other_data_type, DataType) and isinstance(self_data_type, DataType)):
                raise TypeError(
                    f"Operator + is not supported with data types {self_data_type} and "
                    f"{other_data_type}"
                )
            ret_data_type = (
                DataType.STRING_ARRAY
                if self_data_type.is_array() or other_data_type.is_array()
                else DataType.STRING
            )
            return Formula(ret_data_type, f"({other.to_string()} & {self.to_string()})")

        return _numerical_operation(other, self, "+")

    def __mul__(self, other: Operand | float | int) -> Formula:
        if isinstance(other, (float, int)):
            return self * CONST(other)
        return _numerical_operation(self, other, "*")

    def __rmul__(self, other: Operand | float | int) -> Formula:
        if isinstance(other, (float, int)):
            return CONST(other) * self
        return _numerical_operation(other, self, "*")

    def __sub__(self, other: Operand | float | int) -> Formula:
        if isinstance(other, (float, int)):
            return self - CONST(other)
        return _numerical_operation(self, other, "-")

    def __rsub__(self, other: Operand | float | int) -> Formula:
        if isinstance(other, (float, int)):
            return CONST(other) - self
        return _numerical_operation(other, self, "-")

    def __truediv__(self, other: Operand | float | int) -> Formula:
        if isinstance(other, (float, int)):
            return self / CONST(other)
        return _numerical_operation(self, other, "/")

    def __rtruediv__(self, other: Operand | float | int) -> Formula:
        if isinstance(other, (float, int)):
            return CONST(other) / self
        return _numerical_operation(other, self, "/")

    def __xor__(self, other: Operand | float | int) -> Formula:
        if isinstance(other, (float, int)):
            return self ^ CONST(other)
        return _numerical_operation(self, other, "^")

    def __rxor__(self, other: Operand | float | int) -> Formula:
        if isinstance(other, (float, int)):
            return CONST(other) ^ self
        return _numerical_operation(other, self, "^")

    def __lt__(self, other: Operand | float | int) -> Formula:
        if isinstance(other, (float, int)):
            return self < CONST(other)
        return _numerical_operation(self, other, "<")

    def __gt__(self, other: Operand | float | int) -> Formula:
        if isinstance(other, (float, int)):
            return self > CONST(other)
        return _numerical_operation(self, other, ">")

    def __le__(self, other: Operand | float | int) -> Formula:
        if isinstance(other, (float, int)):
            return self <= CONST(other)
        return _numerical_operation(self, other, "<=")

    def __ge__(self, other: Operand | float | int) -> Formula:
        if isinstance(other, (float, int)):
            return self >= CONST(other)
        return _numerical_operation(self, other, ">=")

    def __neg__(self) -> Formula:
        if isinstance(self.to_data_type(), DataType) and self.to_data_type() in [
            DataType.INTEGER,
            DataType.INTEGER_ARRAY,
            DataType.DECIMAL,
            DataType.DECIMAL_ARRAY,
        ]:
            return Formula(self.to_data_type(), f"-({self.to_string()})")

        raise TypeError(f"Cannot negate the data type {self.to_data_type()}")

    def __getitem__(self, other_id: str) -> Formula:
        self_data_type = self.to_data_type()

        if not isinstance(self_data_type, ObjectDataType):
            raise TypeError(
                "Cannot call __getitem__ on field which is not of type OBJECT or OBJECT_ARRAY"
            )

        fields = self_data_type._source_table.get_fields()

        other_field = next((field for field in fields if field.id == other_id), None)
        if not other_field:
            raise ValueError(f"Field with ID {other_id} does not exist in this object")

        other_data_type = other_field.to_data_type()

        if isinstance(other_data_type, DataType):
            if other_data_type.is_array() and self_data_type.is_array():
                raise TypeError(
                    "Cannot call __getitem__ on OBJECT_ARRAY with an array type as input"
                )
            ret_data_type: DataType = (
                other_data_type.to_array() if self_data_type.is_array() else other_data_type
            )
            return Formula(ret_data_type, f"{self.to_string()}.{other_field.to_string()}")
        if isinstance(other_data_type, ObjectDataType):
            if other_data_type.is_array() and self_data_type.is_array():
                raise TypeError(
                    "Cannot call __getitem__ on OBJECT_ARRAY with an array type as input"
                )
            return Formula(
                ObjectDataType(
                    other_data_type._source_table,
                    self_data_type.is_array() or other_data_type.is_array(),
                ),
                f"{self.to_string()}.{other_field.to_string()}",
            )
        if isinstance(other_data_type, MapDataType):
            if self_data_type.is_array():
                raise TypeError("Cannot call __getitem__ on OBJECT_ARRAY with a map type as input")
            return Formula(other_data_type, f"{self.to_string()}.{other_field.to_string()}")
        raise TypeError("Invalid data type")

    def equal_to(self, other: Operand | float | int | bool | str) -> Formula:
        """
        Return a ``BOOLEAN`` (or ``BOOLEAN_ARRAY``) formula testing equality with *other*.

        Use this instead of ``==`` because Python's ``__eq__`` cannot return a ``Formula``.

        Args:
            other: The value or operand to compare against.

        Returns:
            A ``Formula`` that evaluates to ``True`` when this operand equals *other*.
        """
        if isinstance(other, (float, int, bool, str)):
            return self.equal_to(CONST(other))

        data_type = (
            DataType.BOOLEAN_ARRAY
            if (self.to_data_type().is_array() or other.to_data_type().is_array())
            else DataType.BOOLEAN
        )

        return Formula(data_type, f"{self.to_string()} = {other.to_string()}")

    def not_equal_to(self, other: Operand | float | int | bool | str) -> Formula:
        """
        Return a ``BOOLEAN`` (or ``BOOLEAN_ARRAY``) formula testing inequality with *other*.

        Use this instead of ``!=`` because Python's ``__ne__`` cannot return a ``Formula``.

        Args:
            other: The value or operand to compare against.

        Returns:
            A ``Formula`` that evaluates to ``True`` when this operand does not equal *other*.
        """
        if isinstance(other, (float, int, bool, str)):
            return self.not_equal_to(CONST(other))

        data_type = (
            DataType.BOOLEAN_ARRAY
            if (self.to_data_type().is_array() or other.to_data_type().is_array())
            else DataType.BOOLEAN
        )

        return Formula(data_type, f"{self.to_string()} <> {other.to_string()}")


@typechecked
class Formula(Buildable, Operand):
    """
    Represents a formula used in calculations or data processing.

    Attributes:
        data_type (DataType | ObjectDataType): The type of data that the formula returns.
        formula_string (str): The Excel formula as a string.
    """

    def __init__(self, data_type: BaseDataType, formula_string: str):
        self.data_type = data_type
        self.formula_string = formula_string

    def to_data_type(self) -> BaseDataType:
        """
        Retrieves the data type of the formula.

        Returns:
            BaseDataType: The data type associated with the formula.
        """
        return self.data_type

    def to_string(self) -> str:
        """
        Converts the formula expression to its string representation.

        Returns:
            str: The string representation of the formula expression.
        """
        return self.formula_string

    def __iadd__(self, other: Operand | float | int | str) -> Formula:
        formula = self + other
        self.data_type = formula.data_type
        self.formula_string = formula.formula_string
        return self

    def __imul__(self, other: Operand | float | int) -> Formula:
        formula = self * other
        self.data_type = formula.data_type
        self.formula_string = formula.formula_string
        return self

    def __isub__(self, other: Operand | float | int) -> Formula:
        formula = self - other
        self.data_type = formula.data_type
        self.formula_string = formula.formula_string
        return self

    def __itruediv__(self, other: Operand | float | int) -> Formula:
        formula = self / other
        self.data_type = formula.data_type
        self.formula_string = formula.formula_string
        return self
