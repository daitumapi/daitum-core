"""Sphinx configuration for the unified daitum-core documentation."""

import sys
from pathlib import Path

# Make all three packages importable by autodoc without installation.
_repo_root = Path(__file__).parent.parent
for _pkg_src in [
    _repo_root / "daitum-model" / "src",
    _repo_root / "daitum-ui" / "src",
    _repo_root / "daitum-configuration" / "src",
]:
    sys.path.insert(0, str(_pkg_src))

# ---------------------------------------------------------------------------
# Project metadata
# ---------------------------------------------------------------------------

project = "daitum-core"
author = "Daitum"
copyright = f"2026, {author}"  # noqa: A001

# Pull version from the root pyproject.toml so it stays in sync.
import re as _re

_version_match = _re.search(
    r'^version\s*=\s*"([^"]+)"',
    (_repo_root / "pyproject.toml").read_text(),
    _re.MULTILINE,
)
release = _version_match.group(1) if _version_match else "0.1.0"
version = ".".join(release.split(".")[:2])

add_module_names = False

templates_path = ["_templates"]

html_theme = "sphinx_rtd_theme"
html_static_path = ["_static"]
html_show_sphinx = False

# ---------------------------------------------------------------------------
# Extensions
# ---------------------------------------------------------------------------

extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.napoleon",  # Google-style docstrings
    "sphinx.ext.viewcode",  # [source] links next to API entries
    "sphinx.ext.intersphinx",  # Cross-references to Python stdlib docs
    "sphinx_autodoc_typehints",  # Type hints in signature and description
]

# ---------------------------------------------------------------------------
# autodoc settings
# ---------------------------------------------------------------------------

autodoc_default_options = {
    "members": True,
    "undoc-members": False,
    "show-inheritance": True,
    "member-order": "bysource",
}

autodoc_typehints = "description"
autodoc_typehints_description_target = "documented"

# ---------------------------------------------------------------------------
# napoleon settings (Google-style docstrings)
# ---------------------------------------------------------------------------

napoleon_google_docstring = True
napoleon_numpy_docstring = False
napoleon_include_init_with_doc = True
napoleon_use_param = True
napoleon_use_rtype = True

# ---------------------------------------------------------------------------
# intersphinx
# ---------------------------------------------------------------------------

intersphinx_mapping = {
    "python": ("https://docs.python.org/3", None),
}

# ---------------------------------------------------------------------------
# HTML output
# ---------------------------------------------------------------------------

html_theme = "furo"
html_title = "daitum-core"

# ---------------------------------------------------------------------------
# General
# ---------------------------------------------------------------------------

exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]
nitpicky = False


# ---------------------------------------------------------------------------
# Formula docs generation
# ---------------------------------------------------------------------------


def setup(app):  # type: ignore[no-untyped-def]
    """Regenerate per-formula RST files before each Sphinx build."""
    import subprocess

    subprocess.run(
        [sys.executable, str(Path(__file__).parent / "generate_formula_docs.py")],
        check=True,
    )
