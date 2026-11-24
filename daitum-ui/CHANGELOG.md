# Changelog

## [4.2.0]

### Added
- `SchedulerView` (`@type: "scheduler"`), the Gantt scheduler: tasks drawn as cards on a
  timeline, grouped into nested levels of lines. Create it with
  `UiBuilder.add_scheduler_view(source_table, display_name=None, hidden=False)`, then
  `add_card_template`, `set_task`, `add_level` and `set_time_axis`. Supporting classes:
  `SchedulerTaskDefinition` (move/resize, change events, per-task backgrounds, default
  background), `SchedulerLevel` (labels, summaries, statistics, collapsing, moving across lines,
  allowed values, add buttons), `SchedulerTimeAxis` with `WorkingTime` and `SchedulerSession`,
  `SchedulerStatistics`, `SchedulerBackground`, `SchedulerTableBackground`,
  `SchedulerResourcePane`, `SchedulerUnscheduledPane` and `SchedulerLayout`, plus the
  `SchedulerScale`, `Weekday`, `SchedulerLineFilter`, `SchedulerPane`, `BackgroundEffect`,
  `StatisticFormat` and `StatisticAggregation` enums.
- Scheduler settings are checked as they are made: `set_*`/`add_*` raise `ValueError` when a
  field is on the wrong table or has the wrong type, a card template is not registered, a change
  event begins its own transaction, and so on. `SchedulerView.validate(ui=None)` adds the rules a
  single call cannot check — that the required pieces are present and that settings made in
  separate calls agree, plus references to context variables, modals, filters and sync groups when
  given the `UiBuilder` — and `UiBuilder.build()` raises `SchedulerValidationError` listing every
  problem.
- `SchedulerResourcePane.set_on_double_click` and `SchedulerUnscheduledPane.set_on_double_click`:
  an optional event fired on double-clicking a pane card, with that resource's or task's row as
  the active row, for example to open a modal that edits it.
- `SchedulerTimeAxis(show_now_line=...)`: draw a vertical line at the current time; off by
  default.
- `SchedulerTimeAxis(period_label=...)`: the toolbar text shown in place of the date range on a
  single-day (TIME) scheduler; `None` keeps "Daily times" and `""` hides it. Only allowed when
  the task times are TIME.
- Scheduler sessions come from a model table, so they can differ by day:
  `SchedulerTimeAxis(sessions=...)` or `SchedulerTimeAxis.set_sessions` with a
  `SchedulerSession`. Each row has a label, a TIME start and end, and optionally a DATE or
  a day of the week; a day uses its dated rows, else its weekday's rows, else the rows with
  neither. There is no fixed list of sessions.
- `SchedulerLevel.set_line_table(table)`: a table with one row per line of the level, joined
  by columns named after the level fields up to and including it (as statistics tables are).
  When set, the summary, summary status and always-show fields are read from it, so they can
  depend on the parent lines, and `showLines` ALL draws every row (a drawn row also draws its
  parent lines). Single-value levels can use summaries, always-show and ALL through a line table.
  `validate` reports a line table whose level columns do not match the levels.
- `SchedulerView.set_resource_pane(..., resource_reference_field=...)`: the pane can list a
  table derived from the resources (for example one carrying per-resource rollups the resource
  table cannot calculate without a cycle) whose OBJECT field points at the resource. One card
  per referenced resource (the first row wins; rows with no reference are not listed);
  `task_resource_field`, `allowed_resources_field` and the allocate edit override reference the
  resource table, and a double-click's active row is the listed table's row.
- `SchedulerView.set_total_row(summary=...)` may insert named values or calculations with
  `${Name}`, so the total summary can show a model rollup.
- `drop_validity` module: `DropOutcomes`, `DropValidity` and `DropValidityOverlay`, the drag
  feedback settings shared by views that support drag and drop.
- `view_layout` module: `ViewLayout`, the base of a view's named layouts.
- `table_toolbar` module: `TableToolbar`, the toolbar shown above a `TableView`, with a search
  bar, filter, column-hiding, density and full-screen controls that can each be turned off, and
  a `default_density` from the `Density` enum (`COMPACT`, `COMFORTABLE`, `SPACIOUS`). Nothing is
  shown unless `show_toolbar` is set. Attach it with `TableView.set_toolbar`.
- `BaseTableView.set_row_actions(row_actions, position=RowActionsPosition.LAST)`: a column on
  each row with the right-click menu's items, shown as one "more" menu button (`MENU`) or as
  separate icon buttons (`BUTTONS`); without it, or with `NONE`, they stay on the right-click menu
  only. `position` puts the column at the start of the row (`FIRST`, after the drag handle and
  row number columns when shown) or at the end (`LAST`); it stays in place when the table scrolls
  sideways.
- `BaseTableView.set_confirm_row_removal(bool)`: ask the user to confirm before a row is removed;
  off by default.
- `ContextMenuEvent.icon` and an `icon` keyword argument on `TableView.add_context_menu_event`
  and `TreeView.add_context_menu_event`: an optional `Icon` shown alongside the command; a
  default icon is used when omitted.
- All of the above round-trip through the UI decoders.

### Changed
- `EditOverride.target_reference_field` may be `None`, meaning the target field is on the
  displayed table itself.

## [4.1.0]

### Added
- `Element.add_property_field_mapping` supports the `"hidden"` property (`DataType.BOOLEAN`) on
  every element, restoring support removed in 4.0.0.
- Chainable cell-geometry setters on elements placed in a form: `set_horizontal_alignment`,
  `set_row_span`, and `set_column_span` on the element returned by `FormView.add_form_element`
  and the per-type `add_*` adders write through to the owning `FormCell`, restoring the pre-4.0
  fluent idiom (e.g. `form.add_text(...).set_horizontal_alignment(...)`). Calling one on an
  element not placed in a form raises; when an element is placed more than once, the last
  placement wins. Serialised output is unchanged.
- `Element.set_size(ElementSize)` — a chainable setter for the existing `size` attribute on
  every element, replacing the removed `FormElement.set_size(FormSize)`. `RangeBar.set_size`
  (validated `SMALL`/`LARGE`) and `ListElement.set_size(height, width)` keep their existing
  signatures.
- `FormView.add_drop_down(..., display_field=)` — sets the dropdown's
  `object_reference_display_field` at construction, for dropdowns whose display label is not
  the referenced table's key column (previously the `Dropdown` constructor raised before
  `set_display_field` could run, forcing manual construction plus `add_form_element`).
- Migration note: the `FormVariant.HEADER` label style removed in 4.0.0 was a bold label — use
  `Text.set_font_weight(FontWeight.BOLD)`.
- Table and tree views auto-detect an `OverridableField` (created by
  `DataTable.add_overridable_field`) in `add_field`: the column is rebound to the override data
  field with a `REFERENCE_WITH_OVERRIDE` default value reference pointing at the calculated
  field, so users see the effective value and can set or reset an override. Tree views apply the
  same wiring to each hierarchy level's child field. Requires `daitum-model>=2.6.0`.
- `ApplicationLinkDestination` and `ApplicationLinkKey` — new `LinkDestination` subtype for
  navigating to another application, with named parameters (`tag` + a model variable or
  literal string), an optional `scenario_id`, and `open_new_tab`.
  `ModelEvent.add_application_navigate_action` adds the corresponding navigate action, and the
  `ApplicationLink` element (plus `FormView.add_application_link`) adds a clickable hyperlink
  to the same destination — mirroring `ModelEditorLinkDestination`'s navigate action and
  `ModelEditorLink` element. `NavigateArgs.destination` is now typed against the new
  `LinkDestination` base rather than the concrete `ModelEditorLinkDestination`; `open_new_tab`
  moved onto that base class (inherited by both subtypes) to match the Java hierarchy.

## [4.0.0]

### Added
- `RangeBar` element (`@type: rangeBar`): a read-only bar from `min` to `max` showing a value
  against error, warning, success and info ranges, as a fill or a marker. Every property is a
  model variable: `RangeBar(value, min_value=None, max_value=None)` plus
  `set_error_ranges`, `set_warning_ranges`, `set_success_ranges`, `set_info_ranges` and
  `set_indicator`. The value, min and max must be `INTEGER`/`DECIMAL`, ranges
  `INTEGER_ARRAY`/`DECIMAL_ARRAY`, and the indicator `STRING`. `set_size` accepts
  `ElementSize.SMALL` or `LARGE` only.
- `FormView.add_range_bar(value, row, column, min_value=None, max_value=None)`.
- `IconCheckbox.set_show_background(show=True)`: draws a background behind the icon
  (`showBackground`, defaults to `false`).
- `Card.shadow`: an optional drop shadow, taking a new `Shadow` enum (`NONE`, `EXTRA_SMALL`, `SMALL`, `MEDIUM`).
  Omitted from the output when unset, leaving the platform default.
- Coordinate fields (`DataType.COORDINATE` / `COORDINATE_ARRAY`) are now filterable, mapping to the
  text filter type.
- First-class input elements in `daitum_ui.elements`, on a new `InputElement` base:
  `TextInput`, `NumberInput`, `Dropdown`, `DateTimePicker`, `ColorPicker`, `IconPicker`. They bind
  to a data source, validate its data type, and wire a bound field's validation rules into
  conditional states — and, being ordinary elements, may be placed in any container.
- `FormView.add_form_element(row, column, element, ...)` — a generic adder that wraps any element
  in a `FormCell`, plus per-type convenience adders (`add_text`, `add_text_input`,
  `add_number_input`, `add_drop_down`, `add_date_time`, `add_check_box`, `add_slider`,
  `add_icon_check_box`, `add_review_rating`, `add_colour_picker_input`, `add_icon_picker`,
  `add_button`, `add_icon`, `add_model_editor_link`, `add_list`).
- `Text` elements can bind a `Field`/`Parameter`/`Calculation` as a read-only data source
  (replacing the former `FormLabel`).
- `Element.add_property_field_mapping` now validates the property against a per-element allowlist
  (`Element.PROPERTY_TYPES`) and checks the bound value's data type, raising a `ValueError` that
  lists the supported properties. It also now returns the element for chaining. A
  `TemplateBindingKey` value skips the type check (resolved later in a list template).
  Fixed-set properties (enums, icon-subset/id and `STRING_ARRAY` fields) are not mappable for now —
  an arbitrary bound value can't be guaranteed valid; see the TODO on `Element.PROPERTY_TYPES`.
- `InputElement.set_list_validation` now takes a `Field`/`Parameter`/`Calculation` and requires it
  to resolve to an **array** of the allowed values (a scalar reference is rejected). `Dropdown` no
  longer reports or accepts list validation, matching the platform.
- **Breaking:** `IconCheckbox` (and `FormView.add_icon_check_box`) now require both `off_icon` and
  `on_icon` — the frontend needs an icon for each state.
- `Dropdown` derives its `object_reference_display_field` from the bound object's referenced-table
  key when not given, and raises if none can be determined (the frontend needs a label per choice).
- A table-bound `FormView` now raises at `build()` if it has no `filter_mode` (nothing selects the
  row). Named-values-only forms are unaffected.
- **Breaking:** icons are now passed as `Icon` enum members, not strings. `IconElement.icon_source`,
  `Button(icon_source=...)`, `IconPicker.set_defaults`, `FormView.add_icon`, and the `Modal`
  button helpers (`add_save_button`/`add_cancel_button`/…) all take `Icon`. Build output is
  unchanged (the enum serialises to the same id string).
- `UiBuilder.build()` now raises if a view references a filter (`show_filter`/`use_filter`) that
  was not registered via `add_filter`, instead of emitting a dangling `showFilter` the platform
  rejects. Pass a filter from `ui.add_filter(name, table)` and reference it by that name.
- `RangeInputType` enum (`DATETIME`, `DATE`) and `GanttView.set_range_input_type(input_type)` —
  choose whether the Gantt range selector's start and end inputs accept a date and time or a
  date only (emitted as `rangeInputType`; defaults to `DATETIME`).
- `ArrayElement` (`@type` `array`) — shows and edits an ARRAY-typed field, named value, or
  context variable's values (editability comes from its element states), laid out per
  `ArrayLayout` (`BADGE`, `LIST`, `COLUMN`). `set_allow_duplicates` and `set_allow_blanks`
  permit repeated and blank (null) values; both default to `False`. `displayFormat`,
  `placeholder`, `allowDuplicates` and `allowBlanks` may be mapped per row via
  `add_property_field_mapping`; `size` may not, so the element is the same size on every row. 
  For an OBJECT_ARRAY, `object_reference_display_field` defaults to the referenced table's key. 
  Added with the `FormView.add_array` adder.
- Add `FIT_WIDTH` for `ElementSize`

### Changed
- **Breaking:** form views serialise `cells` — each a `FormCell` wrapping an element with its grid
  placement (`rowStart`, `columnStart`, `rowSpan`, `columnSpan`, `horizontalAlignment`) — instead
  of `formElements`.
- **Breaking:** `Checkbox`, `Slider`, `IconCheckbox`, and `ReviewRating` now extend `InputElement`
  and serialise the canonical `dataSource` with `onCheck`/`onUncheck`, dropping the legacy
  `*DataSourceId`, `actionType`, and `onClickKey` fields.

### Removed
- **Breaking:** `FormElement` and all `Form*` subclasses, and the `FormSize`, `FormVariant`,
  `FormResize`, and `FormIconSet` enums (use `ElementSize`, `FontWeight`, `TextInputResize`, and
  `IconSet`). `FormView.add_label` is removed — use `add_text`.

## [3.3.1]

### Fixed
- Built UI definitions now emit `schemaVersion: 2`; `schemaVersion: 3` is not yet supported by the
  platform.

## [3.3.0]

### Added
- `Icon` members `EMPTY_FILTER`, `FILLED_FILTER`, `REMOVE_FILTER`, `EMPTY_FILTERS`, and
  `FILLED_FILTERS` (FontAwesome 6).

### Changed
- Built UI definitions now emit `schemaVersion: 3`.

## [3.2.1]

### Added
- `Icon` members `CIRCLE_CHECK`, `TRASH_CAN`, `CIRCLE_MINUS`, `PLUS`, `XMARK`, `GRIP_LINES`, and
  `ROTATE_LEFT` (FontAwesome 6), plus `RESTORE_ORIGINAL`.

### Changed
- `Icon.ADD_ROW`, `REMOVE_ROW`, `MOVE_ROW`, `CHECK`, and `RESET_ICON` now point at their
  FontAwesome 6 equivalents. They are retained as deprecated aliases — prefer `PLUS`, `XMARK`,
  `GRIP_LINES`, `CIRCLE_CHECK`, and `ROTATE_LEFT` respectively.

## [3.2.0]

### Added
- `TableView.add_context_menu_event(name, event)` and
  `TreeView.add_context_menu_event(name, event, levels=None)` — add a named command to a view's
  right-click (context) menu. The command fires its `ModelEvent` with the clicked row as context.
  Only tree views take `levels`, the tree depth(s) — indexed against `table_evaluation_order`,
  `0` being the root — at which the command appears; a single `int` is accepted and coerced to a
  list, and omitting it shows the command at every depth. Levels are validated eagerly against the
  view's `table_evaluation_order` (which must be set first), rejecting negative, duplicate, or
  out-of-range depths. Round-trips through the UI decoders.

### Fixed
- `EditorEvent` (a `ViewField`/`FormElement` on-click/on-change binding) now decodes to a typed
  instance: its `type` becomes an `EditorEventType` member and its nested `event` a real
  `ModelEvent` (with typed, polymorphic actions) rather than a raw `str` and `dict`. The built
  JSON was already correct; only `read_from_file` was affected.

## [3.1.0]

### Added
- `RosterTaskDefinition.add_swap_field(field)` — restored. On drop, the values of the registered
  swap fields are exchanged between the source and target rows. This is the simple drop path, usable
  when the roster is backed by a directly editable table and cards move within a single column; it
  remains supported on the platform. It had been removed in 3.0.0 in favour of `add_drop_write`,
  which is the path for rosters over a derived projection or moves that change a card's column.
  The two paths are mutually exclusive on a single task definition — mixing them raises `ValueError`.
- `RosterTaskDefinition`'s `drop_enabled_field` constructor argument is now optional and moved to
  the end of the parameter list. It is required only for the `add_drop_write` path; swap-based task
  definitions leave it unset. Callers passing all three arguments by keyword are unaffected;
  positional callers that supplied `drop_enabled_field` second must switch to keyword arguments.

## [3.0.0]

### Added
- `ConstantCondition` — a `Condition` with a fixed boolean `value`. Raw booleans passed to a
  condition slot are now coerced to a `ConstantCondition` (via the new `to_condition` helper in
  `data`) rather than being routed through a `TRUE`/`FALSE` context variable.
- `DataMenuItem.set_conditional_hidden(field | parameter | calculation)` and
  `set_permission_hidden(is_base_user)` — hide a custom data-menu entry based on a boolean model
  variable or the user's permission level. The `add_*_entry` methods on `MenuConfiguration` now
  return the created `DataMenuItem` so its visibility can be configured (previously they returned
  `None`), and accept an optional `hidden` boolean.
- `RosterTaskDefinition.add_drop_write` now validates its configuration eagerly, mirroring the
  platform's roster checks: each axis may be written at most once, `identity_field` must be an
  object reference, and (for an edit override) `target_reference_field` must be an object reference
  whose table both contains `target_field_id` and matches the table `identity_field` references.
  Invalid configurations raise `ValueError` at build time instead of failing on upload.
- `FormElement.set_on_change_event(event)` — run a `ModelEvent` when the user changes a form
  element's value instead of the element writing its own bound value; the picked value reaches the
  event as its `editorValue` context entry. Mirrors `ViewField.set_on_change_event` for table views.
  Only `ON_CHANGE` applies to form elements (clicks belong to `FormButton.on_click`). Round-trips
  through the UI decoders.

### Changed
- Element conditional-state methods (`add_conditional_disabled` / `_required` / `_read_only` /
  `_error` / `_warning` / `_success` / `_hidden` / `_info` / `add_conditional_reserve_space`) now
  emit a `constantCondition` for a raw boolean argument instead of a context-variable-backed
  `modelVariableCondition` (via the new `get_boolean_condition` helper). Field / parameter /
  calculation arguments are unchanged.
- `MenuConfiguration`'s `hide_optimisation`, `hide_import`, `hide_bulk_import`, and
  `hide_import_into_sheets` now hold `Condition` objects rather than plain booleans (each serialises
  as a `constantCondition` by default). `set_menu_configuration(...)` keeps its name and still
  accepts plain booleans, so modeller code is unaffected.
- The serialised top-level key changes from `menuConfigurations` to `menuConfiguration`, and the
  backing `UiBuilder` attribute is renamed to match (`menu_configurations` → `menu_configuration`).
  Configuring the menu through `set_menu_configuration(...)` is unaffected.
- `RosterTaskDefinition` now models directional drops instead of symmetric swaps. Its constructor
  takes a new required `drop_enabled_field` (gating which rows may receive a drop), and drops are
  configured via `add_drop_write(axis, identity_field, enabled_field, ...)` — each write records the
  target row/column identity (`RosterAxis.ROW` / `RosterAxis.COLUMN`) and may carry an optional edit
  override redirecting the write to another table. The edit-override parameters
  (`target_reference_field`, `target_field_id`, `map_key_field`) now take `Field` objects rather
  than field-id strings, enabling build-time validation of the override. `RosterTaskDefinition`
  (with its drop writes and edit overrides) now round-trips through `read_from_file`, which it
  previously did not.
- `FormView` and `CardView` now select their row through a generic `filter_mode` (serialised as
  `filterMode`) accepting any `FilterMode`, so a view can be pointed at a row by field value with a
  `MatchFieldFilterMode`, not only by row index/key with a `MatchRowFilterMode`. On `FormView` the
  `add_form_view` / `FormView` / `FormView.set_table` parameter is renamed `match_row` →
  `filter_mode`; on `CardView` the setter is renamed `set_match_row_filter_mode` →
  `set_filter_mode`. The backing attribute `match_row_filter_mode` → `filter_mode` on both (aligning
  with `TableView` / `TreeView`). Round-trips through the UI decoders.
- Requires `daitum-model>=2.1.0`.

### Removed
- `RosterTaskDefinition.add_swap_field` and the `swapFields` output — superseded by
  `add_drop_write` / `dropWrites`.
- **Breaking:** the `match_row_filter_mode` attribute and `matchRowFilterMode` output on `FormView`
  and `CardView` — along with the `match_row` parameter on `add_form_view` / `FormView` /
  `set_table` and the `CardView.set_match_row_filter_mode` method — superseded by `filter_mode` /
  `filterMode` and `CardView.set_filter_mode` (which also carry `MatchRowFilterMode`).

## [2.0.0]

### Added
- UI decoder layer (`_decoders/`) that reconstructs typed `UiBuilder` graphs from
  `build()` output, registered against the shared `daitum_model.decoding` core. UI classes
  set attributes via `set_*`/`add_*`, so they decode through a template mechanism that learns
  each attribute's type from a reference instance.
- `UiBuilder.read_from_file(model_directory, model)` — reconstruct a `UiBuilder` from a
  previously written `ui-definition.json` (the inverse of `write_to_file`).
- `UiBuilder.read_from_dict(definition, model)` — the dict-level equivalent; `read_from_file`
  reads the JSON from disk and delegates to it.
- Baseline capture/revert support: `ModelEvent.add_capture_baseline_action` and
  `add_revert_baseline_action` (a `CAPTURE_BASELINE` / `REVERT_BASELINE` action, with an
  optional tracking-group subset and conditional execution), and
  `ViewField.set_baseline_reset` / `FormElement.set_baseline_reset` for a per-cell baseline
  reset icon (a `BASELINE` `DefaultValueReference`). All round-trip through the UI decoders.
- Custom data-menu support: `MenuConfiguration` with a `data_menu` list and the fluent
  `add_import_sheet_entry` / `add_import_entry` / `add_bulk_import_entry` /
  `add_data_source_entry` / `add_report_entry` / `add_divider_entry` / `add_event_entry`
  methods, plus the `DataMenuItem` / `DataMenuEntryType` entry types (covering import, bulk
  import, import-into-sheet, data source, report, divider, and model-event actions, with an
  optional icon and confirmation prompt).
- `Text.set_wrap` — controls whether text wraps onto multiple lines when it exceeds the
  available width (defaults to `False`).
- `ModelVariableSource` — a `Source` wrapping a `ModelVariable`, so values for set-value
  actions can be read at runtime from a `Field`, `Parameter`, `Calculation`, or
  `ContextVariable`.
- `ModelEvent.add_run_optimisation_action` — adds a `RUN_OPTIMISATION` action that triggers an
  optimisation run, with optional conditional execution via a `ContextVariable`.

### Changed
- Requires `daitum-model>=2.0.0` (was `>=1.0.0`); the decoder layer depends on the
  `daitum_model.decoding` module and shared serialisation core.
- The internal `Buildable` base now derives from the shared core in
  `daitum_model.serialisation` rather than defining its own `snake_to_camel`,
  `json_type_info`, and `Buildable` (no public API or output change).
- `ModelEvent.add_set_table_value_action` and `add_set_named_value_action` now accept any of
  `Value`, `Field`, `Parameter`, `Calculation`, or `ContextVariable` as `value_source` (and
  `add_set_table_value_action` accepts the same model variables as `target_row`). A `Value`
  becomes a `ConstantSource`; a model variable becomes a `ModelVariableSource`.

### Removed
- **Breaking:** `ContextVariableSource` — replaced by `ModelVariableSource`, which covers
  context variables and the other model variable kinds via the wrapped `ModelVariable`.

### Renamed
- **Breaking:** `ModelEvent.add_set_name_value_action` → `add_set_named_value_action`; its
  `name_value_target` parameter → `named_value_target`.

## [1.1.0]

### Added
- `NavigateArgs` — new `EventArgs` subclass for navigating to a link destination.
- `ModelEditorLinkDestination` — link destination targeting the Daitum model editor.
- `ModelEditorLink` element — hyperlink that opens the Daitum model editor.
- `FormLink` form element.
- `ModelEvent.add_model_editor_navigate_action(model_id, scenario_id, open_new_tab, condition)`
  — fluent action that opens the Daitum model editor, optionally pre-selecting a model and
  scenario.
- `RosterTaskDefinition` describing drag and drop configuration for roster cards; attached
  to a column via `RosterColumn.set_task_definition(...)`.

### Changed
- `RosterColumn.add_template_field_mapping` and `add_model_event_mapping`
  now return `self` for fluent chaining.

### Fixed
- `TableView` / `TreeView` `children=None` now means "no field at this level", serialising
  child entries as `{"fieldId": null}` (via a `_NullViewField` placeholder); validation is
  skipped for null children.
- `GanttTaskDefinition` — corrected the `on_click_source_field` datatype check.

## [1.0.1]

### Fixed
- `ChartView` module docstring example now references real attributes
  (``xaxis_label``/``yaxis_label``) and a valid `add_chart_view` /
  `add_data_series` signature, so the example is runnable as written.

### Changed
- Tidied docstrings in `chart_view`, `base_view`, and `named_value_view`:
  ``Optional[X]``/``List[X]`` → ``X | None``/``list[X]`` and Australian
  English (``labelled``, ``organised``, ``colour``).

## [1.0.0]

### Added
- `CellStyle.time_interval`: minute granularity for time/datetime cell pickers
  (defaults to 30 minutes when unset).
- `FormDropdown.set_nullable(...)` and the matching `is_nullable` attribute,
  allowing dropdown form elements to be marked nullable.
- `UiBuilder.write_to_file(model_directory)` emits `ui-definition.json` into
  the given directory, mirroring the model and configuration builders.

### Changed
- `Severity` is now imported from the top-level `daitum_model`
  (`daitum_model.enums` was removed in `daitum-model` 1.0.0).

## [0.1.1]

### Changed
- Update `daitum_model` dependency to v0.1.1.

## [0.1.0]

- Initial release.
