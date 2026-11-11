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
Context variable system for runtime data management in views.

Provides the ``ContextVariable`` class and the ``CVType`` enum. A context
variable is a typed, uniquely identified runtime value within a view. Its
default may be a literal or calculated from a ``Parameter``/``Calculation``,
and it may hold a scalar or an array of values.

Example:
    >>> from daitum_ui import UiBuilder
    >>> from daitum_ui.context_variable import CVType
    >>> builder = UiBuilder()
    >>> selected_row = builder.add_context_variable(
    ...     id="selected_row_id",
    ...     type=CVType.INTEGER,
    ...     default_value=0,
    ... )
"""

from enum import Enum

from daitum_model import Calculation, Parameter
from typeguard import typechecked

from daitum_ui._buildable import Buildable


class CVType(Enum):
    """
    Enumeration of supported context variable data types.

    Members:
        INTEGER: Represents integer numeric values.
        DECIMAL: Represents floating-point numeric values.
        STRING: Represents textual values.
        BOOLEAN: Represents True/False logical values.
    """

    INTEGER = "INTEGER"
    DECIMAL = "DECIMAL"
    STRING = "STRING"
    BOOLEAN = "BOOLEAN"


@typechecked
class ContextVariable(Buildable):
    """
    Represents a variable available within the view.

    A ContextVariable defines a typed value that can be supplied,
    defaulted, or dynamically calculated at runtime.

    Attributes:
        id:
            Unique identifier of the context variable.
        type:
            The declared data type of the variable (e.g., INTEGER, DECIMAL, STRING, BOOLEAN).
        default_value:
            The optional default value to apply when no explicit value is
            provided.
        default_value_is_calculated:
            Indicates whether the default value is dynamically computed
            rather than a fixed literal.
        is_array:
            Whether this variable represents a list of values rather than
            a single scalar value.
    """

    def __init__(
        self,
        id: str,
        type: CVType,
        default_value: bool | int | float | str | Parameter | Calculation | None = None,
        is_array: bool = False,
    ):
        """
        Args:
            id: Unique identifier for this context variable.
            type: The data type of the variable value.
            default_value: Initial value, or a ``Parameter``/``Calculation`` whose ID is used
                as a calculated default.
            is_array: If ``True``, the variable holds a list of values rather than a scalar.
        """
        self.id = id
        self.type = type
        self.is_array = is_array

        self.default_value: bool | int | float | str | None = None
        if isinstance(default_value, Parameter | Calculation):
            self.default_value = default_value.id
            self.default_value_is_calculated = True
        else:
            self.default_value = default_value
            self.default_value_is_calculated = False
