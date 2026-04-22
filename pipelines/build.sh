#!/bin/bash
# Builds sdist and wheel artifacts for packages changed since the last git tag.
# Outputs go to each package's dist/ directory.
# Must be run from the repository root.

set -e

# shellcheck source=pipelines/changed_packages.sh
source "$(dirname "$0")/changed_packages.sh"

if [ "${BUILD_CORE:-false}" = "false" ] || [ "${#CHANGED_SUB_PKGS[@]}" -eq 0 ]; then
    echo "No changed sub-packages since last tag — nothing to build."
    exit 0
fi

for pkg in "${CHANGED_SUB_PKGS[@]}"; do
    echo "Building $pkg..."
    python -m build "$pkg" --outdir "$pkg/dist"
done

echo "Building daitum-core..."
python -m build . --outdir dist

echo "Build complete. Artifacts:"
for pkg in "${CHANGED_SUB_PKGS[@]}"; do
    ls "$pkg/dist"
done
ls dist
