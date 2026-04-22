"""Generate per-formula Sphinx RST pages for daitum_model.formulas.

Run this script directly or let docs/conf.py invoke it automatically during a Sphinx build.

Outputs:
    docs/daitum_model/formulas/{NAME}.rst  — one file per formula function
    docs/daitum_model/formulas.rst         — index page with toctree
"""

import importlib
import inspect
import os
import sys
from pathlib import Path

MODULE_NAME = "daitum_model.formulas"
DOCS_DIR = Path(__file__).parent
OUTPUT_DIR = DOCS_DIR / "daitum_model" / "formulas"
INDEX_PATH = DOCS_DIR / "daitum_model" / "formulas.rst"


def is_formula_function(obj: object) -> bool:
    return inspect.isfunction(obj) and obj.__name__.isupper() and obj.__name__[0].isalpha()  # type: ignore[union-attr]


def main() -> None:
    # Ensure daitum_model is importable when run standalone.
    repo_root = DOCS_DIR.parent
    for pkg_src in [
        repo_root / "daitum-model" / "src",
        repo_root / "daitum-ui" / "src",
        repo_root / "daitum-configuration" / "src",
    ]:
        sys.path.insert(0, str(pkg_src))

    module = importlib.import_module(MODULE_NAME)

    formulas = [(name, obj) for name, obj in inspect.getmembers(module, is_formula_function)]
    formulas.sort(key=lambda x: x[0])

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    for name, _ in formulas:
        rst_path = OUTPUT_DIR / f"{name}.rst"
        rst_path.write_text(
            f"{name}\n{'=' * len(name)}\n\n.. autofunction:: {MODULE_NAME}.{name}\n",
            encoding="utf-8",
        )
        print(f"Generated {rst_path}")

    toctree_entries = "\n".join(f"   formulas/{name}" for name, _ in formulas)
    index_content = f"""\
Formulas
========

Formula functions live in the ``daitum_model.formulas`` submodule:

.. code-block:: python

   from daitum_model.formulas import SUM, ROWS

   result = SUM(ROWS(my_table["amount"]))

.. toctree::
   :maxdepth: 1
   :caption: Formula Reference:

{toctree_entries}
"""
    INDEX_PATH.write_text(index_content, encoding="utf-8")
    print(f"Generated {INDEX_PATH}")


if __name__ == "__main__":
    main()
