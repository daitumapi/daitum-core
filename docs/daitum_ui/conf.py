import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join("..", "..")))

project = "UI Generator"
copyright = "2025, Daitum"
author = "Daitum"
release = "0.5.1"
add_module_names = False

templates_path = ["_templates"]

html_theme = "sphinx_rtd_theme"
html_static_path = ["_static"]
html_show_sphinx = False

extensions = ["sphinx.ext.autodoc", "sphinx.ext.napoleon", "sphinx.ext.intersphinx"]

intersphinx_mapping = {
    "python": ("https://docs.python.org/3", None),
}

autodoc_preserve_defaults = True
autodoc_typehints = "description"
