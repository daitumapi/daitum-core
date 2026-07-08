"""
Tests for the daitum_ui JSON decoder layer.

Each test generates a fixture by building a UI with :class:`UiBuilder`, then asserts the
structural round-trip ``decode(x.build()).build() == x.build()`` holds byte-for-byte.
There is no committed ``ui-definition.json`` golden; the builder is the source of truth.
"""

import json

import pytest

from daitum_model import DataType, ModelBuilder
from daitum_ui._decoders.ui import decode_ui
from daitum_ui._decoders.views import decode_view
from daitum_ui.base_view import BaseView
from daitum_ui.context_variable import CVType
from daitum_ui.filter_component import FilterOperator
from daitum_ui.layout import GridLayout
from daitum_ui._data_menu_item import DataMenuEntryType
from daitum_ui.ui_builder import UiBuilder


def _model():
    model = ModelBuilder()
    table = model.add_data_table("Jobs")
    table.add_data_field("ID", DataType.STRING)
    table.add_data_field("Cost", DataType.DECIMAL)
    table.add_data_field("Active", DataType.BOOLEAN)
    table.set_key_column("ID")
    return model, table


def assert_faithful(original, decoded):
    """A decoded object must be the same concrete type and re-build identically."""
    assert type(decoded) is type(
        original
    ), f"decoded type {type(decoded).__name__} != original {type(original).__name__}"
    assert decoded.build() == original.build(), "decoded.build() differs from original.build()"


class TestViewRoundTrip:
    def _roundtrip(self, builder, view, model=None):
        built = view.build()
        decoded = decode_view(built, _ctx(model))
        assert_faithful(view, decoded)
        # The exact random id must be preserved, not regenerated.
        assert decoded.id == built["id"]

    def test_table_view(self):
        model, table = _model()
        ui = UiBuilder()
        view = ui.add_table_view(table, display_name="Jobs")
        view.add_field("ID")
        view.add_field("Cost")
        self._roundtrip(ui, view, model)

    def test_table_view_with_hidden_conditions(self):
        model, table = _model()
        ui = UiBuilder()
        view = ui.add_table_view(table, display_name="Jobs")
        view.add_field("ID")
        flag = ui.add_context_variable("flag", CVType.BOOLEAN, default_value=False)
        view.add_variable_hidden_condition(flag)
        view.add_permission_hidden_condition(hide_from_base_user=True)
        self._roundtrip(ui, view, model)

    def test_table_view_with_filter_and_title(self):
        model, table = _model()
        ui = UiBuilder()
        flt = ui.add_filter("jobfilter", table)
        flt.add_filter_option(table.get_field("Cost"), "Cost")
        view = ui.add_table_view(table, display_name="Jobs", hidden=True)
        view.add_field("ID")
        view.set_show_filter("jobfilter")
        view.set_title("Jobs Title")
        self._roundtrip(ui, view, model)

    def test_tree_view(self):
        model, table = _model()
        ui = UiBuilder()
        view = ui.add_tree_view(table, display_name="Tree")
        self._roundtrip(ui, view, model)

    def test_form_view(self):
        model, table = _model()
        ui = UiBuilder()
        view = ui.add_form_view(display_name="Form", table=table)
        view.add_column("100px")
        view.add_text_input(table.get_field("ID"), row=1, column=1)
        self._roundtrip(ui, view, model)

    def test_fixed_value_view(self):
        ui = UiBuilder()
        view = ui.add_fixed_value_view(display_name="Constants")
        self._roundtrip(ui, view)

    def test_named_value_view(self):
        ui = UiBuilder()
        view = ui.add_named_value_view(display_name="Stats")
        self._roundtrip(ui, view)

    def test_grid_view(self):
        model, table = _model()
        ui = UiBuilder()
        child = ui.add_table_view(table, display_name="Child")
        child.add_field("ID")
        layout = GridLayout(
            columns=["1fr", "2fr"], rows=["auto", "1fr"], areas=[["a", "b"], ["c", "d"]]
        )
        view = ui.add_grid_view(layout, display_name="Grid")
        view.add_child(child, grid_area="a")
        self._roundtrip(ui, view, model)

    def test_flex_view(self):
        model, table = _model()
        ui = UiBuilder()
        child = ui.add_table_view(table, display_name="Child")
        child.add_field("ID")
        view = ui.add_flex_view(display_name="Flex")
        view.add_child(child, flex_grow=1)
        self._roundtrip(ui, view, model)

    def test_tabbed_view(self):
        model, table = _model()
        ui = UiBuilder()
        view = ui.add_tabbed_view(display_name="Tabs")
        self._roundtrip(ui, view, model)

    def test_chart_view(self):
        from daitum_ui.charts import ChartSeries, ChartType

        model, table = _model()
        ui = UiBuilder()
        view = ui.add_chart_view(
            ChartSeries(table.get_field("Cost")), ChartType.BAR, table, display_name="Chart"
        )
        self._roundtrip(ui, view, model)

    def test_combination_chart_view(self):
        from daitum_ui.charts import ChartSeries, ChartType

        model, table = _model()
        ui = UiBuilder()
        view = ui.add_combination_chart_view(
            ChartSeries(table.get_field("Cost")), ChartType.LINE, table, display_name="Combo"
        )
        self._roundtrip(ui, view, model)

    def test_card_view(self):
        from daitum_ui.elements import Card

        model, table = _model()
        ui = UiBuilder()
        view = ui.add_card_view(Card(), table, display_name="Cards")
        self._roundtrip(ui, view, model)

    def test_category_gantt_view(self):
        from daitum_ui.gantt_view import CategoryGanttTaskDefinition

        model, table = _model()
        ui = UiBuilder()
        view = ui.add_category_gantt_view(
            table, CategoryGanttTaskDefinition(table.get_field("ID")), display_name="Gantt"
        )
        self._roundtrip(ui, view, model)

    def test_tree_grid_gantt_view(self):
        from daitum_ui.gantt_view import TreeGridGanttTaskDefinition

        model, table = _model()
        ui = UiBuilder()
        view = ui.add_tree_grid_gantt_view(
            table, TreeGridGanttTaskDefinition(table.get_field("ID")), display_name="TreeGantt"
        )
        self._roundtrip(ui, view, model)

    def test_map_view(self):
        model, table = _model()
        table.add_data_field("Lat", DataType.DECIMAL)
        table.add_data_field("Lon", DataType.DECIMAL)
        ui = UiBuilder()
        view = ui.add_location_view(table, table.get_field("Lat"), table.get_field("Lon"))
        self._roundtrip(ui, view, model)

    def test_roster_view(self):
        model, table = _model()
        ui = UiBuilder()
        view = ui.add_roster_view(table, display_name="Roster")
        self._roundtrip(ui, view, model)

    def test_card_type_discriminator_does_not_collide_with_card_element(self):
        # Both CardView and the Card element declare @type "card". A view decodes through the
        # BaseView registry (-> CardView); a nested value decodes through the leaf @type map
        # (-> Card element). The two registries are independent — pin that they stay distinct.
        from daitum_ui._decoders.leaves import register as register_leaves
        from daitum_ui._decoders.leaves import resolve_at_type
        from daitum_ui.card_view import CardView
        from daitum_ui.elements import Card

        register_leaves()
        assert _VIEW_TYPES_card_class() is CardView
        assert resolve_at_type("card") is Card


def _VIEW_TYPES_card_class():
    from daitum_ui._decoders.views import _VIEW_TYPES

    return _VIEW_TYPES["card"]


class TestUiRoundTrip:
    def test_empty_builder(self):
        ui = UiBuilder()
        assert_faithful(ui, decode_ui(ui.build(), _ctx()))

    def test_builder_with_views_and_navigation(self):
        model, table = _model()
        ui = UiBuilder()
        table_view = ui.add_table_view(table, display_name="Jobs")
        table_view.add_field("ID")
        table_view.add_field("Cost")
        form_view = ui.add_form_view(display_name="Form", table=table)
        group = ui.add_navigation_group("Data")
        group.add_view(table_view)
        ui.add_navigation_item(form_view)
        assert_faithful(ui, decode_ui(ui.build(), _ctx(model)))

    def test_builder_with_modal_filter_menu_variables(self):
        model, table = _model()
        ui = UiBuilder()
        form_view = ui.add_form_view(display_name="Form", table=table)
        ui.add_modal(form_view, title="Edit", height="500px", width="700px")
        ui.add_context_variable("page_size", CVType.INTEGER, default_value=25)
        flt = ui.add_filter("jobfilter", table)
        flt.add_filter_option(table.get_field("Cost"), "Cost")
        flt.add_default_filter(table.get_field("ID"), FilterOperator.EQUAL, _string_value("x"))
        menu = ui.set_menu_configuration(hide_optimisation=True)
        menu.add_import_entry()
        menu.add_data_source_entry("some_source")
        menu.add_divider_entry()
        assert menu.data_menu[1].type is DataMenuEntryType.DATA_SOURCE
        assert_faithful(ui, decode_ui(ui.build(), _ctx(model)))

    def test_builder_default_view_ordering_preserved(self):
        model, table = _model()
        ui = UiBuilder()
        first = ui.add_table_view(table, display_name="First")
        first.add_field("ID")
        second = ui.add_table_view(table, display_name="Second")
        second.add_field("ID")
        ui.set_default_view(second)
        # Default view is ordered first by build(); the decoded order must match.
        assert_faithful(ui, decode_ui(ui.build(), _ctx(model)))

    def test_round_trip_via_files(self, tmp_path):
        model, table = _model()
        ui = UiBuilder()
        view = ui.add_table_view(table, display_name="Jobs")
        view.add_field("ID")
        ui.add_navigation_item(view)
        ui.write_to_file(str(tmp_path))
        decoded = UiBuilder.read_from_file(str(tmp_path), model)
        with (tmp_path / "ui-definition.json").open() as fp:
            written = json.load(fp)
        assert decoded.build() == written


class TestRealisticLoadIsStubFree:
    """With a model supplied, reference resolution returns live objects — never id-only stubs.

    These UI constructors keep only the referenced object's ``id`` string, so the decoded
    state is the same id either way; what matters is that the realistic path *feeds the
    constructor a real object* (the live view / model table registered in the context),
    fabricating nothing. The ``resolve_*`` helpers are the single seam where that choice is
    made, so we assert directly that they return the registered instances and that a stub
    appears only in the model-less fallback.
    """

    def test_resolvers_return_live_objects_when_model_present(self):
        from daitum_ui._decoders._stubs import resolve_field, resolve_table, resolve_view

        model, table = _model()
        ui = UiBuilder()
        view = ui.add_table_view(table, display_name="Jobs")
        view.add_field("ID")

        ctx = _ctx(model)
        for v in (view,):
            ctx.register(v.id, v)

        assert resolve_table(table.id, ctx) is ctx.resolve(table.id)
        assert resolve_field(table.get_field("ID").id, ctx) is ctx.resolve(table.get_field("ID").id)
        assert resolve_view(view.id, ctx) is view

    def test_resolvers_fall_back_to_stub_only_without_model(self):
        from daitum_model.decoding import LoadContext
        from daitum_ui._decoders._stubs import resolve_table

        stub = resolve_table("SomeTable", LoadContext())  # ctx.model is None
        assert stub.id == "SomeTable"

    def test_full_load_references_have_correct_ids(self):
        from daitum_ui.filter_component import FilterComponent
        from daitum_ui.modal import Modal
        from daitum_ui.navigation_items import SingleViewNavItem

        model, table = _model()
        ui = UiBuilder()
        view = ui.add_table_view(table, display_name="Jobs")
        view.add_field("ID")
        ui.add_navigation_item(view)
        ui.add_modal(view, title="Edit", height="500px", width="700px")
        flt = ui.add_filter("jobfilter", table)
        flt.add_filter_option(table.get_field("Cost"), "Cost")

        decoded = decode_ui(ui.build(), _ctx(model))

        nav = next(n for n in decoded.navigation if isinstance(n, SingleViewNavItem))
        modal = next(m for m in decoded.modals if isinstance(m, Modal))
        flt_cmp = next(f for f in decoded.filters if isinstance(f, FilterComponent))

        assert nav.view == view.id
        assert modal.view_id == view.id
        assert flt_cmp.source_table == table.id


class TestTemplateFactoryFragilityGuard:
    """Every registered template factory must still construct from its class's build() output.

    The template decoder learns an attribute's type from a reference instance produced by
    that class's factory. If a templated class gains a constructor-required argument the
    factory does not supply, decoding breaks deep inside a load with a runtime ``LoadError``.
    This guard promotes that failure to an explicit, enumerated CI check: it builds a real
    instance of each templated class via the public API and asserts ``_make_template`` (the
    exact step that would fail) succeeds and yields an instance of the right class.
    """

    def _representative_instances(self):
        """A real instance of each templated UI class, built via the public builders."""
        from daitum_ui.navigation_items import GroupViewNavItem

        # GroupViewNavItem keeps a process-wide name registry; clear it for test isolation.
        GroupViewNavItem._registry.clear()

        model, table = _model()
        ui = UiBuilder()
        flag = ui.add_context_variable("flag", CVType.BOOLEAN, default_value=False)

        table_view = ui.add_table_view(table, display_name="Jobs")
        table_view.add_field("ID")
        tree_view = ui.add_tree_view(table, display_name="Tree")
        form_view = ui.add_form_view(display_name="Form", table=table)
        fixed_view = ui.add_fixed_value_view(display_name="Fixed")
        nv_view = ui.add_named_value_view(display_name="Stats")
        tabbed_view = ui.add_tabbed_view(display_name="Tabs")
        flex_view = ui.add_flex_view(display_name="Flex")
        flex_view.add_child(table_view, flex_grow=1)
        grid_view = ui.add_grid_view(
            GridLayout(columns=["1fr"], rows=["1fr"], areas=[["a"]]), display_name="Grid"
        )
        grid_view.add_child(tree_view, grid_area="a")

        nav_single = ui.add_navigation_item(table_view)
        nav_group = ui.add_navigation_group("Data")
        nav_group.add_view(form_view)
        modal = ui.add_modal(form_view, title="Edit", height="500px", width="700px")
        flt = ui.add_filter("jobfilter", table)
        flt.add_filter_option(table.get_field("Cost"), "Cost")
        flt_field = flt.filter_options[0]
        menu = ui.set_menu_configuration(hide_optimisation=True)
        menu.add_data_source_entry("some_source")
        data_menu_item = menu.data_menu[0]

        from daitum_ui.filter_component import (
            DefaultFilter,
            FilterOperator,
            SearchConfiguration,
            SearchType,
        )

        default_filter = DefaultFilter(table.get_field("ID"), FilterOperator.EQUAL)
        search_config = SearchConfiguration(SearchType.CONTAINS_PHRASE)

        from daitum_ui.charts import ChartSeries, ChartType
        from daitum_ui.elements import Card
        from daitum_ui.gantt_view import CategoryGanttTaskDefinition, TreeGridGanttTaskDefinition

        table.add_data_field("Lat", DataType.DECIMAL)
        table.add_data_field("Lon", DataType.DECIMAL)
        chart_view = ui.add_chart_view(
            ChartSeries(table.get_field("Cost")), ChartType.BAR, table, display_name="Chart"
        )
        combo_view = ui.add_combination_chart_view(
            ChartSeries(table.get_field("Cost")), ChartType.LINE, table, display_name="Combo"
        )
        card_view = ui.add_card_view(Card(), table, display_name="Cards")
        cat_gantt = ui.add_category_gantt_view(
            table, CategoryGanttTaskDefinition(table.get_field("ID")), display_name="Gantt"
        )
        tree_gantt = ui.add_tree_grid_gantt_view(
            table, TreeGridGanttTaskDefinition(table.get_field("ID")), display_name="TreeGantt"
        )
        map_view = ui.add_location_view(table, table.get_field("Lat"), table.get_field("Lon"))
        roster_view = ui.add_roster_view(table, display_name="Roster")
        series = ChartSeries(table.get_field("Cost"))
        cat_task = CategoryGanttTaskDefinition(table.get_field("ID"))
        tree_task = TreeGridGanttTaskDefinition(table.get_field("ID"))

        return model, [
            table_view,
            tree_view,
            form_view,
            fixed_view,
            nv_view,
            tabbed_view,
            flex_view,
            grid_view,
            flag,
            nav_single,
            nav_group,
            modal,
            flt,
            flt_field,
            menu,
            data_menu_item,
            chart_view,
            combo_view,
            card_view,
            cat_gantt,
            tree_gantt,
            map_view,
            roster_view,
            series,
            cat_task,
            tree_task,
            default_filter,
            search_config,
        ]

    def test_every_template_factory_constructs(self):
        from daitum_ui._decoders._template import TEMPLATE_FACTORIES, _make_template

        model, instances = self._representative_instances()
        by_type = {type(obj): obj for obj in instances}

        ctx = _ctx(model)
        for obj in instances:
            if hasattr(obj, "id"):
                ctx.register(obj.id, obj)

        missing = [cls for cls in TEMPLATE_FACTORIES if cls not in by_type]
        # ViewConfig is an internal layout wrapper with no standalone public builder; it is
        # exercised by the grid/flex child round-trips, so exempt it from this enumeration.
        from daitum_ui._composite_view import CompositeView, ViewConfig

        allowed_missing = {ViewConfig, CompositeView}
        assert set(missing) <= allowed_missing, f"No representative instance for: {missing}"

        for cls, obj in by_type.items():
            if cls not in TEMPLATE_FACTORIES:
                continue
            built = obj.build()
            # A view's build() is an envelope; the factory consumes the inner viewDefinition.
            data = built.get("viewDefinition", built)
            template = _make_template(cls, data, ctx)
            assert isinstance(template, cls), f"{cls.__name__} factory returned {type(template)}"

    def test_every_representative_decodes_faithfully(self):
        # Stronger than "the factory constructs": actually run the full decode of each
        # representative instance and assert the contract — same type, byte-identical rebuild,
        # no replay placeholder, and typed wherever the original is (no dict degradation).
        from daitum_ui._decoders._template import decode_by_template
        from daitum_ui._decoders.leaves import LEAF_DECODERS

        model, instances = self._representative_instances()
        ctx = _ctx(model)
        for obj in instances:
            if hasattr(obj, "id"):
                ctx.register(obj.id, obj)

        for obj in instances:
            if isinstance(obj, BaseView):
                decoded = decode_view(obj.build(), ctx)
            else:
                decoder = LEAF_DECODERS.get(type(obj))
                decoded = (
                    decoder(obj.build(), ctx)
                    if decoder is not None
                    else decode_by_template(type(obj), obj.build(), ctx)
                )
            assert_faithful(obj, decoded)


def _ctx(model=None):
    from daitum_model.decoding import LoadContext

    ctx = LoadContext()
    ctx.model = model
    if model is not None:
        for table in model.get_tables():
            ctx.register(table.id, table)
            for field in table.get_fields():
                ctx.register(field.id, field)
    return ctx


def _string_value(text):
    from daitum_ui.data import StringValue

    return StringValue(text)


class TestNegativeDecoding:
    """Malformed UI payloads fail loudly with a useful LoadError."""

    def test_unsupported_view_type_raises(self):
        from daitum_model.decoding import LoadError

        envelope = {"id": "x", "viewDefinition": {"@type": "no-such-view"}}
        with pytest.raises(LoadError, match="Unsupported view '@type'"):
            decode_view(envelope, _ctx())

    def test_view_envelope_missing_view_definition_raises(self):
        from daitum_model.decoding import LoadError

        with pytest.raises(LoadError, match="missing required key"):
            decode_view({"id": "x"}, _ctx())

    def test_unsupported_nested_at_type_raises(self):
        from daitum_model.decoding import LoadError

        from daitum_ui._decoders._value import decode_value

        with pytest.raises(LoadError, match="Unsupported UI @type"):
            decode_value({"@type": "no-such-leaf"}, None, None, _ctx())
