# CLAUDE.md — daitum-configuration

This package lives inside the `daitum-core` monorepo. The root `CLAUDE.md` at `../CLAUDE.md`
contains global conventions (Australian English, linting workflow, virtual environment, etc.) that
apply here too. Read it first.


## Package Purpose

`daitum-configuration` is a builder library for constructing optimisation model configuration for
the Daitum platform. A configuration specifies the algorithm, decision variables, objectives,
constraints, data sources, and schedule. The final output is produced via
`Configuration.write_to_file()` → JSON.

The package depends on `daitum-model` because decision variables, objectives, and constraints
reference model objects (`Parameter`, `Calculation`, `DataField`, `Table`).


## Package Structure

```
daitum-configuration/
├── src/daitum_configuration/
│   ├── __init__.py                         # Public API
│   ├── configuration.py                    # Configuration — main entry point
│   │
│   ├── algorithm_configuration/
│   │   ├── algorithm.py                    # Abstract Algorithm base
│   │   ├── genetic_algorithm.py            # GeneticAlgorithm + operator enums/classes
│   │   ├── cmaes_algorithm.py              # CMAESAlgorithm
│   │   ├── vns_algorithm.py                # VariableNeighbourhoodSearch
│   │   └── numeric_expression.py           # NumericExpression (NUM_VARIABLES support)
│   │
│   ├── model_configuration/
│   │   ├── model_configuration.py          # ModelConfiguration
│   │   ├── decision_variable.py            # DecisionVariable, DVType enum
│   │   ├── objective.py                    # Objective
│   │   ├── constraint.py                   # Constraint, ConstraintType enum
│   │   ├── priority.py                     # Priority enum (LOW/MEDIUM/HIGH)
│   │   ├── stochastic_configuration.py     # StochasticConfiguration
│   │   ├── external_configuration.py       # ExternalModelConfiguration + mappings
│   │   └── scenario_output.py              # ScenarioOutput
│   │
│   ├── data_source/
│   │   ├── data_source.py                  # DataSource wrapper (metadata + config)
│   │   ├── data_source_config.py           # Abstract DataSourceConfig
│   │   ├── data_source_type.py             # DataSourceType enum
│   │   ├── batched_data_source/            # BatchedDataSourceConfig, BatchDataSourceType
│   │   ├── data_store/                     # DataStoreConfig + filter implementations
│   │   ├── excel_transform/                # ExcelTransformConfig
│   │   ├── model_transform/                # ModelTransformConfig
│   │   ├── distance_matrix/                # DistanceMatrixConfig, OutputMatrix
│   │   ├── run_report/                     # RunReportConfig
│   │   ├── geo_location_config.py          # GeoLocationConfig
│   │   └── set_features_config.py          # SetFeaturesConfig
│   │
│   ├── model_property/
│   │   ├── model_property.py               # ModelProperty
│   │   ├── model_import_options.py         # ModelImportOptions
│   │   └── overlay_config.py               # OverlayConfig
│   │
│   ├── report_property/
│   │   ├── report_property.py              # ReportProperty
│   │   ├── report_export_format.py         # ReportExportFormat enum
│   │   └── report_data.py                  # ReportData
│   │
│   └── schedule_configuration/
│       ├── schedule_configuration.py       # ScheduleConfiguration
│       ├── step_configuration.py           # StepConfiguration
│       └── step_type.py                    # StepType enum (SINGLE/PARALLEL/SEQUENCE)
└── tests/
    └── test_configuration.py
```


## Key Abstractions

### Configuration
The single top-level entry point. Use setter and `add_*` methods to compose a complete
configuration, then call `write_to_file()`.

```python
config = Configuration()
config.set_algorithm(GeneticAlgorithm(population_size=100))
config.set_model_configuration(model_cfg)
config.add_excel_transform("Inputs", ExcelTransformConfig(...))
config.write_to_file("configuration.json")
```

**Setter methods:** `set_algorithm`, `set_model_configuration`, `set_schedule_configuration`,
`set_model_property`.

**Data source add methods:** `add_excel_transform`, `add_model_transform`, `add_data_store`,
`add_batched_data_source`, `add_distance_matrix`, `add_geo_location`, `add_set_features`,
`add_report_data_source`.

**Report:** `add_report_property`.

### Algorithm Hierarchy
All algorithms inherit from the abstract `Algorithm` base dataclass. Common parameters are
defined there (evaluation budget, time limits, stopping criteria, restart count, PRNG seed).

| Class | Purpose |
|---|---|
| `GeneticAlgorithm` | Population-based evolutionary algorithm |
| `CMAESAlgorithm` | Covariance Matrix Adaptation Evolution Strategy |
| `VariableNeighbourhoodSearch` | Metaheuristic using adaptive neighbourhood changes |

All numeric parameters accept either a plain `int`/`float` or a `NumericExpression`.

### NumericExpression
Symbolic math for algorithm parameters that should scale with problem dimension. The special
variable `NUM_VARIABLES` is replaced at runtime with the number of decision variables.

```python
from daitum_configuration import NumericExpression

# Scales evaluations with problem size
evaluations = 100_000 * NumericExpression("NUM_VARIABLES")
mutation_rate = 1 / NumericExpression("NUM_VARIABLES")
```

Supports `+`, `-`, `*`, `/` operators (all return a new `NumericExpression`).

### ModelConfiguration
Accumulates decision variables, objectives, and constraints that define the optimisation problem.

```python
model_cfg = ModelConfiguration()
model_cfg.add_decision_variable(field, dv_min=0, dv_max=100, dv_type=DVType.RANGE)
model_cfg.add_objective(total_cost_calc, maximise=False, priority=Priority.HIGH)
model_cfg.add_constraint(capacity_calc, constraint_type=ConstraintType.INEQUALITY, upper_bound=500)
```

**DVType:** `RANGE` (discrete int), `LIST` (discrete int from list), `REAL` (continuous float).
**ConstraintType:** `EQUALITY`, `INEQUALITY`.
**Priority:** `LOW`, `MEDIUM`, `HIGH`.

### Data Source Hierarchy
All data source configs inherit from the abstract `DataSourceConfig`. A `DataSource` wrapper
adds metadata (display name, hidden flag, `post_optimise`, notification flags).

`Configuration.add_*` methods accept the config directly and handle wrapping internally.

**Filter types for `DataStoreConfig`:** `EqualityDataFilter`, `InequalityDataFilter`,
`RegexDataFilter`, `SetDataFilter`, `WildcardDataFilter`.

### GeneticAlgorithm Operators

```python
mutation  = Mutation.mutation(MutationType.GAUSSIAN_MUTATION, variation_range=0.5)
selection = Selection.selection(SelectionType.TOURNAMENT_SELECTION, pool_size=4)

ga = GeneticAlgorithm(mutation=mutation, selection=selection, recombinator=RecombinatorType.UNIFORM_CROSSOVER)
```

**MutationType:** `GAUSSIAN_MUTATION`, `UNIFORM_MUTATION`.
**SelectionType:** `TOURNAMENT_SELECTION`, `FAST_TOURNAMENT_SELECTION`, `RANDOM_SELECTION`.
**RecombinatorType:** `UNIFORM_CROSSOVER`, `N_POINT_CROSSOVER`.

### ScheduleConfiguration
Defines a hierarchy of algorithm steps for multi-phase optimisation. Each `StepConfiguration`
has a `StepType` (`SINGLE`, `PARALLEL`, `SEQUENCE`) and references an `Algorithm` instance.


## Import Conventions

```python
from daitum_configuration import Configuration, GeneticAlgorithm, CMAESAlgorithm
from daitum_configuration import ModelConfiguration, DVType, Priority, ConstraintType
from daitum_configuration import NumericExpression
from daitum_configuration import ExcelTransformConfig, DataStoreConfig
from daitum_configuration import EqualityDataFilter, InequalityDataFilter
```

All public symbols are re-exported from `daitum_configuration.__init__`. Do not import from
internal submodules directly.


## Serialisation

All objects expose `to_dict()`. `Configuration.write_to_file(filename)` is the canonical
output method. Do not add alternative serialisation paths.
