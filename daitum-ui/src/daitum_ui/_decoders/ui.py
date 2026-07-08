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
Top-level UI decoder: reconstruct a :class:`UiBuilder` from :meth:`UiBuilder.build` output.

Every section is decoded into typed objects — ``views`` into concrete :class:`BaseView`
subclasses, ``variables`` into :class:`ContextVariable`, ``navigation`` into the right nav
item, ``modals`` into :class:`Modal`, ``filters`` into :class:`FilterComponent`,
``menuConfigurations`` into :class:`MenuConfiguration`. Nothing is replayed verbatim. The
builder is created without running ``__init__`` (which would re-seed the default
``TRUE``/``FALSE`` context variables already present in ``variables``).
"""

from __future__ import annotations

from typing import Any

from daitum_model.decoding import LoadContext, LoadError, decode_into

from daitum_ui._decoders._template import decode_by_template
from daitum_ui._decoders.views import decode_view
from daitum_ui.context_variable import ContextVariable
from daitum_ui.filter_component import FilterComponent
from daitum_ui.menu_configuration import MenuConfiguration
from daitum_ui.modal import Modal
from daitum_ui.navigation_items import NavItem
from daitum_ui.ui_builder import UiBuilder

#: The exact top-level keys ``UiBuilder.build`` emits.
_UI_KEYS = {
    "navigation",
    "modals",
    "variables",
    "menuConfigurations",
    "filters",
    "views",
    "optimisationValidationViewId",
}


def decode_ui(data: dict[str, Any], ctx: LoadContext) -> UiBuilder:
    """Reconstruct a :class:`UiBuilder` from a built ``ui-definition`` dict."""
    if not isinstance(data, dict):
        raise LoadError(f"Expected a UI definition dict, got {type(data).__name__}")
    extra = set(data) - _UI_KEYS
    if extra:
        raise LoadError(f"UI definition: unmapped key(s) {sorted(extra)!r}")

    builder = UiBuilder.__new__(UiBuilder)

    # Decode views first and register each by id, so the sections that reference a view
    # (navigation items, modals) resolve to the live decoded view rather than a stub.
    views = [decode_view(view, ctx) for view in data.get("views", [])]
    for view in views:
        ctx.register(view.id, view)
    builder._views = views  # noqa: SLF001
    builder._default_view = None  # noqa: SLF001 - ordering already baked into the view list

    builder.variables = [
        decode_by_template(ContextVariable, v, ctx) for v in data.get("variables", [])
    ]
    builder.navigation = [decode_into(NavItem, n, ctx) for n in data.get("navigation", [])]
    builder.modals = [decode_by_template(Modal, m, ctx) for m in data.get("modals", [])]
    builder.filters = [decode_by_template(FilterComponent, f, ctx) for f in data.get("filters", [])]
    builder.menu_configurations = decode_by_template(
        MenuConfiguration, data.get("menuConfigurations", {}), ctx
    )
    builder.optimisation_validation_view_id = data.get("optimisationValidationViewId")

    return builder
