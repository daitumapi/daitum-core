#!/bin/bash
# Publishes built package artifacts to PyPI using twine.
# Only publishes packages changed since the last git tag.
# Requires PYPI_TOKEN to be set in the environment.
# Must be run after build.sh (expects dist/ directories to exist).

set -e

if [ -z "$PYPI_TOKEN" ]; then
    echo "Error: PYPI_TOKEN environment variable is not set." >&2
    exit 1
fi

# shellcheck source=pipelines/changed_packages.sh
source "$(dirname "$0")/changed_packages.sh"

if [ "${BUILD_CORE:-false}" = "false" ] || [ "${#CHANGED_SUB_PKGS[@]}" -eq 0 ]; then
    echo "No changed sub-packages since last tag — nothing to publish."
    exit 0
fi

for pkg in "${CHANGED_SUB_PKGS[@]}"; do
    echo "Publishing $pkg..."
    twine upload \
        --username __token__ \
        --password "$PYPI_TOKEN" \
        --non-interactive \
        "$pkg/dist/"*
done

echo "Publishing daitum-core..."
twine upload \
    --username __token__ \
    --password "$PYPI_TOKEN" \
    --non-interactive \
    "dist/"*

echo "All changed packages published to PyPI."
