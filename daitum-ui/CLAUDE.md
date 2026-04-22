# CLAUDE.md — daitum-ui

This package lives inside the `daitum-core` monorepo. The root `CLAUDE.md` at `../CLAUDE.md`
contains global conventions (Australian English, linting workflow, virtual environment, etc.) that
apply here too. Read it first.


## Package Purpose

`daitum-ui` is a fluent builder library for constructing UI definitions for the Daitum platform.
A UI definition describes views (tables, forms, charts, maps, etc.), navigation, modals, filters,
and context variables. The final output is produced via `UiBuilder.build()` → JSON.

The package depends on `daitum-model` because views bind directly to tables, fields, and named
values defined there.


## Package Structure

```
daitum-ui/
├── src/daitum_ui/
│   ├── __init__.py              # Public API — all user-facing symbols re-exported here
│   ├── ui_builder.py            # UiBuilder — main entry point
│   │
│   ├── base_view.py             # BaseView (abstract), ActionBar
│   ├── tabular.py               # TableView, TreeView, ViewField, DisplayState
│   ├── form_view.py             # FormView and FormElement subclasses
│   ├── chart_view.py            # ChartView, CombinationChartView
│   ├── card_view.py             # CardView
│   ├── named_value_view.py      # NamedValueView
│   ├── fixed_value_view.py      # FixedValueView
│   ├── gantt_view.py            # CategoryGanttView, TreeGridGanttView
│   ├── map_view.py              # MapView (locations + routes)
│   ├── roster_view.py           # RosterView (staff rosters)
│   ├── tabbed_view.py           # TabbedView
│   ├── layout.py                # FlexView, GridView, layout enums
│   │
│   ├── navigation_items.py      # SingleViewNavItem, GroupViewNavItem
│   ├── modal.py                 # Modal (overlay dialogs)
│   ├── filter_component.py      # FilterComponent, FilterField, default filters
│   ├── elements.py              # Button, Text, Card, Container, Slider, etc.
│   ├── charts.py                # ChartSeries, ChartType enums
│   ├── data.py                  # Value types, Condition, validation enums
│   ├── context_variable.py      # ContextVariable, CVType enum
│   ├── template_binding_key.py  # TemplateBindingKey (dynamic binding)
│   ├── model_event.py           # ModelEvent, EditorEvent
│   ├── styles.py                # Title, BaseStyle, ColumnStyle, ConditionalFormatting
│   ├── icons.py                 # Icon enum
│   ├── menu_configurations.py   # MenuConfigurations
│   │
│   ├── _buildable.py            # Internal: Buildable base class, snake_to_camel
│   ├── _composite_view.py       # Internal: CompositeView, ViewConfig
│   ├── _colours.py              # Internal: colour constants
│   ├── _data.py                 # Internal: ModelVariable, EditOverride, DataValidationRule
│   ├── _events.py               # Internal: ValueType, ActionType, RowSelectionMode enums
│   └── _validation.py           # Internal: validation formatting helpers
└── tests/
    └── test_ui_builder.py
```


## Key Abstractions

### UiBuilder
The single entry point. Its factory methods create and register views automatically.

```python
builder = UiBuilder()

table_view = builder.add_table_view(table=jobs, display_name="Jobs")
nav_group  = builder.add_navigation_group("Data")
nav_group.views.append(table_view)

ui_def = builder.build()   # → dict, serialise to JSON
```

**Factory methods:** `add_table_view`, `add_tree_view`, `add_form_view`, `add_chart_view`,
`add_combination_chart_view`, `add_card_view`, `add_named_value_view`, `add_fixed_value_view`,
`add_gantt_view`, `add_location_view`, `add_route_view`, `add_grid_view`, `add_flex_view`,
`add_tabbed_view`, `add_roster_view`, `add_modal`, `add_context_variable`,
`add_navigation_item`, `add_navigation_group`.

### View Hierarchy
All concrete views inherit from `BaseView` (abstract). `BaseView` provides: `id`,
`display_name`, `hidden`, `title`, `action_bar_definition`, and `show_filter`.

| View | Purpose |
|---|---|
| `TableView` | Tabular data; supports sorting and editing |
| `TreeView` | Hierarchical tabular data |
| `FormView` | Grid-based data-entry form |
| `ChartView` | Bar, line, pie, scatter charts |
| `CombinationChartView` | Multi-series / mixed-type charts |
| `CardView` | Card-layout presentation |
| `NamedValueView` | Displays calculations and parameters |
| `FixedValueView` | Static fixed-value display |
| `CategoryGanttView` | Gantt chart with category rows |
| `TreeGridGanttView` | Gantt with hierarchical task rows |
| `MapView` | Geographic locations or routes |
| `RosterView` | Staff rostering / scheduling grid |
| `TabbedView` | Tab container for other views |
| `GridView` / `FlexView` | CSS Grid / Flexbox layout containers |

### Elements
Fine-grained interactive and display components that compose into views. All inherit from
`BaseElement` and support `.set_hidden()`, `.set_disabled()`, `.set_read_only()`, and state
methods (`.set_error()`, `.set_warning()`, etc.).

Key elements: `Button`, `Text`, `Card`, `Container`, `Badge`, `Checkbox`, `IconCheckbox`,
`Slider`, `ReviewRating`, `IconElement`, `ListElement`.

### Navigation
```
UiBuilder.navigation
├── SingleViewNavItem  — links to one view
└── GroupViewNavItem   — collapsible group; holds a list of views
```

Both support colour customisation and conditional visibility.

### FilterComponent
Reusable filter registered on `UiBuilder` and attached to views via `set_show_filter(name)`.
A filter has a source table, a list of `FilterField` options, and optional `DefaultFilter` rules.

### ContextVariable
Typed runtime state (`CVType.INTEGER`, `DECIMAL`, `STRING`, `BOOLEAN`) used for dynamic data
flow between views, elements, and modals. Create via `builder.add_context_variable()`.

### Modal
An overlay dialog (`edit_dialog=True` for transactional editing with SAVE / CANCEL / RESET /
DELETE buttons). A modal wraps another view as its content.

### Serialisation — Buildable Framework
Every class inherits from `Buildable` (in `_buildable.py`). `.build()` recursively converts the
object graph to a dict, applying `snake_case` → `camelCase` key transformation. The
`@json_type_info("type_name")` decorator injects a `@type` discriminator field into the output.
Do **not** bypass this mechanism — always override `.build()` rather than calling `.to_dict()`.


## Import Conventions

```python
from daitum_ui import UiBuilder
from daitum_ui import tabular, form_view, chart_view   # module access
from daitum_ui.tabular import TableView, ViewField
from daitum_ui.elements import Button, Text
from daitum_ui.context_variable import ContextVariable, CVType
```

All public symbols are re-exported from `daitum_ui.__init__`. Avoid importing from `_`-prefixed
modules.


## Adding New View Types

1. Create a new module in `src/daitum_ui/` (no `_` prefix if public).
2. Inherit from `BaseView`; decorate the class with `@json_type_info("your_type")`.
3. Override `.build()` to serialise view-specific attributes.
4. Re-export from `__init__.py` and add a factory method to `UiBuilder`.
