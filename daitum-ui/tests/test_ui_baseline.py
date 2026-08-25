"""
UI baseline-tracking round-trip tests.

Covers the UI surface the baseline framework added: capture/revert model-event actions and the
per-cell baseline reset icon (a ``BASELINE`` ``DefaultValueReference``). Each asserts the
structural round-trip ``decode(x.build()).build() == x.build()`` holds, proving the decoders
reconstruct the new constructs faithfully.
"""

from daitum_model import DataType, ModelBuilder
from daitum_model.decoding import LoadContext
from daitum_ui._decoders.views import decode_view
from daitum_ui.elements import Button
from daitum_ui.model_event import ModelEvent
from daitum_ui.ui_builder import UiBuilder


def _model():
    model = ModelBuilder()
    group = model.add_tracking_group("edits")
    baseline = model.add_baseline("optimised", [group])
    table = model.add_data_table("Jobs")
    table.set_id_field("ID")
    table.add_data_field("ID", DataType.STRING)
    table.add_data_field("Cost", DataType.DECIMAL).set_tracking_groups([group])
    table.set_key_column("ID")
    return model, table, baseline


def _ctx(model):
    ctx = LoadContext()
    ctx.model = model
    for table in model.get_tables():
        ctx.register(table.id, table)
        for field in table.get_fields():
            ctx.register(field.id, field)
    return ctx


def test_view_field_baseline_reset_round_trips():
    model, table, baseline = _model()
    ui = UiBuilder()
    view = ui.add_table_view(table, display_name="Jobs")
    view.add_field("ID")
    view.add_field("Cost").set_baseline_reset(baseline)

    built = view.build()
    fields = built["viewDefinition"]["fields"]
    assert fields[1]["defaultValueReference"] == {
        "type": "BASELINE",
        "value": "optimised",
        "behaviour": "DEFAULT",
    }

    decoded = decode_view(built, _ctx(model))
    assert decoded.build() == built


def test_capture_and_revert_actions_round_trip():
    model, table, baseline = _model()
    event = ModelEvent()
    event.add_capture_baseline_action(baseline, tracking_groups=["edits"])
    event.add_revert_baseline_action("optimised")

    ui = UiBuilder()
    view = ui.add_table_view(table, display_name="Jobs")
    view.add_field("ID")
    view.add_action_element(Button("Snapshot", on_click=event))

    built = view.build()
    items = built["viewDefinition"]["actionBarDefinition"]["items"]
    action_types = [a["@type"] for a in items[0]["onClick"]["actions"]]
    assert action_types == ["CAPTURE_BASELINE", "REVERT_BASELINE"]

    decoded = decode_view(built, _ctx(model))
    assert decoded.build() == built
