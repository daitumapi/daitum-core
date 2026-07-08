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
Reference-resolution helpers shared by the configuration decoders.

Configuration JSON refers to model objects in several rendered forms, all resolved
against the model's :class:`~daitum_model.decoding.LoadContext` symbol table:

* ``"!!!TOTAL_COST"`` / ``"TOTAL_COST"`` — a named value (calculation/parameter) by id.
* ``"!!!Items[Quantity]"`` / ``"Items[Quantity]"`` — a per-row field, ``table[field]``.
* ``"!!![Quantity]"`` / ``"[Quantity]"`` — a field, bracketed form.
"""

from __future__ import annotations

import re
from typing import Any

from daitum_model.decoding import LoadContext
from daitum_model.references import REFERENCE_PREFIX

_COLUMN_RE = re.compile(r"^(?P<table>[^\[\]]+)\[(?P<field>[^\[\]]+)\]$")
_BRACKET_RE = re.compile(r"^\[(?P<field>[^\[\]]+)\]$")


def strip_prefix(rendered: str) -> str:
    """Remove a leading ``!!!`` if present."""
    return rendered.removeprefix(REFERENCE_PREFIX)


def resolve_value(rendered: str, ctx: LoadContext) -> Any:
    """Resolve a rendered reference (any of the supported forms) to the live model object."""
    body = strip_prefix(rendered)

    column = _COLUMN_RE.match(body)
    if column:
        # A ``table[field]`` reference is resolved *through* its table so a field id that is
        # not unique across tables still resolves to the correct field (the shared symbol
        # table is keyed by bare field id, so the table qualifier is the disambiguator).
        # Resolve the table shadow-proof: a field/named value may share the table's id and would
        # otherwise mask it in the symbol table.
        table = ctx.find_table(column.group("table"))
        field = column.group("field")
        if table is not None:
            return table.get_field(field)
        return ctx.resolve(field)

    bracket = _BRACKET_RE.match(body)
    if bracket:
        return ctx.resolve(bracket.group("field"))

    return ctx.resolve(body)


def resolve_table(rendered: str, ctx: LoadContext) -> Any | None:
    """Resolve the owning table of a ``table[field]`` reference, or ``None`` for a bare id.

    The table is resolved shadow-proof (see :meth:`LoadContext.find_table`) so a field/named value
    sharing the table's id cannot mask it.
    """
    body = strip_prefix(rendered)
    column = _COLUMN_RE.match(body)
    if column:
        return ctx.find_table(column.group("table"))
    return None
