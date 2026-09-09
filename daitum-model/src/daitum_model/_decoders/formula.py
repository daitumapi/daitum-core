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
Decoder for :class:`Formula`.

A :class:`Formula` serialises to ``{"dataType": ..., "formulaString": ...}`` and is reconstructed by
parsing the string back into its structured node tree.

The decode is verified for *faithfulness*, not byte-identity. This library's renderer emits a
canonical, fully-parenthesised form, so a formula it produced re-renders to exactly its original
string. But a formula generated elsewhere may use sparser bracketing and standard operator
precedence (e.g. ``A - B + 28 * C``); the parser normalises such input to the canonical form, so its
re-rendering deliberately differs from the input string. The faithfulness check is therefore that
the parse is a **fixed point**: re-parsing the reconstructed tree's rendering reproduces that same
rendering (the parser has reached canonical, stable form), and the declared ``dataType`` — which is
authoritative — is reproduced exactly. A genuine parse corruption fails this; a mere re-bracketing
does not. The decoder still fails loudly rather than fabricating a degraded result.

The JSON ``dataType`` is authoritative and is supplied to the parser so type-parameterised functions
whose type is not in the rendered string (notably ``BLANK``, which always renders ``BLANK()``)
reconstruct with their real type.

References (``[field]``, bare named-value ids, ``table[field]``) resolve through the
:class:`LoadContext` symbol table — fields relative to the owning table first, then any table — so a
calculated field's formula reconstructs against the right columns even when field ids collide across
tables. Because a formula may reference symbols not yet registered when it is first encountered, the
model decoder defers formula parsing to phase 2 (see :func:`defer_formula`); by then every table,
field and named value is registered, so resolution always succeeds for valid output.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any, cast

from daitum_model._decoders.data_types import decode_data_type
from daitum_model._parser import ParseError, Resolver, parse_formula
from daitum_model.decoding import LoadContext, LoadError, register_decoder
from daitum_model.formula import Formula, Operand


class _ContextResolver(Resolver):
    """Resolve a formula's references against the load context (owning table first)."""

    def __init__(self, ctx: LoadContext, owning_table: Any | None):
        self._ctx = ctx
        self._owning_table = owning_table

    def field(self, field_id: str) -> Operand:
        if self._owning_table is not None:
            found = self._owning_table.field_definitions.get(field_id)
            if found is not None:
                return cast(Operand, found)
        for obj in self._ctx.symbols.values():
            if _is_table(obj):
                found = obj.field_definitions.get(field_id)
                if found is not None:
                    return cast(Operand, found)
        raise ParseError(f"unresolved field reference {field_id!r}")

    def named_value(self, identifier: str) -> Operand:
        obj = self._ctx.symbols.get(identifier)
        if obj is None or _is_table(obj):
            raise ParseError(f"unresolved named value {identifier!r}")
        return cast(Operand, obj)

    def table(self, table_id: str) -> object:
        # Resolve tables shadow-proof: a field/named value may share a table's id and would
        # otherwise mask the table in the shared symbol table (e.g. a column access
        # ``Role_Specifications[UI Display]`` where a field is also named ``Role_Specifications``).
        table = self._ctx.find_table(table_id)
        if table is None:
            raise ParseError(f"unresolved table {table_id!r}")
        return table

    def maybe_table(self, identifier: str) -> object | None:
        return self._ctx.find_table(identifier)


def _is_table(obj: Any) -> bool:
    from daitum_model.tables import Table

    return isinstance(obj, Table)


def decode_formula(
    data: dict[str, Any], ctx: LoadContext, owning_table: Any | None = None
) -> Formula:
    """Reconstruct a :class:`Formula` from its built dict by parsing it into a structured tree.

    Raises :class:`LoadError` if the string cannot be parsed, does not resolve its references, or
    the reconstructed tree is not a faithful parse — its rendering is not a stable fixed point
    (i.e. re-parsing corrupts it), or its inferred type differs from the authoritative declared
    type. A formula produced by this library round-trips its string exactly; a formula authored
    elsewhere with sparser bracketing is normalised to the canonical form, which is what the
    fixed-point check verifies.
    """
    if "dataType" not in data or "formulaString" not in data:
        raise LoadError(f"Formula missing 'dataType'/'formulaString': {data!r}")
    data_type = decode_data_type(data["dataType"], ctx)
    expression = data["formulaString"]
    resolver = _ContextResolver(ctx, owning_table)
    try:
        parsed = parse_formula(expression, resolver, expected_type=data_type)
    except (ParseError, ValueError) as exc:
        raise LoadError(f"Cannot decode formula {expression!r}: {exc}") from exc
    if not isinstance(parsed, Formula):
        # A formula may be a single reference — a calculated field that just aliases another field
        # or a named value (its ``formulaString`` is a bare ``[field]`` / id). ``parse_formula``
        # resolves that to the referenced operand (not a ``Formula`` node), which is exactly what
        # the builder wraps in a ``Reference`` via ``to_formula`` (see ``add_calculated_field``).
        # Mirror that here so decode is the inverse of build and the reference stays visible to
        # ``dependencies()``.
        from daitum_model.formula import Reference  # noqa: PLC0415 - avoid an import cycle

        parsed = Reference(parsed)
    if parsed.to_data_type() != data_type:
        raise LoadError(
            f"Decoded formula type mismatch: {expression!r} declared {data_type} but inferred "
            f"{parsed.to_data_type()}"
        )
    _verify_faithful_parse(expression, parsed, resolver, data_type)
    return parsed


def _verify_faithful_parse(
    expression: str, parsed: Formula, resolver: Resolver, data_type: object
) -> None:
    """Assert *parsed* is a faithful, non-degraded parse of *expression*.

    The parser normalises to a canonical, fully-parenthesised rendering, so a foreign expression
    with sparser bracketing legitimately re-renders to a different string. Faithfulness is therefore
    a *fixed point*: re-parsing the canonical rendering must reproduce that same rendering (and the
    same type). A genuine corruption — a tree that renders to something that parses differently —
    fails this; a mere re-bracketing round-trips on the second pass. When the input was already
    canonical (this library's own output) the first rendering equals the input, so this reduces to
    the exact round-trip it replaced.
    """
    canonical = parsed.to_string()
    try:
        reparsed = parse_formula(canonical, resolver, expected_type=data_type)
    except (ParseError, ValueError) as exc:  # pragma: no cover - a stable render should reparse
        raise LoadError(
            f"Decoded formula {expression!r} rendered to {canonical!r}, which does not parse: {exc}"
        ) from exc
    # Compare renderings, not node kinds: a bare-reference formula (a field/named-value alias)
    # re-parses to the referenced operand rather than a ``Formula`` node, but still renders the same
    # canonical string. Faithfulness is that stable rendering.
    if not isinstance(reparsed, Operand) or reparsed.to_string() != canonical:
        got = reparsed.to_string() if isinstance(reparsed, Operand) else repr(reparsed)
        raise LoadError(
            f"Decoded formula is not a faithful parse: {expression!r} rendered to {canonical!r} "
            f"but re-parsing yielded {got!r}"
        )


def placeholder_formula(data: dict[str, Any], ctx: LoadContext) -> Formula:
    """A typed stand-in carrying the formula's declared type + string, used until phase 2 parses the
    real tree. It builds identically to the final formula, so an owner (field/calculation) is valid
    the moment it is constructed even though its structured formula is attached later."""
    from daitum_model.formula import Constant

    data_type = decode_data_type(data["dataType"], ctx)
    return Constant(data_type, data["formulaString"])


def defer_formula(
    data: dict[str, Any],
    ctx: LoadContext,
    owning_table: Any | None,
    attach: Callable[[Formula], None],
) -> None:
    """Queue a formula for phase-2 parsing, attaching the result to its owner via *attach*.

    Used by the model decoder so a formula is parsed only after every symbol it may reference is
    registered. The parse itself is :func:`decode_formula`, which fails loudly on any problem.
    """
    ctx.defer_formula(lambda: attach(decode_formula(data, ctx, owning_table)))


def register() -> None:
    """Register the formula decoder."""
    register_decoder(Formula, decode_formula)
