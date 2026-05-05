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
Data types and value wrappers for the UI Generator system.

This module provides a comprehensive type system for representing and validating
data values in UI definitions. It includes type-safe wrappers for primitive and
complex data types, along with configuration enums and filter modes.

Main Components
---------------

**Configuration Enums:**
    - DefaultValueType: Specifies the source of default values (FIELD or NAMED_VALUE)
    - DefaultValueBehaviour: Controls how defaults interact with user overrides
    - DataValidationType: Defines validation types (LIST or RANGE)
    - ValidationFlag: Specifies boundary inclusion/exclusion for range validation

**Value Classes:**
    All value classes extend the generic `Value[T]` base class and are serializable
    to JSON with type information.

    Primitive Values:
        - IntegerValue, StringValue, BooleanValue, DecimalValue
        - DateValue, TimeValue, DateTimeValue

    Array Values:
        - IntegerArrayValue, StringArrayValue, BooleanArrayValue, DecimalArrayValue
        - DateArrayValue, TimeArrayValue, DateTimeArrayValue

    Object References:
        - ObjectValue: References a single row by rowUid or stringKey
        - ObjectArrayValue: References multiple rows

    Map Values:
        Maps associate row identifiers with typed values:
        - IntegerMapValue, DecimalMapValue, StringMapValue, BooleanMapValue
        - DateMapValue, TimeMapValue, DateTimeMapValue

**Filter Classes:**
    - ObjectReferenceFilter: References source table/field for filtering
    - FilterMode: Base class for filter mode definitions
    - MatchRowFilterMode: Filters by matching row index from context variable
    - MatchFieldFilterMode: Filters by matching field value from context variable

**Base Classes:**
    - Value[T]: Generic base class for all value types
    - MapValue[T]: Generic base class for map types
    - Condition: Base class for conditional logic (supports negation)

Type Safety and Validation
---------------------------
All classes use @typechecked decorators and implement validation in __post_init__
or __init__ methods to ensure type correctness at runtime. Date/time values are
serialized to arrays for JSON compatibility ([year, month, day] format, etc.).

Examples
--------
Creating values::

    # Primitive value
    age = IntegerValue(25)

    # Array value
    tags = StringArrayValue(["python", "ui", "generator"])

    # Date value (serializes to [2024, 1, 15])
    start_date = DateValue(date(2024, 1, 15))

    # Object reference by row number
    user = ObjectValue(row_num=42)

    # Object reference by string key (requires table with id_field)
    user = ObjectValue(string_key="user_123", table=user_table)

    # Map value
    scores = IntegerMapValue({"row1": 100, "row2": 95})
"""

from dataclasses import dataclass, field
from datetime import date, datetime, time
from enum import Enum
from typing import Generic, TypeVar

from daitum_model import Table
from typeguard import typechecked

from daitum_ui._buildable import Buildable, json_type_info
from daitum_ui.context_variable import ContextVariable


class DefaultValueType(Enum):
    """
    Specifies the source type of the default value.

    Attributes:
        FIELD: The default value is derived from another field.
        NAMED_VALUE: The default value is specified as a named constant or parameter.
    """

    FIELD = "FIELD"
    NAMED_VALUE = "NAMED_VALUE"


class DefaultValueBehaviour(Enum):
    """
    Specifies how the default value behaves in relation to user-overridden values.

    Attributes:
        DEFAULT:
            If the current value differs from the reference value, a reset icon is shown to
            restore it.
        REFERENCE_WITH_OVERRIDE:
            The reference value is shown when the underlying value is blank.
            If a user enters a value, it overrides the reference, and a reset icon will
            clear it.
    """

    DEFAULT = "DEFAULT"
    REFERENCE_WITH_OVERRIDE = "REFERENCE_WITH_OVERRIDE"


class DataValidationType(Enum):
    """
    The type of data validation to apply.

    Attributes:
        LIST:
            The value must match an item in a predefined list (like a dropdown).
        RANGE:
            The value must fall within a minimum and maximum range.
    """

    LIST = "LIST"
    RANGE = "RANGE"


class ValidationFlag(Enum):
    """
    Specifies whether the range boundaries are inclusive or exclusive.

    Attributes:
        INCLUSIVE:
            The boundary values (min and max) are included as valid values.
        EXCLUSIVE:
            The boundary values are excluded from the valid range.
    """

    INCLUSIVE = "INCLUSIVE"
    EXCLUSIVE = "EXCLUSIVE"


T = TypeVar("T")


@dataclass
@typechecked
class Value(Generic[T], Buildable):
    """
    Base class for all value types in the UI generator.

    This generic class wraps primitive and complex values, providing a consistent
    interface for building and retrieving typed values.

    Attributes:
        value (T): The underlying value of generic type T.
    """

    value: T

    def get_value(self):
        """
        Retrieve the underlying value.

        Returns:
            T: The stored value of type T.
        """
        return self.value


@dataclass
@typechecked
@json_type_info("INTEGER")
class IntegerValue(Value[int]):
    """
    Represents a single integer value.

    This class wraps an integer value for use in the UI definition system.
    """

    pass


@dataclass
@typechecked
@json_type_info("STRING")
class StringValue(Value[str]):
    """
    Represents a single string value.

    This class wraps a string value for use in the UI definition system.
    """

    pass


@dataclass
@typechecked
@json_type_info("BOOLEAN")
class BooleanValue(Value[bool]):
    """
    Represents a single boolean value.

    This class wraps a boolean value for use in the UI definition system.
    """

    pass


@dataclass
@typechecked
@json_type_info("DECIMAL")
class DecimalValue(Value[float]):
    """
    Represents a single decimal (floating-point) value.

    This class wraps a float value for use in the UI definition system.
    """

    pass


@dataclass
@typechecked
@json_type_info("INTEGER_ARRAY")
class IntegerArrayValue(Value[list[int]]):
    """
    Represents an array of integer values.

    This class wraps a list of integers for use in the UI definition system.
    Validates that all items in the array are integers.

    Raises:
        TypeError: If the value is not a list or if any item is not an integer.
    """

    def __post_init__(self):
        """Validate that the value is a list of integers."""
        if not isinstance(self.value, list):
            raise TypeError(f"Expected list for IntArrayValue, got {type(self.value).__name__}")
        if not all(isinstance(item, int) for item in self.value):
            raise TypeError("All items in IntArrayValue must be integers")


@dataclass
@typechecked
@json_type_info("STRING_ARRAY")
class StringArrayValue(Value[list[str]]):
    """
    Represents an array of string values.

    This class wraps a list of strings for use in the UI definition system.
    Validates that all items in the array are strings.

    Raises:
        TypeError: If the value is not a list or if any item is not a string.
    """

    def __post_init__(self):
        """Validate that the value is a list of strings."""
        if not isinstance(self.value, list):
            raise TypeError(f"Expected list for StringArrayValue, got {type(self.value).__name__}")
        if not all(isinstance(item, str) for item in self.value):
            raise TypeError("All items in StringArrayValue must be strings")


@dataclass
@typechecked
@json_type_info("BOOLEAN_ARRAY")
class BooleanArrayValue(Value[list[bool]]):
    """
    Represents an array of boolean values.

    This class wraps a list of booleans for use in the UI definition system.
    Validates that all items in the array are booleans.

    Raises:
        TypeError: If the value is not a list or if any item is not a boolean.
    """

    def __post_init__(self):
        """Validate that the value is a list of booleans."""
        if not isinstance(self.value, list):
            raise TypeError(f"Expected list for BooleanArrayValue, got {type(self.value).__name__}")
        if not all(isinstance(item, bool) for item in self.value):
            raise TypeError("All items in BooleanArrayValue must be booleans")


@dataclass
@typechecked
@json_type_info("DECIMAL_ARRAY")
class DecimalArrayValue(Value[list[float]]):
    """
    Represents an array of decimal (floating-point) values.

    This class wraps a list of floats for use in the UI definition system.
    Validates that all items in the array are numeric (int or float).

    Raises:
        TypeError: If the value is not a list or if any item is not numeric.
    """

    def __post_init__(self):
        """Validate that the value is a list of numbers."""
        if not isinstance(self.value, list):
            raise TypeError(f"Expected list for DecimalArrayValue, got {type(self.value).__name__}")
        if not all(isinstance(item, (int, float)) for item in self.value):
            raise TypeError("All items in DecimalArrayValue must be numbers")


@dataclass
@typechecked
@json_type_info("DATE")
class DateValue(Value[date]):
    """
    Represents a single date value.

    This class wraps a Python date object for the UI definition system.
    """

    pass


@dataclass
@typechecked
@json_type_info("DATE_ARRAY")
class DateArrayValue(Value[list[date]]):
    """
    Represents an array of date values.

    This class wraps a list of Python date objects for the UI definition system.

    Raises:
        TypeError: If the value is not a list or if any item is not a date object.
    """

    def __post_init__(self):
        """Initialize a DateArrayValue with a list of date objects."""
        if not isinstance(self.value, list):
            raise TypeError(f"Expected list for DateArrayValue, got {type(self.value).__name__}")
        if not all(
            isinstance(item, date) and not isinstance(item, datetime) for item in self.value
        ):
            raise TypeError("All items in DateArrayValue must be date objects (not datetime)")


@dataclass
@typechecked
@json_type_info("TIME")
class TimeValue(Value[time]):
    """
    Represents a single time value.

    This class wraps a Python time object for the UI definition system.
    """

    pass


@dataclass
@typechecked
@json_type_info("TIME_ARRAY")
class TimeArrayValue(Value[list[time]]):
    """
    Represents an array of time values.

    This class wraps a list of Python time objects and serializes each as
    [hour, minute, second] for the UI definition system.

    Raises:
        TypeError: If the value is not a list or if any item is not a time object.
    """

    def __post_init__(self):
        """Initialize a TimeArrayValue with a list of time objects."""
        if not isinstance(self.value, list):
            raise TypeError(f"Expected list for TimeArrayValue, got {type(self.value).__name__}")
        if not all(isinstance(item, time) for item in self.value):
            raise TypeError("All items in TimeArrayValue must be time objects")


@dataclass
@typechecked
@json_type_info("DATETIME")
class DateTimeValue(Value[datetime]):
    """
    Represents a single datetime value.

    This class wraps a Python datetime object for the UI definition system.
    """

    pass


@dataclass
@typechecked
@json_type_info("DATETIME_ARRAY")
class DateTimeArrayValue(Value[list[datetime]]):
    """
    Represents an array of datetime values.

    This class wraps a list of Python datetime objects for the UI definition system.

    Raises:
        TypeError: If the value is not a list or if any item is not a datetime object.
    """

    def __post_init__(self):
        """Initialize a DateTimeArrayValue with a list of datetime objects."""
        if not isinstance(self.value, list):
            raise TypeError(
                f"Expected list for DateTimeArrayValue, got {type(self.value).__name__}"
            )
        if not all(isinstance(item, datetime) for item in self.value):
            raise TypeError("All items in DateTimeArrayValue must be datetime objects")


@typechecked
@json_type_info("OBJECT")
class ObjectValue(Value[dict]):
    """
    Represents an object row reference.

    Exactly one of (row_num, string_key) must be provided.

    - row_num -> serialises to: {"rowUid": <int>}
    - string_key -> serialises to: {"stringKey": <str>}
      Only valid if the referenced table has an id_field.
    """

    def __init__(
        self,
        table: Table,
        row_num: int | None = None,
        string_key: str | ContextVariable | None = None,
    ):
        if row_num is None and string_key is None:
            raise ValueError("Exactly one of 'row_num' or 'string_key' must be provided")

        if row_num is not None:
            super().__init__({"rowUid": row_num, "tableId": table.id})
        else:
            if table is None or table.id_field is None:
                raise ValueError("string_key is only valid when table has an id_field")
            if isinstance(string_key, ContextVariable):
                super().__init__({"stringKey": string_key.id, "tableId": table.id})
                self._string_key: str | None = string_key.id
            else:
                super().__init__({"stringKey": string_key, "tableId": table.id})
                self._string_key = string_key

        self._row_num = row_num


@typechecked
@json_type_info("OBJECT_ARRAY")
class ObjectArrayValue(Value[list[dict]]):
    """
    Represents an array of object row references.

    Each element must be either:

    - row_num -> {"rowUid": <int>}
    - string_key -> {"stringKey": <str>}
      Only valid if the referenced table has an id_field.
    """

    def __init__(
        self,
        objects: list[ObjectValue],
    ):
        if not objects:
            raise ValueError("ObjectArrayValue requires at least one ObjectValue")

        super().__init__([obj.get_value() for obj in objects])

        self._objects = objects


@dataclass
@typechecked
class MapValue(Value[dict[int, T]]):
    """
    Base class for all MAP values.

    Maps associate row identifiers (string keys) with primitive values of type T.
    This provides a dictionary-like structure for mapping rows to values in the UI.

    Attributes:
        value (dict[int, T]): The underlying dictionary mapping row IDs to values.
    """

    def add_mapping(self, row: int, value: T) -> None:
        """
        Add or update a row-to-value mapping.

        Args:
            row (int): The row identifier (key).
            value (T): The value to associate with this row.
        """
        self.value[row] = value


@dataclass
@typechecked
@json_type_info("INTEGER_MAP")
class IntegerMapValue(MapValue[int]):
    """
    Represents a map of row identifiers to integer values.

    This class wraps a dictionary with string keys and integer values
    for use in the UI definition system.

    Raises:
        TypeError: If the value is not a dict, if keys are not strings,
            or if values are not integers.
    """

    def __post_init__(self):
        """Validate that the value is a dict with string keys and integer values."""

        if not isinstance(self.value, dict):
            raise TypeError("IntegerMapValue expects a dict")

        for k, v in self.value.items():
            if not isinstance(k, str):
                raise TypeError("Map keys must be strings")
            if not isinstance(v, int):
                raise TypeError("All values in IntegerMapValue must be integers")


@dataclass
@typechecked
@json_type_info("DECIMAL_MAP")
class DecimalMapValue(MapValue[float]):
    """
    Represents a map of row identifiers to decimal (floating-point) values.

    This class wraps a dictionary with string keys and numeric (int or float) values
    for use in the UI definition system.

    Raises:
        TypeError: If the value is not a dict, if keys are not strings,
            or if values are not numeric.
    """

    def __post_init__(self):
        """Validate that the value is a dict with string keys and numeric values."""

        if not isinstance(self.value, dict):
            raise TypeError("DecimalMapValue expects a dict")

        for k, v in self.value.items():
            if not isinstance(k, str):
                raise TypeError("Map keys must be strings")
            if not isinstance(v, (int, float)):
                raise TypeError("All values in DecimalMapValue must be numbers")


@dataclass
@typechecked
@json_type_info("STRING_MAP")
class StringMapValue(MapValue[str]):
    """
    Represents a map of row identifiers to string values.

    This class wraps a dictionary with string keys and string values
    for use in the UI definition system.

    Raises:
        TypeError: If the value is not a dict, if keys are not strings,
            or if values are not strings.
    """

    def __post_init__(self):
        """Validate that the value is a dict with string keys and string values."""

        if not isinstance(self.value, dict):
            raise TypeError("StringMapValue expects a dict")

        for k, v in self.value.items():
            if not isinstance(k, str):
                raise TypeError("Map keys must be strings")
            if not isinstance(v, str):
                raise TypeError("All values in StringMapValue must be strings")


@dataclass
@typechecked
@json_type_info("BOOLEAN_MAP")
class BooleanMapValue(MapValue[bool]):
    """
    Represents a map of row identifiers to boolean values.

    This class wraps a dictionary with string keys and boolean values
    for use in the UI definition system.

    Raises:
        TypeError: If the value is not a dict, if keys are not strings,
            or if values are not booleans.
    """

    def __post_init__(self):
        """Validate that the value is a dict with string keys and boolean values."""

        if not isinstance(self.value, dict):
            raise TypeError("BooleanMapValue expects a dict")

        for k, v in self.value.items():
            if not isinstance(k, str):
                raise TypeError("Map keys must be strings")
            if not isinstance(v, bool):
                raise TypeError("All values in BooleanMapValue must be booleans")


@dataclass
@typechecked
@json_type_info("DATE_MAP")
class DateMapValue(MapValue[date]):
    """
    Represents a map of row identifiers to date values.

    This class wraps a dictionary with string keys and date values,
    for the UI definition system.

    Raises:
        TypeError: If the value is not a dict, if keys are not strings,
            or if values are not date objects (datetime objects are not allowed).
    """

    def __post_init__(self):
        """Initialize a DateMapValue with a dictionary of dates."""
        if not isinstance(self.value, dict):
            raise TypeError("DateMapValue expects a dict")

        for k, v in self.value.items():
            if not isinstance(k, str):
                raise TypeError("Map keys must be strings")
            if not isinstance(v, date) or isinstance(v, datetime):
                raise TypeError("All values in DateMapValue must be date objects (not datetime)")


@dataclass
@typechecked
@json_type_info("TIME_MAP")
class TimeMapValue(MapValue[time]):
    """
    Represents a map of row identifiers to time values.

    This class wraps a dictionary with string keys and time values for the UI definition system.

    Raises:
        TypeError: If the value is not a dict, if keys are not strings,
            or if values are not time objects.
    """

    def __post_init__(self):
        """Initialize a TimeMapValue with a dictionary of times."""
        if not isinstance(self.value, dict):
            raise TypeError("TimeMapValue expects a dict")

        for k, v in self.value.items():
            if not isinstance(k, str):
                raise TypeError("Map keys must be strings")
            if not isinstance(v, time):
                raise TypeError("All values in TimeMapValue must be time objects")


@dataclass
@typechecked
@json_type_info("DATETIME_MAP")
class DateTimeMapValue(MapValue[datetime]):
    """
    Represents a map of row identifiers to datetime values.

    This class wraps a dictionary with string keys and datetime values,
    for the UI definition system.

    Raises:
        TypeError: If the value is not a dict, if keys are not strings,
            or if values are not datetime objects.
    """

    def __post_init__(self):
        """Initialize a DateTimeMapValue with a dictionary of datetimes."""
        if not isinstance(self.value, dict):
            raise TypeError("DateTimeMapValue expects a dict")

        for k, v in self.value.items():
            if not isinstance(k, str):
                raise TypeError("Map keys must be strings")
            if not isinstance(v, datetime):
                raise TypeError("All values in DateTimeMapValue must be datetime objects")


@dataclass
@typechecked
class ObjectReferenceFilter(Buildable):
    """
    Represents a reference to a source table and field used in filtering.

    Attributes:
        source_table (str): The name of the source table.
        source_field (str): The field in the source table.
    """

    source_table: str
    source_field: str


@dataclass
@typechecked
class FilterMode(Buildable):
    """
    Base class for defining filter modes in a UI model.

    Attributes:
        context_variable_ids (Dict[str, str]):
            A mapping of context variable names to their associated IDs.

        object_reference_filter (Optional[ObjectReferenceFilter]):
            When populated, specifies an external table and field to use as
            the source of the filter value.
    """

    context_variable_ids: dict[str, str] = field(default_factory=dict)
    object_reference_filter: ObjectReferenceFilter | None = None


@json_type_info("MATCH_ROW_INDEX")
@dataclass
@typechecked
class MatchRowFilterMode(FilterMode):
    """
    Filter mode that matches rows based on a context variable identifying the row index.

    This filter mode uses a context variable containing a row index to filter
    and display only the matching row.
    """

    def set_filter_row(self, filter_row: str):
        """
        Set the context variable used to identify the row for filtering.

        Args:
            filter_row (str): The ID of the context variable containing the row index.
        """
        self.context_variable_ids["filterRow"] = filter_row


@json_type_info("MATCH_FIELD_VALUE")
@dataclass
@typechecked
class MatchFieldFilterMode(FilterMode):
    """
    Filter mode that matches rows based on a comparison between a context variable value
    and a target field value in the table.

    This filter mode compares a context variable's value against a specified field
    in the table, displaying only rows where the field value matches.

    Attributes:
        filter_target_field (Optional[str]):
            The field in the target table to compare against.
    """

    filter_target_field: str | None = None

    def set_filter_source_value(self, filter_source_value: str):
        """
        Set the context variable that provides the source value for filtering.

        Args:
            filter_source_value (str): The ID of the context variable containing
                the value to match against the target field.
        """
        self.context_variable_ids["filterSourceValue"] = filter_source_value


@dataclass
@typechecked
class Condition(Buildable):
    """
    Base condition class. Supports logical negation.

    Attributes:
        negate: If True, the result of the condition will be logically negated.
    """

    negate: bool = False
