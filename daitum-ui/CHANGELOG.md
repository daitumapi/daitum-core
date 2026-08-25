# Changelog

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
