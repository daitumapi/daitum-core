# Adding a Formula Function

Internal guide for adding a new formula function (e.g. `LOG`, `NORMDIST`, `INTERSECTION`) to
`daitum_model.formulas`. New functions are added semi-regularly as the platform gains capabilities,
so follow this end-to-end — a function is only "done" when its node class, public wrapper, tests,
and generated docs are all in place.

> **Read first:** the root `../CLAUDE.md` (Australian English, the lint workflow, the venv) and
> `daitum-model/CLAUDE.md` (package layout).


## 1. The architecture (how a formula works now)

A formula **is** a structured expression tree — not a string. Each function is a node class that
knows its children, validates its arguments, infers its return type, and renders itself to the exact
platform expression string. `data_type` and `formula_string` are *projections* of the tree (how it
type-checks and how it is written to JSON), derived on demand.

Every function spans two layers:

| Layer | File | Responsibility |
|---|---|---|
| **Node class** | `src/daitum_model/_functions.py` | A `Function` subclass owning the argument spec, validation, return-type inference, and rendering. |
| **Public wrapper** | `src/daitum_model/formulas.py` | The user-facing builder. Accepts friendly types (`Operand`, `int`, `float`, `bool`, `str`), constructs the node, and returns it. Owns the user docstring. |

A node `is-a` `Formula` (the abstract base in `formula.py`), so the wrapper returns the node directly
— there is no separate "materialise" step.

`Function.__init__` (in `expression.py`) runs a fixed pipeline for every function:

1. `ensure_operand(arg)` coerces each Python literal to a `Constant` operand (so `SUM(1, [Cost])`
   works without the caller wrapping `1`).
2. `_validate_arity()` — enforced from the declarative `spec` (below).
3. `_validate_types()` — each operand checked against its `Arg.accepts`, from the `spec`.
4. `validate()` — a per-function hook for **cross-argument / structural** rules only.
5. `result_type()` — infers the return `DataType` from the operands.

So most of a function is *declarative*: you describe its arguments in a `spec`, and the engine does
arity + per-argument type checking. You only write imperative code for return-type inference and any
rule that spans multiple arguments.


## 2. Write the node class (`_functions.py`)

A concrete `Function` subclass sets:

- `name` — the **wire name** the function renders as (usually the public function name, uppercase).
- `spec` — a tuple of `Arg` declaring each argument (name + accepted types + flags).
- `result_type(self)` — returns the inferred `BaseDataType`.
- `validate(self)` — *optional*; only for cross-argument/structural rules.

### `Arg` — the declarative argument spec

```python
from daitum_model.expression import Arg

Arg(
    name="input_string",          # shown in errors and generated docs
    accepts=frozenset(_STRINGS),  # accepted DataTypes, or None for ANY (no restriction)
    variadic=False,               # True ⇒ captures all remaining operands
    optional=False,               # True ⇒ may be omitted
    literal_only=False,           # True ⇒ must be a literal, not an operand (rare)
)
```

The module defines reusable type sets (`_NUMERIC`, `_STRINGS`, `_DECIMALS`, `_DATES`, `_BOOLEANISH`,
`_INT_OR_ARRAY`, …) near the top of `_functions.py` — reuse them rather than re-listing `DataType`s.

### Prefer a shape base class

Most functions fit an existing shape base; subclass it and you inherit the spec + validation:

| Base | Shape | Examples |
|---|---|---|
| `_TypedUnary` (+ `_PreserveUnary` / `_DecimalUnary` / `_IntegerUnary` / `_StringUnary`) | one operand of `accepts`, result by strategy | `ABS`, `LOG`, `ROUND`, `LOWER` |
| `_Reducer` (+ `_ArrayReducer` / `_DecimalReducer` / `_BooleanReducer`) | variadic operands of `accepts` (≥1) | `SUM`, `AVERAGE`, `AND` |
| `_MinMax` | variadic numeric/date/time with family rules | `MIN`, `MAX` |
| `_BranchMerge` | two branches, array-of-scalar compatible | `IFBLANK`, `IFERROR` |
| `_LeftRight`, `_BitOp`, `_Between`, `_ProbabilityDist`, … | other recurring shapes | `LEFT`, `BITAND`, `DAYSBETWEEN` |

Example — a new unary that returns `DECIMAL`:

```python
class MyFunc(_DecimalUnary):
    name = "MYFUNC"
    accepts = frozenset(_NUMERIC)   # the shape base derives its spec from `accepts`
```

Example — a bespoke two-argument function:

```python
class MyFunc(Function):
    name = "MYFUNC"
    spec = (
        Arg("amount", accepts=frozenset(_NUMERIC)),
        Arg("label", accepts=frozenset(_STRINGS)),
    )

    def validate(self) -> None:
        # Only cross-argument / structural rules belong here — per-argument type checks are already
        # done by the engine from `spec`. Raise via the standardised helpers:
        #   self.type_error(dt) / self.incompatible_error(a, b) / self.arity_error() / self.invalid(reason)
        ...

    def result_type(self) -> BaseDataType:
        amount = self._operands[0].to_data_type()
        return amount  # e.g. preserve the first operand's type
```

### Rules of thumb

- **Errors are always `ValueError`**, raised through the `Function` helpers (`type_error`,
  `incompatible_error`, `arity_error`, `invalid`) so messages share one shape: `"<NAME>: <reason>."`.
- **Zero-operand functions** (like `ROWVECTOR`) leave `spec = ()`. `ROW`/`CONST` are special constants
  built in the wrapper, not node classes.
- **A different wire name** (rendered ≠ class `name`): override `render_name()` — see
  `LookupArray` → `LOOKUP_ARRAY`. Keep `name` matching the public function for the registries.
- **Custom argument shapes** (optional/variadic via a hand-written `__init__`): see `Find`, `Text`,
  `Choose`, `Lookup`, `ToMap`. Still declare a `spec` (with `optional=True` / `variadic=True`) so the
  docs and validation engine see every argument.
- **Non-default rendering** (rare): override `to_string()`. The default is
  `NAME(arg1, arg2, …)` joined by `separator` (`", "`).


## 3. Write the public wrapper (`formulas.py`)

A thin builder that accepts friendly types and constructs the node. The whole file is
`@typechecked`, so annotate arguments precisely.

```python
def MYFUNC(
    amount: Operand | int | float,
    label: Operand | str,
) -> Formula:
    """
    One-line summary of what MYFUNC does.

    <Behaviour description: what it computes, array handling, blank/error behaviour.>

    Arguments:
        amount: ...
        label: ...

    Returns:
        ...

    Raises:
        ValueError: if `amount` is not numeric.
        ValueError: if `label` is not a string.

    Examples:
        .. code-block:: python

            MYFUNC(cost, "total")
    """
    return _functions.MyFunc(amount, label)
```

- The **docstring describes behaviour only** — do *not* hand-write "Supported types" tables; those
  are generated from the `spec` (§5).
- Literals are coerced automatically (`ensure_operand`), so accept `int`/`float`/`bool`/`str`
  alongside `Operand` where it makes sense and let the node wrap them.
- The wrapper is the docs/round-trip surface: its name must be uppercase (the docs reflector and the
  parser registry key on it).

(Editing the existing `_functions.py` / `formulas.py` needs no new licence header; a brand-new source
file under `daitum-model/src` does — see the Apache 2.0 header in the root `CLAUDE.md`.)


## 4. Tests — required, in this order

Run `pytest` and `./pipelines/lint.sh` (Black, Ruff, MyPy) before considering the change done.

### 4a. Argument-spec coverage gate (automatic)

`tests/test_expression_nodes.py::test_every_function_declares_an_argument_spec` fails CI if your
node class has no `spec` (empty allowed only for the zero-operand `BLANK`/`ROWVECTOR`). Filling the
`spec` (§2) satisfies it — and is what makes the generated per-argument docs correct.

### 4b. Characterisation corpus (required)

Add at least one case to **`tests/fixtures/contract_cases.py`** (`function_cases()`), naming it with
the function name as the leading token:

```python
Case("MYFUNC", lambda fx: formulas.MYFUNC(fx.fields["Cost"], "total")),
```

`tests/test_formula_contract.py::test_every_public_function_is_covered` fails CI until every public
function has a corpus case. The harness captures `(to_string(), to_data_type())` into a golden file.

### 4c. Drift corpus (required for behaviour coverage)

`tests/fixtures/drift_corpus.py` exhaustively sweeps functions × typed-operand specimens, pinning
each outcome (rendered string + type on success, exception type on rejection). Register your function
in the registry that matches its shape:

- `UNARY` / `BINARY` — one / two operands swept over the specimen set.
- `VARIADIC_NUMERIC` / `VARIADIC_LOGICAL` — variadic groups.
- For a bespoke shape (optional/variadic/literal args), add explicit invocations in
  `_add_bespoke_cases`.

The golden files (`tests/fixtures/drift_*_golden.json`) are **auto-captured on first run when
absent**. To accept a new function's behaviour, run the suite once (capturing its cases), inspect the
new golden entries to confirm they are correct, and commit them. When you *change* existing
behaviour deliberately, delete the affected golden and re-capture — and note the change in the PR.

### 4d. Bespoke behaviour tests (optional)

If the function has non-trivial validation or inference, add a focused test in
`tests/test_formulas.py`. Don't add redundant tests the corpus already covers.


## 5. Docs (generated — verify, don't hand-write)

The reference is generated from the `spec` and the drift corpus by `docs/generate_formula_docs.py`:

- **Per-argument "Accepted types"** tables come from your `Arg` spec (names + accepted types).
- **"Return types"** come from the function's successful outcomes in the drift golden.
- `tests/test_doc_spec.py` cross-checks that the declared `spec` accepts every input type the corpus
  exercises — so a spec that under-declares fails CI.

Regenerate and confirm it builds:

```bash
cd docs && python generate_formula_docs.py        # writes daitum_model/formulas/MYFUNC.rst etc.
```

You do **not** hand-edit the generated `formulas/*.rst` stubs.


## 6. The parser & decoder (usually automatic — know the one caveat)

A formula loaded from JSON is parsed back into its node tree by `_parser.py`, and the decoder
(`_decoders/formula.py`) requires an **exact** round-trip: `parse(formula.to_string())` must
reproduce the original string and type, or it raises `LoadError`. There is no string fallback.

For a normal function this is automatic: the parser finds your node class by its `name` (or the
`LOOKUP_ARRAY`-style override) and reconstructs `MyFunc(*parsed_args)`. **The drift conformance gate
(`test_parser.py::TestParserDriftConformance`) will fail** if your function does not round-trip — so
a green suite confirms the parser handles it.

The one thing to watch: if your function's **type cannot be recovered from its rendered string**
(as `BLANK()` erases its declared type), the parser needs the authoritative type. `BLANK` is handled
by passing the decoder's `dataType` as `expected_type`; a new function with the same property would
need similar handling in `_parser.py`. This is rare — most functions render all the information their
type depends on.


## 7. Checklist

- [ ] Node class in `_functions.py` — `name`, `spec` (named `Arg`s), `result_type`, `validate` if
      cross-argument rules exist. Reused a shape base where one fit.
- [ ] Errors raise `ValueError` via the `Function` helpers.
- [ ] Public wrapper in `formulas.py` — friendly types, behaviour-only docstring, returns the node.
- [ ] Case added to `contract_cases.py`.
- [ ] Registered in `drift_corpus.py` (or `_add_bespoke_cases`); golden re-captured and inspected.
- [ ] `./pipelines/lint.sh` clean; `pytest` green (incl. the spec gate, doc cross-check, and parser
      drift conformance).
- [ ] Docs regenerate and build.
