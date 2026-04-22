# Coding Guidelines

This document outlines coding standards and best practices for this project.

## Code Quality Requirements

**All code must pass Ruff linting and formatting checks before commit.**

Run checks locally:
```bash
./pipelines/lint.sh

# Or individually:
ruff check daitum-model/src daitum-ui/src daitum-configuration/src
black --check daitum-model/src daitum-ui/src daitum-configuration/src
mypy --explicit-package-bases daitum-model/src daitum-ui/src daitum-configuration/src
```

Ruff will automatically fix many issues when run with `ruff check --fix`.

## Python Style Guide

This project follows the [Google Python Style Guide](https://google.github.io/styleguide/pyguide.html)
with specific adaptations for the Daitum platform.

### Import Conventions

The rule depends on what you're importing:

| What | Rule | Example |
|------|------|---------|
| Classes, enums, types | `from x import ClassName` | `from pathlib import Path`, `from daitum_model import DataType` |
| Functions and modules | `import module` | `import daitum_model`, `import os` |

✅ **GOOD**:
```python
# Standard library functions — import module directly
import os
import json

# Classes, enums, types — always import directly
from pathlib import Path
from typing import Any, cast
from dataclasses import dataclass
from daitum_model import DataType, JoinType
from daitum_model.tables import JoinCondition
from daitum_ui.styles import CellStyle
```

❌ **BAD**:
```python
# Verbose aliases for accessing classes — use direct imports instead
import daitum_model.enums as mg_enums        # use: from daitum_model import DataType
import daitum_ui.styles as ug_styles          # use: from daitum_ui.styles import CellStyle

# Module imports instead of class imports
import pathlib                                # use: from pathlib import Path
import typing                                 # use: from typing import Any
```

**Import Order** (enforced by Ruff):
1. Standard library imports
2. Third-party imports
3. First-party imports (`daitum_model`, `daitum_ui`, `daitum_configuration`)

### Naming Conventions

| Type | Convention | Example |
|------|------------|---------|
| **Field names** | Title Case | `"Start Time"`, `"Lock to Resource"`, `"Cost"` |
| **Table names** | PascalCase | `Resources`, `UiJobs`, `CurrentSchedule` |
| **Calculation names** | SCREAMING_SNAKE_CASE | `TOTAL_COST`, `SCHEDULE_RESOLUTION` |
| **Parameter names** | SCREAMING_SNAKE_CASE | `START_TIME`, `LAST_DAY` |
| **Variables** | snake_case | `ui_builder`, `jobs_table` |
| **Functions** | snake_case | `build_jobs_screen()`, `create_ui_table()` |
| **Classes** | PascalCase | `InputTables`, `ModelConfiguration` |
| **Constants** | SCREAMING_SNAKE_CASE | `MAXIMUM_ATTRIBUTES`, `ERROR_STYLE` |

### Type Hints

**All functions must have type hints** (enforced by MyPy).

```python
from daitum_model import ModelBuilder, Table

def build_joined_table(
    model: ModelBuilder,
    left_table: Table,
    right_table: Table,
) -> Table:
    ...
```

### Line Length

Maximum 100 characters per line (enforced by Black and Ruff).

### Docstrings

Use docstrings for modules, classes, and public functions.

**Module docstrings**:
```python
"""
Defines the core model builder for constructing Daitum model definitions.
"""
```

**Function docstrings** (optional for simple functions, required for complex logic):
```python
def build_mapped_preprocessor(file_path: Path, table: Table, maximum_rows: int) -> None:
    """
    Generates flexible column-mapped preprocessors for data tables.

    Creates an Excel file with Input (hidden) and Output sheets that use MATCH/INDEX
    formulas to map flexible input column orders to fixed model table structures.
    """
```

### Avoid Nested Formulas

**DO NOT deeply nest formula calls.** Extract intermediate formulas into variables.

❌ **BAD** (deeply nested):
```python
validation = formulas.IF(
    formulas.ISBLANK(field),
    allow_blank,
    formulas.AND(
        formulas.IF(formulas.ISBLANK(minimum), True, field >= minimum),
        formulas.IF(formulas.ISBLANK(maximum), True, field <= maximum)
    )
)
```

✅ **GOOD** (extracted helpers):
```python
min_valid = formulas.IF(formulas.ISBLANK(minimum), True, field >= minimum)
max_valid = formulas.IF(formulas.ISBLANK(maximum), True, field <= maximum)
valid = formulas.AND(min_valid, max_valid)
validation = formulas.IF(formulas.ISBLANK(field), allow_blank, valid)
```

## Google Python Style Guide Highlights

### Classes

- Use `self` for instance methods
- Use `cls` for class methods
- Private attributes start with underscore: `self._model`

### Functions

- Use snake_case for function names
- Keep functions focused on a single task
- Limit function length (aim for < 40 lines)

### Exceptions

- Raise exceptions rather than returning error codes
- Use specific exception types (`ValueError`, `TypeError`, etc.)
- Provide informative error messages

```python
if data_type not in supported_types:
    raise NotImplementedError(
        f"Range validation is not yet supported for the data type {data_type.to_dict()}."
    )
```

### Comments

- Use comments sparingly — prefer self-documenting code
- Comments should explain *why*, not *what*
- Keep comments up-to-date with code changes

### String Formatting

- Prefer f-strings for string formatting

```python
# Good
error_msg = f"The field {field_name} is invalid"
```

### List Comprehensions

- Use list comprehensions for simple transformations
- Extract to regular loops for complex logic

## Pre-Commit Checklist

Before committing code:

- [ ] All Ruff checks pass (`ruff check daitum-model/src daitum-ui/src daitum-configuration/src`)
- [ ] Code is formatted with Black
- [ ] Type checking passes (`mypy --explicit-package-bases ...`)
- [ ] Classes/enums/types imported directly (`from x import ClassName`)
- [ ] Nested formulas extracted into helpers
- [ ] Type hints on all functions
- [ ] Docstrings on modules and complex functions
