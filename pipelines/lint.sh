#!/bin/bash

# Exit immediately if any command fails
set -e

echo "Running Ruff (format check)..."
ruff format --check daitum-model/src daitum-ui/src daitum-configuration/src

echo "Running Ruff (linting, import sorting)..."
ruff check daitum-model/src daitum-ui/src daitum-configuration/src

echo "Running MyPy (type checking)..."
mypy --explicit-package-bases daitum-model/src daitum-ui/src daitum-configuration/src

echo "All checks passed!"
