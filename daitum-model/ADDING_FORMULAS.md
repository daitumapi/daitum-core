# Adding Formulas

Internal guide for adding a new formula function to `daitum_model.formulas`.

A formula function is a public Python builder (e.g. `LOG`, `NORMDIST`, `INTERSECTION`) that
returns a `Formula` wrapping an expression string and a `DataType`. Every formula is split into
two layers:

| Layer | File | Responsibility |
|---|---|---|
| Internal builder | `src/daitum_model/_base_formulas.py` | Takes already-serialised `str` operands, returns `Formula(data_type, "NAME(arg1, arg2, ...)")`. No validation, no docstring. |
| Public wrapper | `src/daitum_model/formulas.py` | Accepts user-friendly types (`Operand`, `int`, `float`, `bool`, etc.), coerces literals via `CONST`, validates data types, computes the return type, and calls the internal builder. Owns the docstring. |

This split keeps the wire-format trivially easy to inspect and lets the public API do all
type-checking and Pythonic ergonomics in one place.


## Step-by-step

### 1. Add the internal builder

In `_base_formulas.py`, add a one-liner returning a `Formula`. The expression string must
exactly match what the platform expects.

```python
def _MYFUNC(data_type: DataType, arg1: str, arg2: str) -> Formula:
    return Formula(data_type, f"MYFUNC({arg1}, {arg2})")
```

Variadic arguments use `*args: str` and `", ".join(...)`:

```python
def _MYFUNC(data_type: DataType, ignore_blanks: str, *values: str) -> Formula:
    return Formula(data_type, f"MYFUNC({ignore_blanks}, {', '.join(values)})")
```

If the return type can be a composite (`ObjectDataType`, `MapDataType`), widen the
`data_type` parameter accordingly — see `_INTERSECTION`, `_UNION` for examples.

### 2. Import the builder in `formulas.py`

The import block at the top of `formulas.py` is alphabetical. Insert the new `_MYFUNC` in
alphabetical position.

### 3. Add the public wrapper

Place the new public function near related ones (e.g. numeric next to numeric, set-ops next to
set-ops). The file is grouped by topic, not strictly alphabetical.

The wrapper's job is always the same five things:

1. **Coerce Python literals** (`int`, `float`, `bool`, sometimes `str`) into `Operand`s by
   recursively calling itself with `CONST(value)` substituted.
2. **Extract data types** of every operand via `.to_data_type()`.
3. **Validate** each data type against the appropriate allowed set
   (`NUMERIC_AND_ARRAY_TYPES`, `BOOLEANISH_AND_ARRAY_TYPES`, `DATE_AND_ARRAY_TYPES`, etc. —
   defined near the top of `formulas.py`). Raise `ValueError` with a descriptive message on
   mismatch.
4. **Compute the return type.** Two common patterns:
   - *Type-preserving* (e.g. `ABS`): pass the input data type straight through.
   - *Type-fixing* (e.g. `EXP`, `LOG`, `NORMDIST`): force `DECIMAL` for scalar inputs and
     `DECIMAL_ARRAY` if **any** input is an array. Use `data_type.is_array()` to detect arrays.
5. **Call the internal builder** with the computed return type and `operand.to_string()` for
   each argument.

Skeleton (single-argument numeric, return type fixed to DECIMAL):

```python
def MYFUNC(value: int | float | Operand) -> Formula:
    """<see Docstring conventions below>"""
    if isinstance(value, int | float):
        return MYFUNC(CONST(value))

    data_type = value.to_data_type()

    if data_type not in NUMERIC_AND_ARRAY_TYPES or not isinstance(data_type, DataType):
        raise ValueError(f"MYFUNC invalid with data type {data_type}")

    ret_data_type = DataType.DECIMAL_ARRAY if data_type.is_array() else DataType.DECIMAL

    return _MYFUNC(ret_data_type, value.to_string())
```

Skeleton (multi-argument, mixed numeric + boolean, return type fixed to DECIMAL):

```python
def MYFUNC(
    x: Operand | int | float,
    flag: Operand | bool,
) -> Formula:
    """<see Docstring conventions below>"""
    if isinstance(x, (int, float)):
        return MYFUNC(CONST(x), flag)
    if isinstance(flag, bool):
        return MYFUNC(x, CONST(flag))

    x_dt = x.to_data_type()
    flag_dt = flag.to_data_type()

    if x_dt not in NUMERIC_AND_ARRAY_TYPES:
        raise ValueError(f"MYFUNC invalid with the argument {x_dt}")
    if flag_dt not in BOOLEANISH_AND_ARRAY_TYPES:
        raise ValueError(f"MYFUNC invalid with the argument {flag_dt}")

    ret_data_type = DataType.DECIMAL
    if x_dt.is_array() or flag_dt.is_array():
        ret_data_type = DataType.DECIMAL_ARRAY

    return _MYFUNC(ret_data_type, x.to_string(), flag.to_string())
```

For variadic, set-returning, or composite-typed functions (e.g. `INTERSECTION`, `ARRAY`,
`LOOKUP`), the same five steps apply — adapt the validation and return-type logic. Read the
nearest existing analogue before writing a new one.

The `typechecked()` call at the top of `formulas.py` automatically enforces the type
annotations on every public function — keep your annotations precise.

### 4. Re-export

Public functions defined in `formulas.py` are accessed as `daitum_model.formulas.MYFUNC` (or
via `from daitum_model import formulas`). Nothing else to do — no `__all__`, no edits to
`__init__.py`.


## Docstring conventions

Docstrings are rendered directly into the user-facing documentation, so they must be
consistent. Match the style of `NORMDIST`, `NORMINV`, `GAMMADIST` exactly. The required
sections, in order:

1. **One-line summary** — verb-led, ends with a full stop.
2. **Paragraph description** — what the function does, array-element behaviour, edge cases
   (blank/error inputs, domain restrictions).
3. **Arguments** — one entry per parameter. Each entry has a short prose description followed
   by a `*Supported types*:` block:

   ```
   *Supported types*:

   .. container:: supported-types

       - INTEGER
       - DECIMAL
       - INTEGER_ARRAY
       - DECIMAL_ARRAY
   ```

4. **Returns** — what the formula evaluates to, scalar-vs-array rules, and a `*Supported
   types*:` block listing the possible return types.
5. **Raises** — every `ValueError` the wrapper can raise, with the triggering condition.
6. **Examples** — at least three `.. code-block:: python` blocks: a scalar literal, a model
   field / `Operand`, and an array. Each block ends with a `# Returns ...` comment showing the
   evaluated result (approximate is fine).

Notes:
- **Australian English** throughout (per the root `CLAUDE.md`).
- Keep the prose tight. The supported-types containers carry the type information — don't
  duplicate it in prose.
- Don't reference internal builders (`_MYFUNC`) or other implementation details in docstrings.


## Verification

Run the standard checks before committing:

```bash
source venv/bin/activate
./pipelines/lint.sh                       # Black, Ruff, MyPy
pytest daitum-model/                      # full test suite
```

Smoke-test the new function in a REPL to confirm:

- scalar input → expected scalar return type
- array input → expected `_ARRAY` return type
- a non-matching `DataType` raises `ValueError`
- the emitted `formula_string` contains the function name and the expected number of arguments


## When to add a test

Per the root `CLAUDE.md` ("only add tests that verify internal behaviours or fix specific
bugs"), most new formulas do **not** need a dedicated test. Add a test in
`tests/test_formulas.py` only if the wrapper has non-trivial logic — e.g. unusual return-type
inference, multi-branch validation, or a fix for a specific bug. Trivial single-argument
wrappers that mirror an existing pattern (`ABS`, `EXP`, `LOG`, `SIN`, `COS`) do not warrant
their own tests.

When you do add a test, follow the existing pattern in `tests/test_formulas.py`: assert the
returned `data_type` and that the function name appears in the formula string, for both scalar
and array inputs.
