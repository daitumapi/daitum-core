Tree View
=========

The ``TreeView`` displays hierarchical data in a tree structure. In most models you do not instantiate ``TreeView`` directly.
Instead, create it via the :class:`~daitum_ui.ui_builder.UiBuilder` API, ``UiBuilder.add_tree_view()``,
which registers the view with the UI definition and ensures it is included in the build output.

.. autoclass:: daitum_ui.tabular.TreeView
    :no-index:
    :members:
    :show-inheritance:

Supporting Types
----------------

.. autoclass:: daitum_ui.tabular.TreeViewField
    :no-index:
    :members:
    :show-inheritance:
