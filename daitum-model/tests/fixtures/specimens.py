"""
Typed operand *specimens* for the exhaustive drift corpus.

Each specimen is a named, reproducible operand of a known data-type shape, plus the Python
literals the formula API also accepts. The drift harness combines these across every function's
arity to explore all validation branches and type-inference paths — not just the happy path.

Specimens are rebuilt from a fresh fixture per call so cases never share mutable state.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from .contract_model import Fixture


@dataclass
class Specimen:
    """A named operand-or-literal, reconstructed from the fixture on demand."""

    name: str
    get: Callable[[Fixture], Any]


# Field operands: one scalar + one array per primitive type, plus object/map operands.
FIELD_SPECIMENS: list[Specimen] = [
    Specimen("int", lambda fx: fx.fields["Qty"]),
    Specimen("dec", lambda fx: fx.fields["Cost"]),
    Specimen("str", lambda fx: fx.fields["Name"]),
    Specimen("bool", lambda fx: fx.fields["Flag"]),
    Specimen("date", lambda fx: fx.fields["Day"]),
    Specimen("datetime", lambda fx: fx.fields["Stamp"]),
    Specimen("time", lambda fx: fx.fields["Clock"]),
    Specimen("int_arr", lambda fx: fx.fields["Qtys"]),
    Specimen("dec_arr", lambda fx: fx.fields["Costs"]),
    Specimen("str_arr", lambda fx: fx.fields["Names"]),
    Specimen("bool_arr", lambda fx: fx.fields["Flags"]),
    Specimen("date_arr", lambda fx: fx.fields["Days"]),
    Specimen("datetime_arr", lambda fx: fx.fields["Stamps"]),
    Specimen("time_arr", lambda fx: fx.fields["Clocks"]),
    Specimen("object", lambda fx: fx.fields["Site"]),
    Specimen("object_arr", lambda fx: fx.fields["SiteList"]),
    Specimen("map", lambda fx: fx.fields["CostMap"]),
    Specimen("int_map", lambda fx: fx.fields["IntMap"]),
    Specimen("str_map", lambda fx: fx.fields["StrMap"]),
    Specimen("bool_map", lambda fx: fx.fields["BoolMap"]),
    Specimen("date_map", lambda fx: fx.fields["DateMap"]),
    Specimen("datetime_map", lambda fx: fx.fields["StampMap"]),
    Specimen("time_map", lambda fx: fx.fields["ClockMap"]),
    Specimen("calc", lambda fx: fx.calc),
    Specimen("param", lambda fx: fx.param),
    Specimen("col_dec_arr", lambda fx: fx.table["Cost"]),
]

# Python literals the API coerces via CONST.
LITERAL_SPECIMENS: list[Specimen] = [
    Specimen("lit_int", lambda fx: 7),
    Specimen("lit_float", lambda fx: 1.5),
    Specimen("lit_str", lambda fx: "abc"),
    Specimen("lit_bool", lambda fx: True),
]

# The table receiver (for Table | Operand functions).
TABLE_SPECIMENS: list[Specimen] = [
    Specimen("table_jobs", lambda fx: fx.table),
    Specimen("table_sites", lambda fx: fx.other_table),
]

ALL_OPERAND_SPECIMENS = FIELD_SPECIMENS + LITERAL_SPECIMENS

__all__ = [
    "Specimen",
    "FIELD_SPECIMENS",
    "LITERAL_SPECIMENS",
    "TABLE_SPECIMENS",
    "ALL_OPERAND_SPECIMENS",
]
