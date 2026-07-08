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
Structured expression-node representation for Daitum formulas.

This internal module backs the public ``daitum_model.formulas`` surface and the operator overloads
on :class:`~daitum_model.formula.Operand`. Every formula and operator is an :class:`ExpressionNode`
that knows its children, its inferred return :class:`~daitum_model.data_types.BaseDataType`, and how
to render itself to the exact platform expression string.

The node hierarchy:

- :class:`ExpressionNode` — abstract base; an :class:`~daitum_model.formula.Operand`.
- :class:`Constant` — a literal int/float/bool/str (the body of ``CONST``).
- :class:`UnaryOperator` / :class:`BinaryOperator` — the arithmetic/comparison/concat/equality
  operators promoted from ad-hoc dunder methods to first-class, introspectable nodes.
- :class:`MemberAccess` (``base.[field]``) / :class:`ColumnAccess` (``table[field]``) — the two
  distinct subscript operators.

The module also houses the shared type-combinator helpers (``numeric_result`` etc.) and the
declarative :class:`OperatorDef` registry that drives operator construction, validation, and
(eventually) documentation.

It is deliberately *not* re-exported from the package ``__init__``; the public surface is unchanged.
"""

from __future__ import annotations

from abc import abstractmethod
from collections.abc import Sequence
from dataclasses import dataclass, field
from typing import Any

from daitum_model.data_types import (
    PRIMITIVE_DATA_TYPES,
    BaseDataType,
    DataType,
    MapDataType,
    ObjectDataType,
)
from daitum_model.formula import CONST, Formula, Operand

# ---------------------------------------------------------------------------
# Type classes & combinators (the shared type engine)
# ---------------------------------------------------------------------------

#: Numeric scalar + array types.
NUMERIC_TYPES = frozenset(
    {DataType.INTEGER, DataType.DECIMAL, DataType.INTEGER_ARRAY, DataType.DECIMAL_ARRAY}
)
STRING_TYPES = frozenset({DataType.STRING, DataType.STRING_ARRAY})


def _non_array(dt: DataType) -> DataType:
    return dt.from_array() if dt.is_array() else dt


def _propagate_array(result: DataType, *operands: BaseDataType) -> DataType:
    """Return the array variant of *result* if any operand is an array, else *result*."""
    if any(op.is_array() for op in operands):
        return result.to_array()
    return result


def numeric_result(x: BaseDataType, y: BaseDataType) -> DataType:
    """Result type of a numeric binary op: INTEGER if both integer, else DECIMAL; array-propagated.

    Raises:
        ValueError: if either operand is not a numeric (scalar or array) type.
    """
    if not isinstance(x, DataType) or not isinstance(y, DataType):
        raise _binary_type_error(x, y)
    if x not in NUMERIC_TYPES or y not in NUMERIC_TYPES:
        raise _binary_type_error(x, y)
    both_integer = _non_array(x) == DataType.INTEGER and _non_array(y) == DataType.INTEGER
    base = DataType.INTEGER if both_integer else DataType.DECIMAL
    return _propagate_array(base, x, y)


def _binary_type_error(x: BaseDataType, y: BaseDataType, symbol: str = "") -> ValueError:
    op = symbol or "operator"
    return ValueError(f"{op}: unsupported operand type(s): {x}, {y}.")


# ---------------------------------------------------------------------------
# ExpressionNode base + Constant
# ---------------------------------------------------------------------------


#: ``ExpressionNode`` is now :class:`~daitum_model.formula.Formula` — the merged structured base.
#: Retained as an alias so existing references keep resolving; new code should use ``Formula``.
ExpressionNode = Formula


def ensure_operand(value: Operand | bool | int | float | str) -> Operand:
    """Coerce a Python literal to a :class:`~daitum_model.formula.Operand` via ``CONST``.

    An existing operand is returned unchanged. Mirrors the ``isinstance(x, Operand) else CONST(x)``
    idiom repeated throughout the legacy ``formulas`` module.
    """
    if isinstance(value, Operand):
        return value
    return CONST(value)


# ---------------------------------------------------------------------------
# Operator registry
# ---------------------------------------------------------------------------


# Operand/result type-class label tuples for the operator docs. These are the operators' declared
# accepted-operand and possible-result data types — the single source of truth the docs read, and
# what the operator drift golden is cross-checked against (``tests/test_doc_spec.py``) so a
# declaration can never silently diverge from the operators' actual behaviour.
_NUMERIC_LABELS = ("INTEGER", "INTEGER_ARRAY", "DECIMAL", "DECIMAL_ARRAY")
_STRING_LABELS = ("STRING", "STRING_ARRAY")
_BOOLEAN_LABELS = ("BOOLEAN", "BOOLEAN_ARRAY")
_DATETIME_LABELS = ("DATE", "DATETIME", "DATE_ARRAY", "DATETIME_ARRAY", "TIME", "TIME_ARRAY")
#: Comparison operands: numeric, date/datetime, time and boolean — but NOT string (``<`` etc. reject
#: strings; only ``=`` / ``<>`` compare strings). This is the rule ``build_numeric`` enforces.
_ORDERED_LABELS = _NUMERIC_LABELS + _DATETIME_LABELS + _BOOLEAN_LABELS
#: Concatenation operands: any primitive/array type (composites are rejected by ``build_concat``).
_CONCAT_LABELS = _NUMERIC_LABELS + _STRING_LABELS + _BOOLEAN_LABELS + _DATETIME_LABELS
#: Equality operands: any data type (all primitives plus the composite object/map kinds compare for
#: equality). The composite kinds are not ``DataType`` enum members, so they are listed explicitly.
_ANY_LABELS = (
    tuple(dt.name for dt in DataType if dt is not DataType.NULL)
    + ("OBJECT", "OBJECT_ARRAY")
    + tuple(f"{dt.name}_MAP" for dt in DataType if dt is not DataType.NULL)
)


@dataclass(frozen=True)
class OperatorDef:
    """Declarative definition of a binary operator.

    Attributes:
        name: Symbolic operator name (``"ADD"``, ``"CONCAT"``, ``"EQUALS"`` …).
        symbol: The rendered operator symbol (``"+"``, ``"&"``, ``"="`` …).
        parenthesise: Whether the rendered form is wrapped in parentheses. Arithmetic and
            comparison are parenthesised (``(L op R)``); equality is not (``L = R``).
        precedence: Binding tightness for parsing *unparenthesised* operator chains — a higher
            number binds tighter (``*`` above ``+`` above ``&`` above comparison above equality).
            The library's own renderer fully parenthesises every arithmetic/comparison operation,
            so this only ever disambiguates operator chains authored elsewhere (which omit the
            canonical brackets); it never changes how a rendered-here formula reparses.
        right_associative: Whether the operator groups right-to-left (only ``^``); all others are
            left-associative, matching the left-nested trees the overloads build.
        operands: The accepted operand data-type labels (the operator's declared type rule).
        result: The possible result data-type labels.
        doc: A one-line behaviour description for the reference.
    """

    name: str
    symbol: str
    # Keyword-only: these are always supplied by name (some via a ``**dict`` splat), and keeping
    # them off the positional axis avoids ambiguous positional/splat alignment.
    parenthesise: bool = field(default=True, kw_only=True)
    precedence: int = field(default=0, kw_only=True)
    right_associative: bool = field(default=False, kw_only=True)
    operands: tuple[str, ...] = field(default=(), kw_only=True)
    result: tuple[str, ...] = field(default=(), kw_only=True)
    doc: str = field(default="", kw_only=True)


class BinaryOperator(ExpressionNode):
    """A binary operator node: ``(left symbol right)`` or ``left symbol right``."""

    def __init__(self, definition: OperatorDef, left: Operand, right: Operand, result: DataType):
        self._def = definition
        self._left = left
        self._right = right
        self._result = result

    def children(self) -> Sequence[Operand]:
        return (self._left, self._right)

    def to_data_type(self) -> BaseDataType:
        return self._result

    def to_string(self) -> str:
        body = f"{self._left.to_string()} {self._def.symbol} {self._right.to_string()}"
        return f"({body})" if self._def.parenthesise else body


class UnaryOperator(ExpressionNode):
    """A unary operator node. Currently only negation: ``-(operand)``."""

    def __init__(self, operand: Operand, result: BaseDataType):
        self._operand = operand
        self._result = result

    def children(self) -> Sequence[Operand]:
        return (self._operand,)

    def to_data_type(self) -> BaseDataType:
        return self._result

    def to_string(self) -> str:
        return f"-({self._operand.to_string()})"


# --- operator definitions ---------------------------------------------------

# Precedence tiers (higher binds tighter). Only ``^`` is right-associative. These drive parsing of
# unparenthesised operator chains authored elsewhere; the renderer here always fully parenthesises
# arithmetic/comparison operations, so a formula produced by this library reparses identically
# regardless of these values.
_PREC_EQUALITY = 1
_PREC_COMPARISON = 2
_PREC_CONCAT = 3
_PREC_ADDITIVE = 4
_PREC_MULTIPLICATIVE = 5
_PREC_POWER = 6

ADD = OperatorDef(
    "ADD",
    "+",
    precedence=_PREC_ADDITIVE,
    operands=_NUMERIC_LABELS,
    result=_NUMERIC_LABELS,
    doc="Numeric addition.",
)
SUBTRACT = OperatorDef(
    "SUBTRACT",
    "-",
    precedence=_PREC_ADDITIVE,
    operands=_NUMERIC_LABELS,
    result=_NUMERIC_LABELS,
    doc="Numeric subtraction.",
)
MULTIPLY = OperatorDef(
    "MULTIPLY",
    "*",
    precedence=_PREC_MULTIPLICATIVE,
    operands=_NUMERIC_LABELS,
    result=_NUMERIC_LABELS,
    doc="Numeric multiplication.",
)
DIVIDE = OperatorDef(
    "DIVIDE",
    "/",
    precedence=_PREC_MULTIPLICATIVE,
    operands=_NUMERIC_LABELS,
    result=_NUMERIC_LABELS,
    doc="Numeric division.",
)
POWER_OP = OperatorDef(
    "POWER",
    "^",
    precedence=_PREC_POWER,
    right_associative=True,
    operands=_NUMERIC_LABELS,
    result=_NUMERIC_LABELS,
    doc="Exponentiation.",
)
CONCAT = OperatorDef(
    "CONCAT",
    "&",
    precedence=_PREC_CONCAT,
    operands=_CONCAT_LABELS,
    result=_STRING_LABELS,
    doc="String concatenation (the ``+`` operator when either operand is a string).",
)
LESS_THAN = OperatorDef(
    "LESS_THAN",
    "<",
    precedence=_PREC_COMPARISON,
    operands=_ORDERED_LABELS,
    result=_BOOLEAN_LABELS,
    doc="Less-than comparison.",
)
GREATER_THAN = OperatorDef(
    "GREATER_THAN",
    ">",
    precedence=_PREC_COMPARISON,
    operands=_ORDERED_LABELS,
    result=_BOOLEAN_LABELS,
    doc="Greater-than comparison.",
)
LESS_EQUAL = OperatorDef(
    "LESS_EQUAL",
    "<=",
    precedence=_PREC_COMPARISON,
    operands=_ORDERED_LABELS,
    result=_BOOLEAN_LABELS,
    doc="Less-than-or-equal comparison.",
)
GREATER_EQUAL = OperatorDef(
    "GREATER_EQUAL",
    ">=",
    precedence=_PREC_COMPARISON,
    operands=_ORDERED_LABELS,
    result=_BOOLEAN_LABELS,
    doc="Greater-than-or-equal comparison.",
)
EQUALS = OperatorDef(
    "EQUALS",
    "=",
    parenthesise=False,
    precedence=_PREC_EQUALITY,
    operands=_ANY_LABELS,
    result=_BOOLEAN_LABELS,
    doc="Equality comparison.",
)
NOT_EQUALS = OperatorDef(
    "NOT_EQUALS",
    "<>",
    parenthesise=False,
    precedence=_PREC_EQUALITY,
    operands=_ANY_LABELS,
    result=_BOOLEAN_LABELS,
    doc="Inequality comparison.",
)

#: All binary operators, for the docs reference and a coverage gate.
BINARY_OPERATORS: tuple[OperatorDef, ...] = (
    ADD,
    SUBTRACT,
    MULTIPLY,
    DIVIDE,
    POWER_OP,
    CONCAT,
    LESS_THAN,
    GREATER_THAN,
    LESS_EQUAL,
    GREATER_EQUAL,
    EQUALS,
    NOT_EQUALS,
)

_ARITHMETIC_SYMBOLS = {"+", "-", "*", "/", "^"}


# --- builders used by the Operand overloads ---------------------------------


def build_numeric(definition: OperatorDef, left: Operand, right: Operand) -> Formula:
    """Construct an arithmetic or comparison operator node and materialise it.

    Reproduces the legacy ``_numerical_operation`` semantics exactly, including the comparison
    rule that permits equal non-string types.
    """
    symbol = definition.symbol
    x = left.to_data_type()
    y = right.to_data_type()
    err = _binary_type_error(x, y, symbol)

    if not isinstance(x, DataType) or not isinstance(y, DataType):
        raise err

    nx, ny = _non_array(x), _non_array(y)

    if symbol in _ARITHMETIC_SYMBOLS:
        if nx not in {DataType.INTEGER, DataType.DECIMAL} or ny not in {
            DataType.INTEGER,
            DataType.DECIMAL,
        }:
            raise err
        both_int = (
            symbol in {"+", "-", "*", "^"} and nx == DataType.INTEGER and ny == DataType.INTEGER
        )
        base = DataType.INTEGER if both_int else DataType.DECIMAL
    else:
        # comparison: numeric, or equal non-string types
        if nx not in {DataType.INTEGER, DataType.DECIMAL} or ny not in {
            DataType.INTEGER,
            DataType.DECIMAL,
        }:
            if nx != ny or nx == DataType.STRING:
                raise err
        base = DataType.BOOLEAN

    result = base.to_array() if (x.is_array() or y.is_array()) else base
    return BinaryOperator(definition, left, right, result)


def build_concat(left: Operand, right: Operand) -> Formula:
    """Construct a string-concatenation operator node and materialise it."""
    x = left.to_data_type()
    y = right.to_data_type()
    if not (isinstance(x, DataType) and isinstance(y, DataType)):
        raise _binary_type_error(x, y, "&")
    result = DataType.STRING_ARRAY if (x.is_array() or y.is_array()) else DataType.STRING
    return BinaryOperator(CONCAT, left, right, result)


def is_stringish(operand: Operand) -> bool:
    """Whether *operand*'s type is STRING or STRING_ARRAY (selects concat over numeric add)."""
    return operand.to_data_type() in STRING_TYPES


def build_negate(operand: Operand) -> Formula:
    """Construct a unary negation node and materialise it."""
    dt = operand.to_data_type()
    if isinstance(dt, DataType) and dt in {
        DataType.INTEGER,
        DataType.INTEGER_ARRAY,
        DataType.DECIMAL,
        DataType.DECIMAL_ARRAY,
    }:
        return UnaryOperator(operand, dt)
    raise ValueError(f"-: unsupported operand type: {dt}.")


def build_equality(definition: OperatorDef, left: Operand, right: Operand) -> Formula:
    """Construct an equality / inequality node and materialise it."""
    result = (
        DataType.BOOLEAN_ARRAY
        if (left.to_data_type().is_array() or right.to_data_type().is_array())
        else DataType.BOOLEAN
    )
    return BinaryOperator(definition, left, right, result)


# ---------------------------------------------------------------------------
# Member access (operand[field]) and column access (table[field])
# ---------------------------------------------------------------------------


def _resolve_member_field(source_table, field_id: str):
    """Find the field on *source_table* matching *field_id*, raising if absent."""
    fields = source_table.get_fields()
    field = next((f for f in fields if f.id == field_id), None)
    if not field:
        raise ValueError(f"Field with ID {field_id} does not exist in this object")
    return field


class MemberAccess(ExpressionNode):
    """``base.[field]`` — member access on a field / named-value / object-array operand."""

    def __init__(self, base: Operand, field_id: str):
        self._base = base
        self._field_id = field_id
        self._field, self._result = self._resolve()

    def _resolve(self) -> tuple[Any, BaseDataType]:
        base_type = self._base.to_data_type()
        if not isinstance(base_type, ObjectDataType):
            raise ValueError("member access: receiver must be of type OBJECT or OBJECT_ARRAY.")
        field = _resolve_member_field(base_type._source_table, self._field_id)
        field_type = field.to_data_type()
        base_is_array = base_type.is_array()

        if isinstance(field_type, DataType):
            if field_type.is_array() and base_is_array:
                raise ValueError("member access: cannot access an array field on an OBJECT_ARRAY.")
            result: BaseDataType = field_type.to_array() if base_is_array else field_type
            return field, result
        if isinstance(field_type, ObjectDataType):
            if field_type.is_array() and base_is_array:
                raise ValueError("member access: cannot access an array field on an OBJECT_ARRAY.")
            return field, ObjectDataType(
                field_type._source_table, base_is_array or field_type.is_array()
            )
        if isinstance(field_type, MapDataType):
            if base_is_array:
                raise ValueError("member access: cannot access a map field on an OBJECT_ARRAY.")
            return field, field_type
        raise ValueError("member access: unsupported field type.")

    def children(self) -> Sequence[Operand]:
        return (self._base,)

    def to_data_type(self) -> BaseDataType:
        return self._result

    def to_string(self) -> str:
        return f"{self._base.to_string()}.{self._field.to_string()}"

    def dependencies(self) -> set[Operand]:
        # The base's own dependencies, plus the accessed field itself.
        deps = self._base.dependencies() if isinstance(self._base, Formula) else {self._base}
        deps.add(self._field)
        return deps


class ColumnAccess(ExpressionNode):
    """``table[field]`` — column access on a raw table (bracket form, array-typed)."""

    def __init__(self, table, field_id: str):
        self._table = table
        self._field_id = field_id
        self._field, self._result = self._resolve()

    def _resolve(self) -> tuple[Any, BaseDataType]:
        field = self._table.field_definitions.get(self._field_id)
        if not field:
            raise ValueError(f"The field with ID {self._field_id} does not exist in this table")
        field_type = field.data_type
        if isinstance(field_type, DataType):
            if field_type.is_array():
                raise ValueError("Cannot call __getitem__ on table with an array field")
            return field, field_type.to_array()
        if isinstance(field_type, ObjectDataType):
            if field_type.is_array():
                raise ValueError("Cannot call __getitem__ on table with an array field")
            return field, ObjectDataType(field_type._source_table, is_array=True)
        raise ValueError("Cannot call __getitem__ on table with a map field")

    def children(self) -> Sequence[Operand]:
        return ()

    def to_data_type(self) -> BaseDataType:
        return self._result

    def to_string(self) -> str:
        return f"{self._table.id}[{self._field_id}]"

    def dependencies(self) -> set[Operand]:
        # A raw-table column reference depends on the accessed field.
        return {self._field}


# ---------------------------------------------------------------------------
# Function nodes: declarative argument spec + validation engine
# ---------------------------------------------------------------------------

#: Named type classes — the declarative replacement for the module-level type sets that the legacy
#: ``formulas`` module hand-rolled (``NUMERIC_AND_ARRAY_TYPES`` etc.).
NUMERIC = NUMERIC_TYPES
BOOLEANISH = frozenset(
    {
        DataType.BOOLEAN,
        DataType.BOOLEAN_ARRAY,
        DataType.DECIMAL,
        DataType.DECIMAL_ARRAY,
        DataType.INTEGER,
        DataType.INTEGER_ARRAY,
    }
)
DATELIKE = frozenset(
    {DataType.DATE, DataType.DATETIME, DataType.DATE_ARRAY, DataType.DATETIME_ARRAY}
)
TIMELIKE = frozenset(
    {DataType.TIME, DataType.DATETIME, DataType.TIME_ARRAY, DataType.DATETIME_ARRAY}
)
STRINGS = STRING_TYPES


# ---------------------------------------------------------------------------
# Composite type-kind tokens
# ---------------------------------------------------------------------------
#
# A :class:`Arg`'s ``accepts`` set lists the data-type *kinds* the argument permits. The 14
# primitive/array kinds are :class:`DataType` enum members and match an operand's data type by
# value (``dt == member``). The composite kinds — object references and maps — are
# :class:`~daitum_model.data_types.ObjectDataType` / :class:`~daitum_model.data_types.MapDataType`
# *instances* parameterised by their source table, so a single value cannot stand for "any object
# array" in a frozenset. These sentinel tokens match such kinds structurally (``isinstance`` + the
# array flag) and carry the verbatim documentation labels (no grouping, no ``ANY``).


@dataclass(frozen=True)
class TypeKind:
    """A composite (non-enum) accepted-type kind: matches structurally, documents verbatim.

    Attributes:
        match_object: Match a non-array object reference (``OBJECT``).
        match_object_array: Match an array object reference (``OBJECT_ARRAY``).
        match_map: Match any map (``<T>_MAP``).
        labels: The verbatim type names shown in the docs for this kind.
    """

    match_object: bool
    match_object_array: bool
    match_map: bool
    labels: tuple[str, ...]

    def matches(self, dt: BaseDataType) -> bool:
        if isinstance(dt, MapDataType):
            return self.match_map
        if isinstance(dt, ObjectDataType):
            return self.match_object_array if dt.is_array() else self.match_object
        return False


#: A non-array object reference (``OBJECT``).
ANY_OBJECT = TypeKind(True, False, False, ("OBJECT",))
#: An array object reference (``OBJECT_ARRAY``).
ANY_OBJECT_ARRAY = TypeKind(False, True, False, ("OBJECT_ARRAY",))
#: Any map, listed verbatim as one ``<T>_MAP`` token per primitive value type.
ANY_MAP = TypeKind(
    False,
    False,
    True,
    tuple(f"{dt.name}_MAP" for dt in DataType if dt in PRIMITIVE_DATA_TYPES),
)


def arg_accepts(accepts: frozenset[DataType | TypeKind], dt: BaseDataType) -> bool:
    """Whether *dt* is permitted by an :class:`Arg`'s ``accepts`` set.

    A :class:`DataType` member matches by value; a :class:`TypeKind` token matches structurally.
    """
    for token in accepts:
        if isinstance(token, TypeKind):
            if token.matches(dt):
                return True
        elif dt == token:
            return True
    return False


def accepts_labels(accepts: frozenset[DataType | TypeKind]) -> list[str]:
    """The verbatim, sorted display labels for an ``accepts`` set (no grouping, no ``ANY``)."""
    labels: set[str] = set()
    for token in accepts:
        if isinstance(token, TypeKind):
            labels.update(token.labels)
        else:
            labels.add(token.name)
    return sorted(labels)


@dataclass(frozen=True)
class Arg:
    """Declarative spec for one function argument.

    Attributes:
        name: The argument name (for error messages and docs).
        accepts: The accepted data-type kinds — a ``frozenset`` of :class:`DataType` members and/or
            :class:`TypeKind` tokens. ``None`` means no restriction, but no function spec uses it
            (a coverage gate forbids it, so the docs never show ``ANY``).
        variadic: Whether this argument captures all remaining operands.
        optional: Whether this argument may be omitted.
        literal_only: Whether the argument must be a literal (e.g. ``field_name`` in ``LOOKUP``).
    """

    name: str
    accepts: frozenset[DataType | TypeKind] | None = None
    variadic: bool = False
    optional: bool = False
    literal_only: bool = False


class Function(ExpressionNode):
    """Base class for a named formula function node.

    A concrete function declares its ``name``, the argument render ``separator`` (``","`` for the
    handful that render without spaces, ``", "`` otherwise), and implements :meth:`result_type`.
    Construction coerces literals to operands, runs the shared spec checks (arity + accepted
    types) from :attr:`spec`, then the function-specific :meth:`validate` hook, and finally infers
    the result type. The rendered string is ``NAME(arg1<sep>arg2<sep>…)`` by default.

    Subclasses that need a different rendering (optional trailing arguments, a special wire name)
    override :meth:`render_name` or :meth:`to_string`.
    """

    name: str = ""
    separator: str = ", "
    spec: Sequence[Arg] = ()

    def __init__(self, *args: Operand | bool | int | float | str):
        self._operands: list[Operand] = [ensure_operand(a) for a in args]
        self._validate_arity()
        self._validate_types()
        self.validate()
        self._result = self.result_type()

    # --- validation engine ---

    def _validate_arity(self) -> None:
        # Derived from the spec: enforce the minimum required leading args, and — when there is no
        # variadic tail — the maximum. A no-op when no spec is declared. Reducers and other
        # "at least one" rules keep their explicit check in :meth:`validate` (the spec's minimum is
        # 0 for a pure-variadic arg). The public function signatures still enforce arity too, so
        # this is an additive guard, not the sole gate.
        if not self.spec:
            return
        required = sum(1 for arg in self.spec if not arg.optional and not arg.variadic)
        if len(self._operands) < required:
            raise self.arity_error()
        if not self.spec[-1].variadic and len(self._operands) > len(self.spec):
            raise self.arity_error()

    def _validate_types(self) -> None:
        for index, operand in enumerate(self._operands):
            arg = self._arg_for_index(index)
            if arg is None or arg.accepts is None:
                continue
            dt = operand.to_data_type()
            if not arg_accepts(arg.accepts, dt):
                raise self.type_error(dt)

    def _arg_for_index(self, index: int) -> Arg | None:
        if not self.spec:
            return None
        if index < len(self.spec) and not self.spec[index].variadic:
            return self.spec[index]
        # variadic / overflow -> the last (variadic) arg, if any
        last = self.spec[-1]
        return last if last.variadic else None

    def validate(self) -> None:
        """Per-function hook for bespoke validation. Default: no extra checks."""
        return

    # --- standardised validation errors ---
    #
    # Every function raises ``ValueError`` for invalid arguments, through one of these helpers, so
    # error messages share a single consistent shape: ``"<NAME>: <reason>."``. Use the most
    # specific helper that fits; ``invalid`` is the catch-all for a bespoke clause.

    def invalid(self, reason: str) -> ValueError:
        """A ``ValueError`` for a function-specific rule: ``"<NAME>: <reason>."``."""
        reason = reason.rstrip(".")
        return ValueError(f"{self.name}: {reason}.")

    def type_error(self, *data_types: object) -> ValueError:
        """A ``ValueError`` for argument(s) of an unsupported data type."""
        rendered = ", ".join(str(dt) for dt in data_types)
        return self.invalid(f"unsupported argument type(s): {rendered}")

    def incompatible_error(self, *data_types: object) -> ValueError:
        """A ``ValueError`` for argument types that are individually valid but mutually
        incompatible (e.g. mismatched element types across variadic arguments)."""
        rendered = ", ".join(str(dt) for dt in data_types)
        return self.invalid(f"arguments must share a compatible type, got {rendered}")

    def arity_error(self) -> ValueError:
        """A ``ValueError`` for too few arguments."""
        return self.invalid("requires at least one argument")

    # --- type inference (abstract) ---

    @abstractmethod
    def result_type(self) -> BaseDataType:
        """Infer the function's return data type from its operands."""

    # --- node contract ---

    def operands(self) -> list[Operand]:
        return self._operands

    def children(self) -> Sequence[Operand]:
        return tuple(self._operands)

    def to_data_type(self) -> BaseDataType:
        return self._result

    def rendered_args(self) -> list[str]:
        return [op.to_string() for op in self._operands]

    def render_name(self) -> str:
        return self.name

    def to_string(self) -> str:
        return f"{self.render_name()}({self.separator.join(self.rendered_args())})"
