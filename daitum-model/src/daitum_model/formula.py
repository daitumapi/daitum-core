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
from collections.abc import Sequence
from enum import Enum
from typing import Any

from typeguard import typechecked

from daitum_model.serialisation import Buildable

from .data_types import BaseDataType, DataType


def escape_string_literal(value: str) -> str:
    """Render *value* as a quoted formula string literal, backslash-escaping ``\\`` and ``"``.

    The platform's string-literal syntax is ``"…"`` with ``\\"`` for an embedded quote and ``\\\\``
    for a literal backslash. Backslash is escaped first so an escape introduced for a quote is not
    itself re-escaped. :func:`unescape_string_literal` is the exact inverse.
    """
    escaped = value.replace("\\", "\\\\").replace('"', '\\"')
    return f'"{escaped}"'


def unescape_string_literal(body: str) -> str:
    """Recover the raw string from a literal's *body* (the characters between the quotes).

    The inverse of :func:`escape_string_literal`: ``\\"`` becomes ``"`` and ``\\\\`` becomes ``\\``.
    A backslash before any other character is preserved verbatim (the platform only escapes those
    two, so a lone backslash is a literal backslash).
    """
    out: list[str] = []
    i, n = 0, len(body)
    while i < n:
        ch = body[i]
        if ch == "\\" and i + 1 < n and body[i + 1] in ('"', "\\"):
            out.append(body[i + 1])
            i += 2
        else:
            out.append(ch)
            i += 1
    return "".join(out)


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
        ValueError: If the input type is not supported.
    """
    if isinstance(x, bool):
        return Constant(DataType.BOOLEAN, "TRUE" if x else "FALSE")
    if isinstance(x, float):
        return Constant(DataType.DECIMAL, f"{x}")
    if isinstance(x, int):
        return Constant(DataType.INTEGER, f"{x}")
    if isinstance(x, str):
        return Constant(DataType.STRING, escape_string_literal(x))
    if isinstance(x, Operand):
        return Constant(x.to_data_type(), x.to_string())
    raise ValueError(f"CONST: unsupported input: {x!r}.")


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
        from daitum_model import expression as _expr

        other = _expr.ensure_operand(other)
        if _expr.is_stringish(self) or _expr.is_stringish(other):
            return _expr.build_concat(self, other)
        return _expr.build_numeric(_expr.ADD, self, other)

    def __radd__(self, other: Operand | float | int | str) -> Formula:
        from daitum_model import expression as _expr

        other = _expr.ensure_operand(other)
        if _expr.is_stringish(self) or _expr.is_stringish(other):
            return _expr.build_concat(other, self)
        return _expr.build_numeric(_expr.ADD, other, self)

    def __mul__(self, other: Operand | float | int) -> Formula:
        from daitum_model import expression as _expr

        return _expr.build_numeric(_expr.MULTIPLY, self, _expr.ensure_operand(other))

    def __rmul__(self, other: Operand | float | int) -> Formula:
        from daitum_model import expression as _expr

        return _expr.build_numeric(_expr.MULTIPLY, _expr.ensure_operand(other), self)

    def __sub__(self, other: Operand | float | int) -> Formula:
        from daitum_model import expression as _expr

        return _expr.build_numeric(_expr.SUBTRACT, self, _expr.ensure_operand(other))

    def __rsub__(self, other: Operand | float | int) -> Formula:
        from daitum_model import expression as _expr

        return _expr.build_numeric(_expr.SUBTRACT, _expr.ensure_operand(other), self)

    def __truediv__(self, other: Operand | float | int) -> Formula:
        from daitum_model import expression as _expr

        return _expr.build_numeric(_expr.DIVIDE, self, _expr.ensure_operand(other))

    def __rtruediv__(self, other: Operand | float | int) -> Formula:
        from daitum_model import expression as _expr

        return _expr.build_numeric(_expr.DIVIDE, _expr.ensure_operand(other), self)

    def __xor__(self, other: Operand | float | int) -> Formula:
        from daitum_model import expression as _expr

        return _expr.build_numeric(_expr.POWER_OP, self, _expr.ensure_operand(other))

    def __rxor__(self, other: Operand | float | int) -> Formula:
        from daitum_model import expression as _expr

        return _expr.build_numeric(_expr.POWER_OP, _expr.ensure_operand(other), self)

    def __lt__(self, other: Operand | float | int) -> Formula:
        from daitum_model import expression as _expr

        return _expr.build_numeric(_expr.LESS_THAN, self, _expr.ensure_operand(other))

    def __gt__(self, other: Operand | float | int) -> Formula:
        from daitum_model import expression as _expr

        return _expr.build_numeric(_expr.GREATER_THAN, self, _expr.ensure_operand(other))

    def __le__(self, other: Operand | float | int) -> Formula:
        from daitum_model import expression as _expr

        return _expr.build_numeric(_expr.LESS_EQUAL, self, _expr.ensure_operand(other))

    def __ge__(self, other: Operand | float | int) -> Formula:
        from daitum_model import expression as _expr

        return _expr.build_numeric(_expr.GREATER_EQUAL, self, _expr.ensure_operand(other))

    def __neg__(self) -> Formula:
        from daitum_model import expression as _expr

        return _expr.build_negate(self)

    def __getitem__(self, other_id: str) -> Formula:
        from daitum_model import expression as _expr

        return _expr.MemberAccess(self, other_id)

    def equal_to(self, other: Operand | float | int | bool | str) -> Formula:
        """
        Return a ``BOOLEAN`` (or ``BOOLEAN_ARRAY``) formula testing equality with *other*.

        Use this instead of ``==`` because Python's ``__eq__`` cannot return a ``Formula``.

        Args:
            other: The value or operand to compare against.

        Returns:
            A ``Formula`` that evaluates to ``True`` when this operand equals *other*.
        """
        from daitum_model import expression as _expr

        return _expr.build_equality(_expr.EQUALS, self, _expr.ensure_operand(other))

    def not_equal_to(self, other: Operand | float | int | bool | str) -> Formula:
        """
        Return a ``BOOLEAN`` (or ``BOOLEAN_ARRAY``) formula testing inequality with *other*.

        Use this instead of ``!=`` because Python's ``__ne__`` cannot return a ``Formula``.

        Args:
            other: The value or operand to compare against.

        Returns:
            A ``Formula`` that evaluates to ``True`` when this operand does not equal *other*.
        """
        from daitum_model import expression as _expr

        return _expr.build_equality(_expr.NOT_EQUALS, self, _expr.ensure_operand(other))

    # In-place operators return the structured result node; Python rebinds the name (``x += y`` is
    # ``x = x.__iadd__(y)``), so ``x`` becomes the real operator node — identical to ``x = x + y``,
    # with full ``children()`` / ``dependencies()``. No state is mutated on ``self``.
    def __iadd__(self, other: Operand | float | int | str) -> Formula:
        return self + other

    def __imul__(self, other: Operand | float | int) -> Formula:
        return self * other

    def __isub__(self, other: Operand | float | int) -> Formula:
        return self - other

    def __itruediv__(self, other: Operand | float | int) -> Formula:
        return self / other

    def __ixor__(self, other: Operand | float | int) -> Formula:
        return self ^ other


@typechecked
class Formula(Buildable, Operand, ABC):
    """
    Abstract base for every structured formula expression.

    A formula *is* its structured expression tree: ``Constant``, the operator nodes
    (``BinaryOperator``/``UnaryOperator``/``MemberAccess``/``ColumnAccess``), and every per-function
    node subclass this base. ``data_type`` and ``formula_string`` are **projections** of the tree
    (how it type-checks and how it is written to JSON), derived from ``to_data_type()`` /
    ``to_string()`` rather than stored.

    Subclasses implement ``to_string`` / ``to_data_type`` (from :class:`Operand`) and
    :meth:`children`.
    """

    @abstractmethod
    def children(self) -> Sequence[Operand]:
        """The immediate operand children of this formula node."""

    def dependencies(self) -> set[Operand]:
        """The reference leaves (``Field`` / ``Calculation`` / ``Parameter`` / ``Table``) this
        formula transitively uses.

        The returned set is keyed by object identity (``Operand`` defines no value ``__eq__`` /
        ``__hash__``), so each referenced object appears once. Reference leaves are operands that
        are not themselves :class:`Formula` nodes; a child that *is* a structured formula recurses.
        """
        found: set[Operand] = set()
        for child in self.children():
            if isinstance(child, Formula):
                found |= child.dependencies()
            else:
                found.add(child)
        return found

    def is_equivalent(self, other: object) -> bool:
        """Whether *other* is a formula equivalent to this one.

        Two formulas are equivalent when they render to the same platform expression and infer the
        same data type. Because rendering is deterministic (the same node tree always produces the
        same string, brackets and spacing included), this reliably distinguishes structurally
        different formulas — e.g. ``(x + y) - z`` from ``x + (y - z)`` — and is exactly the check
        the parser round-trip needs (``parse(f.to_string())`` ≡ ``f``).

        This is a dedicated method rather than an ``__eq__`` override, which would perturb the
        identity-keyed :meth:`dependencies` set and the ``equal_to`` / ``not_equal_to`` operators.
        """
        if not isinstance(other, Operand):
            return False
        return self.to_string() == other.to_string() and self.to_data_type() == other.to_data_type()

    @property
    def data_type(self) -> BaseDataType:
        """The formula's return data type (a projection of the tree)."""
        return self.to_data_type()

    @property
    def formula_string(self) -> str:
        """The rendered platform expression string (a projection of the tree)."""
        return self.to_string()

    def build(self) -> dict[str, Any]:
        """Serialise to ``{"dataType", "formulaString"}``.

        A custom override: the node's real state lives in ``_``-prefixed attributes that the default
        :class:`~daitum_model.serialisation.Buildable` walk skips, so this emits the two projections
        explicitly. The data type serialises as its enum value (``DataType``) or its nested build
        (``ObjectDataType`` / ``MapDataType``) — matching the legacy output.
        """
        dt = self.to_data_type()
        if isinstance(dt, Enum):
            data_type: Any = dt.value
        elif isinstance(dt, Buildable):
            data_type = dt.build()
        else:  # pragma: no cover - BaseDataType is always an Enum or Buildable
            data_type = dt
        return {"dataType": data_type, "formulaString": self.to_string()}


class Constant(Formula):
    """A literal constant formula (the body of :func:`CONST`): a leaf with no children."""

    def __init__(self, data_type: BaseDataType, formula_string: str):
        self._data_type = data_type
        self._formula_string = formula_string

    def to_data_type(self) -> BaseDataType:
        return self._data_type

    def to_string(self) -> str:
        return self._formula_string

    def children(self) -> Sequence[Operand]:
        return ()
