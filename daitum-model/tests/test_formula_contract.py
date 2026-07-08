"""
Formula characterisation harness (Phase A of the formula refactor).

This suite pins the *public contract* of every formula function and operator — the rendered
expression string and the inferred data type — against a frozen golden file captured from the
current implementation. It asserts only on ``to_string()`` / ``to_data_type()`` / ``build()`` /
raised errors, never on internal node classes, so the identical suite proves equivalence both
before and after the structural refactor.

The golden file (``fixtures/formula_golden.json``) is auto-captured on first run if absent. To
re-capture deliberately, delete it and re-run. CI runs with it present, so any drift fails.
"""

from __future__ import annotations

import inspect
import json
from pathlib import Path

import pytest
from fixtures.contract_cases import Case, function_cases, operator_cases
from fixtures.contract_model import build_fixture
from fixtures.drift_corpus import (
    build_drift_cases,
    build_operator_drift_cases,
    capture_all,
)

from daitum_model import DataType, Formula, ModelBuilder, formulas as formulas_module
from daitum_model.decoding import LoadContext

GOLDEN_DIR = Path(__file__).parent / "fixtures"
FUNCTION_GOLDEN = GOLDEN_DIR / "formula_function_golden.json"
OPERATOR_GOLDEN = GOLDEN_DIR / "formula_operator_golden.json"
DRIFT_FUNCTION_GOLDEN = GOLDEN_DIR / "drift_function_golden.json"
DRIFT_OPERATOR_GOLDEN = GOLDEN_DIR / "drift_operator_golden.json"


def _is_formula_function(obj: object) -> bool:
    """The docs reflector's predicate, mirrored for the coverage gate."""
    return (
        inspect.isfunction(obj)
        and getattr(obj, "__name__", "").isupper()
        and obj.__name__[:1].isalpha()
    )


def _public_function_names() -> set[str]:
    return {name for name, obj in inspect.getmembers(formulas_module, _is_formula_function)} | {
        "CONST"
    }


def _capture(case: Case) -> dict[str, str]:
    fx = build_fixture()
    operand = case.build(fx)
    return {"to_string": operand.to_string(), "to_data_type": str(operand.to_data_type())}


def _load_or_capture(path: Path, cases: list[Case]) -> dict[str, dict[str, str]]:
    captured = {c.name: _capture(c) for c in cases}
    if not path.exists():
        path.write_text(json.dumps(captured, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return captured


# ---------------------------------------------------------------------------
# Function corpus
# ---------------------------------------------------------------------------


class TestFunctionCorpus:
    def test_function_cases_match_golden(self):
        cases = function_cases()
        captured = _load_or_capture(FUNCTION_GOLDEN, cases)
        golden = json.loads(FUNCTION_GOLDEN.read_text(encoding="utf-8"))
        for case in cases:
            assert (
                captured[case.name] == golden[case.name]
            ), f"Function case {case.name!r} drifted from golden"

    def test_every_public_function_is_covered(self):
        """Coverage gate: every public formula function appears in the corpus at least once."""
        covered: set[str] = set()
        for case in function_cases():
            # The leading token of the case name is the function it characterises.
            head = case.name.split()[0]
            covered.add(head)
        missing = _public_function_names() - covered
        assert not missing, f"Functions with no characterisation case: {sorted(missing)}"


# ---------------------------------------------------------------------------
# Operator corpus
# ---------------------------------------------------------------------------


class TestOperatorCorpus:
    def test_operator_cases_match_golden(self):
        cases = operator_cases()
        captured = _load_or_capture(OPERATOR_GOLDEN, cases)
        golden = json.loads(OPERATOR_GOLDEN.read_text(encoding="utf-8"))
        for case in cases:
            assert (
                captured[case.name] == golden[case.name]
            ), f"Operator case {case.name!r} drifted from golden"

    def test_member_access_uses_dot_form(self):
        fx = build_fixture()
        assert fx.fields["Site"]["Amount"].to_string() == "[Site].[Amount]"

    def test_column_access_uses_bracket_form(self):
        fx = build_fixture()
        # A raw table column reference MUST render with brackets, never the dot form.
        rendered = fx.table["Cost"].to_string()
        assert rendered == "Jobs[Cost]"
        assert "." not in rendered

    def test_arithmetic_parenthesised_equality_not(self):
        fx = build_fixture()
        assert (fx.fields["Cost"] + 1.0).to_string().startswith("(")
        assert not fx.fields["Cost"].equal_to(1.0).to_string().startswith("(")


class TestTableAsOperandEquivalence:
    """§3.2.1: once ``Table`` is an ``Operand``, the four ``Table | Operand`` functions must render
    a bare table identically whether the table is the *receiver type* ``Table`` or flows through
    the generic operand path. These pin the bare-``Table`` rendering now; the equivalence holds
    by construction post-refactor because ``Table.to_string()`` returns the table id.

    Note the operand-vs-table distinction these do NOT conflate: a table renders its *id*
    (``Sites``) whereas a field/object-array operand renders its *own* string (``[SiteList]``).
    The pinned invariant is that a *table* renders ``Sites`` through every one of these functions.
    """

    def test_lookup_bare_table_renders_table_id(self):
        fx = build_fixture()
        assert formulas_module.LOOKUP(fx.other_table, "Region", "x").to_string() == (
            'LOOKUP(Sites, "Region", "x", FALSE)'
        )

    def test_rows_bare_table_renders_table_id(self):
        fx = build_fixture()
        assert formulas_module.ROWS(fx.table).to_string() == "ROWS(Jobs)"

    def test_filter_bare_table_renders_table_id(self):
        fx = build_fixture()
        assert (
            formulas_module.FILTER(fx.table, fx.fields["Flags"])
            .to_string()
            .startswith("FILTER(Jobs,")
        )

    def test_index_bare_table_renders_table_id(self):
        fx = build_fixture()
        assert formulas_module.INDEX(fx.table, 1).to_string() == "INDEX(Jobs, 1)"


# ---------------------------------------------------------------------------
# Error-parity corpus
# ---------------------------------------------------------------------------

# Every invalid formula construction now raises ``ValueError`` (errors are standardised).
ERROR_CASES = {
    "negate_string": (lambda fx: -fx.fields["Name"], ValueError),
    "member_access_on_scalar": (lambda fx: fx.fields["Cost"]["x"], ValueError),
    "member_access_missing_field": (lambda fx: fx.fields["Site"]["Nope"], ValueError),
    "column_access_missing": (lambda fx: fx.table["Nope"], ValueError),
    "sum_string": (lambda fx: formulas_module.SUM(fx.fields["Name"]), ValueError),
    "add_incompatible": (lambda fx: fx.fields["Day"] + fx.fields["Qty"], ValueError),
}


class TestErrorParity:
    @pytest.mark.parametrize("name", sorted(ERROR_CASES))
    def test_error_type_preserved(self, name):
        builder, expected_exc = ERROR_CASES[name]
        fx = build_fixture()
        with pytest.raises(expected_exc):
            builder(fx)


# ---------------------------------------------------------------------------
# Build / decoder round-trip
# ---------------------------------------------------------------------------


class TestRoundTrip:
    def test_formula_build_shape(self):
        fx = build_fixture()
        formula = formulas_module.SUM(fx.fields["Cost"], 1.0)
        built = formula.build()
        assert set(built) == {"dataType", "formulaString"}
        assert built["dataType"] == "DECIMAL"
        assert built["formulaString"] == formula.to_string()

    def test_formula_decoder_round_trip(self):
        """The decoder reconstructs a structured Formula byte-identically (§0.1 acceptance)."""
        fx = build_fixture()
        formula = formulas_module.IF(fx.fields["Flag"], 0.0, fx.fields["Cost"])
        built = formula.build()
        from daitum_model._decoders.formula import decode_formula

        # The decoder resolves references against the load context; register the fixture's symbols.
        ctx = LoadContext()
        ctx.register(fx.table.id, fx.table)
        decoded = decode_formula(built, ctx, owning_table=fx.table)
        assert isinstance(decoded, Formula)
        assert decoded.build() == built

    def test_full_model_build_round_trips(self):
        """A model built with formulas decodes and re-builds byte-identically (§5.5)."""
        fx = build_fixture()
        fx.table.add_calculated_field(
            "DerivedCost", formulas_module.SUM(fx.fields["Cost"], fx.fields["Qty"])
        )
        built = fx.model.build()
        reloaded = ModelBuilder.read_from_dict(built)
        assert reloaded.build() == built


# ---------------------------------------------------------------------------
# Determinism
# ---------------------------------------------------------------------------


class TestDeterminism:
    def test_function_capture_is_deterministic(self):
        first = {c.name: _capture(c) for c in function_cases()}
        second = {c.name: _capture(c) for c in function_cases()}
        assert first == second

    def test_operator_capture_is_deterministic(self):
        first = {c.name: _capture(c) for c in operator_cases()}
        second = {c.name: _capture(c) for c in operator_cases()}
        assert first == second


# ---------------------------------------------------------------------------
# Exhaustive drift corpus — every validation branch + type-inference path
# ---------------------------------------------------------------------------


_MAX_REPORTED_DIFFS = 15


def _drift_diff(captured: dict, golden: dict) -> list[str]:
    """Return human-readable descriptions of the first handful of drifted cases."""
    diffs: list[str] = []
    for key in sorted(set(captured) | set(golden)):
        if captured.get(key) != golden.get(key):
            diffs.append(f"{key}:\n    golden={golden.get(key)}\n    now   ={captured.get(key)}")
        if len(diffs) >= _MAX_REPORTED_DIFFS:
            diffs.append("... (more)")
            break
    return diffs


class TestDriftCorpus:
    """~14k invocations across every function/operator x typed-operand combination, each pinned to
    its exact outcome — rendered string + inferred output type on success, exception type + message
    on rejection. This is the primary net proving the refactor preserves inputs, outputs, *types*,
    and *validation* — not merely the JSON of successful renders.
    """

    def test_function_drift(self):
        cases = build_drift_cases()
        captured = capture_all(cases)
        if not DRIFT_FUNCTION_GOLDEN.exists():
            DRIFT_FUNCTION_GOLDEN.write_text(
                json.dumps(captured, indent=2, sort_keys=True) + "\n", encoding="utf-8"
            )
        golden = json.loads(DRIFT_FUNCTION_GOLDEN.read_text(encoding="utf-8"))
        diffs = _drift_diff(captured, golden)
        assert not diffs, "Function behaviour drifted:\n" + "\n".join(diffs)

    def test_operator_drift(self):
        cases = build_operator_drift_cases()
        captured = capture_all(cases)
        if not DRIFT_OPERATOR_GOLDEN.exists():
            DRIFT_OPERATOR_GOLDEN.write_text(
                json.dumps(captured, indent=2, sort_keys=True) + "\n", encoding="utf-8"
            )
        golden = json.loads(DRIFT_OPERATOR_GOLDEN.read_text(encoding="utf-8"))
        diffs = _drift_diff(captured, golden)
        assert not diffs, "Operator behaviour drifted:\n" + "\n".join(diffs)

    def test_drift_corpus_is_deterministic(self):
        assert capture_all(build_drift_cases()) == capture_all(build_drift_cases())
        assert capture_all(build_operator_drift_cases()) == capture_all(
            build_operator_drift_cases()
        )


# ---------------------------------------------------------------------------
# Explicit input/output type + validation contracts
# ---------------------------------------------------------------------------
#
# The drift corpus pins behaviour exhaustively but opaquely. These spell out the *intended*
# type-inference and validation rules in a legible, reviewable form so the contract is documented,
# not merely frozen. Each asserts the inferred OUTPUT type for given INPUT types, or that a given
# input combination is rejected with the expected error.

# (input field name(s) -> expected output DataType) for representative type-inference rules.
OUTPUT_TYPE_CONTRACTS = [
    # SUM: INT-only -> INTEGER; any DECIMAL -> DECIMAL; array propagates
    ("SUM int int", lambda fx: formulas_module.SUM(fx.fields["Qty"], 1), DataType.INTEGER),
    ("SUM int dec", lambda fx: formulas_module.SUM(fx.fields["Qty"], 1.0), DataType.DECIMAL),
    ("SUM array", lambda fx: formulas_module.SUM(fx.fields["Qtys"]), DataType.INTEGER),
    # arithmetic: INT op INT -> INTEGER; mixed -> DECIMAL; div always DECIMAL
    ("add int int", lambda fx: fx.fields["Qty"] + 1, DataType.INTEGER),
    ("add int dec", lambda fx: fx.fields["Qty"] + 1.0, DataType.DECIMAL),
    ("mul array", lambda fx: fx.fields["Qtys"] * 2, DataType.INTEGER_ARRAY),
    # comparison / equality -> BOOLEAN(_ARRAY)
    ("lt -> bool", lambda fx: fx.fields["Cost"] < 1.0, DataType.BOOLEAN),
    ("lt array -> bool array", lambda fx: fx.fields["Costs"] < 1.0, DataType.BOOLEAN_ARRAY),
    ("eq -> bool", lambda fx: fx.fields["Name"].equal_to("x"), DataType.BOOLEAN),
    # string ops
    ("concat -> string", lambda fx: fx.fields["Name"] + "x", DataType.STRING),
    ("LEN -> integer", lambda fx: formulas_module.LEN(fx.fields["Name"]), DataType.INTEGER),
    ("UPPER -> string", lambda fx: formulas_module.UPPER(fx.fields["Name"]), DataType.STRING),
    # logical
    ("AND -> boolean", lambda fx: formulas_module.AND(fx.fields["Flag"], True), DataType.BOOLEAN),
    ("ISBLANK -> boolean", lambda fx: formulas_module.ISBLANK(fx.fields["Cost"]), DataType.BOOLEAN),
    # date/time
    ("DATE -> date", lambda fx: formulas_module.DATE(2026, 1, 1), DataType.DATE),
    ("YEAR -> integer", lambda fx: formulas_module.YEAR(fx.fields["Day"]), DataType.INTEGER),
    # IF branch-type: branches must match; NULL branch adopts the other branch's type
    (
        "IF dec/dec -> decimal",
        lambda fx: formulas_module.IF(fx.fields["Flag"], 1.0, fx.fields["Cost"]),
        DataType.DECIMAL,
    ),
    (
        "IF null branch -> decimal",
        lambda fx: formulas_module.IF(
            fx.fields["Flag"], formulas_module.BLANK(), fx.fields["Cost"]
        ),
        DataType.DECIMAL,
    ),
]

# (description, builder, expected exception) for representative input-validation rules.
VALIDATION_CONTRACTS = [
    ("SUM rejects string", lambda fx: formulas_module.SUM(fx.fields["Name"]), ValueError),
    ("SUM rejects no args", lambda fx: formulas_module.SUM(), ValueError),
    ("AND rejects date", lambda fx: formulas_module.AND(fx.fields["Day"], True), ValueError),
    ("arithmetic rejects date+int", lambda fx: fx.fields["Day"] + fx.fields["Qty"], ValueError),
    ("arithmetic rejects string*int", lambda fx: fx.fields["Name"] * fx.fields["Qty"], ValueError),
    ("negate rejects string", lambda fx: -fx.fields["Name"], ValueError),
    ("UPPER rejects integer", lambda fx: formulas_module.UPPER(fx.fields["Qty"]), ValueError),
    ("YEAR rejects time", lambda fx: formulas_module.YEAR(fx.fields["Clock"]), ValueError),
    (
        "LOOKUP rejects scalar receiver",
        lambda fx: formulas_module.LOOKUP(fx.fields["Cost"], "Region", "x"),
        ValueError,
    ),
    (
        "LOOKUP rejects missing field",
        lambda fx: formulas_module.LOOKUP(fx.other_table, "Nope", "x"),
        ValueError,
    ),
    (
        "LOOKUP rejects type-mismatched condition",
        lambda fx: formulas_module.LOOKUP(fx.other_table, "Amount", "x"),
        ValueError,
    ),
    ("member access rejects scalar", lambda fx: fx.fields["Cost"]["Amount"], ValueError),
    ("column access rejects missing", lambda fx: fx.table["Nope"], ValueError),
    (
        "BITMASK rejects non-boolean-array",
        lambda fx: formulas_module.BITMASK(fx.fields["Qtys"]),
        ValueError,
    ),
]


class TestTypeAndValidationContracts:
    @pytest.mark.parametrize(
        "name,builder,expected", OUTPUT_TYPE_CONTRACTS, ids=[c[0] for c in OUTPUT_TYPE_CONTRACTS]
    )
    def test_output_type(self, name, builder, expected):
        fx = build_fixture()
        result = builder(fx)
        assert (
            result.to_data_type() == expected
        ), f"{name}: expected output type {expected}, got {result.to_data_type()}"

    @pytest.mark.parametrize(
        "name,builder,expected_exc", VALIDATION_CONTRACTS, ids=[c[0] for c in VALIDATION_CONTRACTS]
    )
    def test_validation_rejects_bad_input(self, name, builder, expected_exc):
        fx = build_fixture()
        with pytest.raises(expected_exc):
            builder(fx)
