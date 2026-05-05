Named Value View
================

Named value view components for the UI Generator framework.

This module provides the NamedValueView class, which enables displaying labeled
data elements in a clean, organized format. Named value views present key-value
pairs or named metrics in either horizontal or vertical layouts, making them ideal
for summary displays, dashboards, and information panels.

Named value views create simple yet effective displays where each item consists of
a label (name) paired with a corresponding value. The orientation control allows
flexible layout adaptation based on available space and design requirements.

Classes:
    - Orientation: Enum defining HORIZONTAL and VERTICAL layout options
    - NamedValueView: Container view managing named value display

Example:
    >>> # Define calculations for summary metrics
    >>> total_sales = Calculation("total_sales", DataType.DECIMAL)
    >>> order_count = Calculation("order_count", DataType.INTEGER)
    >>> avg_order = Calculation("avg_order_value", DataType.DECIMAL)
    >>>
    >>> # Create horizontal named value view for dashboard
    >>> builder = UiBuilder()
    >>> summary_view = builder.add_named_value_view(
    ...     display_name="Sales Summary",
    ...     orientation=Orientation.HORIZONTAL
    ... )
    >>>
    >>> # Add named values
    >>> summary_view.add_value(
    ...     ViewField(total_sales, display_name="Total Sales")
    ... )
    >>> summary_view.add_value(
    ...     ViewField(order_count, display_name="Orders")
    ... )
    >>> summary_view.add_value(
    ...     ViewField(avg_order, display_name="Average Order Value")
    ... )
    >>>
    >>> # Example: Vertical orientation for detailed view
    >>> details_view = builder.add_named_value_view(
    ...     display_name="Customer Details",
    ...     orientation=Orientation.VERTICAL
    ... )
    >>>
    >>> # Add customer details
    >>> details_view.add_value(
    ...     ViewField(customer_name, display_name="Name")
    ... )
    >>> details_view.add_value(
    ...     ViewField(customer_email, display_name="Email")
    ... )
    >>> details_view.add_value(
    ...     ViewField(member_since, display_name="Member Since")
    ... )

.. automodule:: daitum_ui.named_value_view
    :no-index:
    :members:
    :show-inheritance:
