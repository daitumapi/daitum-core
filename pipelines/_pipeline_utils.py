"""Shared helpers for the version and changelog CI checks."""

import re
import subprocess

VERSION_PATTERN = re.compile(r'^version\s*=\s*"(\d+\.\d+\.\d+)"', re.MULTILINE)


def get_last_tag() -> str | None:
    """Return the most recent release tag, or None if there is none.

    Uses ``git describe`` so the baseline matches pipelines/changed_packages.sh.
    """
    result = subprocess.run(
        ["git", "describe", "--tags", "--abbrev=0"],
        capture_output=True,
        text=True,
        check=False,
    )
    tag = result.stdout.strip()
    return tag if result.returncode == 0 and tag else None


def has_changes(tag: str, package_dir: str) -> bool:
    """Return True if any file under package_dir changed between tag and HEAD."""
    result = subprocess.run(
        ["git", "diff", "--name-only", tag, "HEAD", "--", package_dir],
        capture_output=True,
        text=True,
        check=False,
    )
    return bool(result.stdout.strip())
