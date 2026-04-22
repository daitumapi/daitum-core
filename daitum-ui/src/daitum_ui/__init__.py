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
daitum_ui — UI definition generation for the Daitum platform.

This package provides a comprehensive toolkit for constructing user interfaces
programmatically. It uses a builder pattern centred around :class:`~daitum_ui.ui_builder.UiBuilder`,
which offers factory methods for creating various view types including tables, charts,
forms, Gantt charts, maps, and custom layouts.

Usage::

    from daitum_ui.ui_builder import UiBuilder

    ui = UiBuilder()
"""

from daitum_ui import (
    base_view,
    card_view,
    chart_view,
    charts,
    context_variable,
    data,
    elements,
    filter_component,
    fixed_value_view,
    form_view,
    gantt_view,
    icons,
    layout,
    map_view,
    menu_configurations,
    modal,
    model_event,
    named_value_view,
    navigation_items,
    roster_view,
    styles,
    tabbed_view,
    tabular,
    template_binding_key,
    ui_builder,
)

__all__ = [
    "base_view",
    "card_view",
    "chart_view",
    "charts",
    "context_variable",
    "data",
    "elements",
    "filter_component",
    "fixed_value_view",
    "form_view",
    "gantt_view",
    "icons",
    "layout",
    "map_view",
    "menu_configurations",
    "modal",
    "model_event",
    "named_value_view",
    "navigation_items",
    "roster_view",
    "styles",
    "tabbed_view",
    "tabular",
    "template_binding_key",
    "ui_builder",
]
