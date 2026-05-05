Data Types
==========

The Model Generator API provides a comprehensive type system for defining the data types of fields and named values.

DataType Enum
~~~~~~~~~~~~~

The :class:`~daitum_model.DataType` enumeration defines primitive data types and their array counterparts.

**Primitive Types:**

.. list-table::
   :header-rows: 1
   :widths: 20 80

   * - Type
     - Description
   * - ``INTEGER``
     - Whole numbers
   * - ``DECIMAL``
     - Floating-point numbers
   * - ``STRING``
     - Text values
   * - ``BOOLEAN``
     - True/false values
   * - ``DATE``
     - Date values (year, month, day)
   * - ``DATETIME``
     - Date and time values
   * - ``TIME``
     - Time values (hour, minute, second)

**Array Types:**

Each primitive type has a corresponding array type: ``INTEGER_ARRAY``, ``DECIMAL_ARRAY``, ``STRING_ARRAY``, ``BOOLEAN_ARRAY``, ``DATE_ARRAY``, ``DATETIME_ARRAY``, ``TIME_ARRAY``.

**Example:**

.. code-block:: python

    from daitum_model import DataType

    # Using primitive types
    products.add_data_field("product_id", DataType.INTEGER)
    products.add_data_field("name", DataType.STRING)
    products.add_data_field("price", DataType.DECIMAL)
    products.add_data_field("in_stock", DataType.BOOLEAN)
    products.add_data_field("created_date", DataType.DATE)

    # Using array types
    products.add_data_field("tags", DataType.STRING_ARRAY)
    products.add_data_field("monthly_sales", DataType.INTEGER_ARRAY)

**Type Conversion Methods:**

.. code-block:: python

    # Convert to array type
    int_array = DataType.INTEGER.to_array()  # Returns DataType.INTEGER_ARRAY

    # Convert from array type
    int_type = DataType.INTEGER_ARRAY.from_array()  # Returns DataType.INTEGER

    # Check if array type
    is_array = DataType.STRING_ARRAY.is_array()  # Returns True

.. autoclass:: daitum_model.DataType
    :members:
    :undoc-members:
    :show-inheritance:

ObjectDataType
~~~~~~~~~~~~~~

The :class:`~daitum_model.ObjectDataType` represents references to other tables, enabling relationships between tables.

**Key features:**

- References another table
- Can be singular or array
- Enables table relationships and lookups

**Example:**

.. code-block:: python

    from daitum_model import ObjectDataType

    # Create tables
    products = model.add_data_table("products", id_field="product_id")
    orders = model.add_data_table("orders", id_field="order_id")

    # Add a field that references the products table
    orders.add_data_field(
        "product_ref",
        ObjectDataType(products)
    )

    # Add a field that references multiple products (array)
    orders.add_data_field(
        "related_products",
        ObjectDataType(products, is_array=True)
    )

    # Access fields from referenced table in formulas
    orders.add_calculated_field(
        "product_name",
        DataType.STRING,
        formula=orders["product_ref"]["name"]
    )

.. autoclass:: daitum_model.ObjectDataType
    :members:
    :undoc-members:
    :show-inheritance:

MapDataType
~~~~~~~~~~~

The :class:`~daitum_model.MapDataType` represents key-value mappings where keys reference records in another table.

**Key features:**

- Maps table records to primitive values
- Useful for lookups and configurations
- Cannot be nested (values must be primitive types)

**Example:**

.. code-block:: python

    from daitum_model import MapDataType, DataType

    products = model.add_data_table("products", id_field="product_id")
    warehouses = model.add_data_table("warehouses", id_field="warehouse_id")

    # Add a map field: warehouse -> stock quantity
    products.add_data_field(
        "stock_by_warehouse",
        MapDataType(DataType.INTEGER, warehouses)
    )

    # Map from products to prices
    orders.add_data_field(
        "product_prices",
        MapDataType(DataType.DECIMAL, products)
    )

**Restrictions:**

- Value type must be a primitive :class:`~daitum_model.DataType` (not an array)
- Cannot nest maps or objects as values

.. autoclass:: daitum_model.MapDataType
    :members:
    :undoc-members:
    :show-inheritance:
