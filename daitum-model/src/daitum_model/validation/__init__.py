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
Model-structure validation framework.

Detects structural problems in an assembled model — circular dependencies, references to
fields or tables that do not exist, and missing source fields — at build time, so an
invalid model cannot be serialised only to be rejected on upload to the platform.

This is distinct from the runtime data-quality :class:`~daitum_model.validator.Validator`
hierarchy (which generates ``__invalid__`` / ``__message__`` fields for end users).

Entry points: :func:`validate_model` (non-raising, returns a
:class:`ValidationReport`) and — from ``ModelBuilder`` — ``model.validate()`` /
``model.build()`` (which raises :class:`ModelValidationError`).
"""

from __future__ import annotations

from daitum_model.validation.engine import Rule, validate_model
from daitum_model.validation.errors import (
    CircularDependencyError,
    FieldReferenceError,
    MissingSourceFieldError,
    ModelValidationError,
    TableReferenceError,
    ValidationIssue,
)
from daitum_model.validation.report import ValidationReport

__all__ = [
    "validate_model",
    "Rule",
    "ValidationReport",
    "ValidationIssue",
    "ModelValidationError",
    "CircularDependencyError",
    "FieldReferenceError",
    "MissingSourceFieldError",
    "TableReferenceError",
]
