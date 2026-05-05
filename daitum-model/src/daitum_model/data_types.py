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
Module defining all data types used in the model:

- ``BaseDataType``: Structural protocol shared by every data type.
- ``DataType``: Enumeration of primitive and array data types.
- ``ObjectDataType``: A composite data type for referencing other tables.
- ``MapDataType``: A composite data type representing key-value maps in tables.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Sequence
from enum import Enum
from typing import Protocol, runtime_checkable

from typeguard import typechecked

from ._buildable import Buildable


@runtime_checkable
class BaseDataType(Protocol):
    """
    Structural protocol shared by every data type used in the model:
    :class:`DataType`, :class:`ObjectDataType` and :class:`MapDataType`.

    ``isinstance`` checks against this protocol are supported, but production
    code should generally prefer the concrete classes when behaviour differs.
    """

    def is_array(self) -> bool: ...

    def to_array(self) -> BaseDataType: ...

    def from_array(self) -> BaseDataType: ...

    def __str__(self) -> str: ...


class DataType(Enum):
    """
    Enumeration representing various data types.

    This enumeration is used to specify different data types that can be used in calculations,
    parameters, or tables within a model.
    """

    INTEGER = "INTEGER"
    """Integer data type."""

    DECIMAL = "DECIMAL"
    """Decimal data type."""

    STRING = "STRING"
    """String data type."""

    BOOLEAN = "BOOLEAN"
    """Boolean data type."""

    DATE = "DATE"
    """Date data type."""

    DATETIME = "DATETIME"
    """Datetime data type."""

    TIME = "TIME"
    """Time data type."""

    INTEGER_ARRAY = "INTEGER_ARRAY"
    """Array of `INTEGER` data type."""

    DECIMAL_ARRAY = "DECIMAL_ARRAY"
    """Array of `DECIMAL` data type."""

    STRING_ARRAY = "STRING_ARRAY"
    """Array of `STRING` data type."""

    BOOLEAN_ARRAY = "BOOLEAN_ARRAY"
    """Array of `BOOLEAN` data type."""

    DATE_ARRAY = "DATE_ARRAY"
    """Array of `DATE` data type."""

    DATETIME_ARRAY = "DATETIME_ARRAY"
    """Array of `DATETIME` data type."""

    TIME_ARRAY = "TIME_ARRAY"
    """Array of `TIME` data type."""

    NULL = "NULL"
    """ Used to identify BLANK() formulae. **Should never be used** explicitly in models """

    def is_array(self) -> bool:
        return self.name.endswith("_ARRAY")

    def to_array(self) -> DataType:
        if self.is_array():
            raise ValueError(f"Cannot convert {self.name} to an array type")
        return DataType[self.name + "_ARRAY"]

    def from_array(self) -> DataType:
        if not self.is_array():
            raise ValueError(f"Cannot convert {self.name} from an array type")
        return DataType[self.name.replace("_ARRAY", "")]

    def __str__(self) -> str:
        return self.name


PRIMITIVE_DATA_TYPES = {
    DataType.INTEGER,
    DataType.DECIMAL,
    DataType.STRING,
    DataType.BOOLEAN,
    DataType.DATE,
    DataType.DATETIME,
    DataType.TIME,
}


@typechecked
class _FieldBase(ABC):
    """
    Abstract base class for defining field representations.

    Attributes:
        id (str): The unique identifier for the field.
    """

    def __init__(self, id: str):
        self.id = id

    # pylint: disable=missing-function-docstring
    @abstractmethod
    def to_string(self) -> str:
        pass

    # pylint: disable=missing-function-docstring
    @abstractmethod
    def to_data_type(self) -> BaseDataType:
        pass


@typechecked
class _TableBase(ABC):
    """
    Abstract base class for defining table representations.
    """

    def __init__(self, id: str):
        self._id = id

    # pylint: disable=missing-function-docstring
    @abstractmethod
    def get_fields(self) -> Sequence[_FieldBase]:
        pass

    @property
    def id(self) -> str:
        return self._id


@typechecked
class ObjectDataType(Buildable):
    """
    A composite data type used for references to other Tables.
    """

    def __init__(self, source_table: _TableBase, is_array: bool = False):
        """
        Args:
            source_table: The table this data type references.
            is_array: Whether this is an ``OBJECT_ARRAY`` type rather than a singular ``OBJECT``.
        """
        self._source_table = source_table
        self._is_array = is_array
        self.type = "OBJECT_ARRAY" if is_array else "OBJECT"
        self.table_id = source_table.id

    def is_array(self) -> bool:
        """
        Checks if the data type is an array.

        Returns:
            bool: `True` if the data type is an array, otherwise `False`.
        """
        return self._is_array

    def to_array(self) -> ObjectDataType:
        """
        Converts an object type to an object array type.

        Returns:
            ObjectDataType: The array equivalent of the data type.

        Raises:
            ValueError: If the data type is already an array.
        """
        if not self._is_array:
            new_obj = ObjectDataType(self._source_table, True)
            return new_obj
        raise ValueError("Object data type is already an array")

    def from_array(self) -> ObjectDataType:
        """
        Converts an object array type to a singular object type.

        Returns:
            ObjectDataType: The singular (non-array) equivalent of the data type.

        Raises:
            ValueError: If the data type is not an array.
        """
        if self._is_array:
            new_obj = ObjectDataType(self._source_table, False)
            return new_obj
        raise ValueError("Object data type is not an array")

    def __eq__(self, other):
        if not isinstance(other, ObjectDataType):
            return False
        return self._is_array == other._is_array and self._source_table == other._source_table

    def __hash__(self):
        return hash((self._is_array, self._source_table.id))

    def __str__(self) -> str:
        return f"{self.type}:{self.table_id}"


@typechecked
class MapDataType(Buildable):
    """
    A composite data type used to represent key-value maps into other Tables.

    Raises:
        TypeError: If the data type is an array type.
    """

    def __init__(self, data_type: DataType, source_table: _TableBase):
        """
        Args:
            data_type: The primitive value type stored in the map. Must not be an array type.
            source_table: The table whose rows act as keys for this map.

        Raises:
            TypeError: If *data_type* is an array variant.
        """
        if data_type.is_array():
            raise TypeError(f"Cannot create map field with data type {data_type.name}")
        self._source_table = source_table
        self._data_type = data_type
        self.type = data_type.name + "_MAP"
        self.table_id = source_table.id

    @property
    def data_type(self) -> DataType:
        """
        The primitive data type of the map values.

        Returns:
            DataType: The primitive data type.
        """
        return self._data_type

    def is_array(self) -> bool:
        """
        Always False. Used to simplify array checks without having to check if a data type is a
        MapDataType

        Returns:
            bool: `False`
        """
        return False

    def to_array(self) -> MapDataType:
        """
        Always raises. Mirrors :meth:`from_array` so callers can treat ``MapDataType`` uniformly
        with ``DataType`` and ``ObjectDataType`` without isinstance checks.

        Raises:
            ValueError: Always — map data types cannot be arrays.
        """
        raise ValueError("Map data type cannot be an array")

    def from_array(self) -> MapDataType:
        """
        Always raises an error. Used to simplify array checks without having to check if a data
        type is a MapDataType.

        Returns:
            MapDataType: The singular (non-array) equivalent of the data type.

        Raises:
            ValueError: Always, as map data types cannot be an array.
        """
        raise ValueError("Map data type is not an array")

    def __eq__(self, other):
        if not isinstance(other, MapDataType):
            return False
        return (
            self._data_type == other._data_type and self._source_table.id == other._source_table.id
        )

    def __hash__(self):
        return hash((self._data_type, self._source_table.id))

    def __str__(self) -> str:
        return f"{self.type}:{self.table_id}"
