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
Per-function :class:`~daitum_model.expression.Function` node classes.

Each public formula in :mod:`daitum_model.formulas` is a thin wrapper that constructs one of these
nodes and materialises it via :meth:`~daitum_model.expression.ExpressionNode.as_formula`. The node
owns the function's argument validation, return-type inference, and exact rendering — replacing the
procedural ``formulas`` + ``_base_formulas`` pair.

These classes are internal; the public surface is the wrapper functions in ``formulas``.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, cast

from daitum_model.data_types import (
    PRIMITIVE_DATA_TYPES,
    BaseDataType,
    DataType,
    MapDataType,
    ObjectDataType,
)
from daitum_model.expression import (
    ANY_MAP,
    ANY_OBJECT,
    ANY_OBJECT_ARRAY,
    Arg,
    Function,
    TypeKind,
)

if TYPE_CHECKING:
    from daitum_model.tables import Table

_NUMERIC = {
    DataType.INTEGER,
    DataType.DECIMAL,
    DataType.INTEGER_ARRAY,
    DataType.DECIMAL_ARRAY,
}
_DECIMALS = {DataType.DECIMAL, DataType.DECIMAL_ARRAY}
_DATES = {DataType.DATE, DataType.DATETIME, DataType.DATE_ARRAY, DataType.DATETIME_ARRAY}


_BOOLEANISH = {
    DataType.BOOLEAN,
    DataType.BOOLEAN_ARRAY,
    DataType.DECIMAL,
    DataType.DECIMAL_ARRAY,
    DataType.INTEGER,
    DataType.INTEGER_ARRAY,
}


# ---------------------------------------------------------------------------
# Accepted type-kind sets (the declarative source of truth for validation + docs)
# ---------------------------------------------------------------------------
#
# These mirror the existing ``_NUMERIC`` / ``_DATES`` / ``_BOOLEANISH`` sets but cover the
# *structural* kinds (arrays, maps, objects) that single-arg ``validate()`` bodies used to check
# imperatively. Listing them declaratively lets the docs show every accepted type verbatim — no
# ``ANY``, no grouping. The composite kinds (object/map) are :class:`TypeKind` tokens because they
# are table-parameterised instances, not enum members.

#: Every primitive (non-array) scalar data type.
ALL_SCALARS: frozenset[DataType | TypeKind] = frozenset(PRIMITIVE_DATA_TYPES)
#: The seven primitive array data types (no object array).
PRIMITIVE_ARRAYS: frozenset[DataType | TypeKind] = frozenset(
    {
        DataType.INTEGER_ARRAY,
        DataType.DECIMAL_ARRAY,
        DataType.STRING_ARRAY,
        DataType.BOOLEAN_ARRAY,
        DataType.DATE_ARRAY,
        DataType.DATETIME_ARRAY,
        DataType.TIME_ARRAY,
    }
)
#: Every array data type — the seven primitive arrays plus an object array.
ALL_ARRAYS: frozenset[DataType | TypeKind] = PRIMITIVE_ARRAYS | frozenset({ANY_OBJECT_ARRAY})
#: Any map kind.
ALL_MAPS: frozenset[DataType | TypeKind] = frozenset({ANY_MAP})
#: Any object reference (singular or array).
ALL_OBJECTS: frozenset[DataType | TypeKind] = frozenset({ANY_OBJECT, ANY_OBJECT_ARRAY})
#: Every data type — the verbatim, fully-enumerated replacement for ``ANY``. Used for the genuinely
#: relational argument positions (e.g. ``IF``'s branches), whose cross-argument compatibility is
#: still enforced in ``validate()``. Includes ``NULL`` because such positions accept ``BLANK()``.
ANY_TYPE: frozenset[DataType | TypeKind] = (
    ALL_SCALARS | ALL_ARRAYS | ALL_MAPS | ALL_OBJECTS | frozenset({DataType.NULL})
)
#: Every data type except maps — scalars, arrays and objects (plus ``NULL``). The accepted set for
#: positions that take any value other than a map (e.g. ``ARRAY``'s appended fields).
ANY_NON_MAP: frozenset[DataType | TypeKind] = ANY_TYPE - ALL_MAPS


class _Reducer(Function):
    """A variadic reducer: at least one operand, every operand drawn from :attr:`accepts`.

    Subclasses set ``accepts`` (the permitted operand types) and implement :meth:`result_type`.
    ``SUM``, ``ARRAYMAX``/``ARRAYMIN``, ``AVERAGE``/``MEDIAN``/``STDEV`` and ``AND``/``OR`` all
    share this validation shape, differing only in accepted types and result inference.
    """

    accepts: frozenset[DataType] = frozenset(_NUMERIC)

    @property
    def spec(self) -> tuple[Arg, ...]:  # type: ignore[override]
        # One variadic operand drawn from this reducer's accepted types; the engine's
        # ``_validate_types`` enforces the per-operand type check.
        return (Arg("value", accepts=self.accepts, variadic=True),)

    def validate(self) -> None:
        # The spec's variadic arg carries the type check; reducers additionally require ≥1 operand.
        if not self._operands:
            raise self.arity_error()


class Sum(_Reducer):
    """``SUM`` — numeric reducer returning a scalar INTEGER/DECIMAL (no array propagation)."""

    name = "SUM"

    def result_type(self) -> BaseDataType:
        result = DataType.INTEGER
        for operand in self._operands:
            if operand.to_data_type() in _DECIMALS:
                result = DataType.DECIMAL
        return result


#: TIME only (no datetime) — the time family ``MIN`` / ``MAX`` accept alongside numeric/dates.
_TIME_ONLY = {DataType.TIME, DataType.TIME_ARRAY}
#: Time-like operands incl. datetime (matches the module ``_TIMES`` used by the time functions).
_TIME_LIKE = {DataType.TIME, DataType.DATETIME, DataType.TIME_ARRAY, DataType.DATETIME_ARRAY}
#: Numeric, date/datetime or (singular) time operands — the accepted union for ``MIN`` / ``MAX``.
_MINMAX_ACCEPTS = frozenset(_NUMERIC | _DATES | _TIME_ONLY)
#: Time-like or plain DATE operands — the per-operand accepted set for ``HOURSBETWEEN``.
_TIME_OR_DATE = frozenset(_TIME_LIKE | {DataType.DATE, DataType.DATE_ARRAY})
#: Time-like or any date/datetime operands — the first-arg accepted set for ``PLUSMINUTES``.
_TIME_OR_DATE_ALL = frozenset(_TIME_LIKE | _DATES)


class _MinMax(Function):
    """``MIN`` / ``MAX`` — scalar reducer over numeric *or* date/time/datetime inputs.

    The first operand's type family fixes the result family; every later operand must be
    compatible. Numeric inputs return INTEGER unless any is DECIMAL.
    """

    spec = (Arg("value", accepts=_MINMAX_ACCEPTS, variadic=True),)

    def validate(self) -> None:
        # The spec's variadic arg enforces union membership; the bespoke family-compatibility rule
        # (first operand fixes the family; later operands must match) stays here.
        if not self._operands:
            raise self.arity_error()
        self._result_type = self._compute()

    def _compute(self) -> DataType:
        ret = DataType.INTEGER
        first = self._operands[0].to_data_type()
        for operand in self._operands:
            dt = operand.to_data_type()
            if (
                dt not in _NUMERIC
                and dt not in _DATES
                and dt
                not in {
                    DataType.TIME,
                    DataType.TIME_ARRAY,
                }
            ):
                raise self.type_error(dt)
            if first in _NUMERIC and dt not in _NUMERIC:
                raise self.incompatible_error(dt)
            if first in {DataType.TIME, DataType.TIME_ARRAY}:
                ret = DataType.TIME
                if dt not in {DataType.TIME, DataType.TIME_ARRAY}:
                    raise self.incompatible_error(dt)
            if first in {DataType.DATE, DataType.DATE_ARRAY}:
                ret = DataType.DATE
                if dt not in {DataType.DATE, DataType.DATE_ARRAY}:
                    raise self.incompatible_error(dt)
            if first in {DataType.DATETIME, DataType.DATETIME_ARRAY}:
                ret = DataType.DATETIME
                if dt not in {DataType.DATETIME, DataType.DATETIME_ARRAY}:
                    raise self.incompatible_error(dt)
            if dt in _DECIMALS:
                ret = DataType.DECIMAL
        return ret

    def result_type(self) -> BaseDataType:
        return self._result_type


class Min(_MinMax):
    name = "MIN"


class Max(_MinMax):
    name = "MAX"


class _ArrayReducer(_Reducer):
    """``ARRAYMAX`` / ``ARRAYMIN`` — numeric reducer that propagates array-ness."""

    def result_type(self) -> BaseDataType:
        ret = DataType.INTEGER
        is_array = False
        for operand in self._operands:
            dt = operand.to_data_type()
            if dt in _DECIMALS:
                ret = DataType.DECIMAL
            if dt.is_array():
                is_array = True
        return ret.to_array() if is_array else ret


class ArrayMax(_ArrayReducer):
    name = "ARRAYMAX"


class ArrayMin(_ArrayReducer):
    name = "ARRAYMIN"


class _DecimalReducer(_Reducer):
    """``AVERAGE`` / ``MEDIAN`` / ``STDEV`` — numeric reducer that always returns DECIMAL."""

    def result_type(self) -> BaseDataType:
        return DataType.DECIMAL


class Average(_DecimalReducer):
    name = "AVERAGE"


class Median(_DecimalReducer):
    name = "MEDIAN"


class Stdev(_DecimalReducer):
    name = "STDEV"


# ---------------------------------------------------------------------------
# Logical functions
# ---------------------------------------------------------------------------


class _BooleanReducer(_Reducer):
    """``AND`` / ``OR`` — boolean-compatible reducer.

    Returns BOOLEAN when every operand is BOOLEAN (or a single array operand is given), else
    BOOLEAN_ARRAY.
    """

    accepts = frozenset(_BOOLEANISH)

    def result_type(self) -> BaseDataType:
        all_boolean = all(op.to_data_type() == DataType.BOOLEAN for op in self._operands)
        single_array = len(self._operands) == 1 and self._operands[0].to_data_type().is_array()
        return DataType.BOOLEAN if (all_boolean or single_array) else DataType.BOOLEAN_ARRAY


class And(_BooleanReducer):
    name = "AND"


class Or(_BooleanReducer):
    name = "OR"


class Not(Function):
    name = "NOT"
    spec = (Arg("value", accepts=frozenset(_BOOLEANISH)),)

    def result_type(self) -> BaseDataType:
        dt = self._operands[0].to_data_type()
        return DataType.BOOLEAN_ARRAY if dt.is_array() else DataType.BOOLEAN


class IsBlank(Function):
    name = "ISBLANK"
    spec = (Arg("value", accepts=ANY_TYPE),)

    def result_type(self) -> BaseDataType:
        return DataType.BOOLEAN


class IsError(Function):
    name = "ISERROR"
    spec = (Arg("value", accepts=ANY_TYPE),)

    def result_type(self) -> BaseDataType:
        dt = self._operands[0].to_data_type()
        return DataType.BOOLEAN_ARRAY if dt.is_array() else DataType.BOOLEAN


def _branches_compatible(left: BaseDataType, right: BaseDataType) -> bool:
    """Whether two branch types may be merged (equal, NULL on either side, or array-of-scalar)."""
    if left == right:
        return True
    if DataType.NULL in (left, right):
        return True
    if isinstance(left, DataType):
        return left.is_array() and left.from_array() == right
    if isinstance(left, ObjectDataType) and isinstance(right, ObjectDataType):
        return left.is_array() and left._source_table == right._source_table
    return False


class If(Function):
    name = "IF"
    spec = (
        Arg("condition", accepts=frozenset({DataType.BOOLEAN, DataType.INTEGER})),
        Arg("true_branch", accepts=ANY_TYPE),
        Arg("false_branch", accepts=ANY_TYPE),
    )

    def validate(self) -> None:
        _, true_branch, false_branch = self._operands
        true_dt = true_branch.to_data_type()
        false_dt = false_branch.to_data_type()
        if true_dt != false_dt and DataType.NULL not in (true_dt, false_dt):
            raise self.incompatible_error(true_dt, false_dt)
        if true_dt == DataType.NULL and false_dt == DataType.NULL:
            raise self.invalid("both branches cannot be blank")

    def result_type(self) -> BaseDataType:
        true_dt = self._operands[1].to_data_type()
        false_dt = self._operands[2].to_data_type()
        return true_dt if true_dt != DataType.NULL else false_dt


class _BranchMerge(Function):
    """``IFBLANK`` / ``IFERROR`` — two-arg branch-merge with array-of-scalar compatibility."""

    spec = (Arg("value", accepts=ANY_TYPE), Arg("blank_branch", accepts=ANY_TYPE))

    def validate(self) -> None:
        value_dt = self._operands[0].to_data_type()
        branch_dt = self._operands[1].to_data_type()
        if (
            value_dt != branch_dt
            and DataType.NULL not in (value_dt, branch_dt)
            and not _branches_compatible(value_dt, branch_dt)
        ):
            raise self.incompatible_error(value_dt, branch_dt)
        if value_dt == DataType.NULL and branch_dt == DataType.NULL:
            raise self.invalid("both branches cannot be blank")

    def result_type(self) -> BaseDataType:
        value_dt = self._operands[0].to_data_type()
        branch_dt = self._operands[1].to_data_type()
        return value_dt if value_dt != DataType.NULL else branch_dt


class IfBlank(_BranchMerge):
    name = "IFBLANK"


class IfError(_BranchMerge):
    name = "IFERROR"


class Choose(Function):
    """``CHOOSE(index, *values)`` — all value branches must share a data type."""

    name = "CHOOSE"
    spec = (Arg("index", accepts=ANY_TYPE), Arg("value", accepts=ANY_TYPE, variadic=True))

    def __init__(self, index, *values):
        if not values:
            raise self.arity_error()
        super().__init__(index, *values)

    def validate(self) -> None:
        value_operands = self._operands[1:]
        data_type = value_operands[0].to_data_type()
        for operand in value_operands:
            if operand.to_data_type() != data_type:
                raise self.incompatible_error(*(op.to_data_type() for op in value_operands))

    def result_type(self) -> BaseDataType:
        return self._operands[1].to_data_type()


# ---------------------------------------------------------------------------
# Maths & string functions
# ---------------------------------------------------------------------------

_INT_OR_ARRAY = {DataType.INTEGER, DataType.INTEGER_ARRAY}
_STRINGS = {DataType.STRING, DataType.STRING_ARRAY}
#: INTEGER/STRING and their array variants — the per-operand accepted set for ``BITAND``/``BITOR``.
_INT_OR_STRING = frozenset(
    {DataType.INTEGER, DataType.INTEGER_ARRAY, DataType.STRING, DataType.STRING_ARRAY}
)


class _TypedUnary(Function):
    """A single-operand function: the operand's type must be in :attr:`accepts`.

    Subclasses set ``accepts`` and implement :meth:`result_type`. The ``PRESERVE``/``DECIMAL``/
    ``INTEGER``/``STRING`` result strategies below cover every unary function's return rule.
    """

    accepts: frozenset[DataType] = frozenset(_NUMERIC)

    @property
    def spec(self) -> tuple[Arg, ...]:  # type: ignore[override]
        return (Arg("value", accepts=self.accepts),)

    def _scalar_or_array(self, base: DataType) -> DataType:
        dt = self._operands[0].to_data_type()
        return base.to_array() if dt.is_array() else base


class _PreserveUnary(_TypedUnary):
    """Returns the operand's own type (``ABS``/``EXP``)."""

    def result_type(self) -> BaseDataType:
        return self._operands[0].to_data_type()


class Abs(_PreserveUnary):
    name = "ABS"


class Exp(_PreserveUnary):
    name = "EXP"


class _DecimalUnary(_TypedUnary):
    """Returns DECIMAL(_ARRAY) (``LOG``/``SIN``/``COS``)."""

    def result_type(self) -> BaseDataType:
        return self._scalar_or_array(DataType.DECIMAL)


class Log(_DecimalUnary):
    name = "LOG"


class Sin(_DecimalUnary):
    name = "SIN"


class Cos(_DecimalUnary):
    name = "COS"


class _IntegerUnary(_TypedUnary):
    """Returns INTEGER(_ARRAY)."""

    def result_type(self) -> BaseDataType:
        return self._scalar_or_array(DataType.INTEGER)


class Round(_IntegerUnary):
    name = "ROUND"
    accepts = frozenset(_DECIMALS)


class Floor(_IntegerUnary):
    name = "FLOOR"
    accepts = frozenset(_DECIMALS)


class Ceiling(_IntegerUnary):
    name = "CEILING"
    accepts = frozenset(_DECIMALS)


class Integer(_IntegerUnary):
    name = "INTEGER"
    accepts = frozenset(
        {
            DataType.BOOLEAN,
            DataType.BOOLEAN_ARRAY,
            DataType.DECIMAL,
            DataType.DECIMAL_ARRAY,
            DataType.STRING,
            DataType.STRING_ARRAY,
        }
    )


class Len(_IntegerUnary):
    name = "LEN"
    accepts = frozenset(_NUMERIC | _STRINGS)


class _StringUnary(_TypedUnary):
    """Returns STRING(_ARRAY) (``LOWER``/``UPPER``/``TRIM``)."""

    accepts = frozenset(_STRINGS)

    def result_type(self) -> BaseDataType:
        return self._scalar_or_array(DataType.STRING)


class Lower(_StringUnary):
    name = "LOWER"


class Upper(_StringUnary):
    name = "UPPER"


class Trim(_StringUnary):
    name = "TRIM"


class Char(_StringUnary):
    name = "CHAR"
    accepts = frozenset(_INT_OR_ARRAY)


class Bitmask(_TypedUnary):
    name = "BITMASK"
    accepts = frozenset({DataType.BOOLEAN_ARRAY})

    def result_type(self) -> BaseDataType:
        return DataType.INTEGER


class BitmaskString(_TypedUnary):
    name = "BITMASKSTRING"
    accepts = frozenset({DataType.BOOLEAN_ARRAY})

    def result_type(self) -> BaseDataType:
        return DataType.STRING


_SCALAR_NUMERIC = frozenset({DataType.INTEGER, DataType.DECIMAL})


class Mod(Function):
    name = "MOD"
    spec = (Arg("number", accepts=_SCALAR_NUMERIC), Arg("divisor", accepts=_SCALAR_NUMERIC))

    def result_type(self) -> BaseDataType:
        n = self._operands[0].to_data_type()
        d = self._operands[1].to_data_type()
        if n == DataType.INTEGER and d == DataType.INTEGER:
            return DataType.INTEGER
        return DataType.DECIMAL


class Power(Function):
    name = "POWER"
    spec = (
        Arg("mantissa", accepts=frozenset(_NUMERIC)),
        Arg("exponent", accepts=frozenset(_NUMERIC)),
    )

    def result_type(self) -> BaseDataType:
        m = self._operands[0].to_data_type()
        e = self._operands[1].to_data_type()
        base = DataType.INTEGER if m in _INT_OR_ARRAY and e in _INT_OR_ARRAY else DataType.DECIMAL
        return base.to_array() if (m.is_array() or e.is_array()) else base


class _LeftRight(Function):
    """``LEFT``/``RIGHT`` — (STRING, INTEGER) -> STRING, array-propagating."""

    spec = (
        Arg("input_string", accepts=frozenset(_STRINGS)),
        Arg("length", accepts=frozenset(_INT_OR_ARRAY)),
    )

    def result_type(self) -> BaseDataType:
        s = self._operands[0].to_data_type()
        n = self._operands[1].to_data_type()
        return DataType.STRING_ARRAY if (s.is_array() or n.is_array()) else DataType.STRING


class Left(_LeftRight):
    name = "LEFT"


class Right(_LeftRight):
    name = "RIGHT"


class _BitOp(Function):
    """``BITAND``/``BITOR`` — both operands INTEGER or STRING (and equal base type)."""

    spec = (
        Arg("field_1", accepts=_INT_OR_STRING),
        Arg("field_2", accepts=_INT_OR_STRING),
    )

    def validate(self) -> None:
        # The spec enforces per-operand INTEGER/STRING membership; the equal-base-type rule is
        # cross-argument and stays here.
        a = self._operands[0].to_data_type()
        b = self._operands[1].to_data_type()
        a_base = a.from_array() if a.is_array() else a
        b_base = b.from_array() if b.is_array() else b
        if a_base != b_base:
            raise self.incompatible_error(a, b)

    def result_type(self) -> BaseDataType:
        a = self._operands[0].to_data_type()
        b = self._operands[1].to_data_type()
        return a if a.is_array() else b


class BitAnd(_BitOp):
    name = "BITAND"


class BitOr(_BitOp):
    name = "BITOR"


class Find(Function):
    """``FIND(match, search[, start])`` — STRING search returning INTEGER(_ARRAY)."""

    name = "FIND"
    spec = (
        Arg("match_string", accepts=frozenset(_STRINGS)),
        Arg("search_string", accepts=frozenset(_STRINGS)),
        Arg("start_index", accepts=frozenset(_INT_OR_ARRAY), optional=True),
    )

    def __init__(self, match_string, search_string, start_index=None):
        args = [match_string, search_string]
        if start_index is not None:
            args.append(start_index)
        self._has_start = start_index is not None
        super().__init__(*args)

    def result_type(self) -> BaseDataType:
        m = self._operands[0].to_data_type()
        s = self._operands[1].to_data_type()
        is_array = s.is_array() or m.is_array()
        if self._has_start and self._operands[2].to_data_type().is_array():
            is_array = True
        return DataType.INTEGER_ARRAY if is_array else DataType.INTEGER


class Text(Function):
    """``TEXT(value[, formatting])`` -> STRING(_ARRAY)."""

    name = "TEXT"
    spec = (
        Arg("value", accepts=ANY_TYPE),
        Arg("formatting", accepts=frozenset(_STRINGS), optional=True),
    )

    def __init__(self, value, formatting=None):
        args = [value]
        if formatting is not None:
            args.append(formatting)
        self._has_formatting = formatting is not None
        super().__init__(*args)

    def result_type(self) -> BaseDataType:
        is_array = self._operands[0].to_data_type().is_array()
        if self._has_formatting and self._operands[1].to_data_type().is_array():
            is_array = True
        return DataType.STRING_ARRAY if is_array else DataType.STRING


class TextJoin(Function):
    """``TEXTJOIN(delimiter, ignore_empty, *string_arrays)`` -> STRING."""

    name = "TEXTJOIN"
    spec = (
        Arg("delimiter", accepts=frozenset(_STRINGS)),
        Arg("ignore_empty", accepts=frozenset({DataType.BOOLEAN})),
        Arg("string_array", accepts=frozenset(_STRINGS), variadic=True),
    )

    def __init__(self, delimiter, ignore_empty, *string_arrays):
        if not string_arrays:
            raise self.arity_error()
        self._n_fixed = 2
        super().__init__(delimiter, ignore_empty, *string_arrays)

    def result_type(self) -> BaseDataType:
        return DataType.STRING


# ---------------------------------------------------------------------------
# Date / time functions
# ---------------------------------------------------------------------------

_TIMES = {DataType.TIME, DataType.DATETIME, DataType.TIME_ARRAY, DataType.DATETIME_ARRAY}


class Day(_IntegerUnary):
    name = "DAY"
    accepts = frozenset(_DATES)


class Month(_IntegerUnary):
    name = "MONTH"
    accepts = frozenset(_DATES)


class Year(_IntegerUnary):
    name = "YEAR"
    accepts = frozenset(_DATES)


class Hour(_IntegerUnary):
    name = "HOUR"
    accepts = frozenset(_TIMES)


class Minute(_IntegerUnary):
    name = "MINUTE"
    accepts = frozenset(_TIMES)


class Second(_IntegerUnary):
    name = "SECOND"
    accepts = frozenset(_TIMES)


class _Between(Function):
    """``DAYSBETWEEN``/``MONTHSBETWEEN`` — two date-likes -> INTEGER(_ARRAY)."""

    spec = (
        Arg("first_date", accepts=frozenset(_DATES)),
        Arg("second_date", accepts=frozenset(_DATES)),
    )

    def result_type(self) -> BaseDataType:
        a = self._operands[0].to_data_type()
        b = self._operands[1].to_data_type()
        return DataType.INTEGER_ARRAY if (a.is_array() or b.is_array()) else DataType.INTEGER


class DaysBetween(_Between):
    name = "DAYSBETWEEN"


class MonthsBetween(_Between):
    name = "MONTHSBETWEEN"


class HoursBetween(Function):
    """``HOURSBETWEEN`` — two time-like (or date) values of the same singular type -> DECIMAL."""

    name = "HOURSBETWEEN"
    spec = (
        Arg("first_time", accepts=_TIME_OR_DATE),
        Arg("second_time", accepts=_TIME_OR_DATE),
    )

    def validate(self) -> None:
        # The spec enforces per-operand membership; the same-singular-type rule is cross-argument.
        a = self._operands[0].to_data_type()
        b = self._operands[1].to_data_type()
        sa = a.from_array() if a.is_array() else a
        sb = b.from_array() if b.is_array() else b
        if sa != sb:
            raise self.incompatible_error(a, b)

    def result_type(self) -> BaseDataType:
        a = self._operands[0].to_data_type()
        b = self._operands[1].to_data_type()
        return DataType.DECIMAL_ARRAY if (a.is_array() or b.is_array()) else DataType.DECIMAL


class PlusDays(Function):
    """``PLUSDAYS(date, days)`` — array-ness follows *days*."""

    name = "PLUSDAYS"
    spec = (
        Arg("date", accepts=frozenset(_DATES)),
        Arg("days", accepts=frozenset(_INT_OR_ARRAY)),
    )

    def result_type(self) -> BaseDataType:
        date_dt = self._operands[0].to_data_type()
        days_dt = self._operands[1].to_data_type()
        return date_dt if days_dt == DataType.INTEGER else date_dt.to_array()


class PlusMinutes(Function):
    """``PLUSMINUTES(time, minutes)`` — array-ness follows *minutes*; time may be date or time."""

    name = "PLUSMINUTES"
    spec = (
        Arg("time", accepts=_TIME_OR_DATE_ALL),
        Arg("minutes", accepts=frozenset(_INT_OR_ARRAY)),
    )

    def result_type(self) -> BaseDataType:
        time_dt = self._operands[0].to_data_type()
        minutes_dt = self._operands[1].to_data_type()
        return time_dt if minutes_dt == DataType.INTEGER else time_dt.to_array()


class EoMonth(Function):
    """``EOMONTH(date[, months])`` -> DATE(_ARRAY)."""

    name = "EOMONTH"
    spec = (
        Arg("date", accepts=frozenset(_DATES)),
        Arg("months", accepts=frozenset(_NUMERIC)),
    )

    def __init__(self, date, months=0):
        super().__init__(date, months)

    def result_type(self) -> BaseDataType:
        date_dt = self._operands[0].to_data_type()
        months_dt = self._operands[1].to_data_type()
        return (
            DataType.DATE_ARRAY if (date_dt.is_array() or months_dt.is_array()) else DataType.DATE
        )


class SetTime(Function):
    name = "SETTIME"
    spec = (
        Arg("date", accepts=frozenset(_DATES)),
        Arg("time", accepts=frozenset(_TIMES)),
    )

    def result_type(self) -> BaseDataType:
        date_dt = self._operands[0].to_data_type()
        time_dt = self._operands[1].to_data_type()
        return (
            DataType.DATETIME_ARRAY
            if (date_dt.is_array() or time_dt.is_array())
            else DataType.DATETIME
        )


class Date(Function):
    name = "DATE"
    spec = (
        Arg("year", accepts=frozenset(_NUMERIC)),
        Arg("month", accepts=frozenset(_NUMERIC)),
        Arg("day", accepts=frozenset(_NUMERIC)),
    )

    def result_type(self) -> BaseDataType:
        types = [op.to_data_type() for op in self._operands]
        return DataType.DATE_ARRAY if any(dt.is_array() for dt in types) else DataType.DATE


class Time(Function):
    name = "TIME"
    spec = (
        Arg("hours", accepts=frozenset(_INT_OR_ARRAY)),
        Arg("minutes", accepts=frozenset(_INT_OR_ARRAY)),
        Arg("seconds", accepts=frozenset(_INT_OR_ARRAY)),
    )

    def result_type(self) -> BaseDataType:
        types = [op.to_data_type() for op in self._operands]
        return DataType.TIME_ARRAY if any(dt.is_array() for dt in types) else DataType.TIME


class DateTime(Function):
    name = "DATETIME"
    spec = (
        Arg("year", accepts=frozenset(_NUMERIC)),
        Arg("month", accepts=frozenset(_NUMERIC)),
        Arg("day", accepts=frozenset(_NUMERIC)),
        Arg("hours", accepts=frozenset(_NUMERIC)),
        Arg("minutes", accepts=frozenset(_NUMERIC)),
        Arg("seconds", accepts=frozenset(_NUMERIC)),
    )

    def result_type(self) -> BaseDataType:
        types = [op.to_data_type() for op in self._operands]
        return DataType.DATETIME_ARRAY if any(dt.is_array() for dt in types) else DataType.DATETIME


class Weekday(Function):
    """``WEEKDAY(date[, return_type])`` -> INTEGER(_ARRAY)."""

    name = "WEEKDAY"
    spec = (
        Arg("date", accepts=frozenset(_DATES)),
        Arg("return_type", accepts=frozenset(_NUMERIC), optional=True),
    )

    def __init__(self, date, return_type=None):
        args = [date]
        if return_type is not None:
            args.append(return_type)
        self._has_return_type = return_type is not None
        super().__init__(*args)

    def result_type(self) -> BaseDataType:
        date_dt = self._operands[0].to_data_type()
        base = DataType.INTEGER_ARRAY if date_dt.is_array() else DataType.INTEGER
        if self._has_return_type:
            rt = self._operands[1].to_data_type()
            return (
                DataType.INTEGER
                if (not rt.is_array() and base == DataType.INTEGER)
                else DataType.INTEGER_ARRAY
            )
        return base


class _Timezone(Function):
    """``TOTIMEZONE``/``FROMTIMEZONE`` — (DATETIME, STRING) -> DATETIME(_ARRAY)."""

    spec = (
        Arg("date_time", accepts=frozenset({DataType.DATETIME, DataType.DATETIME_ARRAY})),
        Arg("time_zone", accepts=frozenset(_STRINGS)),
    )

    def result_type(self) -> BaseDataType:
        dt = self._operands[0].to_data_type()
        tz = self._operands[1].to_data_type()
        return DataType.DATETIME_ARRAY if (dt.is_array() or tz.is_array()) else DataType.DATETIME


class ToTimezone(_Timezone):
    name = "TOTIMEZONE"


class FromTimezone(_Timezone):
    name = "FROMTIMEZONE"


# ---------------------------------------------------------------------------
# Array / lookup / object / probability functions
# ---------------------------------------------------------------------------

_BOOLEAN = DataType.BOOLEAN


class RowVector(Function):
    name = "ROWVECTOR"

    def __init__(self):
        super().__init__()

    def result_type(self) -> BaseDataType:
        return DataType.INTEGER_ARRAY


class Blank(Function):
    name = "BLANK"

    def __init__(self, data_type=None):
        self._explicit = data_type
        super().__init__()

    def result_type(self) -> BaseDataType:
        return self._explicit if self._explicit else DataType.NULL


class Prev(Function):
    name = "PREV"
    spec = (Arg("field", accepts=ANY_TYPE),)

    def result_type(self) -> BaseDataType:
        return self._operands[0].to_data_type()


class Next(Function):
    name = "NEXT"
    spec = (Arg("field", accepts=ANY_TYPE),)

    def result_type(self) -> BaseDataType:
        return self._operands[0].to_data_type()


class Size(Function):
    name = "SIZE"
    spec = (Arg("array", accepts=ALL_ARRAYS),)

    def result_type(self) -> BaseDataType:
        return DataType.INTEGER


class Rows(Function):
    name = "ROWS"
    spec = (Arg("array", accepts=ALL_ARRAYS),)

    def result_type(self) -> BaseDataType:
        return DataType.INTEGER


class CountBlanks(Function):
    name = "COUNTBLANKS"
    spec = (Arg("array", accepts=ALL_ARRAYS),)

    def result_type(self) -> BaseDataType:
        return DataType.INTEGER


class Values(Function):
    name = "VALUES"
    spec = (Arg("value", accepts=ALL_MAPS),)

    def result_type(self) -> BaseDataType:
        return cast(MapDataType, self._operands[0].to_data_type())._data_type.to_array()


class Distinct(Function):
    name = "DISTINCT"
    spec = (Arg("array", accepts=ALL_ARRAYS),)

    def result_type(self) -> BaseDataType:
        return self._operands[0].to_data_type()


class Contains(Function):
    name = "CONTAINS"
    spec = (
        Arg("search_array", accepts=ALL_ARRAYS),
        Arg("search_value", accepts=ALL_SCALARS | frozenset({ANY_OBJECT})),
    )  # cross-arg: search_value must be the element type of search_array (checked in validate)

    def validate(self) -> None:
        arr = self._operands[0].to_data_type()
        val = self._operands[1].to_data_type()
        if not arr.is_array():
            raise self.type_error(arr, val)
        if val.is_array():
            raise self.type_error(arr, val)
        if isinstance(arr, DataType) and isinstance(val, DataType):
            if arr.from_array() != val:
                raise self.incompatible_error(arr, val)
        elif isinstance(arr, ObjectDataType) and isinstance(val, ObjectDataType):
            if arr._source_table != val._source_table:
                raise self.incompatible_error(arr, val)
        else:
            raise self.type_error(arr, val)

    def result_type(self) -> BaseDataType:
        return DataType.BOOLEAN


class Distribute(Function):
    name = "DISTRIBUTE"
    spec = (
        Arg("value", accepts=frozenset({DataType.INTEGER})),
        Arg("array", accepts=frozenset({DataType.INTEGER_ARRAY})),
    )

    def result_type(self) -> BaseDataType:
        return DataType.INTEGER_ARRAY


class Count(Function):
    name = "COUNT"
    spec = (
        Arg("array", accepts=ALL_ARRAYS),
        Arg("value", accepts=ALL_SCALARS | ALL_OBJECTS),
    )  # cross-arg: value must be the element type of array (checked in validate)

    def validate(self) -> None:
        arr = self._operands[0].to_data_type()
        val = self._operands[1].to_data_type()
        if isinstance(arr, MapDataType) or isinstance(val, MapDataType):
            raise self.type_error(arr, val)
        if not arr.is_array():
            raise self.type_error(arr, val)
        if not isinstance(arr, ObjectDataType):
            if arr.from_array() != val:
                raise self.incompatible_error(arr, val)
        elif not isinstance(val, ObjectDataType):
            raise self.incompatible_error(arr, val)

    def result_type(self) -> BaseDataType:
        return DataType.INTEGER


class _DuplicateCheck(Function):
    """``COUNTDUPLICATES``/``FINDDUPLICATES`` — (array, BOOLEAN, BOOLEAN)."""

    _result: BaseDataType = DataType.INTEGER
    spec = (
        Arg("array", accepts=ALL_ARRAYS),
        Arg("include_first_instance", accepts=frozenset({DataType.BOOLEAN})),
        Arg("ignore_blanks", accepts=frozenset({DataType.BOOLEAN})),
    )


class CountDuplicates(_DuplicateCheck):
    name = "COUNTDUPLICATES"

    def result_type(self) -> BaseDataType:
        return DataType.INTEGER


class FindDuplicates(_DuplicateCheck):
    name = "FINDDUPLICATES"

    def result_type(self) -> BaseDataType:
        return DataType.BOOLEAN_ARRAY


class Rank(Function):
    name = "RANK"
    spec = (
        # cross-arg: comparison_value must be the (primitive) element type of array (validate)
        Arg("comparison_value", accepts=ALL_SCALARS),
        Arg("array", accepts=PRIMITIVE_ARRAYS),
        Arg("ascending", accepts=frozenset({DataType.BOOLEAN})),
    )

    def __init__(self, comparison_value, array, ascending=False):
        super().__init__(comparison_value, array, ascending)

    def validate(self) -> None:
        cmp = self._operands[0].to_data_type()
        arr = self._operands[1].to_data_type()
        asc = self._operands[2].to_data_type()
        if isinstance(arr, (MapDataType, ObjectDataType)) or isinstance(
            cmp, (MapDataType, ObjectDataType)
        ):
            raise self.type_error(cmp, arr)
        if cmp.is_array() or not arr.is_array():
            raise self.type_error(cmp, arr)
        if cmp.to_array() != arr:
            raise self.incompatible_error(cmp, arr)
        if asc != DataType.BOOLEAN:
            raise self.type_error(asc)

    def result_type(self) -> BaseDataType:
        return DataType.INTEGER


class ToMap(Function):
    """``TOMAP(array, table)`` — *table* is a map key-source rendered as its id, not an operand."""

    name = "TOMAP"
    # ``table`` is a map key-source rendered as its id, not an operand, so it is not in the spec.
    # Maps are keyed by a primitive value type, so an object array has no valid map value type.
    spec = (Arg("array", accepts=PRIMITIVE_ARRAYS),)

    def __init__(self, array, table):
        self._table = table
        super().__init__(array)

    def result_type(self) -> BaseDataType:
        arr = self._operands[0].to_data_type()
        return MapDataType(cast(DataType, arr.from_array()), self._table)

    def to_string(self) -> str:
        return f"TOMAP({self._operands[0].to_string()}, {self._table.id})"


class Get(Function):
    name = "GET"
    spec = (
        Arg("map_object", accepts=ALL_MAPS),
        Arg("key", accepts=frozenset({ANY_OBJECT})),
    )  # cross-arg: key's source table must match the map's (checked in validate)

    def validate(self) -> None:
        map_dt = self._operands[0].to_data_type()
        key_dt = self._operands[1].to_data_type()
        if not isinstance(map_dt, MapDataType):
            raise self.type_error(map_dt)
        if not isinstance(key_dt, ObjectDataType):
            raise self.type_error(key_dt)
        if key_dt.is_array() or key_dt._source_table != map_dt._source_table:
            raise self.incompatible_error(map_dt, key_dt)

    def result_type(self) -> BaseDataType:
        return cast(MapDataType, self._operands[0].to_data_type())._data_type


class Array(Function):
    """``ARRAY(ignore_null, *fields)`` — all non-blank fields share a base type."""

    name = "ARRAY"
    spec = (
        Arg("ignore_null", accepts=frozenset({DataType.BOOLEAN})),
        # cross-arg: all non-blank fields must share a base type, appended element-wise; maps are
        # rejected (their `to_array()` is undefined). Cross-argument compatibility is in validate.
        Arg("field", accepts=ANY_NON_MAP, variadic=True),
    )

    def __init__(self, ignore_null, *fields):
        if not fields:
            raise self.arity_error()
        super().__init__(ignore_null, *fields)

    def validate(self) -> None:
        base = self._base_type()
        for field in self._operands[1:]:
            fdt = field.to_data_type()
            if fdt == DataType.NULL:
                continue
            f_base = fdt.from_array() if fdt.is_array() else fdt
            if f_base != base:
                raise self.incompatible_error(*(op.to_data_type() for op in self._operands[1:]))

    def _base_type(self):
        first = next((f for f in self._operands[1:] if f.to_data_type() != DataType.NULL), None)
        if first is None:
            raise self.invalid("requires at least one non-blank field to determine its type")
        dt = first.to_data_type()
        return dt.from_array() if dt.is_array() else dt

    def result_type(self) -> BaseDataType:
        base = self._base_type()
        if isinstance(base, ObjectDataType):
            return ObjectDataType(base._source_table, is_array=True)
        if isinstance(base, DataType):
            return base.to_array()
        raise self.type_error(base)


class _SetOp(Function):
    """``UNION``/``INTERSECTION`` — (BOOLEAN ignore_blanks, *arrays of one type)."""

    name = ""
    spec = (
        Arg("ignore_blanks", accepts=frozenset({DataType.BOOLEAN})),
        # cross-arg: ≥1 array, all the same type (checked in validate)
        Arg("array", accepts=ALL_ARRAYS, variadic=True),
    )

    def __init__(self, ignore_blanks, *arrays):
        super().__init__(ignore_blanks, *arrays)

    def validate(self) -> None:
        arrays = self._operands[1:]
        if len(arrays) < 1:
            raise self.arity_error()
        first = arrays[0].to_data_type()
        if not first.is_array():
            raise self.type_error(first)
        for arr in arrays:
            if arr.to_data_type() != first:
                raise self.incompatible_error(*(a.to_data_type() for a in arrays))

    def result_type(self) -> BaseDataType:
        return self._operands[1].to_data_type()


class Union(_SetOp):
    name = "UNION"


class Intersection(_SetOp):
    name = "INTERSECTION"


class LookupArray(Function):
    name = "LOOKUPARRAY"
    spec = (
        Arg("source_array", accepts=ALL_ARRAYS),
        Arg("match_array", accepts=ALL_ARRAYS),
        Arg("result_array", accepts=ALL_ARRAYS),
    )  # cross-arg: source_array and match_array must share a type (checked in validate)

    def validate(self) -> None:
        s = self._operands[0].to_data_type()
        m = self._operands[1].to_data_type()
        r = self._operands[2].to_data_type()
        if isinstance(s, MapDataType) or isinstance(m, MapDataType) or isinstance(r, MapDataType):
            raise self.type_error(s, m, r)
        if not s.is_array() or not m.is_array() or not r.is_array():
            raise self.type_error(s, m, r)
        if s != m:
            raise self.incompatible_error(s, m)

    def result_type(self) -> BaseDataType:
        return self._operands[2].to_data_type()

    def render_name(self) -> str:
        return "LOOKUP_ARRAY"


class Index(Function):
    """``INDEX(array, index)`` — receiver-shape sensitive (see breaking-change log)."""

    name = "INDEX"
    spec = (
        # array/object-array/table receiver; the table receiver-shape rule stays in validate
        Arg("array", accepts=ALL_ARRAYS),
        Arg("index", accepts=frozenset(_INT_OR_ARRAY)),
    )

    def __init__(self, array, index):
        from daitum_model.tables import Table

        self._array_is_table = isinstance(array, Table)
        self._table_arg = array if self._array_is_table else None
        super().__init__(array, index)

    def validate(self) -> None:
        # The spec enforces the ``index`` type; the receiver-shape rules stay here.
        if self._array_is_table:
            return
        arr = self._operands[0].to_data_type()
        if isinstance(arr, MapDataType):
            raise self.type_error(arr)
        if isinstance(arr, ObjectDataType):
            if not arr.is_array():
                raise self.type_error(arr)
            return
        if not arr.is_array():
            raise self.type_error(arr)

    def result_type(self) -> BaseDataType:
        idx = self._operands[1].to_data_type()
        is_array = idx.is_array()
        if self._table_arg is not None:
            return ObjectDataType(self._table_arg, is_array)
        arr = self._operands[0].to_data_type()
        if isinstance(arr, ObjectDataType):
            return ObjectDataType(arr._source_table, False)
        return arr if is_array else arr.from_array()


class Match(Function):
    name = "MATCH"
    spec = (
        # cross-arg: lookup_value must be the element type of lookup_array (checked in validate)
        Arg("lookup_value", accepts=ALL_SCALARS | frozenset({ANY_OBJECT})),
        Arg("lookup_array", accepts=ALL_ARRAYS),
        Arg("reverse_search", accepts=frozenset({DataType.BOOLEAN})),
    )

    def __init__(self, lookup_value, lookup_array, reverse_search=False):
        super().__init__(lookup_value, lookup_array, reverse_search)

    def validate(self) -> None:
        arr = self._operands[1].to_data_type()
        if not arr.is_array():
            raise self.type_error(arr)
        value = self._operands[0].to_data_type()
        if arr.from_array() != value:
            raise self.incompatible_error(value, arr)

    def result_type(self) -> BaseDataType:
        return DataType.INTEGER


class _ProbabilityDist(Function):
    """Probability dists returning DECIMAL(_ARRAY): 3 numeric + 1 boolean-ish cumulative arg."""

    _n_numeric = 3
    spec = (
        Arg("x", accepts=frozenset(_NUMERIC)),
        Arg("arg_2", accepts=frozenset(_NUMERIC)),
        Arg("arg_3", accepts=frozenset(_NUMERIC)),
        Arg("cumulative", accepts=frozenset(_BOOLEANISH)),
    )

    def result_type(self) -> BaseDataType:
        if any(op.to_data_type().is_array() for op in self._operands):
            return DataType.DECIMAL_ARRAY
        return DataType.DECIMAL


class NormDist(_ProbabilityDist):
    name = "NORMDIST"


class GammaDist(_ProbabilityDist):
    name = "GAMMADIST"


class BinomDist(_ProbabilityDist):
    name = "BINOMDIST"


class Weibull(_ProbabilityDist):
    name = "WEIBULL"


class _ProbabilityInv(Function):
    """``NORMINV``/``GAMMAINV`` — 3 numeric args -> DECIMAL(_ARRAY)."""

    spec = (
        Arg("probability", accepts=frozenset(_NUMERIC)),
        Arg("arg_2", accepts=frozenset(_NUMERIC)),
        Arg("arg_3", accepts=frozenset(_NUMERIC)),
    )

    def result_type(self) -> BaseDataType:
        if any(op.to_data_type().is_array() for op in self._operands):
            return DataType.DECIMAL_ARRAY
        return DataType.DECIMAL


class NormInv(_ProbabilityInv):
    name = "NORMINV"


class GammaInv(_ProbabilityInv):
    name = "GAMMAINV"


class BinomInv(Function):
    """``BINOMINV(trials, probability_s, probability)`` -> INTEGER(_ARRAY)."""

    name = "BINOMINV"
    spec = (
        Arg("trials", accepts=frozenset(_NUMERIC)),
        Arg("probability_s", accepts=frozenset(_NUMERIC)),
        Arg("probability", accepts=frozenset(_NUMERIC)),
    )

    def result_type(self) -> BaseDataType:
        if any(op.to_data_type().is_array() for op in self._operands):
            return DataType.INTEGER_ARRAY
        return DataType.INTEGER


class Lookup(Function):
    """``LOOKUP(table, field_name, condition[, reverse_search])`` -> OBJECT."""

    name = "LOOKUP"
    spec = (
        Arg("table", accepts=frozenset({ANY_OBJECT_ARRAY})),  # a table or OBJECT_ARRAY
        Arg("field_name", accepts=frozenset({DataType.STRING}), literal_only=True),
        # cross-arg: condition must match the named column's type (checked in validate)
        Arg("condition", accepts=ANY_TYPE),
        Arg("reverse_search", accepts=frozenset({DataType.BOOLEAN})),
    )

    def __init__(self, table, field_name, condition, reverse_search=False):
        from daitum_model.expression import ensure_operand

        # `field_name` may be a raw string referring to a column; keep it as a CONST operand but
        # validate existence/compatibility against the resolved source table.
        if not _operand_is_object_array(table):
            raise self.invalid("can only be called on a table or OBJECT_ARRAY")
        self._table_operand = table
        self._field_is_literal = isinstance(field_name, str)
        self._field_name = field_name
        super().__init__(
            table,
            ensure_operand(field_name),
            ensure_operand(condition),
            ensure_operand(reverse_search),
        )

    def validate(self) -> None:
        table_dt = cast(ObjectDataType, self._operands[0].to_data_type())
        source_table = cast("Table", table_dt._source_table)
        condition = self._operands[2]
        if self._field_is_literal:
            field = source_table.get_field(self._field_name)
            if not field:
                raise self.invalid(f"field '{self._field_name}' does not exist in the table")
            if condition.to_data_type() != field.to_data_type():
                raise self.incompatible_error(field.to_data_type(), condition.to_data_type())

    def result_type(self) -> BaseDataType:
        table_dt = cast(ObjectDataType, self._operands[0].to_data_type())
        return ObjectDataType(table_dt._source_table)

    def to_string(self) -> str:
        return (
            f"LOOKUP({self._table_operand.to_string()}, {self._operands[1].to_string()}, "
            f"{self._operands[2].to_string()}, {self._operands[3].to_string()})"
        )


class Filter(Function):
    name = "FILTER"
    spec = (
        Arg("array", accepts=ALL_ARRAYS),
        Arg(
            "filter_condition",
            accepts=frozenset(
                {DataType.BOOLEAN_ARRAY, DataType.DECIMAL_ARRAY, DataType.INTEGER_ARRAY}
            ),
        ),
    )

    def result_type(self) -> BaseDataType:
        return self._operands[0].to_data_type()


class Baseline(Function):
    """``BASELINE(name, reference[, fallback])`` — the reference's value at a captured baseline.

    Renders ``BASELINE("optimised", [revenue])`` (or with a trailing fallback operand). The result
    type is the reference's type; the optional fallback supplies a value before the baseline is
    captured. User-facing validation (reference must be a single tracked field/named value, fallback
    type must match) lives in the :func:`~daitum_model.formulas.BASELINE` wrapper — the node only
    enforces the structural spec so the parser can reconstruct it on decode.
    """

    name = "BASELINE"
    spec = (
        Arg("baseline", accepts=frozenset({DataType.STRING})),
        Arg("reference", accepts=ANY_TYPE),
        Arg("fallback", accepts=ANY_TYPE, optional=True),
    )

    def result_type(self) -> BaseDataType:
        return self._operands[1].to_data_type()


class HasBaseline(Function):
    """``HASBASELINE(name)`` — BOOLEAN: whether the named baseline has been captured at runtime."""

    name = "HASBASELINE"
    spec = (Arg("baseline", accepts=frozenset({DataType.STRING})),)

    def result_type(self) -> BaseDataType:
        return DataType.BOOLEAN


def _operand_is_object_array(operand) -> bool:
    dt = operand.to_data_type()
    return dt.is_array() if isinstance(dt, ObjectDataType) else False
