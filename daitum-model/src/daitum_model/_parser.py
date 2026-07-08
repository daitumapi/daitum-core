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
Parser: reconstruct a structured :class:`~daitum_model.formula.Formula` tree from a rendered
platform expression string.

This is the inverse of the node renderers (``to_string``). It tokenises the expression grammar and
recursively rebuilds the real ``Function`` / operator / ``Constant`` nodes, so a formula loaded from
JSON regains its structure (and therefore its :meth:`~daitum_model.formula.Formula.dependencies`).

This library's renderer fully parenthesises every arithmetic/comparison operation, so its own
output is always canonically bracketed (``(L op R)``). The parser is a *strict superset* of that
canonical form: it also accepts unparenthesised operator chains authored elsewhere (e.g.
``A - B + 28 * C``), disambiguated by the standard precedence and associativity declared on each
:class:`~daitum_model.expression.OperatorDef`. Because the canonical form is fully bracketed,
those precedence tiers never change how a rendered-here formula reparses — they only give meaning
to foreign, sparsely-bracketed input.

Grammar (whitespace is insignificant — the platform strips it before evaluating)::

    expr(p)     := unary ( binary_op expr(p') )*   # precedence climbing; op.precedence >= p
    unary       := '-' expr(power_prec) | '-' number | member
    member      := primary ( '.' '[' id ']' )*     # postfix member access
    primary     := literal | reference | call | '(' expr(0) ')'
    call        := NAME '(' [ expr(0) (',' expr(0))* ] ')'
    reference   := '[' id ']'                       # field, resolved via the resolver
                 | id '[' id ']'                     # column access  table[field]
                 | id                                # named value (parameter/calculation)
    literal     := number | '"' chars '"' | 'TRUE' | 'FALSE'

Binary operators (tightest-binding last): ``=`` ``<>`` < ``<`` ``>`` ``<=`` ``>=`` < ``&`` <
``+`` ``-`` < ``*`` ``/`` < ``^`` (right-associative). All but ``^`` are left-associative.

References are resolved through a caller-supplied :class:`Resolver`, which knows the owning table
(so a bare ``[field]`` resolves table-locally first, avoiding cross-table id collisions) and the
global symbol table (named values, other tables).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol, cast

from daitum_model import _functions
from daitum_model.expression import (
    ADD,
    CONCAT,
    DIVIDE,
    EQUALS,
    GREATER_EQUAL,
    GREATER_THAN,
    LESS_EQUAL,
    LESS_THAN,
    MULTIPLY,
    NOT_EQUALS,
    POWER_OP,
    SUBTRACT,
    ColumnAccess,
    MemberAccess,
    OperatorDef,
    UnaryOperator,
)
from daitum_model.formula import CONST, Constant, Formula, Operand, unescape_string_literal


class ParseError(Exception):
    """Raised when an expression string cannot be parsed into a structured formula."""


class Resolver(Protocol):
    """Resolves the leaf references a formula string names into live operands."""

    def field(self, field_id: str) -> Operand:
        """A bare ``[field_id]`` reference (resolved relative to the owning table first)."""

    def named_value(self, identifier: str) -> Operand:
        """A bare ``identifier`` reference (a parameter or calculation)."""

    def table(self, table_id: str) -> object:
        """A table id (for ``table[field]`` column access and table-valued function args)."""

    def maybe_table(self, identifier: str) -> object | None:
        """The table named *identifier*, or ``None`` if it is not a table (a named value)."""


# --- function name -> node class -------------------------------------------


#: Map a function's *wire* name (what it renders as) to its node class. The wire name is the
#: ``render_name()`` where overridden (``LOOKUP_ARRAY``), else the class ``name``.
def _function_table() -> dict[str, type]:
    table: dict[str, type] = {}
    for obj in vars(_functions).values():
        if (
            isinstance(obj, type)
            and issubclass(obj, _functions.Function)
            and obj is not _functions.Function
            and obj.name
        ):
            wire = "LOOKUP_ARRAY" if obj.name == "LOOKUPARRAY" else obj.name
            table[wire] = obj
    return table


_FUNCTIONS = _function_table()

# Every binary operator by its rendered symbol. Precedence and associativity for parsing
# unparenthesised chains are read from each :class:`OperatorDef`, so equality and comparison are
# not special-cased here — they differ only in their declared precedence.
_BINARY_BY_SYMBOL: dict[str, OperatorDef] = {
    op.symbol: op
    for op in (
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
}

#: Precedence at which unary negation parses its operand: it binds tighter than every binary
#: operator except power, so ``-A^B`` is ``-(A^B)`` while ``-A*B`` is ``(-A)*B`` — standard maths.
_UNARY_OPERAND_PRECEDENCE = POWER_OP.precedence


# --- tokeniser --------------------------------------------------------------


@dataclass(frozen=True)
class _Token:
    kind: str  # 'num' | 'str' | 'id' | 'sym'
    text: str


# ``[`` / ``]`` are handled specially (bracketed reference tokens), so they are not listed here.
_SYMBOLS = ("<=", ">=", "<>", "(", ")", ".", ",", "+", "-", "*", "/", "^", "&", "<", ">", "=")


def _tokenise(text: str) -> list[_Token]:  # noqa: PLR0912 - a scanner is inherently branchy
    tokens: list[_Token] = []
    i, n = 0, len(text)
    while i < n:
        ch = text[i]
        if ch.isspace():
            i += 1
            continue
        if ch == '"':
            # Scan to the closing quote, honouring backslash escapes (``\"`` / ``\\``) so an escaped
            # quote does not end the literal. The token stores the *unescaped* value; ``CONST``
            # re-escapes it when rendering, keeping the two sides exact inverses.
            j = i + 1
            while j < n and text[j] != '"':
                j += 2 if text[j] == "\\" and j + 1 < n else 1
            if j >= n:
                raise ParseError(f"unterminated string literal in {text!r}")
            tokens.append(_Token("str", unescape_string_literal(text[i + 1 : j])))
            i = j + 1
            continue
        if ch == "[":
            # A bracketed reference captures its raw id verbatim — field/column ids may contain
            # spaces and punctuation (e.g. ``[Row Cost]``), so the content is not sub-tokenised.
            j = text.find("]", i + 1)
            if j == -1:
                raise ParseError(f"unterminated reference in {text!r}")
            tokens.append(_Token("field", text[i + 1 : j]))
            i = j + 1
            continue
        if ch.isdigit() or (ch == "." and i + 1 < n and text[i + 1].isdigit()):
            j = i
            while j < n and (text[j].isdigit() or text[j] == "."):
                j += 1
            tokens.append(_Token("num", text[i:j]))
            i = j
            continue
        if ch.isalpha() or ch == "_":
            j = i
            while j < n and (text[j].isalnum() or text[j] == "_"):
                j += 1
            tokens.append(_Token("id", text[i:j]))
            i = j
            continue
        for sym in _SYMBOLS:
            if text.startswith(sym, i):
                tokens.append(_Token("sym", sym))
                i += len(sym)
                break
        else:
            raise ParseError(f"unexpected character {ch!r} at {i} in {text!r}")
    return tokens


# --- parser -----------------------------------------------------------------


class _Parser:
    def __init__(self, tokens: list[_Token], resolver: Resolver, expected_type: object = None):
        self._tokens = tokens
        self._pos = 0
        self._resolver = resolver
        # The authoritative result type from the decoder, used by functions whose type is not
        # recoverable from the rendered string (only ``BLANK`` — it always renders ``BLANK()``).
        self._expected_type = expected_type

    # -- token helpers --
    def _peek(self) -> _Token | None:
        return self._tokens[self._pos] if self._pos < len(self._tokens) else None

    def _next(self) -> _Token:
        tok = self._peek()
        if tok is None:
            raise ParseError("unexpected end of expression")
        self._pos += 1
        return tok

    def _expect_sym(self, sym: str) -> None:
        tok = self._next()
        if tok.kind != "sym" or tok.text != sym:
            raise ParseError(f"expected {sym!r}, got {tok.text!r}")

    def _at_sym(self, sym: str) -> bool:
        tok = self._peek()
        return tok is not None and tok.kind == "sym" and tok.text == sym

    # -- grammar --
    #
    # A precedence-climbing (Pratt) expression parser. The library's own renderer fully
    # parenthesises every arithmetic/comparison operation — ``(L op R)`` — so a formula produced
    # here is unambiguous whatever the precedence tiers are: its explicit brackets already fix the
    # tree, and reparsing it always yields the same structure. Precedence and associativity
    # (declared on each :class:`OperatorDef`) therefore only ever disambiguate *unparenthesised*
    # operator chains authored elsewhere (e.g. ``A - B + 28 * C``), which the platform evaluates by
    # standard precedence. This makes the parser a strict superset of the canonical grammar.
    def parse(self) -> Operand:
        node = self._expression(0)
        if self._peek() is not None:
            raise ParseError(f"trailing tokens after expression: {self._peek()!r}")
        return node

    def _expression(self, min_precedence: int) -> Operand:
        """Parse an expression whose operators all bind at least as tightly as *min_precedence*."""
        left = self._unary()
        while True:
            tok = self._peek()
            if tok is None or tok.kind != "sym":
                break
            operator = _BINARY_BY_SYMBOL.get(tok.text)
            if operator is None or operator.precedence < min_precedence:
                break
            self._next()
            # Left-associative: the right operand must bind *strictly* tighter, so a following
            # operator of equal precedence is left for this level (giving ``(a-b)-c``).
            # Right-associative (``^``): allow equal precedence on the right (``a^(b^c)``).
            next_min = (
                operator.precedence if operator.right_associative else operator.precedence + 1
            )
            right = self._expression(next_min)
            left = self._apply_binary(operator, left, right)
        return left

    def _apply_binary(self, operator: OperatorDef, left: Operand, right: Operand) -> Operand:
        if operator in (EQUALS, NOT_EQUALS):
            return _build_equality(operator, left, right)
        return _build_binary(operator, left, right)

    def _unary(self) -> Operand:
        tok = self._peek()
        if tok is None:
            raise ParseError("unexpected end of expression")
        # negation: a negative numeric literal ``-3`` / ``-1.5``, the rendered form ``-(expr)``,
        # or (from foreign input) ``-`` before any operand, binding just below power.
        if tok.kind == "sym" and tok.text == "-":
            self._next()
            following = self._peek()
            if following is not None and following.kind == "num":
                self._next()
                return _number("-" + following.text)
            operand = self._expression(_UNARY_OPERAND_PRECEDENCE)
            return UnaryOperator(operand, operand.to_data_type())
        return self._member()

    def _member(self) -> Operand:
        node = self._primary()
        while self._at_sym("."):
            self._next()
            field_tok = self._next()
            if field_tok.kind != "field":
                raise ParseError(f"expected a [field] after '.', got {field_tok.text!r}")
            node = MemberAccess(node, field_tok.text)
        return node

    def _primary(self) -> Operand:
        tok = self._peek()
        if tok is None:
            raise ParseError("unexpected end of expression")
        # parenthesised sub-expression: the canonical ``(L op R)`` group, a redundant ``(x)``, or a
        # foreign multi-operator group ``(a + b + c)`` — all just a full expression in brackets.
        if tok.kind == "sym" and tok.text == "(":
            self._next()
            inner = self._expression(0)
            self._expect_sym(")")
            return inner
        # field reference: [id]
        if tok.kind == "field":
            self._next()
            return self._resolver.field(tok.text)
        if tok.kind == "id":
            return self._identifier()
        return self._literal(tok)

    def _literal(self, tok: _Token) -> Operand:
        if tok.kind == "num":
            self._next()
            return _number(tok.text)
        if tok.kind == "str":
            self._next()
            return CONST(tok.text)
        raise ParseError(f"unexpected token {tok.text!r}")

    def _identifier(self) -> Operand:
        name = self._next().text
        # function call: NAME(...)
        if self._at_sym("("):
            return self._call(name)
        # boolean literals
        if name == "TRUE":
            return CONST(True)
        if name == "FALSE":
            return CONST(False)
        # column access: table[field]
        nxt = self._peek()
        if nxt is not None and nxt.kind == "field":
            self._next()
            table = self._resolver.table(name)
            return ColumnAccess(table, nxt.text)
        # A bare id is either a table used as an object-array operand (ROWS(Jobs), INDEX(Jobs, …))
        # or a named value (parameter / calculation). Tables resolve first.
        table = self._resolver.maybe_table(name)
        if table is not None:
            return cast(Operand, table)
        return self._resolver.named_value(name)

    def _call(self, wire_name: str) -> Operand:
        # The name token was consumed by ``_identifier`` immediately before this call, so it sits
        # one position back; used to tell a root ``BLANK()`` from a nested one.
        start = self._pos - 1
        # ``ROW()`` renders as a no-arg call but is a constant, not a ``_functions`` class.
        if wire_name == "ROW":
            self._expect_sym("(")
            self._expect_sym(")")
            from daitum_model.data_types import DataType

            return Constant(DataType.INTEGER, "ROW()")
        cls = _FUNCTIONS.get(wire_name)
        if cls is None:
            raise ParseError(f"unknown function {wire_name!r}")
        self._expect_sym("(")
        args: list[object] = []
        if not self._at_sym(")"):
            args.append(self._argument(wire_name, len(args)))
            while self._at_sym(","):
                self._next()
                args.append(self._argument(wire_name, len(args)))
        end = self._pos
        self._expect_sym(")")
        # ``BLANK`` carries a declared type it does not render (it always emits ``BLANK()``). The
        # decoder's ``expected_type`` is the *whole formula's* result type, so it may only re-type a
        # ``BLANK()`` that is itself the entire formula. A nested ``BLANK()`` (e.g. the fallback in
        # ``IFERROR(LOOKUP(...), BLANK())``) must stay ``NULL`` and let the surrounding function
        # merge it — otherwise the outer type propagates inward and clashes with its sibling's type.
        if (
            wire_name == "BLANK"
            and not args
            and self._expected_type is not None
            and self._spans_whole_input(start, end)
        ):
            node: Formula = cls(self._expected_type)
        else:
            built = cls(*args)
            assert isinstance(built, Formula)
            node = built
        return node

    def _spans_whole_input(self, start: int, end: int) -> bool:
        """Whether a call occupying tokens ``[start, end]`` is the entire formula (a root node)."""
        return start == 0 and end == len(self._tokens) - 1

    def _argument(self, wire_name: str, index: int) -> object:
        # TOMAP's second argument is a bare table id (a map key-source), not an expression.
        if wire_name == "TOMAP" and index == 1:
            tok = self._next()
            if tok.kind != "id":
                raise ParseError("TOMAP second argument must be a table id")
            return self._resolver.table(tok.text)
        return self._expression(0)


def _number(text: str) -> Formula:
    if "." in text:
        return CONST(float(text))
    return CONST(int(text))


def _build_binary(definition: OperatorDef, left: Operand, right: Operand) -> Formula:
    """Reconstruct an arithmetic/comparison/concat operator, re-deriving the result type."""
    from daitum_model import expression as expr

    if definition is CONCAT:
        return expr.build_concat(left, right)
    return expr.build_numeric(definition, left, right)


def _build_equality(definition: OperatorDef, left: Operand, right: Operand) -> Formula:
    from daitum_model import expression as expr

    return expr.build_equality(definition, left, right)


def parse_formula(expression: str, resolver: Resolver, expected_type: object = None) -> Operand:
    """Parse *expression* into a structured formula, resolving references via *resolver*.

    *expected_type* is the authoritative result type (from the decoder's ``dataType``); it is used
    to reconstruct functions whose type is not in the rendered string (``BLANK``). Returns an
    :class:`~daitum_model.formula.Operand` — a :class:`Formula` node for any compound expression, or
    a bare reference leaf for a single reference. Raises :class:`ParseError` on malformed input.
    """
    tokens = _tokenise(expression)
    if not tokens:
        raise ParseError("empty expression")
    return _Parser(tokens, resolver, expected_type).parse()
