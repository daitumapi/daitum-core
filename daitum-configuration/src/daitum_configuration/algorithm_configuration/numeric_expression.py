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
A class to represent numeric values or mathematical expressions that can include variables.

The class can handle values of type int, float, or string expression of "NUM_VARIABLES". The value
or expression is stored as a string, and the class provides methods to perform arithmetic
operations, check if the expression is an integer or float, and evaluate the string expression.
This makes it useful for scenarios that involve symbolic computation or dynamic evaluation
of mathematical expressions with variables.
"""

from typing import Union


class NumericExpression:
    """
    Wrapper for numeric values or expressions that may depend on NUM_VARIABLES.
    Can hold either a float/int value or a string expression "NUM_VARIABLES".
    """

    NUM_VARIABLES: str = "NUM_VARIABLES"

    def __init__(self, value: Union[int, float, str, "NumericExpression"]):
        if isinstance(value, (int, float)):
            self.expr = str(value)
        elif isinstance(value, str):
            if value in {NumericExpression.NUM_VARIABLES or value == "NUM_VARIABLES"}:
                self.expr = value
            else:
                raise ValueError(f"Only {NumericExpression.NUM_VARIABLES} is allowed as a variable")
        elif isinstance(value, NumericExpression):
            self.expr = value.expr
        else:
            raise TypeError(f"Unsupported type: {type(value)}")

    def __str__(self) -> str:
        return self.expr

    def __add__(self, other: Union[int, float, str, "NumericExpression"]) -> "NumericExpression":
        return NumericExpression._from_expr(f"({self.expr} + {NumericExpression(other).expr})")

    def __radd__(self, other: Union[int, float, str, "NumericExpression"]) -> "NumericExpression":
        return NumericExpression._from_expr(f"({NumericExpression(other).expr} + {self.expr})")

    def __sub__(self, other: Union[int, float, str, "NumericExpression"]) -> "NumericExpression":
        return NumericExpression._from_expr(f"({self.expr} - {NumericExpression(other).expr})")

    def __rsub__(self, other: Union[int, float, str, "NumericExpression"]) -> "NumericExpression":
        return NumericExpression._from_expr(f"({NumericExpression(other).expr} - {self.expr})")

    def __mul__(self, other: Union[int, float, str, "NumericExpression"]) -> "NumericExpression":
        return NumericExpression._from_expr(f"({self.expr} * {NumericExpression(other).expr})")

    def __rmul__(self, other: Union[int, float, str, "NumericExpression"]) -> "NumericExpression":
        return NumericExpression._from_expr(f"({NumericExpression(other).expr} * {self.expr})")

    def __truediv__(
        self, other: Union[int, float, str, "NumericExpression"]
    ) -> "NumericExpression":
        return NumericExpression._from_expr(f"({self.expr} / {NumericExpression(other).expr})")

    def __rtruediv__(
        self, other: Union[int, float, str, "NumericExpression"]
    ) -> "NumericExpression":
        return NumericExpression._from_expr(f"({NumericExpression(other).expr} / {self.expr})")

    def to_string(self) -> str:
        """
        Return string expression.
        """
        return self.expr

    def is_float(self) -> bool:
        """
        Check if the internal expression can be safely interpreted as a float.
        If so, returns True; otherwise, returns False.
        """
        try:
            _ = float(self.expr)
            return "." in self.expr or "e" in self.expr.lower()
        except (ValueError, TypeError):
            return False

    def is_integer(self) -> bool:
        """
        Check if the internal expression can be safely interpreted as an integer.
        If so, returns True; otherwise, returns False.
        """
        try:
            int_val = int(self.expr)
            return str(int_val) == self.expr
        except (ValueError, TypeError):
            return False

    def is_expression(self) -> bool:
        """
        Check if the internal representation is a non-numeric string expression,
        such as containing variables (e.g., 'NUM_VARIABLES').
        """
        if isinstance(self.expr, str):
            return not self.is_integer() and not self.is_float()
        return False

    @classmethod
    def _from_expr(cls, expr: str) -> "NumericExpression":
        """
        Internal method to create a NumericExpression from a string expression.

        Args:
            expr: The mathematical expression as a string

        Returns:
            New NumericExpression instance with the given expression.
        """
        obj = cls.__new__(cls)
        obj.expr = expr
        return obj

    @classmethod
    def from_str(cls, expr: str) -> "NumericExpression":
        """
        Create a NumericExpression from a string expression.

        Args:
            expr: Mathematical expression string (e.g. "2 + 3")

        Returns:
            New NumericExpression representing the given expression.
        """
        return cls(expr)

    @classmethod
    def from_number(cls, num: int | float) -> "NumericExpression":
        """
        Create a NumericExpression from a numeric value.

        Args:
            num: Integer or float value

        Returns:
            New NumericExpression representing the constant value.
        """
        return cls(num)

    @classmethod
    def variable(cls, name: str) -> "NumericExpression":
        """
        Create a NumericExpression representing a variable.

        Args:
            name: Variable name (e.g. for now only support "NUM_VARIABLES")

        Returns:
            New NumericExpression representing the variable.
        """
        return cls(name)
