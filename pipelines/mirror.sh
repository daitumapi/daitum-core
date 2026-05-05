#!/bin/bash
# Snapshot mirror: Bitbucket → GitHub (1 commit per release)

set -euo pipefail

: "${GITHUB_REMOTE_URL:?Missing GITHUB_REMOTE_URL}"
: "${GITHUB_TOKEN:?Missing GITHUB_TOKEN}"
: "${NEW_VERSION:?Missing NEW_VERSION}"

TAG="v${NEW_VERSION}"

SRC_DIR="$(pwd)"
WORKDIR="$(mktemp -d)"

trap 'rm -rf "$WORKDIR"' EXIT

echo "Starting GitHub mirror for release ${TAG}"

git config --global user.email "developers@daitum.com"
git config --global user.name "Daitum Admin"

git clone "$GITHUB_REMOTE_URL" "$WORKDIR"
cd "$WORKDIR"

git checkout -B main || git switch -c main

find . -mindepth 1 -maxdepth 1 ! -name ".git" -exec rm -rf {} +
rsync -a --delete \
  --exclude '.git' \
  --exclude 'bitbucket-pipelines.yml' \
  --exclude 'version.env' \
  "$SRC_DIR"/ "$WORKDIR"/

git add -A

if git diff --cached --quiet; then
    echo "No changes to mirror."
    exit 0
fi

git commit -m "Release ${TAG}"
git push -f https://x-access-token:"${GITHUB_TOKEN}"@github.com/daitumapi/daitum-core.git HEAD:main

echo "Mirror complete: ${TAG}"