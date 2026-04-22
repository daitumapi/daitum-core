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

from dataclasses import dataclass, field
from enum import Enum

from typeguard import typechecked

from daitum_ui._buildable import Buildable, json_type_info
from daitum_ui.data import (
    Condition,
    DataValidationType,
    DefaultValueBehaviour,
    DefaultValueType,
    ValidationFlag,
    Value,
)


@dataclass
@typechecked
class EditOverride(Buildable):
    """
    Specifies an override for editing data that originates from a different source table

    This is used in situations where the visible table (the one being interacted with) does not
    directly contain the data to be edited. Instead, it references another table where the
    actual value resides.

    Attributes:
        target_reference_field (str):
            The field in the current (displayed) table that contains a reference (such as an object
            reference or ID) to the row or table that actually holds the editable data.

        target_field_id (str):
            The field ID within the referenced target (from `target_reference_field`) where the
            value should be written.

        map_key_field (Optional[str]):
            Optional. If the target field is a map-type field, this specifies the field in the
            current table that holds the key to be used for editing the correct entry within that
            map.
    """

    target_reference_field: str
    target_field_id: str
    map_key_field: str | None = None


@dataclass
@typechecked
class DefaultValueReference(Buildable):
    """
    Represents a reference to a default value used in UI fields, allowing for a reset icon
    to be shown so that the user can reset the changed value back to the reference value.

    Attributes:
        type (DefaultValueType):
            The source type of the default value (e.g., another field or named value).

        value (str):
            The identifier for the reference (e.g., field name or named value ID).

        behaviour (DefaultValueBehaviour):
            Determines how the default value behaves when overridden by the user.
            Defaults to `DEFAULT`.
    """

    type: DefaultValueType
    value: str
    behaviour: DefaultValueBehaviour = field(default=DefaultValueBehaviour.DEFAULT)


@dataclass
@typechecked
class DataValidationRule(Buildable):
    """
    Defines a validation rule for data entry in a UI field or cell, supporting
    list-based or range-based validation.

    Attributes:
        type (DataValidationType):
            The validation mode — list-based or range-based.

        flag (ValidationFlag):
            Specifies whether the range is inclusive or exclusive (applies only to RANGE type).

        reference_field (Optional[str]):
            Optional ID of a reference field used for comparison or list derivation.

        min_value (Optional[Value]):
            Minimum value allowed (applies to RANGE type).

        max_value (Optional[Value]):
            Maximum value allowed (applies to RANGE type).

        min_value_column (Optional[str]):
            Field or column name used to dynamically determine the minimum value.

        max_value_column (Optional[str]):
            Field or column name used to dynamically determine the maximum value.
    """

    type: DataValidationType
    flag: ValidationFlag | None = None
    reference_field: str | None = None
    min_value: Value | None = None
    max_value: Value | None = None
    min_value_column: str | None = None
    max_value_column: str | None = None


class ModelVariableType(Enum):
    FIELD = "FIELD"
    NAMED_VALUE = "NAMED_VALUE"
    CONTEXT_VARIABLE = "CONTEXT_VARIABLE"


@dataclass
@typechecked
class ModelVariable(Buildable):
    """
    Represents a model variable used for dynamic configuration or referencing.

    Attributes:
        type: The type of model variable (FIELD, NAMED_VALUE, CONTEXT_VARIABLE).
        value: The ID of the field, named value, or context variable this variable references.
    """

    type: ModelVariableType
    value: str


@json_type_info("modelVariableCondition")
@dataclass
@typechecked
class ModelVariableCondition(Condition):
    """
    A condition based on the value of a model variable.

    Attributes:
        model_variable: The model variable this condition evaluates.
    """

    model_variable: ModelVariable | None = None


@json_type_info("modelPermissionsCondition")
@dataclass
@typechecked
class ModelPermissionsCondition(Condition):
    """
    A condition based on user permission level.

    Attributes:
        is_advanced_user: If set, defines whether the user must (or must not) be an
        advanced user.
    """

    is_advanced_user: bool | None = None
