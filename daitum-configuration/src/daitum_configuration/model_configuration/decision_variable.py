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
:class:`DecisionVariable` — a single decision variable bound on a parameter or data field.
"""

from enum import Enum
from typing import Any

from daitum_model import Calculation, DataType, Parameter
from daitum_model.fields import DataField, Field
from daitum_model.tables import DataTable
from typeguard import typechecked

from daitum_configuration._buildable import Buildable


class DVType(Enum):
    """Domain of a decision variable.

    Values:
        RANGE: Discrete integer in a contiguous range.
        LIST: Discrete integer drawn from an allowed list.
        REAL: Continuous floating-point value.
    """

    RANGE = "range"
    LIST = "list"
    REAL = "real"


# pylint: disable=too-many-instance-attributes
# pylint: disable=too-many-branches,too-few-public-methods
@typechecked
class DecisionVariable(Buildable):
    """
    A single decision variable bound on a model named value or data field.

    Construct via :meth:`ModelConfiguration.add_decision_variable`; configure
    bounds and behaviour with the chained ``set_*`` methods.
    """

    _tracking_counter = 0

    def __init__(
        self,
        dv: Parameter | DataField,
        dv_table: DataTable | None = None,
        dv_type: DVType = DVType.RANGE,
    ):
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
        """Set the lower bound. Pass a literal/named value for a model-level DV, or a
        :class:`~daitum_model.fields.Field` for a per-row DV."""
        self._dv_min = dv_min
        if dv_min != 0:
            self._set_dv_min()
        return self

    def set_max(
        self, dv_max: int | None | float | Field | Calculation | Parameter
    ) -> "DecisionVariable":
        """Set the upper bound. ``None`` removes the bound. See :meth:`set_min` for the
        literal-vs-field rule."""
        if dv_max is not None:
            if isinstance(self._dv_min, (int, float)) and isinstance(dv_max, (int, float)):
                if self._dv_min > dv_max:
                    raise ValueError("dv_min_value can not be greater than dv_max_value")
        self._dv_max = dv_max
        if dv_max is not None:
            self._set_dv_max()
        return self

    def set_scale(self, scale: int | float) -> "DecisionVariable":
        """Set the granularity at which the solver explores this variable."""
        self._scale = scale
        return self

    def set_seed_source(self, seed_source: str) -> "DecisionVariable":
        """Set an identifier for the source used to seed this variable's initial value."""
        self._seed_source = seed_source
        return self

    def set_disabled(self, disabled: bool) -> "DecisionVariable":
        """Disable this variable, holding it at its seed value."""
        self._disabled = disabled
        return self

    def set_disabled_if_invalid(self, disabled_if_invalid: bool) -> "DecisionVariable":
        """Disable this variable automatically when its row fails validation."""
        self._disabled_if_invalid = disabled_if_invalid
        return self

    def _set_dv(self):
        if self._dv_table is None:
            if not isinstance(self._dv, Parameter):
                raise ValueError(f"Invalid input value {self._dv}")
            self._set_dv_parameter(self._dv)
        else:
            if not isinstance(self._dv, DataField):
                raise ValueError(f"Invalid input value {self._dv}")
            self._set_dv_field(self._dv, self._dv_table)

    def _set_dv_parameter(self, dv: Parameter):
        if self._dv_type in {DVType.RANGE, DVType.LIST}:
            if dv.to_data_type() != DataType.INTEGER:
                raise ValueError(f"{dv.to_data_type()} is not integer")

        if self._dv_type == DVType.REAL:
            if dv.to_data_type() != DataType.DECIMAL:
                raise ValueError(f"{dv.to_data_type()} is not decimal")

        self._dv_string = dv.to_string()

    def _set_dv_field(self, field: DataField, table: DataTable):
        table.get_field(field.id)

        if self._dv_type in {DVType.RANGE, DVType.LIST}:
            if field.to_data_type() != DataType.INTEGER:
                raise ValueError(f"{field.to_data_type()} is not integer")

        if self._dv_type == DVType.REAL:
            if field.to_data_type() != DataType.DECIMAL:
                raise ValueError(f"{field.to_data_type()} is not decimal")

        self._dv_string = f"{table.id}[{field.id}]"

    def _set_dv_min(self):
        if self._dv_table is None:
            if isinstance(self._dv_min, Field):
                raise ValueError(f"Invalid input value {self._dv_min}")
            self._set_dv_minmax_one_arg(self._dv_min, bound_type="min")
        else:
            if not isinstance(self._dv_min, Field):
                raise ValueError(f"Invalid input value {self._dv_min}")
            self._set_dv_minmax_two_args(self._dv_min, self._dv_table, bound_type="min")

    def _set_dv_max(self):
        if self._dv_table is None:
            if isinstance(self._dv_max, Field) or self._dv_max is None:
                raise ValueError(f"Invalid input value {self._dv_max}")
            self._set_dv_minmax_one_arg(self._dv_max, bound_type="max")
        else:
            if not isinstance(self._dv_max, Field):
                raise ValueError(f"Invalid input value {self._dv_max}")
            self._set_dv_minmax_two_args(self._dv_max, self._dv_table, bound_type="max")

    def _set_dv_minmax_one_arg(self, value: int | float | Parameter | Calculation, bound_type: str):
        if bound_type not in ("min", "max"):
            raise TypeError(f"bound_type must be 'min' or 'max', got {bound_type}")

        target_attr = f"_dv_{bound_type}_value"

        if self._dv_type in {DVType.RANGE, DVType.LIST}:
            if not isinstance(value, (int, float)):
                if value.to_data_type() != DataType.INTEGER:
                    raise ValueError(f"{value} is not integer")
                setattr(self, target_attr, value.to_string())
            else:
                if not isinstance(value, int):
                    raise ValueError(f"{value} is not integer")
                setattr(self, target_attr, value)

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
        if bound_type not in ("min", "max"):
            raise TypeError(f"bound must be 'min' or 'max', got {bound_type}")

        table.get_field(field.id)

        if self._dv_type in {DVType.RANGE, DVType.LIST}:
            if field.to_data_type() != DataType.INTEGER:
                raise ValueError(f"{field.to_data_type()} is not integer")

        elif self._dv_type == DVType.REAL:
            if field.to_data_type() != DataType.DECIMAL:
                raise ValueError(f"{field.to_data_type()} is not decimal")

        setattr(self, f"_dv_{bound_type}_value", f"{table.id}[{field.id}]")

    def build(self) -> dict[str, Any]:
        """Serialise to a JSON-compatible dict."""
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
