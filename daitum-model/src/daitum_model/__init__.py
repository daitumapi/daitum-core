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
daitum_model — Model and formula generation for the Daitum platform.

A **model** consists of three main parts: the **model definition**, **model configuration**, and
**UI definition**.

- The **model definition** contains tables, named values (calculations and parameters), and fields.
  These elements either contain static data or can be dynamic, such as calculations and calculated
  fields. Calculated fields and named values use a custom modelling language which is loosely based
  on Microsoft Excel.

- The **model configuration** specifies the optimisation parameters, such as decision
  variables, objectives, and constraints. It also sets up the algorithm configuration, data stores
  and data processors.

- The **UI definition** specifies the user interface components and functionality that
  will be visible when the model is uploaded to the platform.

This package covers the **model definition**, and also provides all formula functions via
:mod:`daitum_model.formulas`.

Usage::

    from daitum_model import ModelBuilder, DataType, formulas

    model = ModelBuilder()
    table = model.add_data_table("Jobs", key_column="ID")
    cost = table.add_data_field("Cost", DataType.DECIMAL)
    is_valid = formulas.NOT(formulas.ISBLANK(cost))
"""

from .data_types import BaseDataType, DataType, MapDataType, ObjectDataType
from .decoding import LoadError
from .derived_table import AggregationMethod, DerivedTable, SortDirection
from .fields import Field
from .formula import Formula
from .joined_table import JoinCondition, JoinedTable, JoinType
from .model import ModelBuilder
from .named_values import Calculation, Parameter
from .tables import Table
from .tracking import AutoCapture, Baseline, TrackingGroup
from .union_table import FoldedTable, UnionSource, UnionTable
from .validation import (
    CircularDependencyError,
    FieldReferenceError,
    MissingSourceFieldError,
    ModelValidationError,
    TableReferenceError,
    ValidationIssue,
    ValidationReport,
    validate_model,
)
from .validator import (
    LengthValidator,
    ListValidator,
    NonBlankValidator,
    RangeValidator,
    Severity,
    UniqueValidator,
    Validator,
)

__all__ = [
    "BaseDataType",
    "DataType",
    "ObjectDataType",
    "MapDataType",
    "SortDirection",
    "AggregationMethod",
    "JoinType",
    "Severity",
    "ModelBuilder",
    "Table",
    "Formula",
    "Field",
    "Calculation",
    "Parameter",
    "UnionSource",
    "FoldedTable",
    "FieldMapping",
    "Validator",
    "RangeValidator",
    "NonBlankValidator",
    "UniqueValidator",
    "ListValidator",
    "LengthValidator",
    "DerivedTable",
    "JoinedTable",
    "JoinCondition",
    "LoadError",
    "TrackingGroup",
    "Baseline",
    "AutoCapture",
    "validate_model",
    "ValidationReport",
    "ValidationIssue",
    "ModelValidationError",
    "CircularDependencyError",
    "FieldReferenceError",
    "MissingSourceFieldError",
    "TableReferenceError",
]

FieldMapping = UnionTable.FieldMapping

# Register every model decoder on the shared registries. Imported after __all__ to avoid
# partial-init cycles; the explicit call (not an import side effect) makes the wiring visible.
from . import _decoders  # noqa: E402

_decoders.register_all()
