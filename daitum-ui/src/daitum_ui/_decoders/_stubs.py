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
Reference resolution for model tables/fields and views, with an id-only fallback.

Several UI constructors take a live ``Table``/``Field``/``BaseView`` but only read its
``id`` (storing the id string in ``build()``). The ``resolve_*`` helpers below return the
**real** decoded object from the load context's symbol table — which is populated for a
normal ``read_from_file`` load — so the realistic decode path never fabricates objects.

Only when a load is performed *without* a model (``ctx.model is None``) do they fall back
to an id-only stub: an instance of the correct type carrying just the id, created via
``__new__`` to bypass the real (validating, side-effecting) constructors. The stub carries
no behaviour; it exists solely so an id-only round-trip is possible in the model-less case.

The ``SLF001`` (private-member access) suppressions here are intentional: the stubs write
the same private id attribute the real constructors set, which is the only state ``build()``
reads back out.
"""

from __future__ import annotations

from daitum_model.decoding import LoadContext
from daitum_model.fields import DataField, Field
from daitum_model.tables import DataTable, Table

from daitum_ui.base_view import BaseView
from daitum_ui.tabular import TableView


def stub_table(table_id: str) -> Table:
    """A :class:`Table`-typed stand-in carrying only ``id`` (model-less fallback)."""
    stub = DataTable.__new__(DataTable)
    stub._id = table_id  # noqa: SLF001
    return stub


def stub_field(field_id: str) -> Field:
    """A :class:`Field`-typed stand-in carrying only ``id`` (model-less fallback)."""
    stub = DataField.__new__(DataField)
    stub.id = field_id
    return stub


def stub_view(view_id: str) -> BaseView:
    """A :class:`BaseView`-typed stand-in carrying only ``id`` (model-less fallback)."""
    stub = TableView.__new__(TableView)
    stub._id = view_id  # noqa: SLF001
    return stub


def resolve_table(table_id: str, ctx: LoadContext) -> Table:
    """The real :class:`Table` from the model, or an id-only stub if model-less.

    Resolved shadow-proof via :meth:`LoadContext.resolve_table` so a field/named value sharing the
    table's id cannot mask it in the shared symbol table.
    """
    return ctx.resolve_table(table_id) if ctx.model is not None else stub_table(table_id)


def resolve_field(field_id: str, ctx: LoadContext) -> Field:
    """The real :class:`Field` from the symbol table, or an id-only stub if model-less."""
    return ctx.resolve(field_id) if ctx.model is not None else stub_field(field_id)


def resolve_view(view_id: str, ctx: LoadContext) -> BaseView:
    """The real :class:`BaseView` from the symbol table, or an id-only stub if model-less."""
    return ctx.resolve(view_id) if ctx.model is not None else stub_view(view_id)
