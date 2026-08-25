"""
Exhaustive drift corpus generator.

For every public formula function and operator, this module enumerates a broad matrix of typed
operand combinations and records, for each invocation, the observable outcome:

- success  -> ``{"ok": True, "to_string": ..., "to_data_type": ...}``
- failure  -> ``{"ok": False, "exc": "<ExceptionType>"}``

It captures the rendered string + inferred return type on success, and the exception *type* on
failure — deliberately **not** the exception message. Pinning messages is too brittle for a
refactor (reformatting an error string is not a behavioural change), so the corpus pins which
validation branch raises and what kind of error it raises, not the prose. Any render change,
type-inference change, or different/removed/added error still fails CI.

The cases assert only on the public contract, never on node classes.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

import daitum_model.formulas as formulas
from daitum_model import DataType
from daitum_model.formulas import CONST

from .contract_model import Fixture, build_fixture
from .specimens import ALL_OPERAND_SPECIMENS, FIELD_SPECIMENS, LITERAL_SPECIMENS, Specimen

# A representative subset used where a full cross-product would explode combinatorially.
CORE_SPECIMENS: list[Specimen] = [
    s
    for s in FIELD_SPECIMENS
    if s.name
    in {
        "int",
        "dec",
        "str",
        "bool",
        "date",
        "datetime",
        "time",
        "int_arr",
        "dec_arr",
        "str_arr",
        "bool_arr",
        "object",
        "object_arr",
        "map",
    }
] + LITERAL_SPECIMENS


def _outcome(fn: Callable[[Fixture], Any], fx: Fixture) -> dict[str, Any]:
    """Evaluate one invocation thunk against *fx*, capturing success or failure.

    Reading an operand's ``to_string``/``to_data_type`` never mutates the fixture, so a single
    shared fixture is reused across read-only cases for speed. The few in-place-mutation operator
    cases build their own throwaway operands internally, so they are also safe.
    """
    try:
        result = fn(fx)
        return {
            "ok": True,
            "to_string": result.to_string(),
            "to_data_type": str(result.to_data_type()),
        }
    except Exception as exc:  # noqa: BLE001 — we are characterising every raised exception
        return {"ok": False, "exc": type(exc).__name__}


# ---------------------------------------------------------------------------
# Invocation templates: how each function maps specimens to arguments.
# ---------------------------------------------------------------------------

# Unary functions: f(x) swept over every operand specimen.
UNARY: dict[str, Callable[[Any], Any]] = {
    "ABS": formulas.ABS,
    "CEILING": formulas.CEILING,
    "FLOOR": formulas.FLOOR,
    "ROUND": formulas.ROUND,
    "INTEGER": formulas.INTEGER,
    "EXP": formulas.EXP,
    "LOG": formulas.LOG,
    "SIN": formulas.SIN,
    "COS": formulas.COS,
    "NOT": formulas.NOT,
    "ISBLANK": formulas.ISBLANK,
    "ISERROR": formulas.ISERROR,
    "LEN": formulas.LEN,
    "LOWER": formulas.LOWER,
    "UPPER": formulas.UPPER,
    "TRIM": formulas.TRIM,
    "CHAR": formulas.CHAR,
    "TEXT": formulas.TEXT,
    "BITMASK": formulas.BITMASK,
    "BITMASKSTRING": formulas.BITMASKSTRING,
    "DAY": formulas.DAY,
    "MONTH": formulas.MONTH,
    "YEAR": formulas.YEAR,
    "HOUR": formulas.HOUR,
    "MINUTE": formulas.MINUTE,
    "SECOND": formulas.SECOND,
    "WEEKDAY": formulas.WEEKDAY,
    "EOMONTH": formulas.EOMONTH,
    "SIZE": formulas.SIZE,
    "DISTINCT": formulas.DISTINCT,
    "COUNTBLANKS": formulas.COUNTBLANKS,
    "VALUES": formulas.VALUES,
    "NEXT": formulas.NEXT,
    "PREV": formulas.PREV,
    "CONST": CONST,
}

# Binary functions: f(x, y) swept over a curated specimen list on each side.
BINARY: dict[str, Callable[[Any, Any], Any]] = {
    "MOD": formulas.MOD,
    "POWER": formulas.POWER,
    "BITAND": formulas.BITAND,
    "BITOR": formulas.BITOR,
    "DISTRIBUTE": formulas.DISTRIBUTE,
    "DAYSBETWEEN": formulas.DAYSBETWEEN,
    "HOURSBETWEEN": formulas.HOURSBETWEEN,
    "MONTHSBETWEEN": formulas.MONTHSBETWEEN,
    "PLUSDAYS": formulas.PLUSDAYS,
    "PLUSMINUTES": formulas.PLUSMINUTES,
    "LEFT": formulas.LEFT,
    "RIGHT": formulas.RIGHT,
    "FIND": formulas.FIND,
    "COUNT": formulas.COUNT,
    "CONTAINS": formulas.CONTAINS,
    "MATCH": formulas.MATCH,
    "SETTIME": formulas.SETTIME,
    "GET": formulas.GET,
    "FROMTIMEZONE": formulas.FROMTIMEZONE,
    "TOTIMEZONE": formulas.TOTIMEZONE,
    "EOMONTH2": formulas.EOMONTH,
}

# Variadic numeric reducers: swept over groups of operands.
VARIADIC_NUMERIC: dict[str, Callable[..., Any]] = {
    "SUM": formulas.SUM,
    "MIN": formulas.MIN,
    "MAX": formulas.MAX,
    "AVERAGE": formulas.AVERAGE,
    "MEDIAN": formulas.MEDIAN,
    "STDEV": formulas.STDEV,
    "ARRAYMAX": formulas.ARRAYMAX,
    "ARRAYMIN": formulas.ARRAYMIN,
}

VARIADIC_LOGICAL: dict[str, Callable[..., Any]] = {
    "AND": formulas.AND,
    "OR": formulas.OR,
}


def _named(prefix: str, spec_names: list[str]) -> str:
    return f"{prefix}({','.join(spec_names)})"


def build_drift_cases() -> dict[str, Callable[[Fixture], Any]]:
    """Return ``{case_name: thunk}`` for the entire exhaustive corpus."""
    cases: dict[str, Callable[[Fixture], Any]] = {}

    # --- unary sweep over all operand specimens ---
    for fname, fn in UNARY.items():
        for s in ALL_OPERAND_SPECIMENS:
            cases[_named(fname, [s.name])] = lambda fx, fn=fn, s=s: fn(s.get(fx))

    # --- binary sweep over core x core ---
    for fname, fn in BINARY.items():
        for a in CORE_SPECIMENS:
            for b in CORE_SPECIMENS:
                cases[_named(fname, [a.name, b.name])] = lambda fx, fn=fn, a=a, b=b: fn(
                    a.get(fx), b.get(fx)
                )

    # --- variadic numeric: 1-arg and 2-arg groups ---
    for fname, fn in VARIADIC_NUMERIC.items():
        for s in CORE_SPECIMENS:
            cases[_named(fname, [s.name])] = lambda fx, fn=fn, s=s: fn(s.get(fx))
        for a in CORE_SPECIMENS:
            for b in CORE_SPECIMENS:
                cases[_named(fname, [a.name, b.name])] = lambda fx, fn=fn, a=a, b=b: fn(
                    a.get(fx), b.get(fx)
                )

    # --- variadic logical ---
    for fname, fn in VARIADIC_LOGICAL.items():
        for a in CORE_SPECIMENS:
            for b in CORE_SPECIMENS:
                cases[_named(fname, [a.name, b.name])] = lambda fx, fn=fn, a=a, b=b: fn(
                    a.get(fx), b.get(fx)
                )

    # --- functions with bespoke shapes need explicit invocations ---
    _add_bespoke_cases(cases)
    return cases


def _add_bespoke_cases(cases: dict[str, Callable[[Fixture], Any]]) -> None:
    """Functions whose argument shapes don't fit the unary/binary/variadic templates."""
    f = lambda fx: fx.fields  # noqa: E731

    bespoke: dict[str, Callable[[Fixture], Any]] = {
        # constants / no-arg
        "ROW()": lambda fx: formulas.ROW(),
        "ROWVECTOR()": lambda fx: formulas.ROWVECTOR(),
        "BLANK()": lambda fx: formulas.BLANK(),
        "BLANK(int)": lambda fx: formulas.BLANK(DataType.INTEGER),
        "BLANK(obj)": lambda fx: formulas.BLANK(f(fx)["Site"].to_data_type()),
        # IF / branch merging
        "IF(bool,dec,dec)": lambda fx: formulas.IF(f(fx)["Flag"], 1.0, f(fx)["Cost"]),
        "IF(bool,int,dec)": lambda fx: formulas.IF(f(fx)["Flag"], 1, f(fx)["Cost"]),
        "IF(bool,str,str)": lambda fx: formulas.IF(f(fx)["Flag"], "a", "b"),
        "IF(bool,blank,dec)": lambda fx: formulas.IF(
            f(fx)["Flag"], formulas.BLANK(), f(fx)["Cost"]
        ),
        "IF(bool,dec,blank)": lambda fx: formulas.IF(
            f(fx)["Flag"], f(fx)["Cost"], formulas.BLANK()
        ),
        "IF(int,dec,dec)": lambda fx: formulas.IF(f(fx)["Qty"], 1.0, f(fx)["Cost"]),
        "IF(str,dec,dec)": lambda fx: formulas.IF(f(fx)["Name"], 1.0, f(fx)["Cost"]),
        "IF(bool,dec,str)": lambda fx: formulas.IF(f(fx)["Flag"], 1.0, "x"),
        "IFBLANK(dec,dec)": lambda fx: formulas.IFBLANK(f(fx)["Cost"], 0.0),
        "IFBLANK(str,str)": lambda fx: formulas.IFBLANK(f(fx)["Name"], "x"),
        "IFERROR(dec,dec)": lambda fx: formulas.IFERROR(f(fx)["Cost"], 0.0),
        "IFERROR(str,str)": lambda fx: formulas.IFERROR(f(fx)["Name"], "x"),
        # CHOOSE
        "CHOOSE(int,3int)": lambda fx: formulas.CHOOSE(f(fx)["Qty"], 1, 2, 3),
        "CHOOSE(int,2dec)": lambda fx: formulas.CHOOSE(f(fx)["Qty"], 1.0, f(fx)["Cost"]),
        "CHOOSE(str,2int)": lambda fx: formulas.CHOOSE(f(fx)["Name"], 1, 2),
        # ARRAY
        "ARRAY(bool,2dec)": lambda fx: formulas.ARRAY(True, f(fx)["Cost"], 1.0),
        "ARRAY(bool,2str)": lambda fx: formulas.ARRAY(False, "a", f(fx)["Name"]),
        "ARRAY(bool,mixed)": lambda fx: formulas.ARRAY(True, f(fx)["Cost"], "x"),
        # DATE / DATETIME / TIME constructors
        "DATE(3int)": lambda fx: formulas.DATE(2026, 1, 1),
        "DATE(fields)": lambda fx: formulas.DATE(f(fx)["Qty"], f(fx)["Qty"], f(fx)["Qty"]),
        "DATE(str)": lambda fx: formulas.DATE("a", 1, 1),
        "DATETIME(6int)": lambda fx: formulas.DATETIME(2026, 1, 1, 0, 0, 0),
        "TIME(3int)": lambda fx: formulas.TIME(1, 2, 3),
        "TIME(str)": lambda fx: formulas.TIME("a", 2, 3),
        "WEEKDAY(date,rt)": lambda fx: formulas.WEEKDAY(f(fx)["Day"], 1),
        # literal-only range guards (must still raise after migration)
        "WEEKDAY(date,bad_rt)": lambda fx: formulas.WEEKDAY(f(fx)["Day"], 99),
        "CHAR(out_of_range)": lambda fx: formulas.CHAR(300),
        "CHAR(in_range)": lambda fx: formulas.CHAR(65),
        "FIND(str,str,idx)": lambda fx: formulas.FIND("x", f(fx)["Name"], 2),
        "TEXT(dec,fmt)": lambda fx: formulas.TEXT(f(fx)["Cost"], "0.00"),
        "EOMONTH(date,m)": lambda fx: formulas.EOMONTH(f(fx)["Day"], 2),
        # TEXTJOIN
        "TEXTJOIN(d,e,arr)": lambda fx: formulas.TEXTJOIN(",", True, f(fx)["Names"]),
        "TEXTJOIN(d,e,2)": lambda fx: formulas.TEXTJOIN(",", False, f(fx)["Names"], "x"),
        # COUNTDUPLICATES / FINDDUPLICATES
        "COUNTDUP": lambda fx: formulas.COUNTDUPLICATES(f(fx)["Costs"], True, True),
        "FINDDUP": lambda fx: formulas.FINDDUPLICATES(f(fx)["Costs"], True, True),
        # set ops
        "UNION(b,2)": lambda fx: formulas.UNION(True, f(fx)["Costs"], f(fx)["Costs"]),
        "UNION(b,obj)": lambda fx: formulas.UNION(False, f(fx)["SiteList"], f(fx)["SiteList"]),
        "INTERSECTION(b,2)": lambda fx: formulas.INTERSECTION(True, f(fx)["Costs"], f(fx)["Costs"]),
        # RANK / DISTRIBUTE arrays
        "RANK(dec,arr)": lambda fx: formulas.RANK(f(fx)["Cost"], f(fx)["Costs"]),
        "RANK(dec,arr,asc)": lambda fx: formulas.RANK(f(fx)["Cost"], f(fx)["Costs"], True),
        # LOOKUPARRAY
        "LOOKUPARRAY(dec,dec,str)": lambda fx: formulas.LOOKUPARRAY(
            f(fx)["Costs"], f(fx)["Costs"], f(fx)["Names"]
        ),
        # probability
        "NORMDIST": lambda fx: formulas.NORMDIST(1.0, 0.0, 1.0, True),
        "NORMINV": lambda fx: formulas.NORMINV(0.5, 0.0, 1.0),
        "BINOMDIST": lambda fx: formulas.BINOMDIST(1, 10, 0.5, True),
        "BINOMINV": lambda fx: formulas.BINOMINV(10, 0.5, 0.5),
        "GAMMADIST": lambda fx: formulas.GAMMADIST(1.0, 1.0, 1.0, True),
        "GAMMAINV": lambda fx: formulas.GAMMAINV(0.5, 1.0, 1.0),
        "WEIBULL": lambda fx: formulas.WEIBULL(CONST(1.0), CONST(1.0), CONST(1.0), CONST(True)),
    }
    cases.update(bespoke)

    # --- Table | Operand functions: bare-table AND object-array-operand paths ---
    table_operand: dict[str, Callable[[Fixture], Any]] = {
        "ROWS(table_jobs)": lambda fx: formulas.ROWS(fx.table),
        "ROWS(table_sites)": lambda fx: formulas.ROWS(fx.other_table),
        "ROWS(object_arr)": lambda fx: formulas.ROWS(f(fx)["SiteList"]),
        "INDEX(table_jobs,1)": lambda fx: formulas.INDEX(fx.table, 1),
        "INDEX(object_arr,1)": lambda fx: formulas.INDEX(f(fx)["SiteList"], 1),
        "INDEX(table,scalar_idx)": lambda fx: formulas.INDEX(fx.table, f(fx)["Qty"]),
        # array index: a raw table yields OBJECT_ARRAY, an object-array field yields OBJECT.
        "INDEX(table,array_idx)": lambda fx: formulas.INDEX(fx.table, f(fx)["Qtys"]),
        "INDEX(object_arr,array_idx)": lambda fx: formulas.INDEX(f(fx)["SiteList"], f(fx)["Qtys"]),
        "FILTER(table,flags)": lambda fx: formulas.FILTER(fx.table, f(fx)["Flags"]),
        "FILTER(object_arr,flags)": lambda fx: formulas.FILTER(f(fx)["SiteList"], f(fx)["Flags"]),
        "LOOKUP(table_sites,Region,x)": lambda fx: formulas.LOOKUP(fx.other_table, "Region", "x"),
        "LOOKUP(object_arr,Region,x)": lambda fx: formulas.LOOKUP(f(fx)["SiteList"], "Region", "x"),
        "LOOKUP(table,Amount,dec)": lambda fx: formulas.LOOKUP(fx.other_table, "Amount", 1.0),
        "LOOKUP(table,rev)": lambda fx: formulas.LOOKUP(fx.other_table, "Region", "x", True),
        "LOOKUP(scalar_field)": lambda fx: formulas.LOOKUP(f(fx)["Cost"], "Region", "x"),
        "TOMAP(arr,table)": lambda fx: formulas.TOMAP(f(fx)["Costs"], fx.other_table),
        "TOMAP(strarr,table)": lambda fx: formulas.TOMAP(f(fx)["Names"], fx.other_table),
    }
    cases.update(table_operand)


# ---------------------------------------------------------------------------
# Operator corpus (exhaustive over operand pairs).
# ---------------------------------------------------------------------------

ARITH_OPS = {
    "add": lambda a, b: a + b,
    "sub": lambda a, b: a - b,
    "mul": lambda a, b: a * b,
    "div": lambda a, b: a / b,
    "pow": lambda a, b: a ^ b,
    "lt": lambda a, b: a < b,
    "gt": lambda a, b: a > b,
    "le": lambda a, b: a <= b,
    "ge": lambda a, b: a >= b,
    "eq": lambda a, b: a.equal_to(b),
    "ne": lambda a, b: a.not_equal_to(b),
}


def build_operator_drift_cases() -> dict[str, Callable[[Fixture], Any]]:
    """Exhaustive operator corpus: every binary op over core operand pairs, plus unary/access."""
    cases: dict[str, Callable[[Fixture], Any]] = {}

    op_specimens = [s for s in CORE_SPECIMENS if not s.name.startswith("lit_")] + LITERAL_SPECIMENS
    for opname, op in ARITH_OPS.items():
        for a in op_specimens:
            for b in op_specimens:
                # left operand must be an Operand (literals have no overloads on the left here)
                if a.name.startswith("lit_"):
                    continue
                cases[f"{opname}({a.name},{b.name})"] = lambda fx, op=op, a=a, b=b: op(
                    a.get(fx), b.get(fx)
                )

    # reflected forms (literal on the left)
    f = lambda fx: fx.fields  # noqa: E731
    reflected = {
        "radd": lambda fx: 1 + f(fx)["Qty"],
        "rsub": lambda fx: 1 - f(fx)["Qty"],
        "rmul": lambda fx: 2 * f(fx)["Cost"],
        "rdiv": lambda fx: 1 / f(fx)["Cost"],
        "rpow": lambda fx: 2 ^ f(fx)["Qty"],
        "rconcat": lambda fx: "x" + f(fx)["Name"],
    }
    cases.update(reflected)

    # unary negate over all
    for s in CORE_SPECIMENS:
        if s.name.startswith("lit_"):
            continue
        cases[f"neg({s.name})"] = lambda fx, s=s: -s.get(fx)

    # member access (Operand.__getitem__) and column access (Table.__getitem__)
    access = {
        "member(object,Amount)": lambda fx: f(fx)["Site"]["Amount"],
        "member(object_arr,Amount)": lambda fx: f(fx)["SiteList"]["Amount"],
        "member(object,Region)": lambda fx: f(fx)["Site"]["Region"],
        "member(object_arr,missing)": lambda fx: f(fx)["SiteList"]["Nope"],
        "member(scalar)": lambda fx: f(fx)["Cost"]["Amount"],
        "member(object_arr,object)": _site_with_ref,
        "column(jobs,Cost)": lambda fx: fx.table["Cost"],
        "column(jobs,Site)": lambda fx: fx.table["Site"],
        "column(jobs,missing)": lambda fx: fx.table["Nope"],
        "column(jobs,array_field)": lambda fx: fx.table["Costs"],
    }
    cases.update(access)

    # in-place mutation family
    cases["iadd"] = _iadd
    cases["imul"] = _imul
    cases["isub"] = _isub
    cases["itruediv"] = _itruediv
    return cases


def _site_with_ref(fx: Fixture) -> Any:
    # object-array operand whose member is itself an object reference, exercising the
    # ObjectDataType branch of member access.
    return fx.fields["SiteList"]["SiteId"]


def _iadd(fx: Fixture) -> Any:
    g = fx.table["Cost"]
    g += 1.0
    return g


def _imul(fx: Fixture) -> Any:
    g = fx.table["Cost"]
    g *= 2
    return g


def _isub(fx: Fixture) -> Any:
    g = fx.table["Cost"]
    g -= 1.0
    return g


def _itruediv(fx: Fixture) -> Any:
    g = fx.table["Cost"]
    g /= 2
    return g


def capture_all(cases: dict[str, Callable[[Fixture], Any]]) -> dict[str, dict[str, Any]]:
    """Capture the outcome of every case deterministically against one shared fixture."""
    fx = build_fixture()
    return {name: _outcome(thunk, fx) for name, thunk in sorted(cases.items())}
