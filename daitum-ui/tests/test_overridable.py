"""
Overridable-field auto-wiring tests.

Table and tree views detect an ``OverridableField`` in ``add_field`` and rebind the column to
the override data field with a ``REFERENCE_WITH_OVERRIDE`` default value reference pointing at
the calculated field.
"""

from daitum_model import DataType, ModelBuilder
from daitum_model.decoding import LoadContext

from daitum_ui._decoders.views import decode_view
from daitum_ui.ui_builder import UiBuilder


def _ctx(model):
    ctx = LoadContext()
    ctx.model = model
    for table in model.get_tables():
        ctx.register(table.id, table)
        for field in table.get_fields():
            ctx.register(field.id, field)
    return ctx


def test_table_view_auto_wires_overridable_field():
    model = ModelBuilder()
    table = model.add_data_table("Jobs")
    table.set_key_column("ID")
    table.add_data_field("ID", DataType.STRING)
    cost = table.add_data_field("Cost", DataType.DECIMAL)
    price = table.add_overridable_field("Price", cost * 1.1)

    ui = UiBuilder()
    view = ui.add_table_view(table, display_name="Jobs")
    view.add_field("ID")
    view.add_field(price.id)

    built = view.build()
    fields = built["viewDefinition"]["fields"]
    assert fields[1]["fieldId"] == "Price__override"
    assert fields[1]["defaultValueReference"] == {
        "type": "FIELD",
        "value": "Price__calculated",
        "behaviour": "REFERENCE_WITH_OVERRIDE",
    }

    decoded = decode_view(built, _ctx(model))
    assert decoded.build() == built


def test_tree_view_auto_wires_overridable_children():
    model = ModelBuilder()
    parent = model.add_data_table("Parent")
    child = model.add_data_table("Child")
    child.add_data_field("CID", DataType.STRING)
    child_cost = child.add_data_field("Cost", DataType.DECIMAL)
    child.add_overridable_field("Price", child_cost * 1.1)
    parent_cost = parent.add_data_field("Cost", DataType.DECIMAL)
    parent.add_overridable_field("Price", parent_cost * 1.1)
    parent.add_object_reference_field("Kids", child, is_array=True)

    ui = UiBuilder()
    tree = ui.add_tree_view(parent)
    tree.set_table_evaluation_order(parent, child)
    tree.set_children_field("Kids")
    tree.add_field("Price__effective")

    built = tree.build()
    field = built["viewDefinition"]["fields"][0]
    assert field["fieldId"] == "Price__override"
    assert field["defaultValueReference"] == {
        "type": "FIELD",
        "value": "Price__calculated",
        "behaviour": "REFERENCE_WITH_OVERRIDE",
    }
    assert field["children"][0]["fieldId"] == "Price__override"
    assert field["children"][0]["defaultValueReference"] == {
        "type": "FIELD",
        "value": "Price__calculated",
        "behaviour": "REFERENCE_WITH_OVERRIDE",
    }
