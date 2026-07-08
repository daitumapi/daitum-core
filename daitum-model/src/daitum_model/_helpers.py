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
Internal helpers for name validation.
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
