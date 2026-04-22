"""
Verifies that each changed sub-package has a new CHANGELOG.md entry matching its current
version.

For each changed sub-package:
- Reads the current version from pyproject.toml.
- Checks that CHANGELOG.md contains a heading ## [X.Y.Z] for that version.
- If a prior tag exists, confirms the heading was absent at that tag (so it is genuinely new).

The root daitum-core package has no CHANGELOG and is not checked.

Exit code 1 if any required changelog entry is missing.
"""

import re
import subprocess
import sys
from pathlib import Path

VERSION_PATTERN = re.compile(r'^version\s*=\s*"(\d+\.\d+\.\d+)"', re.MULTILINE)

SUB_PACKAGES = [
    # (label, package_dir, pyproject_path, changelog_path)
    ("daitum-model", "daitum-model", "daitum-model/pyproject.toml", "daitum-model/CHANGELOG.md"),
    ("daitum-ui", "daitum-ui", "daitum-ui/pyproject.toml", "daitum-ui/CHANGELOG.md"),
    (
        "daitum-configuration",
        "daitum-configuration",
        "daitum-configuration/pyproject.toml",
        "daitum-configuration/CHANGELOG.md",
    ),
]


def read_version(pyproject_path: str) -> str:
    text = Path(pyproject_path).read_text()
    m = VERSION_PATTERN.search(text)
    if not m:
        raise ValueError(f"No version found in {pyproject_path}")
    return m.group(1)


def changelog_heading_pattern(version: str) -> re.Pattern[str]:
    escaped = re.escape(version)
    return re.compile(rf"^## \[{escaped}\]", re.MULTILINE)


def get_last_tag() -> str | None:
    result = subprocess.run(
        ["git", "tag", "--list", "v*", "--sort=-version:refname"],
        capture_output=True,
        text=True,
        check=False,
    )
    tags = [t.strip() for t in result.stdout.splitlines() if t.strip()]
    return tags[0] if tags else None


def has_changes(tag: str, package_dir: str) -> bool:
    result = subprocess.run(
        ["git", "diff", "--name-only", tag, "HEAD", "--", package_dir],
        capture_output=True,
        text=True,
        check=False,
    )
    return bool(result.stdout.strip())


def old_changelog_content(tag: str, changelog_path: str) -> str | None:
    result = subprocess.run(
        ["git", "show", f"{tag}:{changelog_path}"],
        capture_output=True,
        text=True,
        check=False,
    )
    return result.stdout if result.returncode == 0 else None


def main() -> None:
    last_tag = get_last_tag()
    failures: list[str] = []

    for label, package_dir, pyproject_path, changelog_path in SUB_PACKAGES:
        try:
            version = read_version(pyproject_path)
        except ValueError as e:
            print(f"FAIL  {label}: {e}")
            failures.append(label)
            continue

        if last_tag is not None and not has_changes(last_tag, package_dir):
            print(f"SKIP  {label}: no changes since {last_tag}")
            continue

        heading_re = changelog_heading_pattern(version)

        changelog_file = Path(changelog_path)
        if not changelog_file.exists():
            print(f"FAIL  {label}: {changelog_path} does not exist")
            failures.append(label)
            continue

        current_content = changelog_file.read_text()
        if not heading_re.search(current_content):
            print(f"FAIL  {label}: no '## [{version}]' heading found in {changelog_path}")
            failures.append(label)
            continue

        if last_tag is not None:
            old_content = old_changelog_content(last_tag, changelog_path)
            if old_content is not None and heading_re.search(old_content):
                print(
                    f"FAIL  {label}: '## [{version}]' heading already existed at {last_tag} — "
                    "bump the version and add a new changelog entry"
                )
                failures.append(label)
                continue

        print(f"PASS  {label}: ## [{version}] found in {changelog_path}")

    if failures:
        print(
            f"\n{len(failures)} package(s) failed changelog check: {', '.join(failures)}",
            file=sys.stderr,
        )
        sys.exit(1)


if __name__ == "__main__":
    main()
