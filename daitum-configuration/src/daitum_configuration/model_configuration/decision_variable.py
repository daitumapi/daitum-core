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
This module defines the `DecisionVariable` class used to represent decision variables
in optimisation models, supporting various types and validation mechanisms.

Classes:
    - DecisionVariable: Represents a configurable decision variable with bounds, scaling,
      and validation capabilities.
    - DVType: Enum defining supported decision variable types (RANGE, LIST, REAL).

Features:
    - Automatic unique ID generation for variable tracking
    - Support for both static values and dynamic field references
    - Type validation for values and bounds
    - Configurable scaling and initialisation options
    - Serialisation to optimisation-compatible dictionary format
"""

from enum import Enum

from daitum_model import Calculation, DataType, Parameter
from daitum_model.fields import DataField, Field
from daitum_model.tables import DataTable
from typeguard import typechecked


class DVType(Enum):
    """
    Enumeration of decision variable types.

    Members:
        RANGE: Integer range between min/max bounds (discrete values)
        LIST: Discrete set of possible values
        REAL: Continuous decimal values
    """

    RANGE = "range"
    LIST = "list"
    REAL = "real"


# pylint: disable=too-many-instance-attributes
# pylint: disable=too-many-branches,too-few-public-methods
@typechecked
class DecisionVariable:
    """
    Configurable decision variable for optimisation models.

    Supports multiple value types (static/dynamic) with validation and serialisation.
    Tracks instances with automatic unique IDs.

    Raises:
        ValueError: On invalid type combinations or reference errors

    Notes:
        - When dv_type is REAL, dv, dv_min and dv_max are decimal values
        - When dv_type is RANGE or LIST, dv, dv_min and dv_max are integer values
    """

    _tracking_counter = 0

    def __init__(
        self,
        dv: Parameter | DataField,
        dv_table: DataTable | None = None,
        dv_type: DVType = DVType.RANGE,
    ):
        """
        Initialises a new DecisionVariable instance.

        Args:
            dv (Parameter | DataField): Primary value or reference.
            dv_table (Optional[DataTable]): Associated table, if field-based.
            dv_type (DVType): Type of the decision variable (range, list, real).

        Raises:
            ValueError: On invalid types or inconsistent value assignments.
        """

        self._dv_string: str | None = None
        self._dv_min_value: int | float | str = 0
        self._dv_max_value: int | None | float | str = None
        self._tracking_id = DecisionVariable._tracking_counter
        DecisionVariable._tracking_counter += 1
        self._dv_type = dv_type
        self._scale: int | float = 0
        self._seed_source: str | None = None
        self._disabled: bool = False
        self._disabled_if_invalid: bool = False

        self._dv = dv
        self._dv_table = dv_table
        self._dv_min: float | int | Field | Calculation | Parameter = 0
        self._dv_max: int | None | float | Field | Calculation | Parameter = None

        self._set_dv()

    def set_min(self, dv_min: float | int | Field | Calculation | Parameter) -> "DecisionVariable":
        """
        Sets the minimum bound for the decision variable.

        Args:
            dv_min (float | int | Field | Calculation | Parameter): Minimum bound
                value or reference.

        Returns:
            DecisionVariable: self, for method chaining.
        """
        self._dv_min = dv_min
        if dv_min != 0:
            self._set_dv_min()
        return self

    def set_max(
        self, dv_max: int | None | float | Field | Calculation | Parameter
    ) -> "DecisionVariable":
        """
        Sets the maximum bound for the decision variable.

        Args:
            dv_max (int | None | float | Field | Calculation | Parameter): Maximum bound
                value or reference.

        Returns:
            DecisionVariable: self, for method chaining.
        """
        if dv_max is not None:
            if isinstance(self._dv_min, (int, float)) and isinstance(dv_max, (int, float)):
                if self._dv_min > dv_max:
                    raise ValueError("dv_min_value can not be greater than dv_max_value")
        self._dv_max = dv_max
        if dv_max is not None:
            self._set_dv_max()
        return self

    def set_scale(self, scale: int | float) -> "DecisionVariable":
        """
        Sets the optional scaling factor for the decision variable.

        Args:
            scale (int | float): Scaling factor.

        Returns:
            DecisionVariable: self, for method chaining.
        """
        self._scale = scale
        return self

    def set_seed_source(self, seed_source: str) -> "DecisionVariable":
        """
        Sets the source identifier for seeding/initialisation.

        Args:
            seed_source (str): Source identifier for seeding/initialisation.

        Returns:
            DecisionVariable: self, for method chaining.
        """
        self._seed_source = seed_source
        return self

    def set_disabled(self, disabled: bool) -> "DecisionVariable":
        """
        Marks the variable as disabled.

        Args:
            disabled (bool): If True, marks the variable as disabled.

        Returns:
            DecisionVariable: self, for method chaining.
        """
        self._disabled = disabled
        return self

    def set_disabled_if_invalid(self, disabled_if_invalid: bool) -> "DecisionVariable":
        """
        Sets whether the variable is automatically disabled if invalid.

        Args:
            disabled_if_invalid (bool): If True, automatically disables variable if invalid.

        Returns:
            DecisionVariable: self, for method chaining.
        """
        self._disabled_if_invalid = disabled_if_invalid
        return self

    def _set_dv(self):
        """
        Configures the main decision variable reference.

        Determines appropriate setter based on input type (parameter or field).

        Raises:
            ValueError: If inputs don't match expected type for variable type
                      Or if field references are invalid
        """
        if self._dv_table is None:
            if not isinstance(self._dv, Parameter):
                raise ValueError(f"Invalid input value {self._dv}")
            self._set_dv_parameter(self._dv)
        else:
            if not isinstance(self._dv, DataField):
                raise ValueError(f"Invalid input value {self._dv}")
            self._set_dv_field(self._dv, self._dv_table)

    def _set_dv_parameter(self, dv: Parameter):
        """
        Sets variable using a parameter reference.

        Args:
            dv: Parameter to use as decision variable

        Raises:
            ValueError: If parameter type doesn't match variable type
        """

        if self._dv_type in {DVType.RANGE, DVType.LIST}:
            if dv.to_data_type() != DataType.INTEGER:
                raise ValueError(f"{dv.to_data_type()} is not integer")

        if self._dv_type == DVType.REAL:
            if dv.to_data_type() != DataType.DECIMAL:
                raise ValueError(f"{dv.to_data_type()} is not decimal")

        self._dv_string = dv.to_string()

    def _set_dv_field(self, field: DataField, table: DataTable):
        """
        Sets variable using a table field reference.

        Args:
            field: DataField to reference
            table: Containing DataTable

        Raises:
            ValueError: If field not found or has incompatible type
        """

        table.get_field(field.id)

        if self._dv_type in {DVType.RANGE, DVType.LIST}:
            if field.to_data_type() != DataType.INTEGER:
                raise ValueError(f"{field.to_data_type()} is not integer")

        if self._dv_type == DVType.REAL:
            if field.to_data_type() != DataType.DECIMAL:
                raise ValueError(f"{field.to_data_type()} is not decimal")

        self._dv_string = f"{table.id}[{field.id}]"

    def _set_dv_min(self):
        """
        Configures the minimum bound for the variable.

        Determines appropriate setter based on input type.

        Raises:
            ValueError: On invalid input types or references
        """
        if self._dv_table is None:
            if isinstance(self._dv_min, Field):
                raise ValueError(f"Invalid input value {self._dv_min}")
            self._set_dv_minmax_one_arg(self._dv_min, bound_type="min")
        else:
            if not isinstance(self._dv_min, Field):
                raise ValueError(f"Invalid input value {self._dv_min}")
            self._set_dv_minmax_two_args(self._dv_min, self._dv_table, bound_type="min")

    def _set_dv_max(self):
        """
        Configures the maximum bound for the variable.

        Determines appropriate setter based on input type.

        Raises:
            ValueError: On invalid input types or references
        """
        if self._dv_table is None:
            if isinstance(self._dv_max, Field) or self._dv_max is None:
                raise ValueError(f"Invalid input value {self._dv_max}")
            self._set_dv_minmax_one_arg(self._dv_max, bound_type="max")
        else:
            if not isinstance(self._dv_max, Field):
                raise ValueError(f"Invalid input value {self._dv_max}")
            self._set_dv_minmax_two_args(self._dv_max, self._dv_table, bound_type="max")

    def _set_dv_minmax_one_arg(self, value: int | float | Parameter | Calculation, bound_type: str):
        """
        Sets a DV bound (min or max) from a single value or reference.

        Args:
            value: Value or dynamic reference.
            bound_type: Either "min" or "max" to specify which bound to set.

        Raises:
            ValueError: If type or format is invalid for the DV type.
            TypeError: If bound_type is not "min" or "max".
        """
        if bound_type not in ("min", "max"):
            raise TypeError(f"bound_type must be 'min' or 'max', got {bound_type}")

        target_attr = f"_dv_{bound_type}_value"

        # Integer validation for RANGE/LIST type
        if self._dv_type in {DVType.RANGE, DVType.LIST}:
            if not isinstance(value, (int, float)):
                if value.to_data_type() != DataType.INTEGER:
                    raise ValueError(f"{value} is not integer")
                setattr(self, target_attr, value.to_string())
            else:
                if not isinstance(value, int):
                    raise ValueError(f"{value} is not integer")
                setattr(self, target_attr, value)

        # Decimal validation for REAL type
        elif self._dv_type == DVType.REAL:
            if not isinstance(value, (int, float)):
                if value.to_data_type() != DataType.DECIMAL:
                    raise ValueError(f"{value} is not decimal")
                setattr(self, target_attr, value.to_string())
            else:
                if not isinstance(value, float):
                    raise ValueError(f"{value} is not decimal")
                setattr(self, target_attr, value)

    def _set_dv_minmax_two_args(self, field: Field, table: DataTable, bound_type: str):
        """
        Sets a DV bound (min or max) using a field and table reference.

        Args:
            field: Field object to reference.
            table: DataTable containing the field.
            bound_type: Which bound to set ("min" or "max").

        Raises:
            ValueError: If field is missing or has incompatible data type.
            TypeError: If bound is not "min" or "max".
        """
        if bound_type not in ("min", "max"):
            raise TypeError(f"bound must be 'min' or 'max', got {bound_type}")

        # Validate field exists in table
        table.get_field(field.id)

        # Validate field type matches DV type requirements
        if self._dv_type in {DVType.RANGE, DVType.LIST}:
            if field.to_data_type() != DataType.INTEGER:
                raise ValueError(f"{field.to_data_type()} is not integer")

        elif self._dv_type == DVType.REAL:
            if field.to_data_type() != DataType.DECIMAL:
                raise ValueError(f"{field.to_data_type()} is not decimal")

        # Set the appropriate bound
        setattr(self, f"_dv_{bound_type}_value", f"{table.id}[{field.id}]")

    def to_dict(self) -> dict:
        """
        Serialises the decision variable to a dictionary.

        Returns:
            dict: A dictionary with DV reference, bounds, type, and metadata.

        Raises:
            ValueError: If the main DV value is not yet set.
        """

        return {
            "cellReference": f"!!!{self._dv_string}",
            "trackingId": self._tracking_id,
            "specification": {
                "@type": self._dv_type.value,
                "minimumValue": (
                    self._dv_min_value if isinstance(self._dv_min_value, (int, float)) else None
                ),
                "maximumValue": (
                    self._dv_max_value if isinstance(self._dv_max_value, (int, float)) else None
                ),
                "scale": self._scale,
                "minimumValueReference": (
                    f"!!!{self._dv_min_value}" if isinstance(self._dv_min_value, str) else None
                ),
                "maximumValueReference": (
                    f"!!!{self._dv_max_value}" if isinstance(self._dv_max_value, str) else None
                ),
                "seedSource": self._seed_source,
            },
            "disabled": self._disabled,
            "disabledIfInvalid": self._disabled_if_invalid,
        }
