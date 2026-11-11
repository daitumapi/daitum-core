Filter Component
================

.. automodule:: daitum_ui.filter_component
    :no-index:
    :members:
    :show-inheritance:

Examples
--------

Creating a basic filter component:

.. code-block:: python

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

Adding default filters:

.. code-block:: python

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

Filtering object fields:

.. code-block:: python

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

Attaching filter to a view:

.. code-block:: python

    from daitum_ui.view import TabularView

    # Create a filterable view
    class ProductTableView(TabularView, FilterableView):
        def __init__(self):
            TabularView.__init__(self, ...)
            FilterableView.__init__(self, use_filter=product_filter)

Text search example:

.. code-block:: python

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

Date range filtering:

.. code-block:: python

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
