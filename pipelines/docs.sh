#!/bin/bash

# Exit immediately if any command fails
set -e

echo "Installing docs dependencies..."
pip install -r docs/requirements.txt

echo "Building Sphinx documentation..."
# -W treats warnings as errors; --keep-going collects all errors before failing
sphinx-build -W --keep-going -b html docs/ docs/_build/html

echo "Documentation build passed!"
