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
Decoders for the view hierarchy and the :class:`BaseView` envelope.

A built view is a two-layer structure::

    {"id", "displayName", "hidden", "hiddenConditions", "viewDefinition": {"@type", ...}}

The concrete view class is selected by ``viewDefinition.@type``. The view is reconstructed
through the template machinery (:func:`decode_by_template`) so its attributes are genuinely
typed — enums become enum members, ``fields`` become :class:`ViewField` objects, children
become :class:`ViewConfig` objects — and the random ``id`` is preserved from the envelope.

Every concrete :class:`BaseView` subclass has a registered ``@type`` and template factory;
a new view added without one is caught by the coverage gate
(``test_every_view_type_is_decodable``) rather than failing silently at load time.
"""

from __future__ import annotations

from typing import Any

from daitum_model.decoding import LoadContext, LoadError, register_type

from daitum_ui._composite_view import CompositeView, ViewConfig
from daitum_ui._data import DataValidationRule, DefaultValueReference, EditOverride
from daitum_ui._decoders._stubs import resolve_field, resolve_table
from daitum_ui._decoders._template import (
    MapOf,
    decode_by_template,
    register_elements,
    register_template,
)
from daitum_ui._decoders._value import decode_value
from daitum_ui.base_view import BaseView
from daitum_ui.card_view import CardView
from daitum_ui.chart_view import ChartView, CombinationChartView
from daitum_ui.charts import ChartSeries, ChartType, CombinationChartComponent
from daitum_ui.data import Condition, FilterMode
from daitum_ui.elements import Card
from daitum_ui.fixed_value_view import Cell, FixedValueView
from daitum_ui.form_view import FormElement, FormView, _FormColumn
from daitum_ui.gantt_view import (
    CategoryGanttTaskDefinition,
    CategoryGanttView,
    TreeGridGanttTaskDefinition,
    TreeGridGanttView,
)
from daitum_ui.layout import FlexView, GridLayout, GridView
from daitum_ui.map_view import MapType, MapView
from daitum_ui.model_event import EditorEvent
from daitum_ui.named_value_view import NamedValueView
from daitum_ui.roster_view import RosterColumn, RosterView
from daitum_ui.styles import ColumnStyle, ConditionalFormattingRule, Title
from daitum_ui.tabbed_view import TabbedView, TabDefinition
from daitum_ui.tabular import TableView, TreeView, ViewField

_ENVELOPE_KEYS = frozenset({"id", "displayName", "hidden", "hiddenConditions"})
_VIEW_DEF_SKIP = frozenset({"@type"})


def decode_view(data: dict[str, Any], ctx: LoadContext) -> BaseView:
    """Decode a built view envelope into a typed concrete :class:`BaseView` instance."""
    if not isinstance(data, dict):
        raise LoadError(f"Expected a view envelope dict, got {type(data).__name__}")
    for key in ("id", "viewDefinition"):
        if key not in data:
            raise LoadError(f"View envelope missing required key {key!r}")

    view_definition = data["viewDefinition"]
    cls = _resolve_view_class(view_definition)

    view: BaseView = decode_by_template(cls, view_definition, ctx, skip_keys=_VIEW_DEF_SKIP)
    _apply_envelope(view, data, ctx)
    return view


def _resolve_view_class(view_definition: dict[str, Any]) -> type[BaseView]:
    discriminator = view_definition.get("@type")
    if discriminator is None:
        raise LoadError("View definition has no '@type' discriminator")
    if discriminator == "composite":
        # GridView/FlexView/CompositeView share the discriminator; the CSS ``display``
        # value distinguishes the concrete subclass.
        display = view_definition.get("parentStyles", {}).get("display")
        composite: dict[str, type[BaseView]] = {"grid": GridView, "flex": FlexView}
        return composite.get(display, CompositeView)
    cls = _VIEW_TYPES.get(discriminator)
    if cls is None:
        raise LoadError(f"Unsupported view '@type': {discriminator!r}")
    return cls


def _apply_envelope(view: BaseView, data: dict[str, Any], ctx: LoadContext) -> None:
    """Restore the envelope's id/displayName/hidden/hiddenConditions onto ``view``."""
    view._id = data["id"]  # noqa: SLF001 - decoder restores private envelope state
    view._display_name = data.get("displayName", "")  # noqa: SLF001
    view._hidden = data.get("hidden", False)  # noqa: SLF001
    conditions = data.get("hiddenConditions")
    view._hidden_conditions = (  # noqa: SLF001
        None if conditions is None else [decode_value(c, None, Condition, ctx) for c in conditions]
    )


# --- Template factories: resolve required constructor args from the built viewDefinition ---


def _table_view_template(cls: type):
    def factory(data: dict[str, Any], ctx: LoadContext):
        return cls(resolve_table(data["table"], ctx))

    return factory


def _form_view_template(data: dict[str, Any], ctx: LoadContext) -> FormView:
    table = None if data.get("table") is None else resolve_table(data["table"], ctx)
    return FormView(table=table)


def _composite_view_template(_data: dict[str, Any], _ctx: LoadContext) -> CompositeView:
    return CompositeView()


def _flex_view_template(_data: dict[str, Any], _ctx: LoadContext) -> FlexView:
    return FlexView()


def _grid_view_template(_data: dict[str, Any], _ctx: LoadContext) -> GridView:
    # The placeholder layout's emitted styles are overwritten by the decoded parentStyles.
    return GridView(GridLayout(columns=["1fr"], rows=["1fr"], areas=[["a"]]))


def _view_config_template(data: dict[str, Any], _ctx: LoadContext) -> ViewConfig:
    return ViewConfig(element_styles=dict(data["elementStyles"]), view_id=data["viewId"])


def _no_arg_template(cls: type):
    def factory(_data: dict[str, Any], _ctx: LoadContext):
        return cls()

    return factory


def _chart_view_template(cls: type):
    """Template for chart views: resolve series/type/table; the walk restores the real state."""

    def factory(data: dict[str, Any], ctx: LoadContext):
        series = decode_value(data["primarySeries"], ChartSeries(_seed_field(data, ctx)), None, ctx)
        return cls(series, ChartType(data["type"]), resolve_table(data["table"], ctx))

    return factory


def _gantt_view_template(cls: type, task_cls: type):
    """Template for gantt views: resolve table and a task definition from the built data."""

    def factory(data: dict[str, Any], ctx: LoadContext):
        task = decode_value(
            data["ganttTaskDefinition"], task_cls(_seed_field(data, ctx)), None, ctx
        )
        return cls(resolve_table(data["table"], ctx), task)

    return factory


def _card_view_template(data: dict[str, Any], ctx: LoadContext) -> CardView:
    # The source table is restored from sourceTable by the walk; the ctor only needs the card.
    card = decode_value(data["cardTemplate"], Card(), None, ctx)
    return CardView(card)


def _map_view_template(data: dict[str, Any], ctx: LoadContext) -> MapView:
    config = data["mapConfig"]
    latitude = resolve_field(config["latitudeColumn"], ctx)
    longitude = resolve_field(config["longitudeColumn"], ctx)
    return MapView(
        resolve_table(data["sourceTable"], ctx), MapType(data["mapType"]), latitude, longitude
    )


def _roster_view_template(data: dict[str, Any], ctx: LoadContext) -> RosterView:
    return RosterView(resolve_table(data["sourceTable"], ctx))


def _chart_series_template(data: dict[str, Any], ctx: LoadContext) -> ChartSeries:
    # ChartSeries/gantt task definitions take a live Field but store its id string; build()
    # emits only ids, so the walk restores the id strings — the factory just needs the
    # required Field resolved so the (typechecked) constructor accepts it.
    return ChartSeries(resolve_field(data["sourceField"], ctx))


def _gantt_task_template(cls: type):
    def factory(data: dict[str, Any], ctx: LoadContext):
        return cls(resolve_field(data["idField"], ctx))

    return factory


def _seed_field(data: dict[str, Any], ctx: LoadContext):
    """Resolve any field of a chart/gantt view's table to seed a placeholder template arg.

    The genuine series/task definition is decoded over this placeholder by the template walk;
    the seed only needs to be a real :class:`Field` so the placeholder constructs.
    """
    table = resolve_table(data["table"], ctx)
    fields = table.get_fields()
    if not fields:
        raise LoadError(f"Cannot seed a chart/gantt template: table {table.id!r} has no fields")
    return fields[0]


#: Concrete view classes keyed by their ``viewDefinition.@type`` discriminator.
_VIEW_TYPES: dict[str, type[BaseView]] = {
    "standard": TableView,
    "tree": TreeView,
    "form": FormView,
    "fixed layout": FixedValueView,
    "named values": NamedValueView,
    "tabbed": TabbedView,
    "composite": CompositeView,
    "chart": ChartView,
    "combination chart": CombinationChartView,
    "card": CardView,
    "category gantt": CategoryGanttView,
    "tree grid gantt": TreeGridGanttView,
    "map": MapView,
    "roster": RosterView,
}


def register() -> None:
    """Register decodable view types: their ``@type`` and template factories."""
    register_template(
        TableView,
        factory=_table_view_template(TableView),
        elements={"fields": ViewField, "_hidden_conditions": Condition, "filter_mode": FilterMode},
    )
    register_template(
        TreeView,
        factory=_table_view_template(TreeView),
        elements={"fields": ViewField, "_hidden_conditions": Condition, "filter_mode": FilterMode},
    )
    register_template(
        FormView,
        factory=_form_view_template,
        elements={"form_elements": FormElement, "form_columns": _FormColumn},
    )
    register_template(
        FixedValueView,
        factory=_no_arg_template(FixedValueView),
        elements={"columns": Cell, "cells": MapOf(Cell, depth=2)},
    )
    register_template(
        NamedValueView, factory=_no_arg_template(NamedValueView), elements={"values": ViewField}
    )
    register_template(
        TabbedView, factory=_no_arg_template(TabbedView), elements={"tabs": TabDefinition}
    )
    register_template(
        CompositeView, factory=_composite_view_template, elements={"children": ViewConfig}
    )
    register_template(FlexView, factory=_flex_view_template, elements={"children": ViewConfig})
    register_template(GridView, factory=_grid_view_template, elements={"children": ViewConfig})
    register_template(
        ViewConfig, factory=_view_config_template, elements={"_hidden_conditions": Condition}
    )
    register_template(
        ChartView,
        factory=_chart_view_template(ChartView),
        elements={"secondary_series": ChartSeries, "data_series": ChartSeries},
    )
    register_template(
        CombinationChartView,
        factory=_chart_view_template(CombinationChartView),
        elements={"chart_components": CombinationChartComponent},
    )
    register_template(
        CardView, factory=_card_view_template, elements={"match_row_filter_mode": FilterMode}
    )
    register_template(
        CategoryGanttView,
        factory=_gantt_view_template(CategoryGanttView, CategoryGanttTaskDefinition),
    )
    register_template(
        TreeGridGanttView,
        factory=_gantt_view_template(TreeGridGanttView, TreeGridGanttTaskDefinition),
    )
    register_template(MapView, factory=_map_view_template)
    register_template(
        RosterView,
        factory=_roster_view_template,
        elements={
            "card_templates": MapOf(Card),
            "resource_column": RosterColumn,
            "shift_columns": RosterColumn,
            "summary_column": RosterColumn,
        },
    )

    # Nested chart/gantt value types that take a live Field but store only its id string.
    register_template(ChartSeries, factory=_chart_series_template)
    register_template(
        CategoryGanttTaskDefinition, factory=_gantt_task_template(CategoryGanttTaskDefinition)
    )
    register_template(
        TreeGridGanttTaskDefinition, factory=_gantt_task_template(TreeGridGanttTaskDefinition)
    )

    # title is a body-assigned BaseView attribute shared by every concrete view; registering it
    # on the base class makes it apply to all subclasses via the MRO-merged schema.
    register_elements(BaseView, {"title": Title})

    # ViewField is decoded as a leaf, but its nested optional Buildables are body-assigned, so
    # their types are declared here rather than auto-derived from the (field_id, readonly) ctor.
    register_elements(
        ViewField,
        {
            "editor_event": EditorEvent,
            "edit_override": EditOverride,
            "default_value_reference": DefaultValueReference,
            "data_validation_rule": DataValidationRule,
            "conditional_formatting_rules": ConditionalFormattingRule,
            "column_style": ColumnStyle,
        },
    )

    for discriminator, cls in _VIEW_TYPES.items():
        register_type(BaseView, discriminator, cls)
