Table View
==========

The ``TableView`` displays data in a standard table layout. In most models you do not instantiate ``TableView`` directly.
Instead, create it via the :class:`~daitum_ui.ui_builder.UiBuilder` API, ``UiBuilder.add_table_view()``,
which registers the view with the UI definition and ensures it is included in the build output.

Basic Example
-------------

Define a data table with a few fields, add a table view for it, and
register the view in the UI's navigation:

.. code-block:: python

    from daitum_model import DataType, ModelBuilder
    from daitum_ui.ui_builder import UiBuilder

    model = ModelBuilder()

    # A simple data table with three fields.
    products = model.add_data_table("Products")
    products.set_key_column("Product Id")
    products.add_data_field("Product Id", DataType.INTEGER)
    products.add_data_field("Name", DataType.STRING)
    products.add_data_field("Price", DataType.DECIMAL)

    builder = UiBuilder()

    # Create the table view, then choose which columns it displays.
    products_view = builder.add_table_view(table=products, display_name="Products")
    products_view.add_field("Product Id")
    products_view.add_field("Name")
    products_view.add_field("Price").set_cell_style(display_format="$#,##0.00")

    # Register the view so it appears in the UI's navigation.
    nav_group = builder.add_navigation_group("Inputs")
    nav_group.add_view(products_view)

API Reference
-------------

.. autoclass:: daitum_ui.tabular.TableView
    :no-index:
    :members:
    :show-inheritance:

Supporting Types
----------------

.. autoclass:: daitum_ui.tabular.ViewField
    :no-index:
    :members:
    :show-inheritance:
