# Changelog

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
