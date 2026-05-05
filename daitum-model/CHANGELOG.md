# Changelog

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
