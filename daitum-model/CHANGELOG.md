# Changelog

## [2.3.0]

### Added
- Pivots on derived tables: `DerivedTable.add_pivot(key_field, value_field, aggregation_method)`
  turns the values of a source field into explicit output columns. It returns a `Pivot` builder
  whose chainable `add_column(field_id, key_value)` declares one column per value. A pivot column
  is a keyed aggregated field — it serialises as an `aggregatedFields` entry carrying `keyField`
  and `keyValue`, so plain aggregates and pivot columns share the one block. `add_pivot` is a
  convenience over `add_aggregated_field(..., key_field=, key_value=)`. Each column is synthesised
  as a read-only derived field (so formulas may reference it). `REFERENCE` is rejected.
- Fluent grouping and filtering on derived tables: `DerivedTable.group_by(*fields)` (call with no
  arguments to collapse to a single row) and `DerivedTable.set_filter_field(field)` — consistent
  with the rest of the builder API and with `UnionTable.set_filter_field`.
- Folded tables: `ModelBuilder.add_folded_table(id, source_table)` returns a new `FoldedTable`
  builder that turns a wide table's columns into rows (the "columns to rows" transform). Declare
  output columns with `add_column`, pass-through columns with `carry`, and call `fold(**outputs)`
  once per column group — each output value is either a source field (mapped directly) or a
  literal (folded in as a typed constant). It wraps a `UnionTable`, exposed as `FoldedTable.table`.
  `FoldedTable` is re-exported from the package root.

### Deprecated
- Passing `group_by=` or `filter_field=` to `ModelBuilder.add_derived_table` /
  `DerivedTable(...)`. Use `DerivedTable.group_by(...)` and `DerivedTable.set_filter_field(...)`
  instead. The keyword arguments still work but emit a warning (a `UserWarning`, so it is shown
  by default even when the deprecated call lives in an imported module).

### Fixed
- Bare reference operands (a `Field` / `Calculation` / `Parameter` / `Table` used directly as a
  formula) are now tracked as formula dependencies. They were previously flattened to a string
  constant, so they were invisible to dependency and cycle detection, and to validation. A bare
  reference is now wrapped in an internal `Reference` node that renders identically.
- Validation now enforces that a bare field reference (unqualified `[id]`) resolves in the
  formula's own scope: on a calculated/combo field it must exist on that field's own table (not
  merely on the source/parent table), and a calculation — being table-less — may not reference a
  bare field at all (fields must be read through a table, e.g. `Table[Field]`). These models
  built cleanly before but were rejected by the platform on upload. Cross-table reads via
  `Table[col]` or `obj.field` remain valid.

## [2.2.0]

### Added
- Model-structure validation framework (new `daitum_model.validation` subpackage) that
  detects invalid models at build time instead of on upload to the platform.
  `ModelBuilder.build()` (and therefore `write_to_file()`) now runs the pass and raises
  `ModelValidationError` — listing every problem found, not just the first — while the new
  `ModelBuilder.validate()` returns a `ValidationReport` without raising. `validate_model`,
  `ValidationReport`, `ValidationIssue`, `ModelValidationError`, `CircularDependencyError`,
  `FieldReferenceError`, `MissingSourceFieldError` and `TableReferenceError` are re-exported
  from the package root. This is distinct from the runtime data-quality `Validator`
  hierarchy.
- Rules covering circular table dependencies (never allowed, including via formula
  references between tables), circular calculation dependencies, and circular field
  dependencies within a table (allowed only for a combo-field pair with opposite
  `calculate_in_optimiser` values, which never resolves as a real cycle).
- Rules verifying that field, calculation and table references resolve, that a derived
  table's group-by / filter / sort / aggregated source fields exist on its source table,
  that join-condition match fields exist, that union source tables and field mappings
  resolve, and that object/map reference fields point at a table in the model.
- The framework is a registry of independent rules, so adding a new check is a single new
  rule module.

## [2.1.0]

### Added
- New public `daitum_model.validation_list` module — a model-only helper that aggregates
  every table's validation errors into a single table. `get_validation_list_table(model)`
  scans each table registered with a `ModelBuilder` for fields following the
  `<base_id>__invalid__<severity>` / `<base_id>__message__<severity>` naming convention,
  adds the per-source calculated fields each row needs (group, subgroup, subgroup order,
  source table id, row number, severity, offending value, field id, message), unions the
  sources into a `ValidationList` table filtered to invalid rows, and returns a
  `ValidationListSorted` derived table ordered by subgroup, row, severity rank and field.
  Returns `None` when the model has no validated fields.
- `get_validation_list_table` is idempotent: a second call returns the table built by the
  first. A single model can therefore carry both a model transform's log table (via
  `ModelTransformConfig.add_log_table`) and a validation list view without building the
  table twice.
- A table's validation group comes from `Table.set_validation_group(...)`; a table with a
  validated field and no group raises `ValueError`. It is resolved from the model alone,
  with no reference to any UI.
- The model makes no claim about subgroup order: every subgroup sorts equal
  (`DEFAULT_SUBGROUP_ORDER`), so they fall back to the next sort key and order by name.
  That suits a model transform's log table, which has no navigation to follow.
- `set_subgroup_order(model, subgroup_order)` — impose a subgroup sort order the model
  does not know about, such as the one the navigation bar uses. Only the constant in
  `__Subgroup Order__` changes: the column, the union mappings and the sort keys are
  untouched, so tables derived from the validation list pick the new order up. Table ids
  that contributed no rows are ignored, and omitted tables keep the default. Raises
  `ValueError` if called before `get_validation_list_table`.
- `SOURCE_TABLE_FIELD` (`__Source Table__`) — every validation list row carries the id of
  the table it came from, so presentation layers can derive their own columns (such as
  per-view navigation flags) on the returned table without the builder knowing about views.
- `get_validated_table_ids(model)` — the ids of tables with at least one validated field,
  in registration order, matching the values in `SOURCE_TABLE_FIELD`. A pure query; it
  does not modify the model.
- Module-level id constants shared with anything built on top of the table:
  `VALIDATION_LIST_TABLE`, `VALIDATION_LIST_SORTED_TABLE`, `GROUP_FIELD`,
  `SUBGROUP_FIELD`, `SOURCE_TABLE_FIELD`, `TYPE_FIELD`, `ROW_FIELD`, `VALUE_FIELD`,
  `FIELD_NAME_FIELD`, `MESSAGE_FIELD`, `SUMMARY_MESSAGE_FIELD`, `SEVERITY_RANK_FIELD`,
  `SUBGROUP_ORDER_FIELD` and `FILTER_FIELD`.

### Changed
- A `DataField`'s `nullable` attribute now defaults based on its data type instead of always being
  `False`. Integer, decimal, string and boolean fields default to not nullable; every other type
  (dates/times, array variants, object references and maps) defaults to nullable. Use
  `set_nullable(...)` to override.
- Introduced single-source-of-truth key vocabularies shared between serialisation and decoding, so
  the two can no longer drift: `MODEL_DEFINITION_KEYS` (with its `_ALWAYS_MODEL_KEYS` /
  `_TRACKING_MODEL_KEYS` split) in `model`, from which `ModelBuilder.build` emits and against which
  the model decoder validates; and `FIELD_BUILD_KEYS` in `fields`, consumed by the field and union
  decoders' unmapped-key guards. No public API or serialised-output change. A new
  `test_guard_key_sets` test pins these sets to the actual `build()` output.

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
