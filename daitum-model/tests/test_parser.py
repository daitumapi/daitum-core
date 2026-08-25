"""
Parser round-trip tests: every rendered expression parses back to an equivalent structured formula.

The corpus conformance test is the safety net for the decoder wiring — it asserts that for every
formula/operator the drift corpus renders, ``parse_formula(f.to_string())`` reconstructs a formula
``is_equivalent`` to the original (same whitespace-insensitive rendering + inferred type). This is a
structural check, not a brittle string compare.
"""

from __future__ import annotations

import pytest
from daitum_model._parser import ParseError, Resolver, parse_formula
from fixtures.contract_cases import function_cases, operator_cases
from fixtures.contract_model import build_fixture


class _FixtureResolver(Resolver):
    """Resolve references against the shared contract fixture (owning table first, then global)."""

    def __init__(self, fx):
        self._fx = fx
        self._tables = {fx.table.id: fx.table, fx.other_table.id: fx.other_table}
        self._named = {fx.calc.id: fx.calc, fx.param.id: fx.param}

    def field(self, field_id: str) -> Operand:
        for table in self._tables.values():
            found = table.field_definitions.get(field_id)
            if found is not None:
                return found
        raise ParseError(f"unknown field {field_id!r}")

    def named_value(self, identifier: str) -> Operand:
        if identifier in self._named:
            return self._named[identifier]
        raise ParseError(f"unknown named value {identifier!r}")

    def table(self, table_id: str):
        if table_id in self._tables:
            return self._tables[table_id]
        raise ParseError(f"unknown table {table_id!r}")

    def maybe_table(self, identifier: str):
        return self._tables.get(identifier)


# One shared fixture so reference leaves (and the tables behind ObjectDataType) are the *same*
# objects in both the built formula and the resolver — type equality compares table identity.
_FIXTURE = build_fixture()
_RESOLVER = _FixtureResolver(_FIXTURE)


# ``BLANK(data_type)`` always renders ``BLANK()`` — the declared type is erased from the string. The
# parser cannot recover it from the *string alone*, so it is excluded from the string-only round-trip
# below; the decoder supplies the type via ``expected_type`` (see ``test_blank_decodes_with_type``).
_UNPARSEABLE = {"BLANK typed"}


def _equivalent_cases():
    """All corpus cases that build a Formula (skip error cases and inherently unparseable ones)."""
    from daitum_model.formula import Formula

    for case in function_cases() + operator_cases():
        if case.name in _UNPARSEABLE:
            continue
        try:
            built = case.build(_FIXTURE)
        except Exception:  # noqa: BLE001 - error cases aren't round-trip candidates
            continue
        if isinstance(built, Formula):
            yield case.name, built


class TestParserRoundTrip:
    @pytest.mark.parametrize(
        "name,built", list(_equivalent_cases()), ids=lambda v: v if isinstance(v, str) else ""
    )
    def test_corpus_formula_round_trips(self, name, built):
        reparsed = parse_formula(built.to_string(), _RESOLVER)
        assert built.is_equivalent(reparsed), (
            f"{name}: {built.to_string()!r} reparsed to {reparsed.to_string()!r} "
            f"(types {built.to_data_type()} vs {reparsed.to_data_type()})"
        )


class TestStringLiteralEscaping:
    """String literals use ``"…"`` with ``\\"`` for an embedded quote and ``\\\\`` for a backslash.
    The tokeniser must honour those escapes (an escaped quote does not end the literal) and the
    renderer must produce them, so a string containing quotes/backslashes round-trips."""

    @pytest.mark.parametrize("value", ['"', "\\", 'a"b', "x\\y", 'say "hi"', "c:\\path", "{}", ""])
    def test_escape_unescape_are_inverse(self, value):
        from daitum_model.formula import escape_string_literal, unescape_string_literal

        literal = escape_string_literal(value)
        assert literal[0] == '"' and literal[-1] == '"'
        assert unescape_string_literal(literal[1:-1]) == value

    def test_const_with_quote_round_trips_through_the_parser(self):
        from daitum_model.formula import CONST

        original = CONST('a"b')
        assert original.to_string() == '"a\\"b"'
        reparsed = parse_formula(original.to_string(), _RESOLVER)
        assert reparsed.is_equivalent(original)

    def test_escaped_quote_literal_does_not_terminate_the_string(self):
        # The escaped-quote token from the reported formula: "\"" is the single-character string ".
        reparsed = parse_formula('TEXTJOIN("", TRUE, ARRAY(TRUE, "\\"", "}"))', _RESOLVER)
        assert reparsed.to_data_type().name == "STRING"


class TestUnparenthesisedChains:
    """Formulas authored elsewhere (or by another tool) omit the canonical per-operation brackets
    this library's renderer always emits, relying on standard operator precedence instead. The
    parser must decode such chains to the same tree the equivalent bracketed/overload-built formula
    produces. Each case parses a sparsely-bracketed string and asserts it is *equivalent* to the
    tree built via the Python operator overloads — i.e. the precedence interpretation is correct.
    """

    def _parse(self, expr: str):
        return parse_formula(expr, _RESOLVER)

    def _fields(self):
        # Resolve the leaves exactly as the parser does for a bare ``[id]`` reference, so an
        # overload-built "expected" tree renders identically (same leaf kind) to the parsed one.
        return _RESOLVER.field("Cost"), _RESOLVER.field("Qty")

    def test_original_reported_formula_parses(self):
        # The formula from the bug report: a function argument that is a flat operator chain.
        expr = (
            "PLUSDAYS([Day], DAYSBETWEEN([Day], [Stamp]) - MOD(DAYSBETWEEN([Day], [Stamp]), 28)"
            " + 28 * ([Qty] - 1))"
        )
        parsed = self._parse(expr)
        # Standard precedence: ((DAYSBETWEEN - MOD) + (28 * (Qty - 1))) inside PLUSDAYS.
        assert parsed.to_string() == (
            "PLUSDAYS([Day], ((DAYSBETWEEN([Day], [Stamp]) - MOD(DAYSBETWEEN([Day], [Stamp]), 28))"
            " + (28 * ([Qty] - 1))))"
        )

    def test_multiplicative_binds_tighter_than_additive(self):
        cost, qty = self._fields()
        assert self._parse("[Cost] + [Qty] * [Cost]").is_equivalent(cost + qty * cost)
        assert self._parse("[Cost] * [Qty] + [Cost]").is_equivalent(cost * qty + cost)
        assert self._parse("[Cost] - [Qty] + [Cost]").is_equivalent(cost - qty + cost)

    def test_additive_chain_is_left_associative(self):
        cost, qty = self._fields()
        assert self._parse("[Cost] - [Qty] - [Cost]").is_equivalent(cost - qty - cost)
        assert self._parse("[Cost] + [Qty] + [Cost]").is_equivalent(cost + qty + cost)

    def test_power_is_right_associative_and_binds_tightest(self):
        cost, qty = self._fields()
        assert self._parse("[Cost] ^ [Qty] ^ [Cost]").is_equivalent(cost ^ (qty ^ cost))
        assert self._parse("2 * [Cost] ^ [Qty]").is_equivalent(2 * (cost ^ qty))

    def test_unary_negation_binds_below_power_but_above_multiply(self):
        cost, qty = self._fields()
        assert self._parse("-[Cost] * [Qty]").is_equivalent((-cost) * qty)
        assert self._parse("-[Cost] ^ [Qty]").is_equivalent(-(cost ^ qty))

    def test_redundant_and_nested_parentheses(self):
        cost, qty = self._fields()
        assert self._parse("(([Cost] + [Qty]))").is_equivalent(cost + qty)
        assert self._parse("([Cost] + [Qty]) * [Cost]").is_equivalent((cost + qty) * cost)

    def test_comparison_and_equality_precedence(self):
        cost, qty = self._fields()
        # comparison binds tighter than equality: `a < b = c` -> `(a < b) = c`
        assert self._parse("[Cost] < [Qty] = [Qty] < [Cost]").is_equivalent(
            (cost < qty).equal_to(qty < cost)
        )

    def test_mixed_chain_matches_standard_precedence(self):
        cost, qty = self._fields()
        # a + b * c - d  ->  ((a + (b*c)) - d)
        assert self._parse("[Cost] + [Qty] * [Cost] - [Qty]").is_equivalent(cost + qty * cost - qty)


# Renderings that cannot round-trip because the string erases the type — see ``_UNPARSEABLE``.
# In the drift corpus these are the ``BLANK(...)`` typed cases, which all render ``BLANK()``.
def _unparseable_drift(name: str) -> bool:
    return name.startswith("BLANK(") and name != "BLANK()"


class TestParserDriftConformance:
    """The full ~14k-case conformance gate (plan §6): every formula the exhaustive drift corpus
    renders must parse back to an equivalent structured formula. This is what proves the parser is
    faithful enough to back the decoder."""

    def test_every_drift_formula_round_trips(self):
        from daitum_model.formula import Formula
        from fixtures.drift_corpus import build_drift_cases

        failures: list[str] = []
        checked = 0
        for name, builder in build_drift_cases().items():
            if _unparseable_drift(name):
                continue
            try:
                built = builder(_FIXTURE)
            except Exception:  # noqa: BLE001 - rejected inputs aren't round-trip candidates
                continue
            if not isinstance(built, Formula):
                continue
            checked += 1
            try:
                reparsed = parse_formula(built.to_string(), _RESOLVER)
            except Exception as exc:  # noqa: BLE001
                failures.append(f"{name}: {built.to_string()!r} -> PARSE ERROR {exc}")
                continue
            if not built.is_equivalent(reparsed):
                failures.append(
                    f"{name}: {built.to_string()!r} -> {reparsed.to_string()!r} "
                    f"(types {built.to_data_type()} vs {reparsed.to_data_type()})"
                )
        assert checked > 1000, f"expected a large corpus, only checked {checked}"
        assert not failures, f"{len(failures)} drift formulas failed to round-trip:\n" + "\n".join(
            failures[:30]
        )

    def test_blank_decodes_with_type(self):
        """``BLANK(type)`` renders ``BLANK()`` (type erased from the string), but the decoder
        supplies the authoritative ``expected_type`` so the typed blank reconstructs exactly."""
        import daitum_model.formulas as formulas
        from daitum_model import DataType

        original = formulas.BLANK(DataType.DECIMAL)
        assert original.to_string() == "BLANK()"
        reparsed = parse_formula("BLANK()", _RESOLVER, expected_type=DataType.DECIMAL)
        assert original.is_equivalent(reparsed)
        assert reparsed.to_data_type() == DataType.DECIMAL

    def test_nested_blank_stays_untyped(self):
        """The decoder's ``expected_type`` re-types only a *top-level* ``BLANK()``. A nested
        ``BLANK()`` (e.g. the fallback of an ``IFERROR``) must stay ``NULL`` — applying the whole
        formula's type to it would clash with its sibling's type, so the parse would wrongly fail
        (``IFERROR: arguments must share a compatible type``)."""
        import daitum_model.formulas as formulas
        from daitum_model import DataType

        # An INTEGER-typed value with a BLANK fallback, wrapped so the *formula's* type is an array
        # that must not propagate into the nested BLANK.
        expr = "IFERROR([Qty], BLANK())"
        parsed = parse_formula(expr, _RESOLVER, expected_type=DataType.INTEGER_ARRAY)
        assert parsed.to_string() == expr
        assert parsed.to_data_type() == DataType.INTEGER
