#!/bin/bash
# Reads the current daitum-core version from root pyproject.toml,
# creates a git tag vX.Y.Z, and pushes it to origin.
# Fails if the tag already exists locally or remotely.

set -e

: "${NEW_VERSION:?Missing NEW_VERSION}"

TAG="v${NEW_VERSION}"

if git tag --list "$TAG" | grep -q .; then
    echo "Error: tag $TAG already exists locally." >&2
    exit 0
fi

git config user.email "developers@daitum.com"
git config user.name "Daitum Admin"
git tag "$TAG"
git push origin "$TAG"
echo "Tagged and pushed $TAG"
