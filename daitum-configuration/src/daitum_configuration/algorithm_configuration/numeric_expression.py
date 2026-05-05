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
Symbolic numeric expression that may depend on the ``NUM_VARIABLES`` variable.

Use this where an algorithm parameter should scale with the problem dimension; the
``NUM_VARIABLES`` token is replaced at runtime with the number of decision variables.
"""

from __future__ import annotations


class NumericExpression:
    """
    Symbolic numeric value supporting ``+``, ``-``, ``*``, ``/`` operators.

    Wraps a numeric literal or an expression in the special variable
    ``NUM_VARIABLES``. Operators return a new :class:`NumericExpression`,
    so expressions compose naturally::

        evals = 100_000 * NumericExpression("NUM_VARIABLES")
        rate  = 1 / NumericExpression("NUM_VARIABLES")
    """

    NUM_VARIABLES: str = "NUM_VARIABLES"

    def __init__(self, value: int | float | str | NumericExpression):
        if isinstance(value, (int, float)):
            self.expr = str(value)
        elif isinstance(value, str):
            if value == NumericExpression.NUM_VARIABLES:
                self.expr = value
            else:
                raise ValueError(f"Only {NumericExpression.NUM_VARIABLES} is allowed as a variable")
        elif isinstance(value, NumericExpression):
            self.expr = value.expr
        else:
            raise TypeError(f"Unsupported type: {type(value)}")

    def __str__(self) -> str:
        return self.expr

    def __add__(self, other: int | float | str | NumericExpression) -> NumericExpression:
        return NumericExpression._from_expr(f"({self.expr} + {NumericExpression(other).expr})")

    def __radd__(self, other: int | float | str | NumericExpression) -> NumericExpression:
        return NumericExpression._from_expr(f"({NumericExpression(other).expr} + {self.expr})")

    def __sub__(self, other: int | float | str | NumericExpression) -> NumericExpression:
        return NumericExpression._from_expr(f"({self.expr} - {NumericExpression(other).expr})")

    def __rsub__(self, other: int | float | str | NumericExpression) -> NumericExpression:
        return NumericExpression._from_expr(f"({NumericExpression(other).expr} - {self.expr})")

    def __mul__(self, other: int | float | str | NumericExpression) -> NumericExpression:
        return NumericExpression._from_expr(f"({self.expr} * {NumericExpression(other).expr})")

    def __rmul__(self, other: int | float | str | NumericExpression) -> NumericExpression:
        return NumericExpression._from_expr(f"({NumericExpression(other).expr} * {self.expr})")

    def __truediv__(self, other: int | float | str | NumericExpression) -> NumericExpression:
        return NumericExpression._from_expr(f"({self.expr} / {NumericExpression(other).expr})")

    def __rtruediv__(self, other: int | float | str | NumericExpression) -> NumericExpression:
        return NumericExpression._from_expr(f"({NumericExpression(other).expr} / {self.expr})")

    def to_string(self) -> str:
        """Return the underlying expression string."""
        return self.expr

    def is_float(self) -> bool:
        """Return True if the expression is a float literal."""
        try:
            _ = float(self.expr)
            return "." in self.expr or "e" in self.expr.lower()
        except (ValueError, TypeError):
            return False

    def is_integer(self) -> bool:
        """Return True if the expression is an integer literal."""
        try:
            int_val = int(self.expr)
            return str(int_val) == self.expr
        except (ValueError, TypeError):
            return False

    def is_expression(self) -> bool:
        """Return True if the expression contains a variable rather than a numeric literal."""
        if isinstance(self.expr, str):
            return not self.is_integer() and not self.is_float()
        return False

    @classmethod
    def _from_expr(cls, expr: str) -> NumericExpression:
        obj = cls.__new__(cls)
        obj.expr = expr
        return obj

    @classmethod
    def from_str(cls, expr: str) -> NumericExpression:
        """Construct from a numeric or ``NUM_VARIABLES`` string."""
        return cls(expr)

    @classmethod
    def from_number(cls, num: int | float) -> NumericExpression:
        """Construct from an int or float literal."""
        return cls(num)

    @classmethod
    def variable(cls, name: str) -> NumericExpression:
        """Construct from a variable name. Currently only ``NUM_VARIABLES`` is supported."""
        return cls(name)
