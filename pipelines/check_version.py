"""
Verifies that every package whose source has changed since the last git tag has had its
version bumped.

Rules:
- Root daitum-core must always have a higher version than at the last tag (or any valid
  semver if there is no tag yet).
- Each sub-package whose directory has changed files must also have a higher version.
- Sub-packages that have NOT changed may keep the same version.

Exit code 1 if any required version bump is missing.
"""

import re
import subprocess
import sys
from pathlib import Path

VERSION_PATTERN = re.compile(r'^version\s*=\s*"(\d+\.\d+\.\d+)"', re.MULTILINE)

PACKAGES = [
    ("daitum-model", "daitum-model", "daitum-model/pyproject.toml"),
    ("daitum-ui", "daitum-ui", "daitum-ui/pyproject.toml"),
    ("daitum-configuration", "daitum-configuration", "daitum-configuration/pyproject.toml"),
]


def parse_version(text: str) -> tuple[int, ...]:
    m = VERSION_PATTERN.search(text)
    if not m:
        raise ValueError("No version found")
    return tuple(int(x) for x in m.group(1).split("."))


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


def read_old_version(tag: str, pyproject_path: str) -> tuple[int, ...] | None:
    result = subprocess.run(
        ["git", "show", f"{tag}:{pyproject_path}"],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        return None
    try:
        return parse_version(result.stdout)
    except ValueError:
        return None


def main() -> None:
    last_tag = get_last_tag()
    failures: list[str] = []

    any_subpackage_changed = False
    for label, package_dir, pyproject_path in PACKAGES:
        current_text = Path(pyproject_path).read_text()
        try:
            current_version = parse_version(current_text)
        except ValueError:
            print(f"FAIL  {label}: could not read version from {pyproject_path}")
            failures.append(label)
            continue

        version_str = ".".join(str(x) for x in current_version)

        if last_tag is None:
            # No prior tag — any valid semver is acceptable.
            print(f"PASS  {label}: {version_str} (no prior tag)")
            continue

        changed = has_changes(last_tag, package_dir)

        if not changed:
            print(f"SKIP  {label}: no changes since {last_tag}")
            continue

        any_subpackage_changed = True

        old_version = read_old_version(last_tag, pyproject_path)
        if old_version is None:
            # Package didn't exist at the last tag — any version is fine.
            print(f"PASS  {label}: {version_str} (new package)")
            continue

        old_str = ".".join(str(x) for x in old_version)
        if current_version > old_version:
            print(f"PASS  {label}: {old_str} → {version_str}")
        else:
            print(
                f"FAIL  {label}: version {version_str} must be greater than {old_str} at {last_tag}"
            )
            failures.append(label)

    root_current = parse_version(Path("pyproject.toml").read_text())
    root_old = read_old_version(last_tag, "pyproject.toml")

    if root_old is not None:
        if any_subpackage_changed:
            if root_current <= root_old:
                print("FAIL  daitum-core: must bump when sub-packages changed")
                failures.append("daitum-core")
            else:
                print("PASS  daitum-core bumped correctly")
        else:
            print("SKIP  daitum-core: no sub-package changes")

    if failures:
        print(
            f"\n{len(failures)} package(s) failed version check: {', '.join(failures)}",
            file=sys.stderr,
        )
        sys.exit(1)


if __name__ == "__main__":
    main()
