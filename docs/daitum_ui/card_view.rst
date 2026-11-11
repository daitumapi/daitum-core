Card View
=========

.. automodule:: daitum_ui.card_view
    :no-index:
    :members:
    :show-inheritance:

Examples
--------

Define a card template, then create and register a card view bound to a source
table:

.. code-block:: python

    # Define the data source
    products_table = Table("products")

    # Create a card template
    product_card = Card(
        title_field=Field("product_name", DataType.STRING),
        subtitle_field=Field("category", DataType.STRING),
        image_field=Field("image_url", DataType.STRING),
        description_field=Field("description", DataType.STRING),
    )

    # Create and register the card view
    builder = UiBuilder()
    card_view = builder.add_card_view(
        card_template=product_card,
        table=products_table,
        display_name="Product Catalog",
    )
