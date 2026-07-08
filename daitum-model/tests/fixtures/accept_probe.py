"""
Exhaustive per-argument *accepted-type* probe.

The declarative ``Arg.accepts`` on each function is documentation **and** validation metadata, so
it must equal the set of data-type kinds the function genuinely accepts at that position — no
wider (an over-declaration the docs would wrongly advertise, e.g. ``ARRAY`` accepting a map) and no
narrower (an under-declaration that would reject a valid input).

This module computes the *true* accepted kind-set for every argument empirically: for each function
it discovers a valid baseline call, then varies one position at a time across a complete operand
pool (one specimen per data-type kind), recording which kinds yield a successful construction.

Both the audit and the ``spec == true-accepted`` CI gate (``tests/test_doc_spec.py``) read this, so
the specs can never silently drift — over- or under-declare — from real behaviour.
"""

from __future__ import annotations

import itertools
from collections.abc import Callable
from typing import Any

from daitum_model.data_types import DataType, MapDataType, ObjectDataType
from daitum_model.expression import Function, arg_accepts

from .contract_model import Fixture, build_fixture
from .specimens import FIELD_SPECIMENS, Specimen

# One specimen per data-type *kind* — the universe a position could possibly accept. Literals are
# excluded (they duplicate the scalar kinds via CONST); the field specimens already cover every
# primitive scalar/array plus object, object-array and map.
PROBE_SPECIMENS: list[Specimen] = [
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
        "date_arr",
        "datetime_arr",
        "time_arr",
        "object",
        "object_arr",
        "map",
        "int_map",
        "str_map",
        "bool_map",
        "date_map",
        "datetime_map",
        "time_map",
    }
]


def kind_label(operand: Any) -> str:
    """The verbatim accepted-type label for an operand's data type (matches the docs vocabulary)."""
    dt = operand.to_data_type()
    if isinstance(dt, MapDataType):
        return f"{dt.data_type.name}_MAP"
    if isinstance(dt, ObjectDataType):
        return "OBJECT_ARRAY" if dt.is_array() else "OBJECT"
    return dt.name


# A few functions take a constructor argument that is *not* a spec operand. ``TOMAP(array, table)``
# uses ``table`` as a map key-source (rendered as its id), so it is absent from the spec; the probe
# must still supply it to construct a call. The adapter returns the extra trailing args, given the
# fixture.
_EXTRA_CTOR_ARGS: dict[str, Callable[[Fixture], tuple]] = {
    "TOMAP": lambda fx: (fx.other_table,),
}


def _build(cls: type, args: list[Any], fx: Fixture) -> Any | None:
    """Construct the function node, returning it on success or ``None`` if the call is invalid."""
    extra = _EXTRA_CTOR_ARGS.get(getattr(cls, "name", ""))
    tail = extra(fx) if extra else ()
    try:
        return cls(*args, *tail)
    except Exception:  # noqa: BLE001 — any failure means "not accepted in this position"
        return None


def _construct(cls: type, args: list[Any], fx: Fixture) -> bool:
    return _build(cls, args, fx) is not None


def true_accepted(cls: type, spec, fx: Fixture) -> dict[int, set[str]]:
    """The set of accepted kind labels for each argument position of *cls*.

    A position's accepted type is defined existentially: kind *K* is accepted at position *p* iff
    **some** valid call exists with *K* there. This matters for cross-argument functions (``IF``'s
    branches must match each other, ``CONTAINS``'s value must be the element of its array): holding
    the other positions at a single fixed baseline would spuriously reject a kind that is fine given
    a *different* sibling choice. So for each (position, kind) we search sibling assignments — drawn
    from each sibling's spec-accepted specimens — for one witness that constructs successfully.
    """
    accepted: dict[int, set[str]] = {pos: set() for pos in range(len(spec))}
    n = len(spec)

    # Per-position candidate specimens (those the spec admits there) — the witness search space.
    cands: list[list[Any]] = []
    for pos in range(n):
        arg = spec[pos]
        cands.append(
            [
                s.get(fx)
                for s in PROBE_SPECIMENS
                if arg.accepts is None or arg_accepts(arg.accepts, s.get(fx).to_data_type())
            ]
        )

    for pos in range(n):
        for probe in PROBE_SPECIMENS:
            op = probe.get(fx)
            label = kind_label(op)
            if label in accepted[pos]:
                continue
            # Search sibling combinations for a witness with `op` fixed at `pos`.
            other_ranges = [cands[i] if i != pos else [op] for i in range(n)]
            for combo in itertools.islice(itertools.product(*other_ranges), 20000):
                if _construct(cls, list(combo), fx):
                    accepted[pos].add(label)
                    break
    return accepted


def declared_accepted(spec, fx: Fixture) -> dict[int, set[str]]:
    """The kind labels each argument's declared ``accepts`` admits, over the probe specimen pool."""
    declared: dict[int, set[str]] = {}
    for pos, arg in enumerate(spec):
        labels: set[str] = set()
        if arg.accepts is not None:
            for s in PROBE_SPECIMENS:
                op = s.get(fx)
                if arg_accepts(arg.accepts, op.to_data_type()):
                    labels.add(kind_label(op))
        declared[pos] = labels
    return declared


def true_returns(cls: type, spec, fx: Fixture) -> set[str]:
    """The set of return-type kind labels *cls* produces over every valid spec-accepted call.

    Runs the function's real :meth:`result_type` across the cartesian product of each position's
    spec-accepted specimens (a complete operand pool, one per kind incl. every ``<T>_MAP``), so the
    published "Return types" reflect the function's true type rule — not the narrow slice a sampled
    corpus happens to exercise (the bug that made ``VALUES`` read ``DECIMAL_ARRAY`` only). A
    zero-operand function is evaluated once.
    """
    returns: set[str] = set()
    if not spec:
        node = _build(cls, [], fx)
        if node is not None:
            returns.add(kind_label(node))
        return returns

    cands: list[list[Any]] = []
    for pos, arg in enumerate(spec):
        cands.append(
            [
                s.get(fx)
                for s in PROBE_SPECIMENS
                if arg.accepts is None or arg_accepts(arg.accepts, s.get(fx).to_data_type())
            ]
        )
    for combo in itertools.islice(itertools.product(*cands), 50000):
        node = _build(cls, list(combo), fx)
        if node is not None:
            returns.add(kind_label(node))
    return returns
