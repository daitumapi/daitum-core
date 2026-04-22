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
Validator framework for field validation in model generator.

This module provides a flexible validation system that allows attaching validators
to fields, combining validators with logical operators, and generating validation
formulas with custom error messages.
"""

from __future__ import annotations

import operator
from abc import ABC, abstractmethod
from collections.abc import Callable, Sequence
from typing import Any

from typeguard import typechecked

from daitum_model import formulas

from .data_types import MapDataType, ObjectDataType
from .enums import SEVERITY_RANK, BoundType, DataType, Severity
from .fields import Field
from .formula import CONST, Formula, Operand
from .model import ModelBuilder
from .named_values import NamedValue
from .tables import Table


@typechecked
class Validator(ABC):
    """
    Abstract base class for field validators.

    Validators check field values and generate error messages when validation fails.
    They can be combined using AND (&) and OR (|) operators to create complex validation rules.
    """

    def __init__(
        self,
        severity: Severity,
        custom_message: Formula | str | None = None,
        custom_summary_message: str | None = None,
    ):
        """
        Initialize a validator.

        Args:
            severity: The severity level of validation failures (INFO, WARNING, ERROR, CRITICAL).
            custom_message: Optional custom error message to use instead of the default message.
            custom_summary_message: Optional custom summary error message to use instead
                of the default summary message.
        """
        self.severity = severity
        self.custom_message = custom_message
        self.custom_summary_message = custom_summary_message
        self.summary_message: str = ""

    @abstractmethod
    def invalid(self, field: Operand, table: Table | None) -> Formula:
        """
        Return a formula indicating whether the field is invalid
        """

    @abstractmethod
    def message(self, field: Operand, table: Table | None) -> Formula | str:
        """
        Return a formula containing the message if the field is invalid
        """

    @abstractmethod
    def get_summary_message(self, field: Operand) -> str:
        """
        Return a str containing the summary message if the field is invalid
        """

    def _attach_to_field(self, field: Field, table: Table):

        invalid = self.invalid(field, table)
        message = self.message(field, table)
        self.summary_message = self.get_summary_message(field)

        invalid_field_name = f"{field.id}__invalid__{self.severity.value}"
        message_field_name = f"{field.id}__message__{self.severity.value}"

        invalid_field = table.add_calculated_field(invalid_field_name, invalid)
        table.add_calculated_field(
            message_field_name, formulas.IF(invalid_field, message, formulas.BLANK())
        )

    def _attach_to_named_value(self, value: NamedValue, model: ModelBuilder):

        invalid = self.invalid(value, None)
        message = self.message(value, None)

        invalid_value_name = f"{value.id}__invalid__{self.severity.value}"
        message_value_name = f"{value.id}__message__{self.severity.value}"

        invalid_value = model.add_calculation(invalid_value_name, invalid)
        model.add_calculation(
            message_value_name, formulas.IF(invalid_value, message, formulas.BLANK())
        )

    def __and__(self, other: Validator) -> Validator:
        """
        Combine two validators with AND logic - both must be valid for result to be valid
        """
        return _AndValidator(self, other)

    def __or__(self, other: Validator) -> Validator:
        """
        Combine two validators with OR logic - either can be valid for result to be valid
        """
        return _OrValidator(self, other)


@typechecked
class _AndValidator(Validator):
    def __init__(self, left: Validator, right: Validator):
        severity = (
            left.severity
            if SEVERITY_RANK[left.severity] > SEVERITY_RANK[right.severity]
            else right.severity
        )
        super().__init__(severity)
        self.left = left
        self.right = right

    def invalid(self, field: Operand, table: Table | None) -> Formula:
        left_invalid = self.left.invalid(field, table)
        right_invalid = self.right.invalid(field, table)
        return formulas.OR(left_invalid, right_invalid)

    def message(self, field: Operand, table: Table | None) -> Formula | str:
        left_invalid = self.left.invalid(field, table)
        right_invalid = self.right.invalid(field, table)
        left_msg = self.left.message(field, table)
        right_msg = self.right.message(field, table)

        return formulas.IF(
            formulas.AND(left_invalid, right_invalid),
            left_msg + " and " + right_msg,
            formulas.IF(left_invalid, left_msg, right_msg),
        )

    def get_summary_message(self, field: Operand) -> str:

        left_summary_msg = self.left.get_summary_message(field)
        right_summary_msg = self.right.get_summary_message(field)

        return left_summary_msg + " and " + right_summary_msg


@typechecked
class _OrValidator(Validator):
    def __init__(self, left: Validator, right: Validator):
        severity = (
            left.severity
            if SEVERITY_RANK[left.severity] > SEVERITY_RANK[right.severity]
            else right.severity
        )
        super().__init__(severity)
        self.left = left
        self.right = right

    def invalid(self, field: Operand, table: Table | None) -> Formula:
        left_invalid = self.left.invalid(field, table)
        right_invalid = self.right.invalid(field, table)
        return formulas.AND(left_invalid, right_invalid)

    def message(self, field: Operand, table: Table | None) -> Formula | str:
        left_msg = self.left.message(field, table)
        right_msg = self.right.message(field, table)

        return left_msg + " or " + right_msg

    def get_summary_message(self, field: Operand) -> str:

        left_summary_msg = self.left.get_summary_message(field)
        right_summary_msg = self.right.get_summary_message(field)

        return left_summary_msg + " or " + right_summary_msg


@typechecked
class RangeValidator(Validator):  # pylint: disable=too-many-instance-attributes
    """
    Validator that checks if a field value is within a specified range.

    The range can have a min_value, max_value, or both bounds. Bounds can be static
    values or dynamic field references.
    """

    def __init__(
        self,
        severity: Severity,
        min_value: int | float | Operand | None,
        max_value: int | float | Operand | None,
    ):
        """
        Initialize a range validator.

        Args:
            severity: The severity level of validation failures.
            min_value: Minimum allowed value, or None for no lower bound.
            max_value: Maximum allowed value, or None for no upper bound.
        """
        super().__init__(severity)
        self._min_value = min_value
        self._max_value = max_value
        self.allow_blank: bool = False
        self.min_bound_type: BoundType = BoundType.INCLUSIVE
        self.max_bound_type: BoundType = BoundType.INCLUSIVE

    def set_allow_blank(self, allow_blank: bool) -> RangeValidator:
        """Sets whether blank values are considered valid."""
        self.allow_blank = allow_blank
        return self

    def set_custom_message(self, custom_message: Formula | str) -> RangeValidator:
        """Sets a custom error message to use instead of the default."""
        self.custom_message = custom_message
        return self

    def set_custom_summary_message(self, custom_summary_message: str) -> RangeValidator:
        """Sets a custom summary error message to use instead of the default."""
        self.custom_summary_message = custom_summary_message
        return self

    def set_min_bound_type(self, min_bound_type: BoundType) -> RangeValidator:
        """Sets whether the lower bound is inclusive or exclusive."""
        self.min_bound_type = min_bound_type
        return self

    def set_max_bound_type(self, max_bound_type: BoundType) -> RangeValidator:
        """Sets whether the upper bound is inclusive or exclusive."""
        self.max_bound_type = max_bound_type
        return self

    @property
    def min_value(self) -> int | float | Operand | None:
        """The minimum bound value, or None if unbounded."""
        return self._min_value

    @property
    def max_value(self) -> int | float | Operand | None:
        """The maximum bound value, or None if unbounded."""
        return self._max_value

    def _apply_cmp(
        self,
        cmp_fn: Callable,
        field: Operand,
        bound: Operand,
        is_array: bool,
        data_type: DataType | MapDataType,
    ):
        if is_array:
            return formulas.AND(cmp_fn(field, bound))
        if isinstance(data_type, MapDataType):
            return formulas.AND(cmp_fn(formulas.VALUES(field), bound))
        return cmp_fn(field, bound)

    @staticmethod
    def _convert_bound_value(
        value: Any, data_type: DataType | MapDataType | ObjectDataType
    ) -> Operand | None:
        if value is None or isinstance(value, Operand):
            return value
        primitive_type = data_type.data_type if isinstance(data_type, MapDataType) else data_type
        if isinstance(value, int) and primitive_type == DataType.DECIMAL:
            return CONST(float(value))
        return CONST(value)

    def _get_invalid(
        self,
        field: Operand,
        is_array: bool,
        data_type: DataType | MapDataType,
        non_array_data_type: DataType,
    ) -> Formula:
        min_value: Operand | None = self._convert_bound_value(self._min_value, non_array_data_type)
        max_value: Operand | None = self._convert_bound_value(self._max_value, non_array_data_type)
        min_invalid = False
        max_invalid = False
        if min_value is not None:
            if min_value.to_data_type() != non_array_data_type:
                raise ValueError(
                    f"The minimum data type {min_value.to_data_type()} "
                    f"is not compatible with the field data type {non_array_data_type}."
                )
            # inclusive: invalid when field < min  |  exclusive: invalid when field <= min
            min_cmp = operator.lt if self.min_bound_type == BoundType.INCLUSIVE else operator.le
            min_invalid = self._apply_cmp(min_cmp, field, min_value, is_array, data_type)

        if max_value is not None:
            if max_value.to_data_type() != non_array_data_type:
                raise ValueError(
                    f"The maximum data type {max_value.to_data_type()} "
                    f"is not compatible with the field data type {non_array_data_type}."
                )
            # inclusive: invalid when field > max  |  exclusive: invalid when field >= max
            max_cmp = operator.gt if self.max_bound_type == BoundType.INCLUSIVE else operator.ge
            max_invalid = self._apply_cmp(max_cmp, field, max_value, is_array, data_type)

        return formulas.OR(min_invalid, max_invalid)

    def invalid(self, field: Operand, table: Table | None) -> Formula:
        """
        Return a formula indicating whether the field value or named value is outside
        the valid range.

        Args:
            field: The field or name valued to validate.
            table: The table containing the field. Optional.

        Returns:
            A Formula that evaluates to True if the field or named value is invalid,
            False otherwise.
        """

        data_type = field.to_data_type()
        is_array = data_type.is_array()

        if isinstance(data_type, DataType):
            non_array_data_type = data_type.from_array() if is_array else data_type
        elif isinstance(data_type, MapDataType):
            non_array_data_type = data_type._data_type  # pylint: disable=protected-access
        else:
            raise NotImplementedError(
                f"Range validation is not supported for the data type {data_type}."
            )

        if isinstance(self._min_value, Field):
            if not table:
                raise ValueError("Table is not yet defined.")
            if self._min_value not in table.get_fields():
                raise ValueError(f"Field {self._min_value.id} not in table {table.id}")

        if isinstance(self._max_value, Field):
            if not table:
                raise ValueError("Table is not yet defined.")
            if self._max_value not in table.get_fields():
                raise ValueError(f"Field {self._max_value.id} not in table {table.id}")

        supported_types = [
            DataType.INTEGER,
            DataType.DECIMAL,
            DataType.TIME,
            DataType.DATE,
            DataType.DATETIME,
        ]

        if non_array_data_type not in supported_types:
            raise NotImplementedError(
                f"Range validation is not supported for the data type " f"{non_array_data_type}."
            )

        invalid = self._get_invalid(field, is_array, data_type, non_array_data_type)
        return formulas.IF(formulas.ISBLANK(field), formulas.NOT(self.allow_blank), invalid)

    def message(self, field: Operand, table: Table | None) -> Formula | str:
        """
        Return a formula containing the validation error message.

        Args:
            field: The field or named value to validate.
            table: The table containing the field. Optional.

        Returns:
            A Formula containing an error message describing the validation failure.
        """

        if isinstance(field, Field):
            id_string = field.id
        elif isinstance(field, NamedValue):
            id_string = field.id
        else:
            raise ValueError("Invalid field type.")

        if self.custom_message:
            return self.custom_message

        min_msg = None
        max_msg = None

        min_value: Operand | None = self._convert_bound_value(self._min_value, field.to_data_type())
        max_value: Operand | None = self._convert_bound_value(self._max_value, field.to_data_type())

        if min_value is not None:
            min_msg = f"{id_string} must be at least " + formulas.TEXT(min_value)

        if max_value is not None:
            max_msg = f"{id_string} can be up to " + formulas.TEXT(max_value)

        if min_value and max_value:
            return (
                f"{id_string} must be between "
                + formulas.TEXT(min_value)
                + " and "
                + formulas.TEXT(max_value)
            )
        if min_msg:
            return min_msg
        if max_msg:
            return max_msg
        return ""

    def get_summary_message(self, field: Operand) -> str:
        """
        Return a string of the summary error message.

        Args:
            field: The field or named value to validate.

        Returns:
            A string of the summary error message describing the validation failure.
        """

        if isinstance(field, Field):
            id_string = field.id
        elif isinstance(field, NamedValue):
            id_string = field.id
        else:
            raise ValueError("Invalid field type.")

        if self.custom_summary_message:
            return self.custom_summary_message

        return f"{id_string} values need attention"


@typechecked
class NonBlankValidator(Validator):
    """
    Validator that checks if a field is not blank.

    A field is considered blank if it is empty or null.
    """

    def invalid(self, field: Operand, table: Table | None) -> Formula:
        """
        Return a formula indicating whether the field or named value is null/empty.
        If array/map provided, performs the validation on each element of the array/map.

        Args:
            field: The field or named value to validate.
            table: The table containing the field. Optional.

        Returns:
            A Formula that evaluates to True if the field or named value is null/empty,
            False otherwise.
        """
        if field.to_data_type() == DataType.STRING:
            return formulas.OR(formulas.ISBLANK(field), field.equal_to(""))

        if field.to_data_type().is_array():
            return formulas.IF(formulas.ISBLANK(field), True, formulas.COUNTBLANKS(field) > 0)

        if isinstance(field.to_data_type(), MapDataType):
            return formulas.IF(
                formulas.ISBLANK(field), True, formulas.COUNTBLANKS(formulas.VALUES(field)) > 0
            )

        return formulas.ISBLANK(field)

    def message(self, field: Operand, table: Table | None) -> Formula | str:
        """
        Return a formula containing the validation error message.

        Args:
            field: The field or named value to validate.
            table: The table containing the field. Optional.

        Returns:
            A Formula containing an error message indicating the field or named value
            cannot be blank.
        """
        if isinstance(field, Field):
            id_string = field.id
        elif isinstance(field, NamedValue):
            id_string = field.id
        else:
            raise ValueError("Invalid field type.")

        if self.custom_message:
            return self.custom_message
        return f"{id_string} cannot be blank"

    def get_summary_message(self, field: Operand) -> str:
        """
        Return a string of the summary error message.

        Args:
            field: The field or named value to validate.

        Returns:
            A string of the summary error message describing the validation failure.
        """

        if isinstance(field, Field):
            id_string = field.id
        elif isinstance(field, NamedValue):
            id_string = field.id
        else:
            raise ValueError("Invalid field type.")

        if self.custom_summary_message:
            return self.custom_summary_message

        return f"Blank entries for {id_string}"


@typechecked
class UniqueValidator(Validator):
    """
    Validator that checks if a field value is unique within the table.

    A field is considered invalid if its value appears more than once across all rows
    in the table for that field.
    """

    def __init__(
        self,
        severity: Severity,
        allow_blank: bool = False,
        custom_message: Formula | str | None = None,
        custom_summary_message: str | None = None,
    ):
        """
        Initialize a Unique validator.

        Args:
            severity: The severity level of validation failures.
            allow_blank: Whether to allow blank values. Defaults to False.
            custom_message: Optional custom error message.
            custom_summary_message: Optional custom summary error message.
        """
        super().__init__(severity, custom_message, custom_summary_message)
        self.allow_blank = allow_blank

    def invalid(self, field: Operand, table: Table | None) -> Formula:
        """
        Return a formula indicating whether the field value is duplicated in the table.

        Args:
            field: The field to validate. Only valid for primitives.
            table: The table containing the field.

        Returns:
            A Formula that evaluates to True if the value appears more than once, False otherwise.
        """

        if not isinstance(field, Field):
            raise ValueError("Invalid field type.")

        if not table:
            raise ValueError("Table cannot be empty.")

        if field.to_data_type().is_array() or isinstance(field.to_data_type(), MapDataType):
            raise NotImplementedError(
                f"Unique validation is not supported for the data type {field.to_data_type()}."
            )
        unique_formula = formulas.COUNT(table[field.id], field).not_equal_to(1)
        return formulas.IF(formulas.ISBLANK(field), formulas.NOT(self.allow_blank), unique_formula)

    def message(self, field: Operand, table: Table | None) -> Formula | str:
        """
        Return a formula containing the validation error message.

        Args:
            field: The field to validate.
            table: The table containing the field.

        Returns:
            A Formula containing an error message indicating the field value must be unique.
        """

        if not isinstance(field, Field):
            raise ValueError("Invalid field type.")

        if not table:
            raise ValueError("Table cannot be empty.")

        if self.custom_message:
            return self.custom_message
        return f"The value {field.id} is not unique"

    def get_summary_message(self, field: Operand) -> str:
        """
        Return a string of the summary error message.

        Args:
            field: The field or named value to validate.

        Returns:
            A string of the summary error message describing the validation failure.
        """

        if isinstance(field, Field):
            id_string = field.id
        elif isinstance(field, NamedValue):
            id_string = field.id
        else:
            raise ValueError("Invalid field type.")

        if self.custom_summary_message:
            return self.custom_summary_message

        return f"Duplicate entries for {id_string}"


@typechecked
class ListValidator(Validator):
    """
    Validator that checks if a field value is within a provided set of allowed values.

    The list of allowed values must be non-empty and all values must share the same data type,
    consistent with the field being validated.
    """

    def __init__(
        self,
        severity: Severity,
        values: Sequence[Operand | str | int | float | bool],
        custom_message: Formula | str | None = None,
        custom_summary_message: str | None = None,
    ):
        """
        Initialize a list validator.

        Args:
            severity: The severity level of validation failures.
            values: The sequence of allowed values. Must be non-empty and all elements must share
                the same data type.
            custom_message: Optional custom error message.
            custom_summary_message: Optional custom summary error message.

        Raises:
            ValueError: If values is empty.
        """
        if not values:
            raise ValueError("values must not be empty")
        super().__init__(severity, custom_message, custom_summary_message)
        self.values = values

    def invalid(self, field: Operand, table: Table | None) -> Formula:
        """
        Return a formula indicating whether the field value or named value is not in the
        allowed set. If array/map provided, performs the validation on each element of
        the array/map.

        Args:
            field: The field or named value to validate.
            table: The table containing the field. Optional.

        Returns:
            A Formula that evaluates to True if the value is not in the allowed list,
            False otherwise.
        """

        allowed_values = formulas.ARRAY(False, *self.values)

        de_duplication_field: Formula | None = None
        if isinstance(field.to_data_type(), MapDataType):
            de_duplication_field = formulas.INTERSECTION(False, formulas.VALUES(field))

        if field.to_data_type().is_array():
            de_duplication_field = formulas.INTERSECTION(False, field)

        if de_duplication_field:
            intersection = formulas.INTERSECTION(False, allowed_values, de_duplication_field)
            return formulas.NOT(
                formulas.SIZE(intersection).equal_to(formulas.SIZE(de_duplication_field))
            )

        blank_type = type(formulas.BLANK())
        # pylint: disable=unidiomatic-typecheck
        if any(type(v) is blank_type for v in self.values):  # noqa: E721
            return formulas.IF(
                formulas.ISBLANK(field),
                False,
                formulas.NOT(formulas.CONTAINS(allowed_values, field)),
            )

        return formulas.IF(
            formulas.ISBLANK(field), True, formulas.NOT(formulas.CONTAINS(allowed_values, field))
        )

    def message(self, field: Operand, table: Table | None) -> Formula | str:
        """
        Return a formula containing the validation error message.

        Args:
            field: The field or named value to validate.
            table: The table containing the field. Optional.

        Returns:
            A Formula containing an error message listing the allowed values.
        """
        if isinstance(field, Field):
            id_string = field.id
        elif isinstance(field, NamedValue):
            id_string = field.id
        else:
            raise ValueError("Invalid field type.")

        if self.custom_message:
            return self.custom_message
        return f"Unexpected values for {id_string}"

    def get_summary_message(self, field: Operand) -> str:
        """
        Return a string of the summary error message.

        Args:
            field: The field or named value to validate.

        Returns:
            A string of the summary error message describing the validation failure.
        """

        if isinstance(field, Field):
            id_string = field.id
        elif isinstance(field, NamedValue):
            id_string = field.id
        else:
            raise ValueError("Invalid field type.")

        if self.custom_summary_message:
            return self.custom_summary_message

        return f"Unexpected values for {id_string}"


@typechecked
class LengthValidator(Validator):
    """
    Validator that checks if an array field has a specified number of elements.

    Only applicable to array fields. The field is considered invalid if its element count
    does not equal the expected length.
    """

    def __init__(
        self,
        severity: Severity,
        length: int,
        custom_message: Formula | str | None = None,
        custom_summary_message: str | None = None,
    ):
        """
        Initialize a length validator.

        Args:
            severity: The severity level of validation failures.
            length: The expected number of elements in the array. Must be non-negative.
            custom_message: Optional custom error message.
            custom_summary_message: Optional custom summary error message.

        Raises:
            ValueError: If length is negative.
        """
        if length < 0:
            raise ValueError("Length must be non-negative")
        super().__init__(severity, custom_message, custom_summary_message)
        self.length = length

    def invalid(self, field: Operand, table: Table | None) -> Formula:
        """
        Return a formula indicating whether the array length does not match the expected length.

        Args:
            field: The array field or named value to validate. Only valid for arrays.
            table: The table containing the field. Optional.

        Returns:
            A Formula that evaluates to True if the element count differs from the expected
            length, False otherwise.
        """

        if not field.to_data_type().is_array():
            raise NotImplementedError(
                f"Length validation is not supported for the data type {field.to_data_type()}."
            )

        return formulas.ROWS(field).not_equal_to(self.length)

    def message(self, field: Operand, table: Table | None) -> Formula | str:
        """
        Return a formula containing the validation error message.

        Args:
            field: The array field or named value to validate.
            table: The table containing the field. Optional.

        Returns:
            A Formula containing an error message stating the expected array length.
        """

        if isinstance(field, Field):
            id_string = field.id
        elif isinstance(field, NamedValue):
            id_string = field.id
        else:
            raise ValueError("Invalid field type.")

        if self.custom_message:
            return self.custom_message

        return f"{id_string} requires {self.length} entries"

    def get_summary_message(self, field: Operand) -> str:
        """
        Return a string of the summary error message.

        Args:
            field: The field or named value to validate.

        Returns:
            A string of the summary error message describing the validation failure.
        """

        if isinstance(field, Field):
            id_string = field.id
        elif isinstance(field, NamedValue):
            id_string = field.id
        else:
            raise ValueError("Invalid field type.")

        if self.custom_summary_message:
            return self.custom_summary_message

        return f"Incorrect number of entries for {id_string}"
