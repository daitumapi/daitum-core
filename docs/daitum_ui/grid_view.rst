Grid View
=========

Grid views arrange content in a two-dimensional grid of rows and columns.

They are commonly used for dashboards and structured layouts where both
horizontal and vertical positioning are required.

In most models you do not instantiate ``GridView`` directly. Instead, create it via the
:class:`~daitum_ui.ui_builder.UiBuilder` API, ``UiBuilder.add_grid_view()``,
which registers the view with the UI definition and ensures it is included in the build output.

.. autoclass:: daitum_ui.layout.GridView
    :no-index:
    :members:
    :show-inheritance:

Supporting Types
----------------

.. autoclass:: daitum_ui.layout.GridLayout
    :no-index:
    :members:
    :show-inheritance:

.. autoclass:: daitum_ui.layout.GridChild
    :no-index:
    :members:
    :show-inheritance:

.. autoclass:: daitum_ui.layout.GridAlignment
    :no-index:
    :show-inheritance:
