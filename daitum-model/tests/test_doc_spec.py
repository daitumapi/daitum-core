"""
Spec ⇄ corpus cross-check for the structure-driven documentation.

The docs generator publishes "Supported types" tables derived from the golden drift corpus and the
operator registry. These tests assert that published metadata stays consistent with what the corpus
actually exercises, so the reference can never silently drift from real behaviour (plan §4).
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

from daitum_model._doc_spec import function_doc_rows, operator_doc_rows
from daitum_model.expression import BINARY_OPERATORS

# Make the docs generator importable.
DOCS_DIR = Path(__file__).resolve().parents[2] / "docs"
sys.path.insert(0, str(DOCS_DIR))

from generate_formula_docs import derive_return_types, is_formula_function  # noqa: E402

# Drift-corpus spec tokens (``NAME(spec)``) -> the data type the spec stands for. Used to map a
# unary corpus case to the input type it exercises, for the spec ⇄ corpus superset cross-check.
_SPEC_TYPES = {
    "int": "INTEGER",
    "dec": "DECIMAL",
    "str": "STRING",
    "bool": "BOOLEAN",
    "date": "DATE",
    "datetime": "DATETIME",
    "time": "TIME",
    "int_arr": "INTEGER_ARRAY",
    "dec_arr": "DECIMAL_ARRAY",
    "str_arr": "STRING_ARRAY",
    "bool_arr": "BOOLEAN_ARRAY",
    "date_arr": "DATE_ARRAY",
    "datetime_arr": "DATETIME_ARRAY",
}


def _public_function_names() -> set[str]:
    import inspect

    import daitum_model.formulas as formulas

    return {name for name, obj in inspect.getmembers(formulas, is_formula_function)}


class TestFunctionDocTypes:
    def test_every_function_publishes_named_arguments(self):
        """The per-argument doc rows come from the declarative specs: every argument is named, and
        every multi/single-operand function exposes at least one argument (only the zero-operand
        BLANK/ROWVECTOR are empty)."""
        rows = function_doc_rows()
        assert rows, "no function doc rows — is _functions importable?"
        for name, args in rows.items():
            for arg in args:
                assert arg["name"], f"{name}: an argument is unnamed"
                assert arg["accepts"], f"{name}: argument {arg['name']!r} has no accepted types"
            if name not in {"BLANK", "ROWVECTOR"}:
                assert args, f"{name}: expected at least one documented argument"

    def test_accepted_types_are_known_datatypes(self):
        """Every published accepted type is a known data type listed verbatim — a DataType name, an
        object kind, or a per-primitive map token. ``ANY`` must never appear."""
        from daitum_model.data_types import DataType

        known = {dt.name for dt in DataType}
        known |= {"OBJECT", "OBJECT_ARRAY"}
        known |= {f"{dt.name}_MAP" for dt in DataType}
        for name, args in function_doc_rows().items():
            for arg in args:
                assert "ANY" not in arg["accepts"], f"{name}.{arg['name']}: 'ANY' must not appear"
                for t in arg["accepts"]:
                    assert t in known, f"{name}.{arg['name']}: unknown accepted type {t!r}"

    def test_return_types_are_known_datatypes(self):
        from daitum_model.data_types import DataType

        known = {dt.name for dt in DataType}
        known |= {"OBJECT", "OBJECT_ARRAY"}
        known |= {f"{dt.name}_MAP" for dt in DataType}
        for name, types in derive_return_types().items():
            for t in types:
                assert t in known, f"{name}: unknown return type {t!r}"

    def test_unary_specs_accept_every_input_the_corpus_exercises(self):
        """Strengthened spec ⇄ corpus cross-check: for every single-argument call the corpus
        accepts, the function's declared spec must accept that input type — so a spec can never
        silently under-declare relative to real behaviour. (Unary cases only, where the operand
        position is unambiguous; ``ANY`` arguments trivially satisfy this.)"""
        import json
        import re

        golden_path = Path(__file__).resolve().parent / "fixtures" / "drift_function_golden.json"
        golden = json.loads(golden_path.read_text(encoding="utf-8"))
        rows = function_doc_rows()
        for key, outcome in golden.items():
            if not outcome.get("ok"):
                continue
            unary = re.fullmatch(r"([A-Z][A-Z_]*)\(([a-z_]+)\)", key)
            if not unary:
                continue
            name, token = unary.group(1), unary.group(2)
            if name not in rows or token not in _SPEC_TYPES or not rows[name]:
                continue
            first_arg = rows[name][0]
            accepted = first_arg["accepts"]
            input_type = _SPEC_TYPES[token]
            assert input_type in accepted, (
                f"{name}: corpus accepts {input_type} at argument {first_arg['name']!r} "
                f"but the spec declares only {accepted}"
            )

    def test_published_return_types_match_result_type_rule(self):
        """The published return types must equal what each function's ``result_type`` actually
        produces over a complete operand pool. The docs derive them from the production pool
        (``_doc_spec.derive_return_types``); this gate cross-checks that against the independent
        test-fixture probe (``true_returns``) so neither pool can silently under-sample. This is the
        gate that pins ``VALUES`` to every ``<T>_ARRAY`` and keeps ``UNION`` ≡ ``INTERSECTION``."""
        from fixtures.accept_probe import true_returns
        from fixtures.contract_model import build_fixture

        from daitum_model._doc_spec import _function_classes, _resolve_spec, derive_return_types

        published = derive_return_types()
        fx = build_fixture()
        mismatches: list[str] = []
        for name, cls in _function_classes().items():
            spec = _resolve_spec(cls)
            probe = true_returns(cls, spec, fx)
            doc = set(published.get(name, []))
            if probe != doc:
                mismatches.append(
                    f"{name}: docs publish {sorted(doc)} but result_type produces {sorted(probe)}"
                )
        assert not mismatches, "published return types diverge from result_type:\n" + "\n".join(
            mismatches
        )

    def test_declared_accepts_equals_true_accepted(self):
        """Exhaustive spec ⇄ behaviour gate: every argument's declared ``accepts`` must equal the
        set of data-type kinds the function genuinely accepts at that position — no wider (an
        over-declaration the docs would wrongly advertise, e.g. ``ARRAY`` accepting a map) and no
        narrower (an under-declaration that rejects a valid input).

        The true accepted set is computed empirically by the accept-probe (a witness search over a
        complete operand pool, co-varying coupled positions), so this catches both directions —
        unlike the corpus cross-check above, which only catches under-declaration over the narrow
        slice the corpus happens to exercise. This is the gate that would have caught the
        ``ARRAY``/map and ``TOMAP``/object-array over-declarations."""
        from fixtures.accept_probe import declared_accepted, true_accepted
        from fixtures.contract_model import build_fixture

        from daitum_model._doc_spec import _function_classes, _resolve_spec

        fx = build_fixture()
        mismatches: list[str] = []
        for name, cls in _function_classes().items():
            spec = _resolve_spec(cls)
            if not spec:
                continue
            true = true_accepted(cls, spec, fx)
            declared = declared_accepted(spec, fx)
            for pos, arg in enumerate(spec):
                over = declared[pos] - true[pos]
                under = true[pos] - declared[pos]
                if over or under:
                    mismatches.append(
                        f"{name}.{arg.name}: over-declares {sorted(over)}, "
                        f"under-declares {sorted(under)}"
                    )
        assert not mismatches, "spec accepts diverge from real behaviour:\n" + "\n".join(mismatches)


class TestOperatorDocRows:
    def test_every_binary_operator_is_documented(self):
        names = {row["name"] for row in operator_doc_rows()}
        for definition in BINARY_OPERATORS:
            assert definition.name in names, f"operator {definition.name} missing from docs"

    def test_access_operators_documented(self):
        names = {row["name"] for row in operator_doc_rows()}
        assert "MEMBER_ACCESS" in names
        assert "COLUMN_ACCESS" in names
        assert "NEGATE" in names

    @pytest.mark.parametrize("row", operator_doc_rows(), ids=lambda r: r["name"])
    def test_operator_rows_are_complete(self, row):
        assert row["operands"], f"{row['name']}: no accepted operand types"
        assert row["result"], f"{row['name']}: no result types"
        assert row["renders"], f"{row['name']}: no render template"

    def test_declared_operator_types_cover_the_golden(self):
        """Spec ⇄ golden cross-check (plan §3.4): every operand/result data type the operator drift
        golden actually exercises must appear in that operator's declared ``OperatorDef`` types — so
        the docs cannot under-declare relative to the operators' real behaviour. Verified to fail
        when a declaration is narrowed below what the golden exercises."""
        import json
        import re
        from collections import defaultdict

        # The ``+`` operator dispatches to ADD (numeric) or CONCAT (string), so the golden's ``add``
        # key conflates both; its union must be covered by ADD ∪ CONCAT.
        golden_to_def = {
            "sub": ["SUBTRACT"],
            "mul": ["MULTIPLY"],
            "div": ["DIVIDE"],
            "pow": ["POWER"],
            "lt": ["LESS_THAN"],
            "gt": ["GREATER_THAN"],
            "le": ["LESS_EQUAL"],
            "ge": ["GREATER_EQUAL"],
            "eq": ["EQUALS"],
            "ne": ["NOT_EQUALS"],
            "add": ["ADD", "CONCAT"],
        }
        by_name = {d.name: d for d in BINARY_OPERATORS}

        golden_path = Path(__file__).resolve().parent / "fixtures" / "drift_operator_golden.json"
        golden = json.loads(golden_path.read_text(encoding="utf-8"))
        operands: dict[str, set[str]] = defaultdict(set)
        results: dict[str, set[str]] = defaultdict(set)
        for key, outcome in golden.items():
            if not outcome.get("ok"):
                continue
            match = re.match(r"([a-z_]+)\((.*)\)", key)
            if not match or match.group(1) not in golden_to_def:
                continue
            op = match.group(1)
            for token in match.group(2).split(","):
                operands[op].add(_token_to_type(token.strip()))
            results[op].add(str(outcome["to_data_type"]).split(":")[0])

        for golden_key, def_names in golden_to_def.items():
            declared_operands = set().union(*(set(by_name[n].operands) for n in def_names))
            declared_results = set().union(*(set(by_name[n].result) for n in def_names))
            assert operands[golden_key] <= declared_operands, (
                f"{golden_key}: golden exercises operands "
                f"{sorted(operands[golden_key] - declared_operands)} not declared by {def_names}"
            )
            assert results[golden_key] <= declared_results, (
                f"{golden_key}: golden produces results "
                f"{sorted(results[golden_key] - declared_results)} not declared by {def_names}"
            )


def _token_to_type(token: str) -> str:
    """Map a drift-corpus operand token (``int``, ``lit_str``, ``int_arr`` …) to its DataType name."""
    token = token.replace("lit_", "")
    token = {"float": "dec"}.get(token, token)
    return _SPEC_TYPES.get(
        token,
        {"object": "OBJECT", "object_arr": "OBJECT_ARRAY", "map": "DECIMAL_MAP"}.get(
            token, token.upper()
        ),
    )
