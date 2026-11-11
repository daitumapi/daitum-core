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


class TestPropertyFieldMappingValidation:
    """add_property_field_mapping validates the key against the element's allowlist and the
    value's data type against the property's expected type."""

    @staticmethod
    def _model():
        model = ModelBuilder()
        table = model.add_data_table("Jobs")
        table.set_key_column("ID")
        table.add_data_field("ID", DataType.STRING)
        table.add_data_field("Colour", DataType.STRING)
        table.add_data_field("Flag", DataType.BOOLEAN)
        table.add_data_field("Count", DataType.INTEGER)
        return model, table

    def test_valid_mapping(self):
        from daitum_ui.elements import Text

        _, table = self._model()
        text = Text("hi").add_property_field_mapping("color", table.get_field("Colour"))
        assert text.property_field_mapping == {"color": "[Colour]"}

    def test_unsupported_key_lists_supported(self):
        from daitum_ui.elements import Text

        _, table = self._model()
        with pytest.raises(ValueError, match="Unsupported property 'colour' for Text"):
            Text("x").add_property_field_mapping("colour", table.get_field("Colour"))

    def test_wrong_value_type_raises(self):
        from daitum_ui.elements import Text

        _, table = self._model()
        # wrap expects BOOLEAN; Colour is STRING.
        with pytest.raises(ValueError, match="expects a BOOLEAN value"):
            Text("x").add_property_field_mapping("wrap", table.get_field("Colour"))

    def test_boolean_property_accepts_boolean_field(self):
        from daitum_ui.elements import Text

        _, table = self._model()
        text = Text("x").add_property_field_mapping("wrap", table.get_field("Flag"))
        assert text.property_field_mapping["wrap"] == "[Flag]"

    def test_template_binding_key_skips_type_check(self):
        from daitum_ui.elements import Text
        from daitum_ui.template_binding_key import TemplateBindingKey

        text = Text("x").add_property_field_mapping("color", TemplateBindingKey("c"))
        assert "color" in text.property_field_mapping

    def test_element_without_mappable_properties_raises(self):
        from daitum_ui.elements import ModelEditorLink

        _, table = self._model()
        link = ModelEditorLink(table.get_field("Count"))
        with pytest.raises(ValueError, match="has no mappable properties"):
            link.add_property_field_mapping("color", table.get_field("Colour"))

    def test_unmappable_icon_property_rejected(self):
        from daitum_ui.elements import ReviewRating

        _, table = self._model()
        rating = ReviewRating(table.get_field("Count"))
        # fill_icon is not mappable; fillColor is.
        with pytest.raises(ValueError, match="Unsupported property 'fillIcon'"):
            rating.add_property_field_mapping("fillIcon", table.get_field("Colour"))
        rating.add_property_field_mapping("fillColor", table.get_field("Colour"))
        assert "fillColor" in rating.property_field_mapping
        rating.add_property_field_mapping("size", table.get_field("Colour"))
        assert "size" in rating.property_field_mapping

    def test_min_max_value_not_mappable(self):
        from daitum_ui.elements import NumberInput

        _, table = self._model()
        number = NumberInput(table.get_field("Count"))
        # minValue/maxValue are driven via set_range_validation, not property mappings.
        with pytest.raises(ValueError, match="Unsupported property 'minValue'"):
            number.add_property_field_mapping("minValue", table.get_field("Count"))

    def test_text_input_rows_only_when_multiline(self):
        from daitum_ui.elements import TextInput

        _, table = self._model()
        single = TextInput(table.get_field("ID"))
        with pytest.raises(ValueError, match="Unsupported property 'rows'"):
            single.add_property_field_mapping("rows", table.get_field("Count"))
        multiline = TextInput(table.get_field("ID"), rows=3)
        multiline.add_property_field_mapping("rows", table.get_field("Count"))
        assert "rows" in multiline.property_field_mapping

    def test_date_time_picker_mode_specific_properties(self):
        from daitum_ui.elements import DateTimeMode, DateTimePicker

        model, table = self._model()
        table.add_data_field("When", DataType.DATE)
        date_picker = DateTimePicker(table.get_field("When"), DateTimeMode.DATE)
        date_picker.add_property_field_mapping("withSelector", table.get_field("Flag"))
        # timeInterval is a TIME/DATE_TIME-only property.
        with pytest.raises(ValueError, match="Unsupported property 'timeInterval'"):
            date_picker.add_property_field_mapping("timeInterval", table.get_field("Count"))


class TestListValidation:
    """set_list_validation enforces the server's two constraints: the reference must be an array
    of allowed values, and Dropdown does not support LIST validation at all."""

    @staticmethod
    def _model():
        model = ModelBuilder()
        table = model.add_data_table("Jobs")
        table.set_key_column("ID")
        table.add_data_field("ID", DataType.STRING)
        table.add_data_field("State", DataType.STRING)
        table.add_data_field("Allowed", DataType.STRING_ARRAY)
        table.add_data_field("N", DataType.INTEGER)
        return model, table

    def test_array_reference_accepted(self):
        from daitum_ui.data import DataValidationType
        from daitum_ui.elements import NumberInput

        _, table = self._model()
        number = NumberInput(table.get_field("N"))
        number.set_list_validation(table.get_field("Allowed"))
        assert number.data_validation_rule.type is DataValidationType.LIST
        assert number.data_validation_rule.reference_field == "Allowed"

    def test_scalar_reference_rejected(self):
        from daitum_ui.elements import NumberInput

        _, table = self._model()
        with pytest.raises(ValueError, match="requires an array reference"):
            NumberInput(table.get_field("N")).set_list_validation(table.get_field("State"))

    def test_dropdown_does_not_support_list_validation(self):
        from daitum_ui.elements import Dropdown

        model, table = self._model()
        table.add_object_reference_field("Ref", table)
        dropdown = Dropdown(table.get_field("Ref"))
        assert dropdown.supports_list_validation() is False
        with pytest.raises(ValueError, match="not supported for Dropdown"):
            dropdown.set_list_validation(table.get_field("Allowed"))


class TestFormViewGuards:
    def test_table_bound_form_without_filter_mode_raises(self):
        model = ModelBuilder()
        table = model.add_data_table("Jobs")
        table.set_key_column("ID")
        table.add_data_field("ID", DataType.STRING)

        ui = UiBuilder()
        view = ui.add_form_view(display_name="F", table=table)
        with pytest.raises(ValueError, match="has no filter_mode"):
            view.build()

    def test_table_bound_form_with_filter_mode_builds(self):
        from daitum_ui.data import MatchRowFilterMode

        model = ModelBuilder()
        table = model.add_data_table("Jobs")
        table.set_key_column("ID")
        table.add_data_field("ID", DataType.STRING)

        fm = MatchRowFilterMode()
        fm.set_filter_row("row")
        ui = UiBuilder()
        view = ui.add_form_view(display_name="F", table=table, filter_mode=fm)
        assert view.build()["viewDefinition"]["@type"] == "form"

    def test_named_values_only_form_needs_no_filter_mode(self):
        ui = UiBuilder()
        view = ui.add_form_view(display_name="F")  # no source table
        assert view.build()["viewDefinition"]["@type"] == "form"


class TestFilterRegistrationGuard:
    @staticmethod
    def _model():
        model = ModelBuilder()
        table = model.add_data_table("Jobs")
        table.set_key_column("ID")
        table.add_data_field("ID", DataType.STRING)
        table.add_data_field("Cost", DataType.DECIMAL)
        return model, table

    def test_unregistered_filter_reference_raises(self):
        from daitum_ui.elements import Card
        from daitum_ui.filter_component import FilterComponent

        _, table = self._model()
        ui = UiBuilder()
        card = ui.add_card_view(Card(), table, display_name="Cards")
        card.set_use_filter(FilterComponent("Card Filter", table))  # never registered
        with pytest.raises(ValueError, match="references filter 'Card Filter'"):
            ui.build()

    def test_registered_filter_builds(self):
        from daitum_ui.elements import Card

        _, table = self._model()
        ui = UiBuilder()
        card = ui.add_card_view(Card(), table, display_name="Cards")
        flt = ui.add_filter("Card Filter", table)
        flt.add_filter_option(table.get_field("Cost"), "Cost")
        card.set_use_filter(flt)
        assert "views" in ui.build()
