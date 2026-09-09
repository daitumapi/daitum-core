"""
Deliberately-broken model builders for the model-validation test suite.

Each factory returns a :class:`ModelBuilder` with exactly one structural defect (unless the
name says otherwise), so a test can assert that ``model.validate()`` reports it. Where a
defect cannot be reached through the fluent API (e.g. a field removed after a formula
already references it), the factory reproduces the broken state by direct mutation — the
same state a decode-then-mutate workflow, or a forgotten build step, would leave behind.
"""

from __future__ import annotations

import daitum_model.formulas as formulas
from daitum_model import AggregationMethod, DataType, ModelBuilder, SortDirection
from daitum_model.data_types import ObjectDataType
from daitum_model.derived_table import DerivedTable


def valid_model() -> ModelBuilder:
    """A small, structurally valid model (regression guard against false positives)."""
    model = ModelBuilder()
    items = model.add_data_table("Items")
    items.set_key_column("Name")
    items.add_data_field("Name", DataType.STRING)
    cost = items.add_data_field("Cost", DataType.DECIMAL)
    qty = items.add_data_field("Qty", DataType.INTEGER)
    items.add_calculated_field("RowCost", cost * qty)
    model.add_calculation("TOTAL", formulas.SUM(items["RowCost"]))
    return model


def table_cycle_via_reference() -> ModelBuilder:
    """A and B reference each other through object-reference fields."""
    model = ModelBuilder()
    a = model.add_data_table("A")
    a.set_key_column("AID")
    a.add_data_field("AID", DataType.STRING)
    b = model.add_data_table("B")
    b.set_key_column("BID")
    b.add_data_field("BID", DataType.STRING)
    a.add_object_reference_field("toB", b)
    b.add_object_reference_field("toA", a)
    return model


def table_cycle_with_self_edge() -> ModelBuilder:
    """A and B reference each other, and A also has a field referencing its own table.

    The self-reference adds a self-edge on A; the reported cycle path must still be the real
    A -> B -> A loop rather than a spurious self-loop.
    """
    model = table_cycle_via_reference()
    a = model.get_table("A")
    val = a.add_data_field("Val", DataType.DECIMAL)
    a.add_calculated_field("Doubled", val * 2)
    del a.field_definitions["Val"]  # leaves a dependency on a field of A -> self-edge
    return model


def table_cycle_via_formula() -> ModelBuilder:
    """B is derived from A, and a calculated field on A reads a column of B."""
    model = ModelBuilder()
    a = model.add_data_table("A")
    a.set_key_column("K")
    key = a.add_data_field("K", DataType.STRING)
    amt = a.add_data_field("AV", DataType.DECIMAL)

    derived = model.add_derived_table("B", a)
    derived.group_by(key)
    derived.add_source_fields([key])
    derived.add_aggregated_field("SumAV", amt, AggregationMethod.SUM)

    a.add_calculated_field("FromB", formulas.SUM(derived["SumAV"]))
    return model


def _table_with_field_pair() -> ModelBuilder:
    """A table T whose calculated field A depends on B; B is a placeholder to be replaced."""
    model = ModelBuilder()
    table = model.add_data_table("T")
    table.set_key_column("Id")
    table.add_data_field("Id", DataType.STRING)
    table.initialise_field("B", DataType.DECIMAL)  # placeholder so A can reference B first
    return model


def field_cycle_plain_calculated() -> ModelBuilder:
    """Two plain calculated fields on one table depend on each other — always invalid."""
    model = _table_with_field_pair()
    table = model.get_table("T")
    b_placeholder = table.field_definitions["B"]
    table.add_calculated_field("A", b_placeholder + 1.0)
    table.add_calculated_field("B", table.field_definitions["A"] + 1.0)
    return model


def field_cycle_combo_opposite_flags() -> ModelBuilder:
    """A combo pair with opposite calculate_in_optimiser values — the allowed exception."""
    model = _table_with_field_pair()
    table = model.get_table("T")
    b_placeholder = table.field_definitions["B"]
    table.add_combo_field("A", b_placeholder + 1.0, calculate_in_optimiser=True)
    table.add_combo_field("B", table.field_definitions["A"] + 1.0, calculate_in_optimiser=False)
    return model


def field_cycle_combo_same_flag() -> ModelBuilder:
    """A combo pair that both calculate in the optimiser — still a real cycle, invalid."""
    model = _table_with_field_pair()
    table = model.get_table("T")
    b_placeholder = table.field_definitions["B"]
    table.add_combo_field("A", b_placeholder + 1.0, calculate_in_optimiser=True)
    table.add_combo_field("B", table.field_definitions["A"] + 1.0, calculate_in_optimiser=True)
    return model


def named_value_cycle() -> ModelBuilder:
    """Two calculations that reference each other."""
    model = ModelBuilder()
    c1 = model.add_calculation("C1", formulas.CONST(1.0))
    c2 = model.add_calculation("C2", c1 + 1.0)
    c1.formula = c2 + 1.0  # close the loop
    return model


def calculated_field_missing_reference() -> ModelBuilder:
    """A calculated field references a field later removed from its table."""
    model = ModelBuilder()
    table = model.add_data_table("T")
    table.set_key_column("Id")
    table.add_data_field("Id", DataType.STRING)
    val = table.add_data_field("Val", DataType.DECIMAL)
    table.add_calculated_field("Doubled", val * 2)
    del table.field_definitions["Val"]  # the calc now dangles
    return model


def derived_calc_references_uncopied_source_field() -> ModelBuilder:
    """A derived table's calculated field references a group-by field it never copied in.

    ``Category`` is a group-by/source field defined on ``Parent``. The modeller forgot to call
    ``add_source_fields`` for it, so it is not a column on ``Child`` — but a calculated field on
    ``Child`` references it directly. The platform rejects this; the local-scope rule must too.
    """
    model = ModelBuilder()
    parent = model.add_data_table("Parent")
    category = parent.add_data_field("Category", DataType.STRING)
    amount = parent.add_data_field("Amount", DataType.DECIMAL)
    child = model.add_derived_table("Child", parent)
    child.group_by(category)
    child.add_aggregated_field("Total", amount, AggregationMethod.SUM)
    # ``Category`` is NOT copied onto ``Child`` (no ``add_source_fields``), yet referenced here.
    child.add_calculated_field("Label", category)
    return model


def calculation_references_bare_field() -> ModelBuilder:
    """A calculation references a bare field, but a calculation has no table context.

    A calculation is table-less, so a bare ``[Value]`` reference cannot resolve — the field must
    be read through a table (e.g. ``T[Value]``). The platform rejects the bare form.
    """
    model = ModelBuilder()
    table = model.add_data_table("T")
    value = table.add_data_field("Value", DataType.DECIMAL)
    model.add_calculation("BadCalc", value)
    return model


def derived_sort_field_missing() -> ModelBuilder:
    """A derived table sorts on a field that is not on its source table."""
    model = ModelBuilder()
    src = model.add_data_table("Src")
    src.set_key_column("Id")
    idf = src.add_data_field("Id", DataType.STRING)
    amt = src.add_data_field("Amt", DataType.DECIMAL)
    derived = model.add_derived_table("Grouped", src)
    derived.group_by(idf)
    derived.add_source_fields([idf])
    derived.add_aggregated_field("Total", amt, AggregationMethod.SUM)

    sort_key = DerivedTable._SortKey.__new__(DerivedTable._SortKey)  # noqa: SLF001
    sort_key.field = "NotOnSource"
    sort_key.direction = SortDirection.ASCENDING
    derived.sort_keys.append(sort_key)
    return model


def object_reference_unknown_table() -> ModelBuilder:
    """An object-reference field points at a table that is not in the model."""
    model = ModelBuilder()
    table = model.add_data_table("A")
    table.set_key_column("K")
    table.add_data_field("K", DataType.STRING)
    ref = table.add_data_field("Ref", DataType.STRING)

    ghost = ObjectDataType.__new__(ObjectDataType)  # noqa: SLF001
    ghost._source_table = table  # noqa: SLF001
    ghost._is_array = False  # noqa: SLF001
    ghost.type = "OBJECT"
    ghost.table_id = "Ghost"
    ref.data_type = ghost
    return model


def three_distinct_problems() -> ModelBuilder:
    """A model carrying three independent defects, for aggregate-reporting tests."""
    model = named_value_cycle()

    table = model.add_data_table("A")
    table.set_key_column("K")
    table.add_data_field("K", DataType.STRING)
    val = table.add_data_field("AV", DataType.DECIMAL)
    table.add_calculated_field("C", val * 2)
    del table.field_definitions["AV"]  # problem: dangling calc reference

    ref = table.add_data_field("Ref", DataType.STRING)
    ghost = ObjectDataType.__new__(ObjectDataType)  # noqa: SLF001
    ghost._source_table = table  # noqa: SLF001
    ghost._is_array = False  # noqa: SLF001
    ghost.type = "OBJECT"
    ghost.table_id = "Ghost"
    ref.data_type = ghost  # problem: unknown target table
    return model
