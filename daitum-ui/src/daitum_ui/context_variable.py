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

This module provides the ContextVariable class, which represents typed variables
that exist within the runtime context of a view. Context variables enable dynamic
data flow, parameter passing, and state management across UI components.

Main Components
---------------

**Data Types:**
    CVType enum defines supported data types:

    - INTEGER: Whole numbers
    - DECIMAL: Floating-point numbers
    - STRING: Text values
    - BOOLEAN: True/False logical values

**Core Class:**
    - ContextVariable: Typed variable with optional default values

Default Values
--------------

Context variables support two types of default values:

**Literal Defaults:**
    Fixed values assigned at initialization (e.g., 0, "default", True)

    - Use for static initial values
    - Set once when variable is created
    - default_value_is_calculated = False

**Calculated Defaults:**
    Dynamic values computed from Parameters or Calculations

    - Use for values derived from other data sources
    - Recomputed when dependencies change
    - default_value_is_calculated = True

Array Variables
---------------

Context variables can represent either:

- **Scalar values** (is_array=False): Single value of the specified type
- **Array values** (is_array=True): List of values of the specified type

Variable Identification
-----------------------

Each ContextVariable has a unique ID used to:

- Reference the variable in UI bindings
- Access the variable in event handlers
- Pass the variable between components
- Store and retrieve values in runtime context

Use Cases
---------

**User Selection Tracking:**
    Track which item a user has selected for detail viewing or editing

**Filter State:**
    Store current filter criteria for dynamic data filtering

**Modal Dialog State:**
    Pass data to/from modal dialogs (e.g., edit form data)

**Computed UI State:**
    Store calculated values used for conditional rendering

**Multi-Step Workflows:**
    Maintain state across multiple views in a wizard or workflow

**Dynamic Validation:**
    Store validation state or error messages

Examples
--------
Creating a simple context variable::

    from daitum_ui import UiBuilder
    from daitum_ui.context_variable import CVType

    # Create builder
    builder = UiBuilder()

    # Selected row ID (integer)
    selected_row = builder.add_context_variable(
        id="selected_row_id",
        type=CVType.INTEGER,
        default_value=0
    )

Creating a context variable with calculated default::

    from daitum_model import Parameter

    # User role parameter
    user_role_param = Parameter(...)

    # Is admin flag derived from parameter
    is_admin = builder.add_context_variable(
        id="is_admin_flag",
        type=CVType.BOOLEAN,
        default_value=user_role_param  # Calculated from parameter
    )

Creating array context variables::

    # List of selected item IDs
    selected_items = builder.add_context_variable(
        id="selected_item_ids",
        type=CVType.INTEGER,
        is_array=True
    )

    # List of filter tags
    active_tags = builder.add_context_variable(
        id="active_filter_tags",
        type=CVType.STRING,
        is_array=True
    )

String context variables for state::

    # Current view mode
    view_mode = builder.add_context_variable(
        id="current_view_mode",
        type=CVType.STRING,
        default_value="grid"  # Default to grid view
    )

    # Search query
    search_query = builder.add_context_variable(
        id="search_text",
        type=CVType.STRING,
        default_value=""  # Empty by default
    )

Decimal context variables for numeric calculations::

    # Calculated total price
    total_price = builder.add_context_variable(
        id="cart_total",
        type=CVType.DECIMAL,
        default_value=0.0
    )

    # User-entered discount percentage
    discount_percentage = builder.add_context_variable(
        id="discount_pct",
        type=CVType.DECIMAL,
        default_value=10.0
    )

Boolean context variables for flags::

    # Show/hide detail panel
    show_details = builder.add_context_variable(
        id="show_detail_panel",
        type=CVType.BOOLEAN,
        default_value=False
    )

    # Edit mode toggle
    is_editing = builder.add_context_variable(
        id="is_edit_mode",
        type=CVType.BOOLEAN,
        default_value=False
    )

Using with calculations::

    from daitum_model import Calculation

    # Calculation that computes if user has premium access
    has_premium_calc = Calculation(...)

    # Context variable using calculated default
    show_premium_features = builder.add_context_variable(
        id="show_premium_ui",
        type=CVType.BOOLEAN,
        default_value=has_premium_calc
    )

Workflow state management::

    # Current step in multi-step form (0-indexed)
    current_step = builder.add_context_variable(
        id="wizard_step",
        type=CVType.INTEGER,
        default_value=0
    )

    # Completed steps array
    completed_steps = builder.add_context_variable(
        id="completed_wizard_steps",
        type=CVType.INTEGER,
        is_array=True
    )
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
