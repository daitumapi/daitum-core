"""
The golden expression corpus: one or more representative invocations per public formula function
and per operator.

Each :class:`Case` is a named ``(builder)`` thunk that constructs an :class:`Operand` from the
shared fixture. The harness (``test_formula_contract.py``) evaluates ``to_string()`` and
``to_data_type()`` for each and asserts them against the frozen golden file — so these cases are
*invocations only*; the expected outputs are captured from the current implementation.

The cases assert on the public contract (rendered string + data type), never on node classes, so
the same corpus proves equivalence before and after the refactor.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

import daitum_model.formulas as formulas
from daitum_model.formulas import CONST

from .contract_model import Fixture


@dataclass
class Case:
    name: str
    build: Callable[[Fixture], object]


def function_cases() -> list[Case]:
    """Representative valid invocations covering every public formula function."""
    f = lambda fx: fx.fields  # noqa: E731

    cases: list[Case] = [
        # --- maths / numeric ---
        Case("ABS scalar", lambda fx: formulas.ABS(f(fx)["Cost"])),
        Case("ABS literal", lambda fx: formulas.ABS(-3)),
        Case("CEILING", lambda fx: formulas.CEILING(f(fx)["Cost"])),
        Case("FLOOR", lambda fx: formulas.FLOOR(f(fx)["Cost"])),
        Case("ROUND", lambda fx: formulas.ROUND(f(fx)["Cost"])),
        Case("INTEGER", lambda fx: formulas.INTEGER(f(fx)["Cost"])),
        Case("MOD", lambda fx: formulas.MOD(f(fx)["Qty"], 2)),
        Case("POWER", lambda fx: formulas.POWER(f(fx)["Cost"], 2)),
        Case("EXP", lambda fx: formulas.EXP(f(fx)["Cost"])),
        Case("LOG", lambda fx: formulas.LOG(f(fx)["Cost"])),
        Case("SIN", lambda fx: formulas.SIN(f(fx)["Cost"])),
        Case("COS", lambda fx: formulas.COS(f(fx)["Cost"])),
        Case("DISTRIBUTE", lambda fx: formulas.DISTRIBUTE(f(fx)["Qty"], f(fx)["Qtys"])),
        # --- reducers ---
        Case("SUM scalars", lambda fx: formulas.SUM(1, 2)),
        Case("SUM decimal", lambda fx: formulas.SUM(f(fx)["Cost"], 1.0)),
        Case("SUM array", lambda fx: formulas.SUM(f(fx)["Costs"])),
        Case("MIN", lambda fx: formulas.MIN(f(fx)["Cost"], 1.0)),
        Case("MAX", lambda fx: formulas.MAX(f(fx)["Cost"], 1.0)),
        Case("AVERAGE", lambda fx: formulas.AVERAGE(f(fx)["Cost"], 1.0)),
        Case("MEDIAN", lambda fx: formulas.MEDIAN(f(fx)["Cost"], 1.0)),
        Case("STDEV", lambda fx: formulas.STDEV(f(fx)["Cost"], 1.0)),
        Case("ARRAYMAX", lambda fx: formulas.ARRAYMAX(f(fx)["Costs"])),
        Case("ARRAYMIN", lambda fx: formulas.ARRAYMIN(f(fx)["Costs"])),
        # --- logical ---
        Case("AND", lambda fx: formulas.AND(f(fx)["Flag"], True)),
        Case("OR", lambda fx: formulas.OR(f(fx)["Flag"], True)),
        Case("NOT", lambda fx: formulas.NOT(f(fx)["Flag"])),
        Case("IF scalar", lambda fx: formulas.IF(f(fx)["Flag"], 0.0, f(fx)["Cost"])),
        Case(
            "IF null branch", lambda fx: formulas.IF(f(fx)["Flag"], formulas.BLANK(), f(fx)["Cost"])
        ),
        Case("IFBLANK", lambda fx: formulas.IFBLANK(f(fx)["Cost"], 0.0)),
        Case("IFERROR", lambda fx: formulas.IFERROR(f(fx)["Cost"], 0.0)),
        Case("ISBLANK", lambda fx: formulas.ISBLANK(f(fx)["Cost"])),
        Case("ISERROR", lambda fx: formulas.ISERROR(f(fx)["Cost"])),
        Case("CHOOSE", lambda fx: formulas.CHOOSE(f(fx)["Qty"], 1, 2, 3)),
        # --- string ---
        Case("LEFT", lambda fx: formulas.LEFT(f(fx)["Name"], 3)),
        Case("RIGHT", lambda fx: formulas.RIGHT(f(fx)["Name"], 3)),
        Case("FIND", lambda fx: formulas.FIND("x", f(fx)["Name"])),
        Case("FIND start", lambda fx: formulas.FIND("x", f(fx)["Name"], 2)),
        Case("LEN", lambda fx: formulas.LEN(f(fx)["Name"])),
        Case("LOWER", lambda fx: formulas.LOWER(f(fx)["Name"])),
        Case("UPPER", lambda fx: formulas.UPPER(f(fx)["Name"])),
        Case("TRIM", lambda fx: formulas.TRIM(f(fx)["Name"])),
        Case("CHAR", lambda fx: formulas.CHAR(f(fx)["Qty"])),
        Case("TEXT", lambda fx: formulas.TEXT(f(fx)["Cost"])),
        Case("TEXT fmt", lambda fx: formulas.TEXT(f(fx)["Cost"], "0.00")),
        Case("TEXTJOIN", lambda fx: formulas.TEXTJOIN(",", True, f(fx)["Names"])),
        Case("BITAND", lambda fx: formulas.BITAND(f(fx)["Qty"], 1)),
        Case("BITOR", lambda fx: formulas.BITOR(f(fx)["Qty"], 1)),
        Case("BITMASK", lambda fx: formulas.BITMASK(f(fx)["Flags"])),
        Case("BITMASKSTRING", lambda fx: formulas.BITMASKSTRING(f(fx)["Flags"])),
        # --- date / time ---
        Case("DATE", lambda fx: formulas.DATE(2026, 1, 1)),
        Case("DATETIME", lambda fx: formulas.DATETIME(2026, 1, 1, 0, 0, 0)),
        Case("TIME", lambda fx: formulas.TIME(1, 2, 3)),
        Case("DAY", lambda fx: formulas.DAY(f(fx)["Day"])),
        Case("MONTH", lambda fx: formulas.MONTH(f(fx)["Day"])),
        Case("YEAR", lambda fx: formulas.YEAR(f(fx)["Day"])),
        Case("HOUR", lambda fx: formulas.HOUR(f(fx)["Clock"])),
        Case("MINUTE", lambda fx: formulas.MINUTE(f(fx)["Clock"])),
        Case("SECOND", lambda fx: formulas.SECOND(f(fx)["Clock"])),
        Case("WEEKDAY", lambda fx: formulas.WEEKDAY(f(fx)["Day"])),
        Case("WEEKDAY rt", lambda fx: formulas.WEEKDAY(f(fx)["Day"], 1)),
        Case("DAYSBETWEEN", lambda fx: formulas.DAYSBETWEEN(f(fx)["Day"], f(fx)["Day"])),
        Case("HOURSBETWEEN", lambda fx: formulas.HOURSBETWEEN(f(fx)["Clock"], f(fx)["Clock"])),
        Case("MONTHSBETWEEN", lambda fx: formulas.MONTHSBETWEEN(f(fx)["Day"], f(fx)["Day"])),
        Case("PLUSDAYS", lambda fx: formulas.PLUSDAYS(f(fx)["Day"], 1)),
        Case("PLUSMINUTES", lambda fx: formulas.PLUSMINUTES(f(fx)["Clock"], 1)),
        Case("EOMONTH", lambda fx: formulas.EOMONTH(f(fx)["Day"])),
        Case("EOMONTH months", lambda fx: formulas.EOMONTH(f(fx)["Day"], 2)),
        Case("SETTIME", lambda fx: formulas.SETTIME(f(fx)["Day"], f(fx)["Clock"])),
        Case("FROMTIMEZONE", lambda fx: formulas.FROMTIMEZONE(f(fx)["Stamp"], "UTC")),
        Case("TOTIMEZONE", lambda fx: formulas.TOTIMEZONE(f(fx)["Stamp"], "UTC")),
        # --- arrays / lookups / object ---
        Case("ARRAY", lambda fx: formulas.ARRAY(True, f(fx)["Cost"], 1.0)),
        Case("ROW", lambda fx: formulas.ROW()),
        Case("ROWVECTOR", lambda fx: formulas.ROWVECTOR()),
        Case("ROWS table", lambda fx: formulas.ROWS(fx.table)),
        Case("ROWS operand", lambda fx: formulas.ROWS(f(fx)["SiteList"])),
        Case("SIZE", lambda fx: formulas.SIZE(f(fx)["Costs"])),
        Case("COUNT", lambda fx: formulas.COUNT(f(fx)["Costs"], 1.0)),
        Case("COUNTBLANKS", lambda fx: formulas.COUNTBLANKS(f(fx)["Costs"])),
        Case("COUNTDUPLICATES", lambda fx: formulas.COUNTDUPLICATES(f(fx)["Costs"], True, True)),
        Case("FINDDUPLICATES", lambda fx: formulas.FINDDUPLICATES(f(fx)["Costs"], True, True)),
        Case("DISTINCT", lambda fx: formulas.DISTINCT(f(fx)["Costs"])),
        Case("CONTAINS", lambda fx: formulas.CONTAINS(f(fx)["Costs"], 1.0)),
        Case("VALUES", lambda fx: formulas.VALUES(f(fx)["CostMap"])),
        Case("RANK", lambda fx: formulas.RANK(f(fx)["Cost"], f(fx)["Costs"])),
        Case("MATCH", lambda fx: formulas.MATCH(1.0, f(fx)["Costs"])),
        Case("INDEX table", lambda fx: formulas.INDEX(fx.table, 1)),
        Case("INDEX operand", lambda fx: formulas.INDEX(f(fx)["SiteList"], 1)),
        Case("FILTER table", lambda fx: formulas.FILTER(fx.table, f(fx)["Flags"])),
        Case("FILTER operand", lambda fx: formulas.FILTER(f(fx)["SiteList"], f(fx)["Flags"])),
        Case("LOOKUP table", lambda fx: formulas.LOOKUP(fx.other_table, "Region", "x")),
        Case("LOOKUP operand", lambda fx: formulas.LOOKUP(f(fx)["SiteList"], "Region", "x")),
        Case(
            "LOOKUPARRAY",
            lambda fx: formulas.LOOKUPARRAY(f(fx)["Costs"], f(fx)["Costs"], f(fx)["Names"]),
        ),
        Case("GET", lambda fx: formulas.GET(f(fx)["CostMap"], f(fx)["Site"])),
        Case("TOMAP", lambda fx: formulas.TOMAP(f(fx)["Costs"], fx.other_table)),
        Case("UNION", lambda fx: formulas.UNION(True, f(fx)["Costs"], f(fx)["Costs"])),
        Case(
            "INTERSECTION", lambda fx: formulas.INTERSECTION(True, f(fx)["Costs"], f(fx)["Costs"])
        ),
        Case("NEXT", lambda fx: formulas.NEXT(f(fx)["Cost"])),
        Case("PREV", lambda fx: formulas.PREV(f(fx)["Cost"])),
        # --- probability ---
        Case("NORMDIST", lambda fx: formulas.NORMDIST(1.0, 0.0, 1.0, True)),
        Case("NORMINV", lambda fx: formulas.NORMINV(0.5, 0.0, 1.0)),
        Case("BINOMDIST", lambda fx: formulas.BINOMDIST(1, 10, 0.5, True)),
        Case("BINOMINV", lambda fx: formulas.BINOMINV(10, 0.5, 0.5)),
        Case("GAMMADIST", lambda fx: formulas.GAMMADIST(1.0, 1.0, 1.0, True)),
        Case("GAMMAINV", lambda fx: formulas.GAMMAINV(0.5, 1.0, 1.0)),
        Case(
            "WEIBULL", lambda fx: formulas.WEIBULL(CONST(1.0), CONST(1.0), CONST(1.0), CONST(True))
        ),
        # --- baselines / change tracking ---
        Case("BASELINE", lambda fx: formulas.BASELINE("optimised", f(fx)["Tracked"])),
        Case(
            "BASELINE fallback",
            lambda fx: formulas.BASELINE("optimised", f(fx)["Tracked"], f(fx)["Tracked"]),
        ),
        Case("HASBASELINE", lambda fx: formulas.HASBASELINE("optimised")),
        # --- constants ---
        Case("BLANK", lambda fx: formulas.BLANK()),
        Case("BLANK typed", lambda fx: formulas.BLANK(__import__("daitum_model").DataType.DECIMAL)),
        Case("CONST int", lambda fx: CONST(5)),
        Case("CONST float", lambda fx: CONST(2.5)),
        Case("CONST str", lambda fx: CONST("hi")),
        Case("CONST bool", lambda fx: CONST(True)),
    ]
    return cases


def operator_cases() -> list[Case]:
    """Characterise every operator from the §3.3.1 inventory."""
    f = lambda fx: fx.fields  # noqa: E731
    cases: list[Case] = [
        # arithmetic
        Case("add ints", lambda fx: f(fx)["Qty"] + 1),
        Case("add decimal", lambda fx: f(fx)["Cost"] + 1.0),
        Case("radd", lambda fx: 1 + f(fx)["Qty"]),
        Case("add array", lambda fx: f(fx)["Costs"] + 1.0),
        Case("sub", lambda fx: f(fx)["Cost"] - f(fx)["Qty"]),
        Case("rsub", lambda fx: 1 - f(fx)["Qty"]),
        Case("mul", lambda fx: f(fx)["Cost"] * f(fx)["Qty"]),
        Case("rmul", lambda fx: 2 * f(fx)["Cost"]),
        Case("div", lambda fx: f(fx)["Cost"] / f(fx)["Qty"]),
        Case("rdiv", lambda fx: 1 / f(fx)["Cost"]),
        Case("pow", lambda fx: f(fx)["Cost"] ^ 2),
        Case("rpow", lambda fx: 2 ^ f(fx)["Qty"]),
        # string concat (the +-when-string path)
        Case("concat", lambda fx: f(fx)["Name"] + "x"),
        Case("rconcat", lambda fx: "x" + f(fx)["Name"]),
        Case("concat array", lambda fx: f(fx)["Names"] + "x"),
        # comparison
        Case("lt", lambda fx: f(fx)["Cost"] < f(fx)["Qty"]),
        Case("gt", lambda fx: f(fx)["Cost"] > 1.0),
        Case("le", lambda fx: f(fx)["Cost"] <= 1.0),
        Case("ge", lambda fx: f(fx)["Cost"] >= 1.0),
        Case("lt array", lambda fx: f(fx)["Costs"] < 1.0),
        # equality
        Case("equal_to", lambda fx: f(fx)["Cost"].equal_to(1.0)),
        Case("equal_to str", lambda fx: f(fx)["Name"].equal_to("x")),
        Case("not_equal_to", lambda fx: f(fx)["Cost"].not_equal_to(1.0)),
        Case("equal_to array", lambda fx: f(fx)["Costs"].equal_to(1.0)),
        # negate
        Case("neg", lambda fx: -f(fx)["Cost"]),
        Case("neg array", lambda fx: -f(fx)["Costs"]),
        # member access (Operand.__getitem__ -> base.[field])
        Case("member access scalar", lambda fx: f(fx)["Site"]["Amount"]),
        Case("member access array", lambda fx: f(fx)["SiteList"]["Amount"]),
        # column access (Table.__getitem__ -> table[field])
        Case("column access", lambda fx: fx.table["Cost"]),
        Case("column access object", lambda fx: fx.table["Site"]),
        # in-place mutation family
        Case("iadd", _iadd),
        Case("imul", _imul),
        Case("isub", _isub),
        Case("itruediv", _itruediv),
        # accumulator-loop pattern external models rely on (formula = CONST(0); for x: formula += x)
        Case("accumulator loop", _accumulator_loop),
    ]
    return cases


def _iadd(fx: Fixture) -> object:
    g = fx.table["Cost"]  # a fresh Formula
    g += 1.0
    return g


def _imul(fx: Fixture) -> object:
    g = fx.table["Cost"]
    g *= 2
    return g


def _isub(fx: Fixture) -> object:
    g = fx.table["Cost"]
    g -= 1.0
    return g


def _itruediv(fx: Fixture) -> object:
    g = fx.table["Cost"]
    g /= 2
    return g


def _accumulator_loop(fx: Fixture) -> object:
    """The build-up pattern external models use: seed a constant, accumulate via ``+=`` in a loop."""
    formula = CONST(0)
    for value in (CONST(1), CONST(2), CONST(3)):
        formula += value
    return formula
