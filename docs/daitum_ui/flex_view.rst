Flex View
=========

Flex views arrange content in a one-dimensional layout using rows or columns.

They are suitable for responsive layouts, toolbars, and simple compositions.

In most models you do not instantiate ``FlexView`` directly. Instead, create it via the
:class:`~daitum_ui.ui_builder.UiBuilder` API, ``UiBuilder.add_flex_view()``,
which registers the view with the UI definition and ensures it is included in the build output.


.. autoclass:: daitum_ui.layout.FlexView
    :no-index:
    :members:
    :show-inheritance:

Supporting Types
----------------

.. autoclass:: daitum_ui.layout.FlexChild
    :no-index:
    :members:
    :show-inheritance:

.. autoclass:: daitum_ui.layout.FlexAlignment
    :no-index:
    :show-inheritance:

.. autoclass:: daitum_ui.layout.FlexAlignSelf
    :no-index:
    :show-inheritance:

.. autoclass:: daitum_ui.layout.FlexDirection
    :no-index:
    :show-inheritance:

.. autoclass:: daitum_ui.layout.FlexWrap
    :no-index:
    :show-inheritance:
