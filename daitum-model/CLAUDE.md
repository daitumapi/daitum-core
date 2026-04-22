# CLAUDE.md — daitum-model

This package lives inside the `daitum-core` monorepo. The root `CLAUDE.md` at `../CLAUDE.md`
contains global conventions (Australian English, linting workflow, virtual environment, etc.) that
apply here too. Read it first.


## Package Purpose

`daitum-model` is a fluent builder library for constructing optimisation model definitions for the
Daitum platform. A model is composed of tables, fields, formulas, named values (calculations and
parameters), and validators. The final output is a JSON file produced via `ModelBuilder.write_to_file()`.


## Package Structure

```
daitum-model/
├── src/daitum_model/
│   ├── __init__.py          # Public API — all user-facing classes re-exported here
│   ├── model.py             # ModelBuilder — main entry point
│   ├── tables.py            # DataTable, DerivedTable, JoinedTable, UnionTable
│   ├── fields.py            # DataField, CalculatedField, ComboField
│   ├── formula.py           # Formula class, CONST(), Operand base
│   ├── named_values.py      # Calculation, Parameter
│   ├── enums.py             # DataType, SortDirection, AggregationMethod, JoinType, Severity
│   ├── data_types.py        # ObjectDataType, MapDataType
│   ├── validator.py         # Validator hierarchy
│   ├── formulas.py          # 100+ formula functions (LOOKUP, IF, SUM, …) — separate module
│   ├── _base_formulas.py    # Internal: low-level formula implementations
│   ├── _helpers.py          # Internal: name validation, field replacement utilities
│   └── change_calculator.py # Change-tracking utilities
└── tests/
    ├── test_model.py
    └── test_formulas.py
```


## Key Abstractions

### ModelBuilder
The single entry point for building a model. Call its factory methods to create tables and named
values; call `write_to_file()` to emit JSON.

```python
model = ModelBuilder()
table = model.add_data_table("Jobs", key_column="ID")
calc  = model.add_calculation("TOTAL_COST", formulas.SUM(table["Cost"]), model_level=True)
model.write_to_file("model.json")
```

Factory methods: `add_data_table`, `add_derived_table`, `add_joined_table`, `add_union_table`,
`add_calculation`, `add_parameter`.

### Table Hierarchy
All table types inherit from `Table`. They manage fields and expose array-subscript access
(`table["id"]`) which returns an array-typed formula.

| Class | Purpose |
|---|---|
| `DataTable` | Raw data input; supports decision variables |
| `DerivedTable` | Filtered/grouped view of another table with aggregations |
| `JoinedTable` | Result of joining multiple tables on conditions |
| `UnionTable` | Stacked rows from multiple source tables |

Factory methods on tables: `add_data_field`, `add_calculated_field`, `add_combo_field`,
`add_object_reference_field`, `add_map_field`.

### Field Hierarchy
All field types inherit from `Field`. Fields track their parent table, data type, and optional
validators.

| Class | Purpose |
|---|---|
| `DataField` | Imported/raw data with optional default, format, and uniqueness |
| `CalculatedField` | Computed via a `Formula` |
| `ComboField` | Data or calculated based on the `calculate_in_optimiser` flag |

### Formula
`Formula` wraps an expression string and a `DataType`. Python operators (`+`, `-`, `*`, `/`, `<`,
`>`, `==`, etc.) are overloaded on `Formula`, `Field`, `Calculation`, and `Parameter` to compose
expressions. Use `CONST(value)` to create a `Formula` from a Python literal.

```python
total = cost * qty                  # Formula with DECIMAL type
is_over = total > CONST(1000)       # Formula with BOOLEAN type
```

### Named Values — Calculation and Parameter
Both participate in formula expressions (they inherit `Operand`).

- **`Calculation`**: a formula computed at runtime; can be model-level or scenario-level.
- **`Parameter`**: a constant value with a data type; can be model-level or scenario-level.

### Validators
Validators attach to fields or named values and automatically generate synthetic `__invalid__` and
`__message__` calculated fields. Combine validators with `&` / `|`.

Available: `RangeValidator`, `NonBlankValidator`, `UniqueValidator`, `ListValidator`,
`LengthValidator`.

### formulas Module
Over 100 formula functions live in `daitum_model.formulas` — imported separately:

```python
import daitum_model.formulas as formulas   # preferred
from daitum_model import formulas          # also valid
```

Functions include: `LOOKUP`, `IF`, `ARRAY`, `FILTER`, `SUM`, `AVERAGE`, `COUNT`, `OR`, `AND`,
`NOT`, `ISBLANK`, `DATE`, `DATETIME`, and many more.

### DataType Enum
Primitive: `INTEGER`, `DECIMAL`, `STRING`, `BOOLEAN`, `DATE`, `DATETIME`, `TIME`, plus `_ARRAY`
variants. Composite: `ObjectDataType` (reference to another table), `MapDataType` (key-value map).


## Import Conventions

```python
from daitum_model import ModelBuilder, DataType, Calculation, Parameter
from daitum_model import RangeValidator, Severity
import daitum_model.formulas as formulas
```

All public symbols are re-exported from `daitum_model.__init__`. Do **not** import from internal
submodules directly (e.g. avoid `from daitum_model.formula import Formula`).


## Adding New Formula Functions

New functions go in `formulas.py`. Follow the exact patterns already used there — each function
returns a `Formula` with an explicit `DataType`. Add a matching test in `tests/test_formulas.py`
only if the function has non-trivial logic that warrants it.


## Serialisation

All objects expose `to_dict()`. `ModelBuilder.write_to_file(filename)` is the canonical way to
produce the final JSON output. Do not add alternative serialisation paths.
