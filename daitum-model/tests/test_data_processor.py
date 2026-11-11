"""Tests for daitum_model.data_processor coordinate seeding."""

import pytest

from daitum_model import DataType, ModelBuilder
from daitum_model.data_processor import _convert


def _field(data_type: DataType):
    table = ModelBuilder().add_data_table("T")
    return table.add_data_field("Loc", data_type)


class TestCoordinateSeeding:
    def test_scalar_space_form(self):
        field = _field(DataType.COORDINATE)
        assert _convert(field, "-33.87 151.21", {}) == {"latitude": -33.87, "longitude": 151.21}

    def test_array_comma_separated_space_form(self):
        field = _field(DataType.COORDINATE_ARRAY)
        assert _convert(field, "-33.87 151.21,-33.81 151.0", {}) == [
            {"latitude": -33.87, "longitude": 151.21},
            {"latitude": -33.81, "longitude": 151.0},
        ]

    def test_out_of_range_rejected(self):
        field = _field(DataType.COORDINATE)
        with pytest.raises(ValueError, match="out of range"):
            _convert(field, "91 0", {})

    def test_malformed_rejected(self):
        field = _field(DataType.COORDINATE)
        with pytest.raises(ValueError, match="Invalid coordinate"):
            _convert(field, "-33.87", {})
