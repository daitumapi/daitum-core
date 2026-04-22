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

# ------------------------------------------------------------
# Clone GitHub repo (supports empty repo)
# ------------------------------------------------------------

git clone "$GITHUB_REMOTE_URL" "$WORKDIR"
cd "$WORKDIR"

git checkout -B main || git switch -c main

# ------------------------------------------------------------
# Clean GitHub working tree completely (keep .git only)
# ------------------------------------------------------------

find . -mindepth 1 -maxdepth 1 ! -name ".git" -exec rm -rf {} +

# ------------------------------------------------------------
# Copy Bitbucket snapshot into GitHub working tree
# ------------------------------------------------------------

rsync -a --delete \
  --exclude '.git' \
  --exclude 'bitbucket-pipelines.yml' \
  --exclude 'version.env' \
  "$SRC_DIR"/ "$WORKDIR"/

# ------------------------------------------------------------
# Commit snapshot if changes exist
# ------------------------------------------------------------

git add -A

if git diff --cached --quiet; then
    echo "No changes to mirror."
    exit 0
fi

git commit -m "Release ${TAG}"

# ------------------------------------------------------------
# Force push single snapshot commit
# ------------------------------------------------------------

git push -f https://x-access-token:"${GITHUB_TOKEN}"@github.com/daitumapi/daitum-core.git HEAD:main

echo "Mirror complete: ${TAG}"