"""
Unit tests for the decoder core (daitum_model.decoding): coercion, dispatch, generic walk.

These exercise the inversion primitives in isolation before they are wired to real classes.
"""

from datetime import date, datetime
from enum import Enum

import pytest

from daitum_model import DataType, ModelBuilder
from daitum_model.decoding import (
    LoadContext,
    LoadError,
    coerce,
    decode_fields,
    decode_into,
    register_type,
)
from daitum_model.references import Reference
from daitum_model.serialisation import Buildable, json_type_info


class _Colour(Enum):
    RED = "red"
    BLUE = "blue"


class TestCoerce:
    def test_enum(self):
        assert coerce("red", _Colour, LoadContext()) is _Colour.RED

    def test_date(self):
        assert coerce([2026, 6, 11], date, LoadContext()) == date(2026, 6, 11)

    def test_datetime(self):
        assert coerce([2026, 6, 11, 9, 30, 0], datetime, LoadContext()) == datetime(
            2026, 6, 11, 9, 30, 0
        )

    def test_list_of_enum(self):
        assert coerce(["red", "blue"], list[_Colour], LoadContext()) == [
            _Colour.RED,
            _Colour.BLUE,
        ]

    def test_dict_passthrough_keys(self):
        # Domain-keyed dicts keep their keys verbatim.
        out = coerce({"TOTAL_COST": "red"}, dict[str, _Colour], LoadContext())
        assert out == {"TOTAL_COST": _Colour.RED}

    def test_optional(self):
        assert coerce(None, _Colour | None, LoadContext()) is None
        assert coerce("blue", _Colour | None, LoadContext()) is _Colour.BLUE

    def test_reference_resolves(self):
        model = ModelBuilder()
        p = model.add_parameter("RATE", DataType.DECIMAL, 0.1, model_level=True)
        ctx = LoadContext()
        ctx.register("RATE", p)
        out = coerce("!!!RATE", str, ctx)
        assert isinstance(out, Reference)
        assert out.target is p

    def test_primitive_passthrough(self):
        assert coerce(5, int, LoadContext()) == 5
        assert coerce("x", str, LoadContext()) == "x"


class TestGenericWalk:
    def test_decode_fields_round_trip(self):
        class Widget(Buildable):
            def __init__(self, size: int, colour: _Colour, label: str | None = None):
                self.size = size
                self.colour = colour
                self.label = label

        w = Widget(3, _Colour.BLUE, label="x")
        built = w.build()
        decoded = decode_fields(Widget, built, LoadContext())
        assert decoded.build() == built
        assert decoded.colour is _Colour.BLUE

    def test_unmapped_key_raises(self):
        class Widget(Buildable):
            def __init__(self, size: int):
                self.size = size

        with pytest.raises(LoadError):
            decode_fields(Widget, {"size": 1, "extra": 2}, LoadContext())


class TestPolymorphicDispatch:
    def test_at_type_dispatch(self):
        class Shape(Buildable):
            pass

        @json_type_info("circle")
        class Circle(Shape):
            def __init__(self, radius: int):
                self.radius = radius

        register_type(Shape, "circle", Circle)
        built = Circle(5).build()
        assert built["@type"] == "circle"
        decoded = decode_into(Shape, built, LoadContext())
        assert isinstance(decoded, Circle)
        assert decoded.radius == 5

    def test_unknown_discriminator_raises(self):
        class Shape(Buildable):
            pass

        register_type(Shape, "circle", Shape)
        with pytest.raises(LoadError):
            decode_into(Shape, {"@type": "square"}, LoadContext())
