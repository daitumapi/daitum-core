# Changelog

## [2.0.0]

### Added
- `SteepestDynamicLocalSearch` — new local-search algorithm with separate
  integer and decimal step controls (`integer_step_size`,
  `decimal_step_size`, `_step_change`, `_lowest_step`) plus an
  `allow_neutral_walks` flag. Serialises with algorithmKey
  `daitum-steepest-dynamic-localsearch-single-objective`.
- `StepConfiguration` — new optional fields for schedule subproblems and
  execution control: `included_tags`, `override_parameters`,
  `split_values_key`, `recalculate_ranges`, `disabled_key`, `deferred`.
  Configured via chained `add_included_tag`, `add_override_parameter`,
  `set_split_values_key`, `set_recalculate_ranges`, `set_disabled_key`, and
  `set_deferred` methods. Fields are emitted flat on the step (e.g.
  `includedTags`, `disabledKey`).
- `DecisionVariable.set_tag_source` — identifies the source for reading
  tags on a decision variable, consumed by step-level `includedTags`
  filters. Serialised as `tagSource` (always emitted; `null` when unset).
- `RunExternalModelConfig` — new data source that triggers the model's
  configured external evaluator. Input, parameter, and output mappings
  live on `ExternalModelConfiguration`; the data source is a marker in
  the calculation chain.
- `DataSourceType.RUN_EXTERNAL_MODEL` — new enum value backing
  `RunExternalModelConfig`.
- `ScheduleConfiguration` re-exported from the top-level
  `daitum_configuration` package (was previously only reachable via its
  submodule).
- `ScheduleConfiguration.add_algorithm(key, algorithm)` — fluent adder
  replacing the previous constructor kwarg and `set_algorithm_configurations`
  setter.
- `ScheduleConfiguration.add_global_parameter(key, value)` — fluent adder
  for entries in the schedule's `globalParameters` map.
- `VariableNeighbourhoodSearch` — `population_size` and `selection` fields
  matching `GeneticAlgorithm`'s shape. VNS is now framed as a (μ+λ) EA where
  λ = `population_size`, μ = `population_size / offspring_size`, and
  `selection` picks the μ parents each generation.
- `VariableNeighbourhoodSearch.mutation_rate_tau` (default `0.5`) — the
  log-normal learning rate τ controlling the per-offspring mutation-rate
  step ``childRate = parentRate × exp(τ × N(0, 1))``.

### Changed
- `ScheduleConfiguration.__init__` now takes a single required
  `schedule_root: StepConfiguration` argument. The `algorithm_configurations`
  kwarg has been removed; register algorithms via `add_algorithm` instead.
- `DecisionVariable.set_tag_source` and `set_seed_source` now accept a
  `Parameter | Calculation | Field` (matching `set_min` / `set_max` and the
  dv constructor itself) instead of a raw string. Per-row decision
  variables require a `Field` resolved against `dv_table`; model-level ones
  require a named value. Both serialise as `!!!`-prefixed references in
  the same format as `cellReference`.

### Removed
- `ScheduleConfiguration.set_algorithm_configurations` — replaced by
  `add_algorithm`.
- `ScheduleConfiguration.set_schedule_root` — `schedule_root` is now a
  required constructor argument.
- `VariableNeighbourhoodSearch.mutation_rate_up_scale` and
  `mutation_rate_down_scale` — replaced by the single
  `mutation_rate_tau` field, which parameterises a true log-normal step
  (`× exp(τ × N(0, 1))`) instead of a uniform draw over a scaled range.
- `StepConfiguration.__init__` `steps` parameter — children are appended
  via `add_step` only; the constructor now takes just `step_type` and
  `algorithm_config_key`.

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
