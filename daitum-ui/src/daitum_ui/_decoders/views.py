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

import copy
from typing import Any

from daitum_model.decoding import LoadContext, LoadError, register_type

from daitum_ui._composite_view import CompositeView, ViewConfig
from daitum_ui._data import DataValidationRule, DefaultValueReference, EditOverride, ModelVariable
from daitum_ui._decoders._stubs import resolve_field, resolve_table
from daitum_ui._decoders._template import (
    MapOf,
    decode_by_template,
    register_elements,
    register_template,
)
from daitum_ui._decoders._value import decode_value
from daitum_ui._events import EditorEventType
from daitum_ui.base_view import BaseView
from daitum_ui.card_view import CardView
from daitum_ui.chart_view import ChartView, CombinationChartView
from daitum_ui.charts import ChartSeries, ChartType, CombinationChartComponent
from daitum_ui.data import Condition, FilterMode
from daitum_ui.drop_validity import DropValidity, DropValidityOverlay
from daitum_ui.elements import (
    ArrayElement,
    Button,
    Card,
    Checkbox,
    ColorPicker,
    DateTimePicker,
    Dropdown,
    Element,
    IconCheckbox,
    IconElement,
    IconPicker,
    InputElement,
    NumberInput,
    RangeBar,
    ReviewRating,
    Slider,
    Text,
    TextInput,
)
from daitum_ui.fixed_value_view import Cell, FixedValueView
from daitum_ui.form_view import FormCell, FormView, _FormColumn
from daitum_ui.gantt_view import (
    CategoryGanttTaskDefinition,
    CategoryGanttView,
    TreeGridGanttTaskDefinition,
    TreeGridGanttView,
)
from daitum_ui.icons import Icon
from daitum_ui.layout import FlexView, GridLayout, GridView
from daitum_ui.map_view import MapType, MapView
from daitum_ui.model_event import EditorEvent, ModelEvent
from daitum_ui.named_value_view import NamedValueView
from daitum_ui.roster_view import (
    RosterAxis,
    RosterColumn,
    RosterDropWrite,
    RosterTaskDefinition,
    RosterView,
)
from daitum_ui.scheduler_view import (
    BackgroundEffect,
    SchedulerBackground,
    SchedulerLayout,
    SchedulerLevel,
    SchedulerLineFilter,
    SchedulerPane,
    SchedulerResourcePane,
    SchedulerScale,
    SchedulerSession,
    SchedulerStatistics,
    SchedulerTableBackground,
    SchedulerTaskDefinition,
    SchedulerTimeAxis,
    SchedulerUnscheduledPane,
    SchedulerView,
    StatisticAggregation,
    StatisticFormat,
    Weekday,
    WorkingTime,
)
from daitum_ui.styles import (
    AxisLabelStyle,
    ColumnStyle,
    ConditionalFormattingRule,
    IconConfig,
    Title,
)
from daitum_ui.tabbed_view import TabbedView, TabDefinition
from daitum_ui.table_toolbar import TableToolbar
from daitum_ui.tabular import (
    BaseTableView,
    ContextMenuEvent,
    RowActionsDisplay,
    RowActionsPosition,
    TableView,
    TreeView,
    ViewField,
)

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


# Template factories: resolve required constructor args from the built viewDefinition


def _table_view_template(cls: type):
    def factory(data: dict[str, Any], ctx: LoadContext):
        return cls(resolve_table(data["table"], ctx))

    return factory


def _form_view_template(data: dict[str, Any], ctx: LoadContext) -> FormView:
    table = None if data.get("table") is None else resolve_table(data["table"], ctx)
    return FormView(table=table)


def _input_element_template(cls: type[InputElement]):
    """Template factory for an input element: reconstruct its bound ``dataSource`` as a typed
    ``ModelVariable`` and construct the element with it (remaining attributes are restored by the
    template walk). Input elements take a required ``data_source`` ctor arg that is not a plain
    build key, so the default signature-walk template cannot build them."""

    def factory(data: dict[str, Any], ctx: LoadContext) -> InputElement:
        model_variable = decode_value(data["dataSource"], None, ModelVariable, ctx)
        return cls(model_variable)

    return factory


def _dropdown_template(data: dict[str, Any], ctx: LoadContext) -> Dropdown:
    # A placeholder display field satisfies the constructor's requirement; the walk overwrites it
    # with the built objectReferenceDisplayField.
    model_variable = decode_value(data["dataSource"], None, ModelVariable, ctx)
    return Dropdown(model_variable, object_reference_display_field="")


def _icon_checkbox_template(data: dict[str, Any], ctx: LoadContext) -> IconCheckbox:
    # Placeholder icons satisfy the constructor; the walk overwrites on_icon/off_icon.
    model_variable = decode_value(data["dataSource"], None, ModelVariable, ctx)
    placeholder = IconConfig(source=Icon.CIRCLE)
    return IconCheckbox(model_variable, off_icon=placeholder, on_icon=placeholder)


def _range_bar_template(data: dict[str, Any], ctx: LoadContext) -> RangeBar:
    model_variable = decode_value(data["value"], None, ModelVariable, ctx)
    return RangeBar(model_variable)


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


def _roster_column_template(data: dict[str, Any], ctx: LoadContext) -> RosterColumn:
    # RosterColumn requires a table field reference or a card-template key; the walk fills the
    # rest, so the factory only needs to satisfy that constructor invariant.
    field_ref = data.get("tableFieldReference")
    return RosterColumn(
        table_field_reference=resolve_field(field_ref, ctx) if field_ref is not None else None,
        default_card_template_key=data.get("defaultCardTemplateKey"),
    )


def _roster_task_template(data: dict[str, Any], ctx: LoadContext) -> RosterTaskDefinition:
    # dropEnabledField is present only for the drop-write path; swap-based task definitions
    # omit it. The walk restores swap_fields/drop_writes; the factory just satisfies the ctor.
    drop_enabled = data.get("dropEnabledField")
    return RosterTaskDefinition(
        resolve_field(data["enableDragAndDropField"], ctx),
        data["highlightWholeColumnOnDrag"],
        resolve_field(drop_enabled, ctx) if drop_enabled is not None else None,
    )


def _roster_drop_write_template(data: dict[str, Any], ctx: LoadContext) -> RosterDropWrite:
    return RosterDropWrite(
        RosterAxis(data["axis"]),
        resolve_field(data["identityField"], ctx),
        resolve_field(data["enabledField"], ctx),
    )


def _chart_series_template(data: dict[str, Any], ctx: LoadContext) -> ChartSeries:
    # ChartSeries/gantt task definitions take a live Field but store its id string; build()
    # emits only ids, so the walk restores the id strings — the factory just needs the
    # required Field resolved so the (typechecked) constructor accepts it.
    return ChartSeries(resolve_field(data["sourceField"], ctx))


def _gantt_task_template(cls: type):
    def factory(data: dict[str, Any], ctx: LoadContext):
        return cls(resolve_field(data["idField"], ctx))

    return factory


def _context_menu_event_template(data: dict[str, Any], ctx: LoadContext) -> ContextMenuEvent:
    # The nested ModelEvent has no @type of its own, so decode it against a live ModelEvent
    # template to reconstruct its polymorphic actions; the walk restores name and levels.
    event = decode_value(data["event"], ModelEvent(), None, ctx)
    return ContextMenuEvent(data["name"], event)


def _editor_event_template(data: dict[str, Any], ctx: LoadContext) -> EditorEvent:
    # type is an enum and the nested ModelEvent has no @type; both ctor args need seeding.
    event = decode_value(data["event"], ModelEvent(), None, ctx)
    return EditorEvent(EditorEventType(data["type"]), event)


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


# Scheduler classes validate their constructor arguments against live fields, so their templates
# are bare instances holding typed defaults; the walk then restores every built key. Private
# table references are re-resolved so a decoded scheduler can still be validated.
# ``test_scheduler_templates_match_real_instances`` keeps these attribute sets in step with the
# classes.


def _bare(cls: type, attributes: dict[str, Any]) -> Any:
    instance = cls.__new__(cls)  # type: ignore[call-overload]
    instance.__dict__.update(attributes)
    return instance


def _table_or_none(data: dict[str, Any], ctx: LoadContext) -> Any:
    table_id = data.get("sourceTable")
    return None if table_id is None else resolve_table(table_id, ctx)


def _scheduler_view_template(data: dict[str, Any], ctx: LoadContext) -> SchedulerView:
    return SchedulerView(resolve_table(data["sourceTable"], ctx))


SCHEDULER_TASK_DEFAULTS: dict[str, Any] = {
    "_table_id": None,
    "_time_kind": None,
    "start_field": None,
    "end_field": None,
    "start_edit_override": None,
    "end_edit_override": None,
    "card_template": None,
    "model_event_mappings": {},
    "allow_move": False,
    "allow_resize": False,
    "editable_field": None,
    "on_move": None,
    "on_resize": None,
    "on_double_click_row": None,
    "double_click_time_context_variable": None,
    "backgrounds": [],
    "default_background": None,
}

SCHEDULER_LEVEL_DEFAULTS: dict[str, Any] = {
    "_kind": None,
    "_referenced": None,
    "_task_table_id": None,
    "field": None,
    "edit_override": None,
    "_line_table": None,
    "label_field": None,
    "line_table": None,
    "summary_field": None,
    "summary_status_field": None,
    "null_label": None,
    "show_lines": None,
    "always_show_field": None,
    "statistics": None,
    "collapsible": False,
    "default_collapsed": False,
    "allow_move_across": False,
    "allowed_values_field": None,
    "on_move_across": None,
    "on_add": None,
    "context_variable": None,
}

# The one-element enum lists type the decoded (always emitted) lists as enum members.
SCHEDULER_TIME_AXIS_DEFAULTS: dict[str, Any] = {
    "scales": [SchedulerScale.DAY],
    "default_scale": None,
    "show_navigation": False,
    "show_now_line": False,
    "period_label": None,
    "working_time": None,
    "enforce_working_time": False,
    "sessions": None,
    "must_fit_session": False,
    "sync_group": None,
}

WORKING_TIME_DEFAULTS: dict[str, Any] = {"days": [Weekday.MONDAY], "start": None, "end": None}

SCHEDULER_SESSION_DEFAULTS: dict[str, Any] = {
    "_source_table": None,
    "source_table": None,
    "label_field": None,
    "start_field": None,
    "end_field": None,
    "date_field": None,
    "day_of_week_field": None,
}

SCHEDULER_STATISTICS_DEFAULTS: dict[str, Any] = {
    "_source_table": None,
    "source_table": None,
    "bucket_start_field": None,
    "bucket_end_field": None,
    "value_field": None,
    "baseline_field": None,
    "status_field": None,
    "format": None,
    "aggregation": None,
}

SCHEDULER_BACKGROUND_DEFAULTS: dict[str, Any] = {
    "start_field": None,
    "end_field": None,
    "label_field": None,
    "status_field": None,
    "effect": None,
}

SCHEDULER_TABLE_BACKGROUND_DEFAULTS: dict[str, Any] = {
    "_source_table": None,
    **SCHEDULER_BACKGROUND_DEFAULTS,
    "source_table": None,
}

SCHEDULER_RESOURCE_PANE_DEFAULTS: dict[str, Any] = {
    "_source_table": None,
    "_resource_table_id": None,
    "_task_table_id": None,
    "title": None,
    "source_table": None,
    "resource_reference_field": None,
    "card_template_key": None,
    "use_filter": None,
    "task_resource_field": None,
    "allocate_edit_override": None,
    "allowed_resources_field": None,
    "filter_on_selection": False,
    "drag_label_field": None,
    "on_allocate": None,
    "on_double_click": None,
    "drop_validity": None,
}

SCHEDULER_UNSCHEDULED_PANE_DEFAULTS: dict[str, Any] = {
    "_task_table_id": None,
    "title": None,
    "card_template_key": None,
    "duration_field": None,
    "drag_label_field": None,
    "on_place": None,
    "on_double_click": None,
}

SCHEDULER_TEMPLATE_DEFAULTS: dict[type, dict[str, Any]] = {
    SchedulerTaskDefinition: SCHEDULER_TASK_DEFAULTS,
    SchedulerLevel: SCHEDULER_LEVEL_DEFAULTS,
    SchedulerTimeAxis: SCHEDULER_TIME_AXIS_DEFAULTS,
    WorkingTime: WORKING_TIME_DEFAULTS,
    SchedulerSession: SCHEDULER_SESSION_DEFAULTS,
    SchedulerStatistics: SCHEDULER_STATISTICS_DEFAULTS,
    SchedulerBackground: SCHEDULER_BACKGROUND_DEFAULTS,
    SchedulerTableBackground: SCHEDULER_TABLE_BACKGROUND_DEFAULTS,
    SchedulerResourcePane: SCHEDULER_RESOURCE_PANE_DEFAULTS,
    SchedulerUnscheduledPane: SCHEDULER_UNSCHEDULED_PANE_DEFAULTS,
}


def _bare_template(cls: type, *, resolves_table: bool = False):
    """Factory for a bare scheduler template, deep-copying the class's typed defaults."""

    def factory(data: dict[str, Any], ctx: LoadContext) -> Any:
        attributes = copy.deepcopy(SCHEDULER_TEMPLATE_DEFAULTS[cls])
        if resolves_table:
            attributes["_source_table"] = _table_or_none(data, ctx)
        return _bare(cls, attributes)

    return factory


def _scheduler_level_template(data: dict[str, Any], ctx: LoadContext) -> SchedulerLevel:
    """A bare level whose line table is re-resolved, so a decoded view can still be validated."""
    attributes = copy.deepcopy(SCHEDULER_LEVEL_DEFAULTS)
    line_table = data.get("lineTable")
    if line_table is not None:
        attributes["_line_table"] = resolve_table(line_table, ctx)
    level: SchedulerLevel = _bare(SchedulerLevel, attributes)
    return level


def _scheduler_layout_template(data: dict[str, Any], _ctx: LoadContext) -> SchedulerLayout:
    return SchedulerLayout(data.get("name") or "layout")


def _register_scheduler() -> None:
    register_template(
        SchedulerView,
        factory=_scheduler_view_template,
        elements={
            "card_templates": MapOf(Card),
            "layouts": SchedulerLayout,
            "task": SchedulerTaskDefinition,
            "levels": SchedulerLevel,
            "time_axis": SchedulerTimeAxis,
            "total_statistics": SchedulerStatistics,
            "backgrounds": SchedulerTableBackground,
            "resource_pane": SchedulerResourcePane,
            "unscheduled_pane": SchedulerUnscheduledPane,
            "default_pane": SchedulerPane,
            "drop_validity": DropValidity,
            "drop_validity_overlay": DropValidityOverlay,
        },
    )
    elements: dict[type, dict[str, type | MapOf]] = {
        SchedulerTaskDefinition: {
            "start_edit_override": EditOverride,
            "end_edit_override": EditOverride,
            "model_event_mappings": MapOf(ModelEvent),
            "on_move": ModelEvent,
            "on_resize": ModelEvent,
            "on_double_click_row": ModelEvent,
            "backgrounds": SchedulerBackground,
            "default_background": BackgroundEffect,
        },
        SchedulerLevel: {
            "edit_override": EditOverride,
            "show_lines": SchedulerLineFilter,
            "statistics": SchedulerStatistics,
            "on_move_across": ModelEvent,
            "on_add": ModelEvent,
        },
        SchedulerTimeAxis: {
            "default_scale": SchedulerScale,
            "working_time": WorkingTime,
            "sessions": SchedulerSession,
        },
        WorkingTime: {},
        SchedulerSession: {},
        SchedulerStatistics: {"format": StatisticFormat, "aggregation": StatisticAggregation},
        SchedulerBackground: {"effect": BackgroundEffect},
        SchedulerTableBackground: {"effect": BackgroundEffect},
        SchedulerResourcePane: {
            "allocate_edit_override": EditOverride,
            "on_allocate": ModelEvent,
            "on_double_click": ModelEvent,
            "drop_validity": DropValidity,
        },
        SchedulerUnscheduledPane: {"on_place": ModelEvent, "on_double_click": ModelEvent},
    }
    for cls, cls_elements in elements.items():
        resolves_table = "_source_table" in SCHEDULER_TEMPLATE_DEFAULTS[cls]
        factory = (
            _scheduler_level_template
            if cls is SchedulerLevel
            else _bare_template(cls, resolves_table=resolves_table)
        )
        register_template(cls, factory=factory, elements=cls_elements)
    register_template(SchedulerLayout, factory=_scheduler_layout_template)


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
    "scheduler": SchedulerView,
}


def register() -> None:
    """Register decodable view types: their ``@type`` and template factories."""
    register_template(
        TableView,
        factory=_table_view_template(TableView),
        elements={
            "fields": ViewField,
            "_hidden_conditions": Condition,
            "filter_mode": FilterMode,
            "toolbar": TableToolbar,
        },
    )
    register_template(
        TreeView,
        factory=_table_view_template(TreeView),
        elements={"fields": ViewField, "_hidden_conditions": Condition, "filter_mode": FilterMode},
    )
    register_template(
        FormView,
        factory=_form_view_template,
        elements={
            "cells": FormCell,
            "form_columns": _FormColumn,
            "filter_mode": FilterMode,
        },
    )
    register_elements(FormCell, {"element": Element})
    # Text exposes an optional data_source whose built value is a resolved ModelVariable; without
    # this the decoder would mis-read the ModelVariable dict as a Field (first Buildable in the
    # ctor hint union).
    register_elements(Text, {"data_source": ModelVariable})
    # Icon-valued attributes build to an id string; register the Icon enum so they decode back to
    # Icon members rather than raw strings (the template default is None, so the walk can't infer).
    register_elements(IconElement, {"icon_source": Icon})
    register_elements(Button, {"icon_source": Icon})
    register_elements(IconPicker, {"defaults": Icon})
    for input_cls in (
        TextInput,
        NumberInput,
        DateTimePicker,
        ColorPicker,
        IconPicker,
        Checkbox,
        Slider,
        ReviewRating,
        ArrayElement,
    ):
        register_template(input_cls, factory=_input_element_template(input_cls))
    # Dropdown and IconCheckbox have required ctor args beyond data_source (a derivable display
    # field / two icons) that the generic factory can't supply from a ModelVariable; the template
    # walk overwrites these placeholders from the built data.
    register_template(Dropdown, factory=_dropdown_template)
    register_template(IconCheckbox, factory=_icon_checkbox_template)
    range_bar_variables = (
        "min",
        "max",
        "error_ranges",
        "warning_ranges",
        "success_ranges",
        "info_ranges",
        "indicator",
    )
    register_template(
        RangeBar,
        factory=_range_bar_template,
        elements=dict.fromkeys(range_bar_variables, ModelVariable),
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
    register_template(CardView, factory=_card_view_template, elements={"filter_mode": FilterMode})
    register_template(
        CategoryGanttView,
        factory=_gantt_view_template(CategoryGanttView, CategoryGanttTaskDefinition),
        elements={
            "y_axis_reference_edit_override": EditOverride,
            "y_axis_label": AxisLabelStyle,
        },
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
    register_template(
        RosterColumn,
        factory=_roster_column_template,
        elements={"task_definition": RosterTaskDefinition},
    )
    register_template(
        RosterTaskDefinition,
        factory=_roster_task_template,
        elements={"drop_writes": RosterDropWrite},
    )
    register_template(
        RosterDropWrite,
        factory=_roster_drop_write_template,
        elements={"edit_override": EditOverride},
    )

    _register_scheduler()

    # Nested chart/gantt value types that take a live Field but store only its id string.
    register_template(ChartSeries, factory=_chart_series_template)
    gantt_task_elements: dict[str, type | MapOf] = {
        "start_date_edit_override": EditOverride,
        "end_date_edit_override": EditOverride,
    }
    register_template(
        CategoryGanttTaskDefinition,
        factory=_gantt_task_template(CategoryGanttTaskDefinition),
        elements=gantt_task_elements,
    )
    register_template(
        TreeGridGanttTaskDefinition,
        factory=_gantt_task_template(TreeGridGanttTaskDefinition),
        elements=gantt_task_elements,
    )

    # title is a body-assigned BaseView attribute shared by every concrete view; registering it
    # on the base class makes it apply to all subclasses via the MRO-merged schema.
    register_elements(BaseView, {"title": Title})

    # context_menu_events and the row actions settings are body-assigned attributes shared by
    # TableView and TreeView whose defaults reveal no type; declaring them on BaseTableView applies
    # to both via the MRO-merged schema.
    register_elements(
        BaseTableView,
        {
            "context_menu_events": ContextMenuEvent,
            "row_actions": RowActionsDisplay,
            "row_actions_position": RowActionsPosition,
        },
    )
    register_template(
        ContextMenuEvent, factory=_context_menu_event_template, elements={"icon": Icon}
    )
    register_template(EditorEvent, factory=_editor_event_template)

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
