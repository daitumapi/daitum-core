Table View
==========

The ``TableView`` displays data in a standard table layout. In most models you do not instantiate ``TableView`` directly.
Instead, create it via the :class:`~daitum_ui.ui_builder.UiBuilder` API, ``UiBuilder.add_table_view()``,
which registers the view with the UI definition and ensures it is included in the build output.

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
