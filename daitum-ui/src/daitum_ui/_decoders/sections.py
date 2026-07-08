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
Template factories and ``@type`` registrations for the non-view UI sections:
context variables, navigation items, modals, filters, and menu configurations.

Each of these stores model/view references as plain id strings (e.g. a nav item keeps a
``view`` id, a filter keeps a ``sourceTable`` id). For a normal load (a model supplied, and
views decoded and registered first) the ``resolve_*`` helpers return the live referenced
object; only a model-less load falls back to an id-only stub.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from daitum_model.decoding import LoadContext, register_decoder, register_type

from daitum_ui._data_menu_item import DataMenuEntryType, DataMenuItem
from daitum_ui._decoders._stubs import resolve_field, resolve_table, resolve_view
from daitum_ui._decoders._template import decode_by_template, register_template
from daitum_ui.context_variable import ContextVariable, CVType
from daitum_ui.data import Condition
from daitum_ui.elements import Button, Element
from daitum_ui.filter_component import (
    DefaultFilter,
    FilterComponent,
    FilterField,
    FilterOperator,
    SearchConfiguration,
    SearchType,
)
from daitum_ui.menu_configuration import MenuConfiguration
from daitum_ui.modal import Modal
from daitum_ui.navigation_items import GroupViewNavItem, NavItem, SingleViewNavItem


def _context_variable_template(data: dict[str, Any], ctx: LoadContext) -> ContextVariable:
    default = data.get("defaultValue")
    if isinstance(default, str) and default.startswith("!!!") and ctx.model is not None:
        from daitum_model.references import Reference

        default = Reference.decode(default, ctx).target
    return ContextVariable(data["id"], CVType(data["type"]), default_value=default)


def _single_nav_template(data: dict[str, Any], ctx: LoadContext) -> SingleViewNavItem:
    return SingleViewNavItem(resolve_view(data["view"], ctx))


def _group_nav_template(data: dict[str, Any], _ctx: LoadContext) -> GroupViewNavItem:
    # The class keeps a process-wide name registry for duplicate detection; clear this name
    # so re-decoding the same definition does not spuriously raise.
    GroupViewNavItem._registry.discard(data["name"])  # noqa: SLF001
    return GroupViewNavItem(data["name"])


def _modal_template(data: dict[str, Any], ctx: LoadContext) -> Modal:
    return Modal(resolve_view(data["viewId"], ctx), height=data["height"], width=data["width"])


def _filter_component_template(data: dict[str, Any], ctx: LoadContext) -> FilterComponent:
    return FilterComponent(data["filterName"], resolve_table(data["sourceTable"], ctx))


def _filter_field_template(data: dict[str, Any], ctx: LoadContext) -> FilterField:
    return FilterField(resolve_field(data["fieldName"], ctx), data.get("displayName"))


def _default_filter_template(data: dict[str, Any], ctx: LoadContext) -> DefaultFilter:
    field = resolve_field(data["fieldName"], ctx)
    return DefaultFilter(field, FilterOperator(data["operator"]))


def _search_configuration_template(data: dict[str, Any], _ctx: LoadContext) -> SearchConfiguration:
    return SearchConfiguration(SearchType(data["searchType"]))


def _menu_template(_data: dict[str, Any], _ctx: LoadContext) -> MenuConfiguration:
    return MenuConfiguration()


def _data_menu_item_template(data: dict[str, Any], _ctx: LoadContext) -> DataMenuItem:
    # ``type`` is required and drives per-type validation. EVENT entries additionally require a
    # ``label`` and a ``model_event`` at construction, so seed placeholders for those; the real
    # attribute values (incl. the decoded ModelEvent) are then restored by ``decode_by_template``
    # over this template.
    from daitum_ui.model_event import ModelEvent

    entry_type = DataMenuEntryType(data["type"])
    if entry_type is DataMenuEntryType.EVENT:
        return DataMenuItem(entry_type, label=data.get("label", ""), model_event=ModelEvent())
    return DataMenuItem(entry_type, key=data.get("key"), label=data.get("label"))


def register() -> None:
    """Register template factories and ``@type`` dispatch for the non-view sections."""
    register_template(ContextVariable, factory=_context_variable_template)
    register_template(SingleViewNavItem, factory=_single_nav_template)
    register_template(
        GroupViewNavItem,
        factory=_group_nav_template,
        elements={"hidden_conditions": Condition},
    )
    register_template(
        Modal,
        factory=_modal_template,
        elements={
            "footer": Element,
            "close_button": Button,
            "save_button": Button,
            "reset_button": Button,
            "delete_button": Button,
        },
    )
    register_template(
        FilterComponent,
        factory=_filter_component_template,
        elements={
            "filter_options": FilterField,
            "default_filters": DefaultFilter,
            "search_configuration": SearchConfiguration,
        },
    )
    register_template(FilterField, factory=_filter_field_template)
    register_template(DefaultFilter, factory=_default_filter_template)
    register_template(SearchConfiguration, factory=_search_configuration_template)
    register_template(
        MenuConfiguration,
        factory=_menu_template,
        elements={"data_menu": DataMenuItem},
    )
    register_template(DataMenuItem, factory=_data_menu_item_template)

    register_type(NavItem, "view", SingleViewNavItem)
    register_type(NavItem, "group", GroupViewNavItem)

    # Make the nav items decodable via decode_into(NavItem, ...) (TYPE_REGISTRY dispatch
    # then DECODER_REGISTRY lookup).
    def _nav_decoder(cls: type) -> Callable[[dict[str, Any], LoadContext], Any]:
        def decode(data: dict[str, Any], ctx: LoadContext) -> Any:
            return decode_by_template(cls, data, ctx)

        return decode

    register_decoder(SingleViewNavItem, _nav_decoder(SingleViewNavItem))
    register_decoder(GroupViewNavItem, _nav_decoder(GroupViewNavItem))
