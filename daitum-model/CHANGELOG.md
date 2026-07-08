# Changelog

## [2.0.0]

### Added
- Baseline change-tracking framework: `TrackingGroup`, `Baseline`, and `AutoCapture`
  (re-exported from the package root). Declare groups/baselines on `ModelBuilder` via
  `add_tracking_group` and `add_baseline`; tag fields, calculations, and parameters with
  `set_tracking_groups([...])`; tables with a tracked field require `set_id_field(...)`.
  `ModelBuilder.build()` validates the declarations and emits `trackingGroupDefinitions`
  and `baselineDefinitions`.
- New formula functions `BASELINE(baseline, reference[, fallback])` and
  `HASBASELINE(baseline)` for reading a tracked value at a captured baseline. Both
  round-trip through the formula parser and the decoder layer.
- New public `daitum_model.decoding` module — the shared decoder core used to reconstruct
  typed builder objects from `build()` output: `LoadContext`, `decode_into`,
  `register_decoder`, `register_type`, `LoadError`, and supporting helpers. `LoadError` is
  also re-exported from the package root.
- New public `daitum_model.references` module for the model's `!!!`-prefixed reference
  encoding/decoding helpers.
- `ModelBuilder.read_from_file(model_directory)` — reconstruct a live, re-editable
  `ModelBuilder` from the canonical Daitum directory layout (the inverse of `write_to_file`).
- `ModelBuilder.read_from_dict(definition, named_values=None)` — the dict-level inverse of
  `build()`; `read_from_file` reads the JSON from disk and delegates to it.
- `ModelBuilder.load_context` — exposes the populated `LoadContext` (symbol table) after a
  load, for a configuration or UI load to consume.
- Per-model decoders under `_decoders/`, registered automatically on import.
- New `JoinType.CROSS` join condition. A `CROSS` join pairs every row from the
  left table with every row from the right table (the Cartesian product) and
  takes no match fields.

### Changed
- **Breaking:** `JoinCondition`'s constructor parameter order changed to
  `left_table, right_table, join_type, left_field, right_field` (was
  `left_table, left_field, right_table, right_field, join_type`). `left_field` and
  `right_field` are now optional (default `None`), and a `CROSS` condition must omit both
  (supplying either raises `ValueError`) while all other join types still require both.
- Renamed the internal `_buildable` module to the public `daitum_model.serialisation`
  (exposing `Buildable`, `camel_to_snake`, `snake_to_camel`). Import from the new path.

## [1.0.2]

### Changed
- Collapsed multi-line `from ... import (...)` statements onto single lines in
  `derived_table`, `formulas`, and `tables` (no API or behaviour change).

## [1.0.1]

### Changed
- `Table.set_export_as_key_column` now returns ``self`` and has explicit type
  hints, matching the other ``Table.set_*`` methods for fluent chaining.
- Tidied docstrings in `formula`, `tables`, and `validator` (typos and
  ``Optional[X]`` → ``X | None`` in the ``add_calculated_field`` parameter
  descriptions).

## [1.0.0]

### Added
- New formula functions: `LOG`, `SIN`, `COS`, `NORMDIST`, `NORMINV`, `BINOMDIST`,
  `BINOMINV`, `GAMMADIST`, `GAMMAINV`.
- Public `BaseDataType` Protocol in `data_types`; field, formula, parameter, and
  named-value APIs that previously required `DataType` now accept any
  `BaseDataType` (`DataType`, `ObjectDataType`, `MapDataType`).
- Re-export `BaseDataType`, `DerivedTable`, `JoinedTable`, `JoinCondition`, and
  `Severity` from the package root.

### Changed
- `UnionTable.add_field_mapping` now resolves sources by underlying-table
  identity and validates that the named field exists and that source/target
  data types match (raises `ValueError` on mismatch).
- `ModelBuilder.write_to_file(model_directory)` replaces the previous
  three-path signature; it writes `model-definition.json`,
  `scenarios/Initial/named-values.json`, and `model-data/named-values.json`
  into the given directory.

### Removed
- `daitum_model.enums` module. `DataType` and `PRIMITIVE_DATA_TYPES` moved to
  `daitum_model.data_types`; `SortDirection` and `AggregationMethod` to
  `daitum_model.derived_table`; `JoinType` to `daitum_model.joined_table`;
  `Severity`, `BoundType`, and `SEVERITY_RANK` to `daitum_model.validator`.
  All remain importable from the package root.
- `Table.create_derived_table()` — use `ModelBuilder.add_derived_table` instead.

## [0.1.1]

### Changed
- Rename class `_ModelObject` to `Operand` and make public

## [0.1.0]

- Initial release.
