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
Filter component system for creating filterable data views.

This module provides a comprehensive filtering system that allows users to filter
data in views by applying comparison operators to field values. It supports defining
reusable filter configurations with customizable display options and default filters.

Main Components
---------------

**Filter Operators:**
    FilterOperator enum defines all supported comparison operators:

    Numeric/Date/Time/DateTime operators:
        - EQUAL, NOT_EQUAL: Equality comparisons
        - GREATER_THAN, LESS_THAN: Strict inequality comparisons
        - GREATER_THAN_OR_EQUAL, LESS_THAN_OR_EQUAL: Inclusive inequality comparisons
        - BETWEEN: Range queries (inclusive)

    Text operators:
        - EQUAL, NOT_EQUAL: Exact match comparisons
        - CONTAINS, NOT_CONTAINS: Substring searches
        - BEGINS_WITH, ENDS_WITH: Prefix/suffix matching

    Boolean operators:
        - EQUAL, NOT_EQUAL: Boolean value comparisons

    Object operators:
        - OBJECT_CONTAINS, OBJECT_NOT_CONTAINS: Membership tests for object references

**Default Filter Classes:**
    Pre-applied filters that automatically filter data when a view loads:

    - DefaultFilter: Abstract base class for all default filters
    - SingleValueDefaultFilter: Compares against one value (EQUAL, GREATER_THAN, etc.)
    - TwoValueDefaultFilter: Compares against two values (BETWEEN ranges)
    - MultiValueDefaultFilter: Compares against 3+ values (OBJECT_CONTAINS, etc.)

**Filter Configuration:**
    - FilterField: Defines a single filterable field with display configuration
    - FilterComponent: Main class for creating reusable filter configurations
    - FilterableView: Mixin class for views that support filtering

Operator Validation
-------------------
The module automatically validates that operators are compatible with field types:

- Numeric fields (INTEGER, DECIMAL): Support comparison and range operators
- Text fields (STRING): Support equality and text-search operators
- Boolean fields: Support only equality operators
- Date/Time/DateTime fields: Support comparison and range operators
- Object fields: Support only membership operators

Invalid operator/field combinations raise ValueError with helpful error messages.

Filter Architecture
-------------------
Filters are organized in a three-tier structure:

1. **FilterField**: Defines individual filterable fields
   - Specifies field to filter, display name, and formatting
   - For object fields, can specify which referenced field to display

2. **FilterComponent**: Groups filter fields and default filters
   - Defines source table for filter data
   - Contains list of available filter options (FilterField instances)
   - Contains list of default filters pre-applied on view load
   - Reusable across multiple views

3. **FilterableView**: Mixin for views supporting filters
   - Attaches a FilterComponent to enable filtering in a view

Examples
--------
Creating a basic filter component::

    # Create filter for a products table
    product_filter = FilterComponent(
        filter_name="product_filter",
        source_table=products_table
    )

    # Add filterable fields
    product_filter.add_filter_option(
        field=products_table.name_field,
        display_name="Product Name"
    )

    product_filter.add_filter_option(
        field=products_table.price_field,
        display_name="Price",
        display_format="${value}"
    )

Adding default filters::

    from daitum_ui.data import IntegerValue, StringValue

    # Single-value filter: Show only active products
    product_filter.add_default_filter(
        field=products_table.status_field,
        operator=FilterOperator.EQUAL,
        StringValue("active")
    )

    # Range filter: Show products between $10-$100
    product_filter.add_default_filter(
        field=products_table.price_field,
        operator=FilterOperator.BETWEEN,
        IntegerValue(10),
        IntegerValue(100)
    )

Filtering object fields::

    # Filter by category (object reference)
    product_filter.add_filter_option(
        field=products_table.category_field,
        display_name="Category",
        display_field=category_table.name_field  # Show category name, not ID
    )

    # Default filter: Show products in specific categories
    from daitum_ui.data import ObjectValue

    product_filter.add_default_filter(
        field=products_table.category_field,
        operator=FilterOperator.OBJECT_CONTAINS,
        ObjectValue(row_num=1),
        ObjectValue(row_num=3),
        ObjectValue(row_num=7)
    )

Attaching filter to a view::

    from daitum_ui.view import TabularView

    # Create a filterable view
    class ProductTableView(TabularView, FilterableView):
        def __init__(self):
            TabularView.__init__(self, ...)
            FilterableView.__init__(self, use_filter=product_filter)

Text search example::

    # Add text search on product descriptions
    product_filter.add_filter_option(
        field=products_table.description_field,
        display_name="Description"
    )

    # Default filter: Show products containing "organic"
    product_filter.add_default_filter(
        field=products_table.description_field,
        operator=FilterOperator.CONTAINS,
        StringValue("organic")
    )

Date range filtering::

    from daitum_ui.data import DateValue
    from datetime import date

    # Filter orders by date range
    order_filter.add_filter_option(
        field=orders_table.order_date_field,
        display_name="Order Date"
    )

    # Default: Show orders from last month
    order_filter.add_default_filter(
        field=orders_table.order_date_field,
        operator=FilterOperator.BETWEEN,
        DateValue(date(2024, 1, 1)),
        DateValue(date(2024, 1, 31))
    )
"""

from abc import ABC
from dataclasses import dataclass
from enum import Enum
from typing import Any

from daitum_model import Calculation, DataType, Field, ObjectDataType, Table
from typeguard import typechecked

from daitum_ui._buildable import Buildable
from daitum_ui.data import Value


class FilterOperator(Enum):
    """
    Defines the supported operators for filtering values.

    This enumeration contains all valid comparison operators that can be used
    when defining filter conditions in a FilterView. The available operators
    depend on the field type being filtered.

    Operators for numeric, date, time, and datetime fields:
        - EQUAL: Field equals the specified value
        - NOT_EQUAL: Field does not equal the specified value
        - GREATER_THAN: Field is greater than the specified value
        - LESS_THAN: Field is less than the specified value
        - GREATER_THAN_OR_EQUAL: Field is greater than or equal to the specified value
        - LESS_THAN_OR_EQUAL: Field is less than or equal to the specified value
        - BETWEEN: Field is between two specified values (inclusive)

    Operators for text fields:
        - EQUAL: Field exactly matches the specified value
        - NOT_EQUAL: Field does not match the specified value
        - CONTAINS: Field contains the specified substring
        - NOT_CONTAINS: Field does not contain the specified substring
        - BEGINS_WITH: Field starts with the specified value
        - ENDS_WITH: Field ends with the specified value

    Operators for boolean fields:
        - EQUAL: Field equals the specified boolean value
        - NOT_EQUAL: Field does not equal the specified boolean value

    Operators for object fields:
        - OBJECT_CONTAINS: Object field contains any of the specified values
        - OBJECT_NOT_CONTAINS: Object field does not contain any of the specified values
    """

    GREATER_THAN = "GREATER_THAN"
    LESS_THAN = "LESS_THAN"
    GREATER_THAN_OR_EQUAL = "GREATER_THAN_OR_EQUAL"
    LESS_THAN_OR_EQUAL = "LESS_THAN_OR_EQUAL"
    EQUAL = "EQUAL"
    NOT_EQUAL = "NOT_EQUAL"
    CONTAINS = "CONTAINS"
    NOT_CONTAINS = "NOT_CONTAINS"
    BEGINS_WITH = "BEGINS_WITH"
    ENDS_WITH = "ENDS_WITH"
    BETWEEN = "BETWEEN"
    OBJECT_CONTAINS = "OBJECT_CONTAINS"
    OBJECT_NOT_CONTAINS = "OBJECT_NOT_CONTAINS"


class _FilterType(Enum):
    NUMBER = "NUMBER"
    TEXT = "TEXT"
    BOOLEAN = "BOOLEAN"
    DATE = "DATE"
    TIME = "TIME"
    DATETIME = "DATETIME"
    OBJECT = "OBJECT"


_OPERATORS_BY_FILTER_TYPE: dict[_FilterType, set[FilterOperator]] = {
    _FilterType.NUMBER: {
        FilterOperator.EQUAL,
        FilterOperator.NOT_EQUAL,
        FilterOperator.GREATER_THAN,
        FilterOperator.LESS_THAN,
        FilterOperator.GREATER_THAN_OR_EQUAL,
        FilterOperator.LESS_THAN_OR_EQUAL,
        FilterOperator.BETWEEN,
    },
    _FilterType.TEXT: {
        FilterOperator.EQUAL,
        FilterOperator.NOT_EQUAL,
        FilterOperator.CONTAINS,
        FilterOperator.NOT_CONTAINS,
        FilterOperator.BEGINS_WITH,
        FilterOperator.ENDS_WITH,
    },
    _FilterType.BOOLEAN: {
        FilterOperator.EQUAL,
        FilterOperator.NOT_EQUAL,
    },
    _FilterType.DATE: {
        FilterOperator.EQUAL,
        FilterOperator.NOT_EQUAL,
        FilterOperator.GREATER_THAN,
        FilterOperator.LESS_THAN,
        FilterOperator.GREATER_THAN_OR_EQUAL,
        FilterOperator.LESS_THAN_OR_EQUAL,
        FilterOperator.BETWEEN,
    },
    _FilterType.TIME: {
        FilterOperator.EQUAL,
        FilterOperator.NOT_EQUAL,
        FilterOperator.GREATER_THAN,
        FilterOperator.LESS_THAN,
        FilterOperator.GREATER_THAN_OR_EQUAL,
        FilterOperator.LESS_THAN_OR_EQUAL,
        FilterOperator.BETWEEN,
    },
    _FilterType.DATETIME: {
        FilterOperator.EQUAL,
        FilterOperator.NOT_EQUAL,
        FilterOperator.GREATER_THAN,
        FilterOperator.LESS_THAN,
        FilterOperator.GREATER_THAN_OR_EQUAL,
        FilterOperator.LESS_THAN_OR_EQUAL,
        FilterOperator.BETWEEN,
    },
    _FilterType.OBJECT: {
        FilterOperator.OBJECT_CONTAINS,
        FilterOperator.OBJECT_NOT_CONTAINS,
    },
}

_SINGLE_VALUE_OPERATORS: set[FilterOperator] = {
    FilterOperator.GREATER_THAN,
    FilterOperator.LESS_THAN,
    FilterOperator.GREATER_THAN_OR_EQUAL,
    FilterOperator.LESS_THAN_OR_EQUAL,
    FilterOperator.EQUAL,
    FilterOperator.NOT_EQUAL,
    FilterOperator.CONTAINS,
    FilterOperator.NOT_CONTAINS,
    FilterOperator.BEGINS_WITH,
    FilterOperator.ENDS_WITH,
}

_TWO_VALUE_OPERATORS: set[FilterOperator] = {
    FilterOperator.BETWEEN,
}

_MULTI_VALUE_OPERATORS: set[FilterOperator] = {
    FilterOperator.OBJECT_CONTAINS,
    FilterOperator.OBJECT_NOT_CONTAINS,
}


def _filter_type_from_field(field: Field) -> _FilterType:  # noqa: PLR0911
    dt = getattr(field, "data_type", None)
    if dt is None:
        raise ValueError("Field has no data_type; cannot validate filter operator")

    number_types = [
        DataType.INTEGER,
        DataType.DECIMAL,
        DataType.INTEGER_ARRAY,
        DataType.DECIMAL_ARRAY,
    ]
    text_types = [DataType.STRING, DataType.STRING_ARRAY]
    bool_types = [DataType.BOOLEAN, DataType.BOOLEAN_ARRAY]
    date_types = [DataType.DATE, DataType.DATE_ARRAY]
    time_types = [DataType.TIME, DataType.TIME_ARRAY]
    datetime_types = [DataType.DATETIME, DataType.DATETIME_ARRAY]

    if isinstance(dt, ObjectDataType):
        return _FilterType.OBJECT
    if dt in number_types:
        return _FilterType.NUMBER
    if dt in text_types:
        return _FilterType.TEXT
    if dt in bool_types:
        return _FilterType.BOOLEAN
    if dt in date_types:
        return _FilterType.DATE
    if dt in time_types:
        return _FilterType.TIME
    if dt in datetime_types:
        return _FilterType.DATETIME

    raise ValueError(f"Unsupported field data_type for filtering: {dt!r}")


def _validate_operator_for_field(field: Field, operator: FilterOperator) -> None:
    filter_type = _filter_type_from_field(field)
    allowed = _OPERATORS_BY_FILTER_TYPE[filter_type]
    if operator not in allowed:
        allowed_str = ", ".join(op.value for op in sorted(allowed, key=lambda o: o.value))
        raise ValueError(
            f"Operator {operator.value} is not valid for field '{field.id}' "
            f"of type {filter_type.value}. Allowed: {allowed_str}"
        )


def _validate_default_filter_value_arity(operator: FilterOperator, value_count: int) -> None:
    if operator in _TWO_VALUE_OPERATORS:
        if value_count != 2:  # noqa: PLR2004
            raise ValueError(f"{operator.value} requires exactly 2 values (TwoValueDefaultFilter).")
        return

    if operator in _MULTI_VALUE_OPERATORS:
        if value_count < 1:  # noqa: PLR2004
            raise ValueError(
                f"{operator.value} requires 1 or more values (MultiValueDefaultFilter)."
            )
        return

    if operator in _SINGLE_VALUE_OPERATORS:
        if value_count != 1:  # noqa: PLR2004
            raise ValueError(
                f"{operator.value} requires exactly 1 value (SingleValueDefaultFilter)."
            )
        return

    raise ValueError(
        f"Unsupported/unmapped operator for default filter validation: {operator.value}"
    )


@typechecked
class DefaultFilter(ABC, Buildable):
    """
    Abstract base class for a default filter.

    A default filter defines an initial filtering rule that is applied
    when a view is first loaded. This allows you to pre-filter data
    before the user interacts with the filter UI.

    Attributes:
        field_name (str):
            The name of the field this filter applies to.
        operator (FilterOperator):
            The operator used to evaluate the filter.
    """

    def __init__(
        self,
        field: Field,
        operator: FilterOperator,
    ):
        """
        Initialize a default filter with a field and operator.

        Args:
            field (Field):
                The field to apply the filter to.
            operator (FilterOperator):
                The comparison operator to use for filtering.

        Raises:
            ValueError:
                If the operator is not valid for the field's data type.
        """
        _validate_operator_for_field(field, operator)
        self.field_name = field.id
        self.operator = operator


@typechecked
class SingleValueDefaultFilter(DefaultFilter):
    """
    A default filter that compares a field against a single value.

    This filter type is used for operators that compare against one value,
    such as EQUAL, NOT_EQUAL, GREATER_THAN, LESS_THAN, CONTAINS, etc.

    Attributes:
        field_name (str):
            The name of the field this filter applies to (inherited).
        operator (FilterOperator):
            The comparison operator (inherited).
        value (Value | Calculation):
            The value to compare against.
    """

    def __init__(
        self,
        field: Field,
        operator: FilterOperator,
        value: Value | Calculation,
    ):
        """
        Initialize a single-value default filter.

        Args:
            field (Field):
                The field to filter.
            operator (FilterOperator):
                The comparison operator. Must be a single-value operator like
                EQUAL, GREATER_THAN, CONTAINS, etc.
            value (Value | Calculation):
                The value to compare against.

        Raises:
            ValueError:
                If the operator is not valid for the field's data type, or
                if the operator requires a different number of values.
        """
        super().__init__(field, operator)
        self.value = value if isinstance(value, Value) else None
        self.value_reference = value.id if isinstance(value, Calculation) else None


@typechecked
class TwoValueDefaultFilter(DefaultFilter):
    """
    A default filter that compares a field against two values.

    This filter type is used for operators that require two values,
    such as BETWEEN (for range queries).

    Attributes:
        field_name (str):
            The name of the field this filter applies to (inherited).
        operator (FilterOperator):
            The comparison operator (inherited).
        first_value (Any):
            The first value. Can be a static Value or a dynamic Calculation.
        second_value (Any):
            The second value. Can be a static Value or a dynamic Calculation.
    """

    def __init__(
        self,
        field: Field,
        operator: FilterOperator,
        first_value: Value | Calculation,
        second_value: Value | Calculation,
    ):
        """
        Initialize a two-value default filter.

        Args:
            field (Field):
                The field to filter.
            operator (FilterOperator):
                The comparison operator. Typically BETWEEN.
            first_value (Value | Calculation):
                The first comparison value. Can be a static Value or a dynamic Calculation.
            second_value (Value | Calculation):
                The second comparison value. Can be a static Value or a dynamic Calculation.

        Raises:
            ValueError:
                If the operator is not valid for the field's data type, or
                if the operator requires a different number of values.
        """
        super().__init__(field, operator)

        self.first_value = first_value if isinstance(first_value, Value) else None
        self.first_value_reference = (
            first_value.id if isinstance(first_value, Calculation) else None
        )

        self.second_value = second_value if isinstance(second_value, Value) else None
        self.second_value_reference = (
            second_value.id if isinstance(second_value, Calculation) else None
        )


@typechecked
class MultiValueDefaultFilter(DefaultFilter):
    """
    A default filter that compares a field against multiple values.

    This filter type is used for operators that require three or more values,
    such as OBJECT_CONTAINS and OBJECT_NOT_CONTAINS (for checking membership
    in a collection).

    Attributes:
        field_name (str):
            The name of the field this filter applies to (inherited).
        operator (FilterOperator):
            The comparison operator (inherited).
        values (list[Any]):
            The list of values to compare against. Each value can be a static Value or
            a dynamic Calculation.
    """

    def __init__(self, field: Field, operator: FilterOperator, values: list[Value | Calculation]):
        """
        Initialize a multi-value default filter.

        Args:
            field (Field):
                The field to filter.
            operator (FilterOperator):
                The comparison operator. Typically OBJECT_CONTAINS or
                OBJECT_NOT_CONTAINS.
            values (list[Value | Calculation]):
                A list of values to compare against. Each value can be a static Value
                or a dynamic Calculation. Must contain at least 3 values.

        Raises:
            ValueError:
                If the operator is not valid for the field's data type, or
                if the operator requires a different number of values.
        """
        super().__init__(field, operator)
        value = values[0]
        if isinstance(value, Value):
            self.values: list[Any] | None = [v for v in values if isinstance(v, Value)]
            self.value_references = None
        else:
            self.values = None
            self.value_references = [v.id for v in values if isinstance(v, Calculation)]


@typechecked
class FilterField(Buildable):
    """
    Represents a single filter component used in a view filter definition.

    A filter component defines a field that users can filter on in the UI.
    It specifies how the field should be displayed and formatted.

    Attributes:
        field_name (str):
            The underlying field name used for filtering.
        display_name (str):
            The user-facing name shown in the UI.
        display_field (str | None):
            The field used for display purposes.
            Only applicable when the filter component refers to an object type
            and needs to resolve a column from a referenced table.
        display_format (str | None):
            The format string used to render the display value.
        include_in_search (bool):
            A boolean indicating if the field can be searched.
    """

    def __init__(
        self,
        field: Field,
        display_name: str | None,
        display_field: str | None = None,
        display_format: str | None = None,
        include_in_search: bool = False,
    ):
        """
        Initialize a filter component.

        Args:
            field (Field):
                The field that this filter component operates on.
            display_name (str | None):
                The name to display in the UI. If None, defaults to the field_id.
            display_field (str | None):
                For object-type fields, specifies which field from the referenced
                table to display. Default is None.
            display_format (str | None):
                A format string for rendering values (e.g., "${value}" for currency).
                Default is None.
            include_in_search (bool):
                A boolean indicating if the field can be searched. Default is False.
        """
        self.field_name = field.id
        self.display_name = display_name if display_name else field.id
        self.display_field = display_field
        self.display_format = display_format
        self.include_in_search = include_in_search


class HorizontalAlignment(Enum):
    """
    Defines horizontal alignment options for filter components.

    This enumeration specifies how filter content should be aligned
    horizontally within its container.

    Attributes:
        LEFT: Align content to the left edge.
        RIGHT: Align content to the right edge.
        JUSTIFIED: Distribute content evenly across the full width.
    """

    LEFT = "LEFT"
    RIGHT = "RIGHT"
    JUSTIFIED = "JUSTIFIED"


class SearchType(Enum):
    """
    Defines search behavior for filter search functionality.

    This enumeration specifies how search queries should match against
    filterable data.

    Attributes:
        CONTAINS_PHRASE: Match the exact phrase in the specified order.
            Example: "hello world" matches "hello world" but not "world hello".
        CONTAINS_WORDS: Match all words regardless of order. The query is split by spaces into
            individual words. A record matches if every word is contained within the field value,
            in any order and at any position.
            Example: "hello world" matches both "hello world" and "world hello".
    """

    CONTAINS_PHRASE = "CONTAINS_PHRASE"
    CONTAINS_WORDS = "CONTAINS_WORDS"


@dataclass
@typechecked
class SearchConfiguration(Buildable):
    """
    Configuration for search functionality in filter components.

    This class defines how search queries should be processed when users
    search through filter options.

    Attributes:
        search_type (SearchType):
            The type of search behavior to use (phrase or word matching).
    """

    search_type: SearchType


@typechecked
class FilterComponent(Buildable):
    """
    Defines a set of filters that can be applied to a view.

    A FilterComponent allows you to create a reusable filter configuration that can
    be attached to multiple views. It defines which fields can be filtered,
    how they should be displayed, and any default filter values that should
    be pre-applied.

    Attributes:
        filter_name (str):
            The unique name of this filter definition.
        source_table (str):
            The table from which filter values are sourced.
        filter_options (list[FilterComponent]):
            The list of available fields that users can filter on.
        default_filters (list[DefaultFilter]):
            The list of default filters automatically applied when the view loads.
        collapsible (bool):
            Whether the filter component can be collapsed/expanded in the UI.
        opacity (float):
            The opacity level of the filter component (0.0 to 1.0).
        search_configuration (SearchConfiguration | None):
            Configuration for search functionality, or None if search is not enabled.
        horizontal_alignment (HorizontalAlignment | None):
            The horizontal alignment of filter content, or None for default alignment.
        size (str | None):
            The CSS size of the element along the main axis.
            When the layout is horizontal, this represents the width.
            When the layout is vertical, this represents the height.
            Accepts any valid CSS size value (e.g., "100px", "50%", "auto").
    """

    def __init__(
        self,
        filter_name: str,
        source_table: Table,
        collapsible: bool = True,
        opacity: float = 1.0,
    ):
        """
        Initialize a FilterComponent.

        Args:
            filter_name (str):
                The unique identifier for this filter definition.
            source_table (Table):
                The table that provides the data to filter.
            collapsible (bool):
                Whether the filter can be collapsed/expanded. Defaults to True.
            opacity (float):
                The opacity level (0.0 to 1.0). Defaults to 1.0 (fully opaque).
        """
        self.filter_name = filter_name
        self.source_table = source_table.id
        self.filter_options: list[FilterField] = []
        self.default_filters: list[DefaultFilter] = []
        self.collapsible = collapsible
        self.opacity = opacity
        self.search_configuration: SearchConfiguration | None = None
        self.horizontal_alignment: HorizontalAlignment | None = None
        self.filter_only: bool = False
        self.search_only: bool = False
        self.default_collapsed: bool = True
        self.size: str | None = None

    def set_horizontal_alignment(
        self, horizontal_alignment: HorizontalAlignment
    ) -> "FilterComponent":
        """Sets the horizontal alignment of filter content."""
        self.horizontal_alignment = horizontal_alignment
        return self

    def set_filter_only(self, filter_only: bool) -> "FilterComponent":
        """Sets whether to render only the filter component."""
        self.filter_only = filter_only
        return self

    def set_search_only(self, search_only: bool) -> "FilterComponent":
        """Sets whether to render only the search component."""
        self.search_only = search_only
        return self

    def set_default_collapsed(self, default_collapsed: bool) -> "FilterComponent":
        """Configures whether the filter and search component are collapsed by default."""
        self.default_collapsed = default_collapsed
        return self

    def set_size(self, size: str) -> "FilterComponent":
        """Sets the CSS size of the element along the main axis."""
        self.size = size
        return self

    def add_filter_option(
        self,
        field: Field,
        display_name: str | None,
        display_field: str | None = None,
        display_format: str | None = None,
    ) -> None:
        """
        Add a filterable field to this filter view.

        This method registers a field as available for filtering in the UI.
        Users will be able to select this field and apply filter conditions to it.

        Args:
            field (Field):
                The field to make filterable.
            display_name (str | None):
                The name to show in the filter UI. If None, uses the field's ID.
            display_field (str | None):
                For object-type fields, specifies which field from the referenced
                table should be displayed to the user. Default is None.
            display_format (str | None):
                A format string for displaying values. Default is None.
        """
        filter_component = FilterField(field, display_name, display_field, display_format)
        self.filter_options.append(filter_component)

    def add_default_filter(
        self,
        field: Field,
        operator: FilterOperator,
        *values: Value | Calculation,
    ) -> None:
        """
        Add a default filter that is automatically applied when the view loads.

        Default filters pre-filter the data before the user interacts with the UI,
        allowing you to set initial filter conditions. The type of default filter
        created depends on the number of values provided and the operator used.

        Filter type selection:
            - 1 value  -> SingleValueDefaultFilter (for EQUAL, GREATER_THAN, etc.)
            - 2 values -> TwoValueDefaultFilter (for BETWEEN)
            - 3+ values -> MultiValueDefaultFilter (for OBJECT_CONTAINS, etc.)

        Args:
            field (Field):
                The field to apply the default filter to.
            operator (FilterOperator):
                The comparison operator to use. Must be valid for the field's
                data type.
            *values (Value | Calculation):
                One or more values to filter by. Each value can be a static Value
                or a dynamic Calculation. The number of values must match
                the operator's requirements.

        Raises:
            ValueError:
                If no values are provided, if the number of values doesn't match
                the operator's requirements, or if the operator is not valid for
                the field's data type.
        """
        if not values:
            raise ValueError("At least one value must be provided for a default filter")

        _validate_default_filter_value_arity(operator, len(values))

        if operator in _MULTI_VALUE_OPERATORS:
            default_filter: DefaultFilter = MultiValueDefaultFilter(
                field=field,
                operator=operator,
                values=list(values),
            )
        elif len(values) == 1:
            default_filter = SingleValueDefaultFilter(
                field=field,
                operator=operator,
                value=values[0],
            )

        elif len(values) == 2:  # noqa: PLR2004
            default_filter = TwoValueDefaultFilter(
                field=field,
                operator=operator,
                first_value=values[0],
                second_value=values[1],
            )
        else:
            default_filter = MultiValueDefaultFilter(
                field=field,
                operator=operator,
                values=list(values),
            )

        self.default_filters.append(default_filter)

    def set_search_configuration(self, search_type: SearchType):
        """
        Configure the search behavior for this filter component.

        This method sets how search queries should match against filter options.
        Once configured, users can search through available filter values using
        the specified search type.

        Args:
            search_type (SearchType):
                The type of search behavior to use. Use CONTAINS_PHRASE for
                exact phrase matching or CONTAINS_WORDS for flexible word matching.
        """
        self.search_configuration = SearchConfiguration(search_type)


@typechecked
class FilterableView(Buildable):
    """
    A mixin class for views that support filtering functionality.

    This class allows other view types (e.g., TabularView, CardView) to
    attach a FilterComponent, enabling users to filter the displayed data.

    Attributes:
        use_filter (str | None):
            The name of the FilterComponent to use for filtering, or None if
            no filter is attached.
        show_filter (str | None):
            The name of the FilterComponent to display in the UI, or None if
            no filter should be shown.
    """

    def __init__(self, use_filter: FilterComponent | None = None):
        """
        Initialize a filterable view.

        Args:
            use_filter (FilterComponent | None):
                The FilterComponent to attach to this view. If provided, the filter
                will be available in the UI for this view. Default is None.
        """
        self.use_filter = use_filter.filter_name if use_filter else None
        self.show_filter = use_filter.filter_name if use_filter else None
