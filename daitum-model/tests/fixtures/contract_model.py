"""
Shared fixture model for the formula characterisation corpus.

Builds a single :class:`ModelBuilder` exposing one field of every relevant data-type shape,
plus an object-reference field and a map field, so the golden corpus can invoke every public
formula function and every operator against representative operands.

This module deliberately contains *no* assertions — it only constructs operands. The golden
expectations live in ``tests/fixtures/formula_golden.json`` (auto-captured on first run).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import daitum_model.formulas as formulas_module
from daitum_model import DataType, ModelBuilder
from daitum_model.data_types import MapDataType, ObjectDataType


@dataclass
class Fixture:
    """Container of named operands used by the corpus cases."""

    model: ModelBuilder
    fields: dict[str, Any]
    table: Any
    other_table: Any
    calc: Any
    param: Any


def build_fixture() -> Fixture:
    """Construct the shared fixture model and return its operands."""
    model = ModelBuilder()

    # A secondary table referenced by object/map fields.
    other = model.add_data_table("Sites")
    other.set_key_column("SiteId")
    other.add_data_field("SiteId", DataType.STRING)
    other.add_data_field("Amount", DataType.DECIMAL)
    other.add_data_field("Region", DataType.STRING)

    table = model.add_data_table("Jobs")
    table.set_key_column("Id")
    fields: dict[str, Any] = {}

    # One scalar field per primitive type.
    scalar_types = {
        "Id": DataType.STRING,
        "Cost": DataType.DECIMAL,
        "Qty": DataType.INTEGER,
        "Name": DataType.STRING,
        "Flag": DataType.BOOLEAN,
        "Day": DataType.DATE,
        "Stamp": DataType.DATETIME,
        "Clock": DataType.TIME,
    }
    for fid, dt in scalar_types.items():
        fields[fid] = table.add_data_field(fid, dt)

    # One array field per primitive type.
    array_types = {
        "Costs": DataType.DECIMAL_ARRAY,
        "Qtys": DataType.INTEGER_ARRAY,
        "Names": DataType.STRING_ARRAY,
        "Flags": DataType.BOOLEAN_ARRAY,
        "Days": DataType.DATE_ARRAY,
        "Stamps": DataType.DATETIME_ARRAY,
        "Clocks": DataType.TIME_ARRAY,
    }
    for fid, dt in array_types.items():
        fields[fid] = table.add_data_field(fid, dt)

    # Object reference (single + array) and a map field per primitive value type. A map per
    # primitive type lets the corpus/probe see every ``<T>_MAP`` kind, so map-consuming functions
    # (VALUES/GET/TOMAP) are exercised across all value types rather than DECIMAL alone.
    fields["Site"] = table.add_object_reference_field("Site", other, is_array=False)
    fields["SiteList"] = table.add_object_reference_field("SiteList", other, is_array=True)
    fields["CostMap"] = table.add_map_field("CostMap", DataType.DECIMAL, other)
    map_types = {
        "IntMap": DataType.INTEGER,
        "StrMap": DataType.STRING,
        "BoolMap": DataType.BOOLEAN,
        "DateMap": DataType.DATE,
        "StampMap": DataType.DATETIME,
        "ClockMap": DataType.TIME,
    }
    for fid, dt in map_types.items():
        fields[fid] = table.add_map_field(fid, dt, other)

    # A tracked field + baseline so the corpus can exercise BASELINE / HASBASELINE. Tracking only
    # affects the field's build() output, not formula rendering, so it is inert for the other cases.
    edits = model.add_tracking_group("edits")
    model.add_baseline("optimised", [edits])
    table.set_id_field("Id")
    fields["Tracked"] = table.add_data_field("Tracked", DataType.DECIMAL).set_tracking_groups(
        [edits]
    )

    # A calculation has no table context, so it references fields through the table
    # (``Jobs[Cost]``) and aggregates them to a scalar rather than using bare ``[Cost]`` refs.
    calc = model.add_calculation(
        "TotalCost", formulas_module.SUM(table["Cost"] * table["Qty"]), model_level=True
    )
    param = model.add_parameter("Threshold", DataType.DECIMAL, 100.0, model_level=True)

    return Fixture(
        model=model,
        fields=fields,
        table=table,
        other_table=other,
        calc=calc,
        param=param,
    )


__all__ = ["Fixture", "build_fixture", "DataType", "ObjectDataType", "MapDataType"]
