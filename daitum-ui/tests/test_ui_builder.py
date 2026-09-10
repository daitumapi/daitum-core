"""
Tests for daitum_ui: UiBuilder instantiation, view creation, and serialisation.
"""

import pytest
from daitum_model import DataType, ModelBuilder

import daitum_ui
from daitum_ui import icons, navigation_items, styles, tabular
from daitum_ui.ui_builder import UiBuilder


class TestImport:
    def test_package_importable(self):
        assert daitum_ui is not None

    def test_ui_builder_importable(self):
        assert UiBuilder is not None

    def test_submodules_accessible(self):
        assert tabular is not None
        assert navigation_items is not None
        assert styles is not None
        assert icons is not None


class TestUiBuilder:
    def test_instantiation(self):
        ui = UiBuilder()
        assert ui is not None

    def test_build_returns_dict(self):
        ui = UiBuilder()
        result = ui.build()
        assert isinstance(result, dict)

    def test_add_table_view(self):
        model = ModelBuilder()
        table = model.add_data_table("Jobs")
        table.add_data_field("ID", DataType.STRING)

        ui = UiBuilder()
        view = ui.add_table_view(table)
        assert view is not None

    def test_add_form_view(self):
        ui = UiBuilder()
        view = ui.add_form_view(display_name="My Form")
        assert view is not None

    def test_navigation_group(self):
        from daitum_ui.navigation_items import GroupViewNavItem

        ui = UiBuilder()
        group = ui.add_navigation_group("My Group")
        assert group is not None
        assert isinstance(group, GroupViewNavItem)


class TestSerialisationCore:
    def test_template_binding_key_serialises_via_to_string(self):
        from daitum_ui._buildable import Buildable
        from daitum_ui.template_binding_key import TemplateBindingKey

        obj = Buildable()
        obj.binding = TemplateBindingKey("employeeName")
        obj.bindings = [TemplateBindingKey("a"), TemplateBindingKey("b")]
        built = obj.build()
        assert built["binding"] == "employeeName"
        assert built["bindings"] == ["a", "b"]

    def test_dict_keys_not_camelised(self):
        from daitum_ui._buildable import Buildable

        obj = Buildable()
        obj.field_mapping = {"start_date": "x", "MY_ID": "y"}
        assert obj.build() == {"fieldMapping": {"start_date": "x", "MY_ID": "y"}}


class TestContextMenuEvents:
    def _tree(self):
        model = ModelBuilder()
        parent = model.add_data_table("Parent")
        child = model.add_data_table("Child")
        child.add_data_field("CID", DataType.STRING)
        parent.add_object_reference_field("Kids", child, is_array=True)

        ui = UiBuilder()
        tree = ui.add_tree_view(parent)
        tree.set_table_evaluation_order(parent, child)
        tree.set_children_field("Kids")
        return tree

    def test_table_view_context_menu_event_serialises(self):
        from daitum_ui.model_event import ModelEvent

        model = ModelBuilder()
        table = model.add_data_table("Jobs")
        table.add_data_field("ID", DataType.STRING)

        ui = UiBuilder()
        view = ui.add_table_view(table)
        event = ModelEvent()
        event.add_switch_view_action("detail")
        view.add_context_menu_event("Open", event)

        built = view.build()["viewDefinition"]["contextMenuEvents"]
        assert built == [
            {"name": "Open", "event": {"actions": [{"@type": "SET_VIEW", "viewId": "detail"}]}}
        ]

    def test_tree_view_levels_coerced_and_serialised(self):
        from daitum_ui.model_event import ModelEvent

        tree = self._tree()
        tree.add_context_menu_event("Single", ModelEvent(), levels=0)
        tree.add_context_menu_event("Both", ModelEvent(), levels=[0, 1])
        tree.add_context_menu_event("Every", ModelEvent())

        built = tree.build()["viewDefinition"]["contextMenuEvents"]
        assert built[0]["levels"] == [0]
        assert built[1]["levels"] == [0, 1]
        assert "levels" not in built[2]

    def test_tree_view_rejects_invalid_levels(self):
        from daitum_ui.model_event import ModelEvent

        tree = self._tree()
        for bad in (2, [-1], [0, 0]):
            with pytest.raises(ValueError):
                tree.add_context_menu_event("Bad", ModelEvent(), levels=bad)

    def test_tree_view_levels_require_evaluation_order(self):
        from daitum_ui.model_event import ModelEvent

        model = ModelBuilder()
        table = model.add_data_table("Jobs")
        table.add_data_field("ID", DataType.STRING)

        ui = UiBuilder()
        tree = ui.add_tree_view(table)
        with pytest.raises(ValueError):
            tree.add_context_menu_event("Bad", ModelEvent(), levels=0)
