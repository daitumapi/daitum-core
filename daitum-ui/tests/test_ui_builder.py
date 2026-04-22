"""
Tests for daitum_ui: UiBuilder instantiation, view creation, and serialisation.
"""

import daitum_ui
from daitum_model import DataType, ModelBuilder
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
