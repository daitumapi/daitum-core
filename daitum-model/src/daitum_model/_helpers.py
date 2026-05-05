# Copyright 2026 Daitum
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
Internal helpers for name validation and formula string manipulation.
"""

# mypy: ignore-errors
import re

_VALID_NAME_RE = re.compile(r"^[a-zA-Z_][a-zA-Z0-9_]*$")


def _validate_name(name: str, label: str) -> None:
    """
    Raise ``ValueError`` if *name* is not a valid identifier.

    Args:
        name: The name to validate.
        label: A human-readable label for the name (used in the error message).

    Raises:
        ValueError: If *name* contains characters other than alphanumerics/underscores,
            or begins with a digit.
    """
    if not _VALID_NAME_RE.match(name):
        raise ValueError(
            f"Invalid {label} '{name}': names may only contain alphanumeric characters and "
            "underscores, and must not begin with a number."
        )


def replace_field(formula: str, field: str, replacement: str) -> str:
    """
    Replace all occurrences of ``[field]`` with ``[replacement]`` in a formula string,
    leaving double-quoted string literals unchanged.

    Args:
        formula: The formula expression string.
        field: The field identifier to replace (without brackets).
        replacement: The replacement field identifier (without brackets).

    Returns:
        The formula string with all out-of-string occurrences substituted.
    """
    result = []
    pattern = re.compile(r'"[^"]*"')  # Match double-quoted strings

    last_index = 0
    for quoted in pattern.finditer(formula):
        start, end = quoted.span()

        # Process the section before the quoted string
        outside = formula[last_index:start]
        replaced_outside = re.sub(rf"\[{re.escape(field)}]", f"[{replacement}]", outside)
        result.append(replaced_outside)

        # Add the quoted string unchanged
        result.append(quoted.group(0))

        last_index = end

    # Process any formula after the last quoted string
    remaining = formula[last_index:]
    replaced_remaining = re.sub(rf"\[{re.escape(field)}]", f"[{replacement}]", remaining)
    result.append(replaced_remaining)

    return "".join(result)


def replace_named_value(formula: str, named_value: str, replacement: str) -> str:
    """
    Replace all bare occurrences of *named_value* with *replacement* in a formula string,
    skipping double-quoted string literals and bracket-enclosed field references.

    The match is word-boundary-aware: the identifier must not be immediately preceded by
    a letter, nor immediately followed by a letter or ``(``.

    Args:
        formula: The formula expression string.
        named_value: The named-value identifier to replace.
        replacement: The replacement identifier.

    Returns:
        The formula string with all eligible occurrences substituted.
    """
    skip_regions = []

    for m in re.finditer(r'"[^"\\]*(?:\\.[^"\\]*)*"', formula):
        skip_regions.append((m.start(), m.end()))

    for m in re.finditer(r"\[[^\[\]]*]", formula):
        skip_regions.append((m.start(), m.end()))

    # Merge overlapping/adjacent regions
    skip_regions.sort()
    merged = []
    for start, end in skip_regions:
        if merged and start <= merged[-1][1]:
            merged[-1] = (merged[-1][0], max(merged[-1][1], end))
        else:
            merged.append((start, end))

    def is_in_skipped(pos):
        return any(start <= pos < end for start, end in merged)

    pattern = re.compile(rf"(?<![A-Za-z]){re.escape(named_value)}(?![A-Za-z(])")

    result = []
    last_pos = 0

    for match in pattern.finditer(formula):
        start, end = match.span()
        if not is_in_skipped(start):
            result.append(formula[last_pos:start])
            result.append(replacement)
            last_pos = end

    result.append(formula[last_pos:])
    return "".join(result)
