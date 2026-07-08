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
Structure-driven documentation metadata for functions and operators.

This module is the single source of truth the docs generator reads to emit the "Supported types"
tables — replacing the per-argument blocks that were hand-written in docstrings. Each entry lists a
function/operator's accepted input data types and its possible return data types.

A cross-check test (``tests/test_doc_spec.py``) asserts these declarations stay consistent with what
the golden drift corpus actually exercises, so the published reference can never silently drift from
real behaviour.
"""

from __future__ import annotations

import itertools
from types import SimpleNamespace
from typing import Any

from daitum_model import _functions
from daitum_model.data_types import (
    PRIMITIVE_DATA_TYPES,
    DataType,
    MapDataType,
    ObjectDataType,
)
from daitum_model.expression import (
    BINARY_OPERATORS,
    Arg,
    Function,
    OperatorDef,
    accepts_labels,
    arg_accepts,
)

# Type label lists used by the non-binary operator rows (NEGATE is numeric; member access can
# resolve to any field type). The binary operators read their labels off the OperatorDef registry
# directly. Every type is listed verbatim — no ``ANY`` token, no grouping.
NUMERIC = ["INTEGER", "INTEGER_ARRAY", "DECIMAL", "DECIMAL_ARRAY"]
#: Every concrete data type a member access can resolve to (a field's type): all primitives/arrays
#: plus the object and per-primitive map kinds.
ALL_TYPES = (
    [dt.name for dt in DataType if dt is not DataType.NULL]
    + ["OBJECT", "OBJECT_ARRAY"]
    + [f"{dt.name}_MAP" for dt in DataType if dt in PRIMITIVE_DATA_TYPES]
)


# ---------------------------------------------------------------------------
# Return-type derivation — a projection of result_type() over a complete pool
# ---------------------------------------------------------------------------
#
# Return types are derived by running each function's real ``result_type`` across a *complete*
# operand pool — one operand per data-type kind, including every ``<T>_MAP`` and object kind — so
# the published "Return types" reflect the function's true type rule. This replaces deriving them
# from a sampled corpus, which only ever showed the slice the corpus happened to exercise (the bug
# that made ``VALUES`` read ``DECIMAL_ARRAY`` only and ``UNION`` ≠ ``INTERSECTION``).


def _kind_label(dt: Any) -> str:
    """The verbatim type label for a data type (matches the accepted-types vocabulary)."""
    if isinstance(dt, MapDataType):
        return f"{dt.data_type.name}_MAP"
    if isinstance(dt, ObjectDataType):
        return "OBJECT_ARRAY" if dt.is_array() else "OBJECT"
    if isinstance(dt, DataType):
        return dt.name
    return str(dt)


def _operand_pool() -> tuple[list[Any], Any]:
    """Build a throwaway model exposing one operand per data-type kind, plus a key table.

    Returns ``(operands, key_table)`` where *operands* covers every primitive scalar/array, an
    object + object array, and a map per primitive value type — the universe a function argument
    could hold. *key_table* is the secondary table used as a map/object key source.
    """
    from daitum_model.model import ModelBuilder

    model = ModelBuilder()
    other = model.add_data_table("Ref")
    other.set_key_column("RefId")
    other.add_data_field("RefId", DataType.STRING)
    other.add_data_field("Amount", DataType.DECIMAL)

    table = model.add_data_table("Pool")
    table.set_key_column("Id")
    table.add_data_field("Id", DataType.STRING)

    operands: list[Any] = []
    for dt in PRIMITIVE_DATA_TYPES:
        operands.append(table.add_data_field(f"s_{dt.name}", dt))
        operands.append(table.add_data_field(f"a_{dt.name}", dt.to_array()))
    operands.append(table.add_object_reference_field("obj", other, is_array=False))
    operands.append(table.add_object_reference_field("obj_arr", other, is_array=True))
    for dt in PRIMITIVE_DATA_TYPES:
        operands.append(table.add_map_field(f"m_{dt.name}", dt, other))
    return operands, other


#: Functions whose constructor takes a trailing non-operand argument absent from the spec. Mirrors
#: the test probe's adapter so the derivation can construct a valid call.
_EXTRA_CTOR_ARGS = {"TOMAP": lambda key_table: (key_table,)}

#: Cap on the per-function operand combinations explored (functions validate well within this).
_MAX_COMBINATIONS = 50000


def derive_return_types() -> dict[str, list[str]]:
    """Each function's possible return types, derived from ``result_type`` over the complete pool.

    For every function, runs its real ``result_type`` across the cartesian product of each
    argument's spec-accepted pool operands and collects every distinct output kind. This is a
    projection of the type rule, not a corpus sample — so map/array/object element types are all
    represented (``VALUES`` → every ``<T>_ARRAY``; ``TOMAP`` → every ``<T>_MAP``).
    """
    operands, key_table = _operand_pool()
    result: dict[str, list[str]] = {}
    for name, cls in _function_classes().items():
        spec = _resolve_spec(cls)
        tail = _EXTRA_CTOR_ARGS.get(name, lambda _kt: ())(key_table)
        returns: set[str] = set()
        if not spec:
            try:
                returns.add(_kind_label(cls(*tail).to_data_type()))
            except Exception:  # noqa: BLE001
                pass
            result[name] = sorted(returns)
            continue
        cands: list[list[Any]] = []
        for arg in spec:
            cands.append(
                [
                    op
                    for op in operands
                    if arg.accepts is None or arg_accepts(arg.accepts, op.to_data_type())
                ]
            )
        for combo in itertools.islice(itertools.product(*cands), _MAX_COMBINATIONS):
            try:
                returns.add(_kind_label(cls(*combo, *tail).to_data_type()))
            except Exception:  # noqa: BLE001 — invalid combinations are simply skipped
                pass
        result[name] = sorted(returns)
    return result


def _function_classes() -> dict[str, type]:
    """Map each function's wire ``name`` (e.g. ``"LOOKUP"``) to its :class:`Function` node class."""
    return {
        obj.name: obj
        for obj in vars(_functions).values()
        if isinstance(obj, type) and issubclass(obj, Function) and obj is not Function and obj.name
    }


def _resolve_spec(cls: type) -> tuple[Arg, ...]:
    """Resolve a function class's ``spec`` — a class tuple, or an ``accepts``-derived property.

    The shape base classes (``_Reducer`` / ``_TypedUnary``) expose ``spec`` as a property reading
    ``self.accepts``; evaluate it against the class's ``accepts`` without constructing an instance.
    """
    for klass in cls.__mro__:
        attr = klass.__dict__.get("spec")
        if isinstance(attr, property) and attr.fget is not None:
            stand_in = SimpleNamespace(accepts=getattr(cls, "accepts", frozenset()))
            return tuple(attr.fget(stand_in))
        if isinstance(attr, tuple):
            return attr
    return ()


def _accepts_labels(arg: Arg) -> list[str]:
    """The verbatim accepted-type display labels for one argument.

    Every accepted type is listed by name — primitives/arrays by their :class:`DataType` name,
    objects as ``OBJECT``/``OBJECT_ARRAY``, and maps as one ``<T>_MAP`` token per primitive value
    type. There is no ``ANY`` and no grouping; a coverage gate forbids ``accepts is None`` on any
    function spec, so this branch is unreachable in practice and present only as a guard.
    """
    if arg.accepts is None:
        return []
    return accepts_labels(arg.accepts)


def function_doc_rows() -> dict[str, list[dict[str, object]]]:
    """Per-function argument documentation, derived from the declarative :class:`Arg` specs.

    Returns ``{FUNCTION_NAME: [{name, accepts, variadic, optional}, …]}`` — one entry per named
    argument, in declaration order. This is the single source of truth for the generated
    "Accepted input types" tables, replacing the old corpus-regex inference that only covered
    single-argument functions. Functions with no node class (``CONST``, ``ROW`` — constants with no
    operands) are omitted; the generator falls back to no argument table for them.
    """
    rows: dict[str, list[dict[str, object]]] = {}
    for name, cls in _function_classes().items():
        rows[name] = [
            {
                "name": arg.name,
                "accepts": _accepts_labels(arg),
                "variadic": arg.variadic,
                "optional": arg.optional,
                "literal_only": arg.literal_only,
            }
            for arg in _resolve_spec(cls)
        ]
    return rows


def operator_doc_rows() -> list[dict[str, object]]:
    """Return one documentation row per binary operator, plus the three non-binary operators.

    Each row: ``{name, symbol, renders, doc, operands, result}``. The binary operators read their
    accepted-operand and result types straight off the :class:`~daitum_model.expression.OperatorDef`
    registry (the operators' own declared type rule, cross-checked against the operator drift golden
    in ``tests/test_doc_spec.py``) rather than a separate hand-keyed table — so the docs cannot
    diverge from the operators.
    """
    rows: list[dict[str, object]] = [
        {
            "name": definition.name,
            "symbol": definition.symbol,
            "renders": _render_template(definition),
            "doc": definition.doc,
            "operands": list(definition.operands),
            "result": list(definition.result),
        }
        for definition in BINARY_OPERATORS
    ]
    rows.append(
        {
            "name": "NEGATE",
            "symbol": "-",
            "renders": "-(x)",
            "doc": "Unary numeric negation.",
            "operands": NUMERIC,
            "result": NUMERIC,
        }
    )
    rows.append(
        {
            "name": "MEMBER_ACCESS",
            "symbol": ".",
            "renders": "base.[field]",
            "doc": (
                "Member access on a field / named-value / object-array operand. Resolves the named "
                "field's type, propagating array-ness from the receiver."
            ),
            "operands": ["OBJECT", "OBJECT_ARRAY"],
            "result": ALL_TYPES,
        }
    )
    rows.append(
        {
            "name": "COLUMN_ACCESS",
            "symbol": "[]",
            "renders": "table[field]",
            "doc": (
                "Column access on a raw table. Renders with brackets (the dot form is invalid on a "
                "raw table) and returns the array variant of the column's type."
            ),
            "operands": ["TABLE"],
            "result": ["<column type>_ARRAY"],
        }
    )
    return rows


def _render_template(definition: OperatorDef) -> str:
    return f"(x {definition.symbol} y)" if definition.parenthesise else f"x {definition.symbol} y"
