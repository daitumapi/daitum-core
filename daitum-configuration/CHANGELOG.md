# Changelog

## [1.0.1]

### Fixed
- `NumericExpression.__init__` — replaced an accidentally short-circuited
  ``value in {NUM_VARIABLES or value == "NUM_VARIABLES"}`` check with a
  direct equality test against ``NUM_VARIABLES``.
- `Mutation.mutation` and `Selection.selection` parameter annotations no
  longer contain a duplicate ``| None`` (``float | None | NumericExpression
  | None`` → ``float | NumericExpression | None``; same for ``int``).

### Changed
- `numeric_expression` migrated from ``typing.Union[...]`` to PEP 604
  ``X | Y`` syntax, matching the rest of the package.
- `ConfigurationBuilder.model_topic_mapping` and `tooltips` typed as
  ``list[Any]`` instead of bare ``list``.

## [1.0.0]

### Added
- `Buildable` base class (`@json_type_info` decorator, snake-to-camel key
  conversion) underlying every public class's `build()` serialisation.
- `ConfigurationBuilder.write_to_file(model_directory)` emits
  `model-configuration.json` into the given directory.
- New chainable setters on `ConfigurationBuilder`: `set_solution_view_allowed`,
  `set_solution_view_enabled`, `set_model_topic_mapping`, `set_tooltips`.
- `ModelTransformConfig.add_direct_upload_input(tables)` plus public input
  classes `ModelTransformInput`, `DynamicValuesInput`, `DataStoreInput`,
  `DataStoreInterfaceInput`, `DirectUploadInput`.
- `DataInputSourceType.DYNAMIC_VALUES` enum value.

### Changed
- Renamed `Configuration` → `ConfigurationBuilder`.
- All public objects now serialise via `build()` instead of `to_dict()`;
  data-filter `@type` discriminators are emitted via `@json_type_info`.
- `ConfigurationBuilder.set_schedule_configuration` now takes a prebuilt
  `ScheduleConfiguration` instead of `(algorithm_configurations, schedule_root)`.
- `ConfigurationBuilder.set_model_property` defaults `calculate_on_load` to
  `True` (was `False`).
- Setter and `add_*` methods are now fluent across the package
  (`ConfigurationBuilder`, `ModelConfiguration`, `ScheduleConfiguration`,
  `BatchedDataSourceConfig`, `ModelTransform`, `ModelTransformConfig`,
  `StepConfiguration`, `StochasticConfiguration`, `ExternalModelConfiguration`,
  `InputDataMapping`, etc.).
- `ModelConfiguration.add_objective` and `add_scenario_output` now return the
  created object (was `None`).
- `Constraint.build()` only emits numeric `lowerBound`/`upperBound` when the
  bound is a `float`; non-numeric bounds are emitted as `null` (with the
  reference fields carrying the resolved expression).
- `ReportProperty.export_interface_key` is now optional;
  `ReportProperty.report_name()` may return `None`.
- `SetDataFilter.values` is stored as a list (was a `set`) so it serialises
  cleanly to JSON.
- Underscore-prefixed attributes across the data-source, model-configuration,
  and property classes are now public.

### Removed
- `ModelProperty.import_options()`, `overlay_config()`,
  `has_defined_import_options()`, and `has_defined_overlay_config()` accessor
  helpers; access the public attributes directly.
- `to_dict()` on every public class (replaced by `build()`).

### Fixed
- `EqualityDataFilter`, `RegexDataFilter`, `WildcardDataFilter`, and
  `InequalityDataFilter` now serialise their source/lower/upper keys via
  `to_string()` rather than the implicit object representation.
- `InequalityDataFilter` and `SetDataFilter` no longer pull `Parameter` from
  the `inspect` stdlib module by mistake.

## [0.1.1]

- Fix serialization of EqualityDataFilter.sourceKey
- Allow ReportProperty.export_interface_key to be optional

## [0.1.0]

- Initial release.
