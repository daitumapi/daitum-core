#!/bin/bash
# Detects which sub-packages have changed since the last git tag.
# Must be sourced (not executed) — populates CHANGED_SUB_PKGS array.
#
# Variables set:
#   CHANGED_SUB_PKGS  — array of changed sub-package names
#   BUILD_CORE        — "true" if any sub-package changed, "false" otherwise

# Ensure tags exist in CI (critical fix)
git fetch --tags --force origin

SUB_PACKAGES=("daitum-model" "daitum-ui" "daitum-configuration")
CHANGED_SUB_PKGS=()

# Robust last-tag resolution (replaces brittle tag listing)
LAST_TAG=$(git describe --tags --abbrev=0 2>/dev/null || true)

echo "Detected LAST_TAG = ${LAST_TAG:-<none>}"

if [ -z "$LAST_TAG" ]; then
    echo "No previous tag found — skipping build (no release baseline)"
    CHANGED_SUB_PKGS=()
    BUILD_CORE="false"
    return 0 2>/dev/null || true
else
    for pkg in "${SUB_PACKAGES[@]}"; do
        if git diff --name-only "$LAST_TAG" HEAD -- "$pkg" | grep -q .; then
            CHANGED_SUB_PKGS+=("$pkg")
        fi
    done
fi

if [ ${#CHANGED_SUB_PKGS[@]} -gt 0 ]; then
    BUILD_CORE="true"
else
    BUILD_CORE="false"
fi

export CHANGED_SUB_PKGS
export BUILD_CORE