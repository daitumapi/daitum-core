#!/bin/bash

# Exit immediately if any command fails
set -e

echo "Running Black..."
black --check daitum-model/src daitum-ui/src daitum-configuration/src

echo "Running Ruff (linting, formatting, import sorting)..."
ruff check daitum-model/src daitum-ui/src daitum-configuration/src

echo "Running MyPy (type checking)..."
mypy --explicit-package-bases daitum-model/src daitum-ui/src daitum-configuration/src

echo "All checks passed!"
