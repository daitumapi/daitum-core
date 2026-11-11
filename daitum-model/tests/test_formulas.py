"""
Tests for daitum_model.formulas: formula functions, types, and serialisation.
"""

from daitum_model import DataType, Formula, ModelBuilder, formulas


class TestFormulasImport:
    def test_formulas_module_importable(self):
        assert formulas is not None

    def test_if_importable(self):
        assert formulas.IF is not None

    def test_and_importable(self):
        assert formulas.AND is not None

    def test_or_importable(self):
        assert formulas.OR is not None

    def test_isblank_importable(self):
        assert formulas.ISBLANK is not None

    def test_not_importable(self):
        assert formulas.NOT is not None


class TestFormulaReturnTypes:
    def test_isblank_returns_boolean(self):
        model = ModelBuilder()
        table = model.add_data_table("T")
        field = table.add_data_field("X", DataType.STRING)
        result = formulas.ISBLANK(field)
        assert isinstance(result, Formula)
        assert result.data_type == DataType.BOOLEAN

    def test_not_returns_boolean(self):
        model = ModelBuilder()
        table = model.add_data_table("T")
        field = table.add_data_field("X", DataType.STRING)
        result = formulas.NOT(formulas.ISBLANK(field))
        assert isinstance(result, Formula)
        assert result.data_type == DataType.BOOLEAN

    def test_if_inherits_branch_type(self):
        model = ModelBuilder()
        table = model.add_data_table("T")
        field = table.add_data_field("Cost", DataType.DECIMAL)
        result = formulas.IF(formulas.ISBLANK(field), 0.0, field)
        assert isinstance(result, Formula)
        assert result.data_type == DataType.DECIMAL

    def test_and_returns_boolean(self):
        model = ModelBuilder()
        table = model.add_data_table("T")
        a = table.add_data_field("A", DataType.BOOLEAN)
        b = table.add_data_field("B", DataType.BOOLEAN)
        result = formulas.AND(a, b)
        assert isinstance(result, Formula)
        assert result.data_type == DataType.BOOLEAN

    def test_or_returns_boolean(self):
        model = ModelBuilder()
        table = model.add_data_table("T")
        a = table.add_data_field("A", DataType.BOOLEAN)
        b = table.add_data_field("B", DataType.BOOLEAN)
        result = formulas.OR(a, b)
        assert isinstance(result, Formula)
        assert result.data_type == DataType.BOOLEAN

    def test_sum_returns_numeric(self):
        model = ModelBuilder()
        table = model.add_data_table("T")
        cost = table.add_data_field("Cost", DataType.DECIMAL)
        result = formulas.SUM(table["Cost"])
        assert isinstance(result, Formula)
        assert result.data_type == DataType.DECIMAL

    def test_blank_returns_formula(self):
        result = formulas.BLANK()
        assert isinstance(result, Formula)

    def test_iferror_returns_formula(self):
        model = ModelBuilder()
        table = model.add_data_table("T")
        field = table.add_data_field("X", DataType.INTEGER)
        result = formulas.IFERROR(field, 0)
        assert isinstance(result, Formula)

    def test_count_returns_integer(self):
        model = ModelBuilder()
        table = model.add_data_table("T")
        flag = table.add_data_field("Flag", DataType.BOOLEAN)
        result = formulas.COUNT(table["Flag"], True)
        assert isinstance(result, Formula)
        assert result.data_type == DataType.INTEGER

    def test_contains_scalar_returns_boolean(self):
        model = ModelBuilder()
        table = model.add_data_table("T")
        arr = table.add_data_field("Arr", DataType.INTEGER_ARRAY)
        val = table.add_data_field("Val", DataType.INTEGER)
        result = formulas.CONTAINS(arr, val)
        assert isinstance(result, Formula)
        assert result.data_type == DataType.BOOLEAN

    def test_contains_array_returns_boolean_array(self):
        model = ModelBuilder()
        table = model.add_data_table("T")
        arr = table.add_data_field("Arr", DataType.INTEGER_ARRAY)
        vals = table.add_data_field("Vals", DataType.INTEGER_ARRAY)
        result = formulas.CONTAINS(arr, vals)
        assert isinstance(result, Formula)
        assert result.data_type == DataType.BOOLEAN_ARRAY

    def test_contains_mismatched_element_type_raises(self):
        model = ModelBuilder()
        table = model.add_data_table("T")
        arr = table.add_data_field("Arr", DataType.STRING_ARRAY)
        vals = table.add_data_field("Vals", DataType.INTEGER_ARRAY)
        try:
            formulas.CONTAINS(arr, vals)
            raise AssertionError("expected ValueError")
        except ValueError:
            pass


class TestFormulaExpression:
    def test_isblank_expression_contains_id(self):
        model = ModelBuilder()
        table = model.add_data_table("T")
        field = table.add_data_field("MyField", DataType.STRING)
        result = formulas.ISBLANK(field)
        assert "MyField" in result.formula_string

    def test_if_expression_structure(self):
        model = ModelBuilder()
        table = model.add_data_table("T")
        field = table.add_data_field("X", DataType.INTEGER)
        result = formulas.IF(formulas.ISBLANK(field), 0, field)
        assert "IF" in result.formula_string
        assert "ISBLANK" in result.formula_string


class TestProbabilityReturnTypes:
    def test_normdist_returns_decimal(self):
        from daitum_model.formula import CONST

        result = formulas.NORMDIST(CONST(0.0), CONST(0.0), CONST(1.0), CONST(True))
        assert isinstance(result, Formula)
        assert result.data_type == DataType.DECIMAL

    def test_norminv_returns_decimal(self):
        from daitum_model.formula import CONST

        result = formulas.NORMINV(CONST(0.5), CONST(0.0), CONST(1.0))
        assert isinstance(result, Formula)
        assert result.data_type == DataType.DECIMAL

    def test_binomdist_returns_decimal(self):
        from daitum_model.formula import CONST

        result = formulas.BINOMDIST(CONST(2), CONST(10), CONST(0.5), CONST(True))
        assert isinstance(result, Formula)
        assert result.data_type == DataType.DECIMAL

    def test_binominv_returns_integer(self):
        from daitum_model.formula import CONST

        result = formulas.BINOMINV(CONST(10), CONST(0.5), CONST(0.9))
        assert isinstance(result, Formula)
        assert result.data_type == DataType.INTEGER

    def test_gammadist_returns_decimal(self):
        from daitum_model.formula import CONST

        result = formulas.GAMMADIST(CONST(1.0), CONST(2.0), CONST(1.0), CONST(True))
        assert isinstance(result, Formula)
        assert result.data_type == DataType.DECIMAL

    def test_gammainv_returns_decimal(self):
        from daitum_model.formula import CONST

        result = formulas.GAMMAINV(CONST(0.5), CONST(2.0), CONST(1.0))
        assert isinstance(result, Formula)
        assert result.data_type == DataType.DECIMAL


class TestProbabilitySerialisation:
    def test_normdist_expression(self):
        from daitum_model.formula import CONST

        result = formulas.NORMDIST(CONST(0.0), CONST(0.0), CONST(1.0), CONST(True))
        assert "NORMDIST" in result.formula_string

    def test_norminv_expression(self):
        from daitum_model.formula import CONST

        result = formulas.NORMINV(CONST(0.5), CONST(0.0), CONST(1.0))
        assert "NORMINV" in result.formula_string

    def test_binomdist_expression(self):
        from daitum_model.formula import CONST

        result = formulas.BINOMDIST(CONST(2), CONST(10), CONST(0.5), CONST(True))
        assert "BINOMDIST" in result.formula_string

    def test_binominv_expression(self):
        from daitum_model.formula import CONST

        result = formulas.BINOMINV(CONST(10), CONST(0.5), CONST(0.9))
        assert "BINOMINV" in result.formula_string

    def test_gammadist_expression(self):
        from daitum_model.formula import CONST

        result = formulas.GAMMADIST(CONST(1.0), CONST(2.0), CONST(1.0), CONST(True))
        assert "GAMMADIST" in result.formula_string

    def test_gammainv_expression(self):
        from daitum_model.formula import CONST

        result = formulas.GAMMAINV(CONST(0.5), CONST(2.0), CONST(1.0))
        assert "GAMMAINV" in result.formula_string


class TestBaseline:
    def _field(self):
        from daitum_model import DataType, ModelBuilder

        model = ModelBuilder()
        table = model.add_data_table("T")
        table.set_id_field("id")
        field = table.add_data_field("revenue", DataType.DECIMAL)
        field.set_tracking_groups(["edits"])
        return field

    def test_baseline_returns_reference_type(self):
        from daitum_model import DataType, Formula

        result = formulas.BASELINE("optimised", self._field())
        assert isinstance(result, Formula)
        assert result.data_type == DataType.DECIMAL
        assert result.formula_string == 'BASELINE("optimised", [revenue])'

    def test_baseline_with_fallback(self):
        field = self._field()
        result = formulas.BASELINE("optimised", field, field)
        assert result.formula_string == 'BASELINE("optimised", [revenue], [revenue])'

    def test_baseline_fallback_type_mismatch_raises(self):
        import pytest

        from daitum_model import DataType, ModelBuilder

        model = ModelBuilder()
        table = model.add_data_table("T")
        table.set_id_field("id")
        decimal_field = table.add_data_field("revenue", DataType.DECIMAL)
        decimal_field.set_tracking_groups(["edits"])
        string_field = table.add_data_field("name", DataType.STRING)
        with pytest.raises(ValueError, match="does not match"):
            formulas.BASELINE("optimised", decimal_field, string_field)

    def test_baseline_untracked_reference_raises(self):
        import pytest

        from daitum_model import DataType, ModelBuilder

        model = ModelBuilder()
        table = model.add_data_table("T")
        table.set_id_field("id")
        field = table.add_data_field("revenue", DataType.DECIMAL)
        with pytest.raises(ValueError, match="not assigned to any tracking group"):
            formulas.BASELINE("optimised", field)

    def test_baseline_expression_reference_raises(self):
        import pytest

        field = self._field()
        with pytest.raises(TypeError, match="must be a field, calculation, or parameter"):
            formulas.BASELINE("optimised", field + field)

    def test_baseline_accepts_baseline_object(self):
        from daitum_model import ModelBuilder

        model = ModelBuilder()
        edits = model.add_tracking_group("edits")
        baseline = model.add_baseline("optimised", [edits])
        result = formulas.BASELINE(baseline, self._field())
        assert result.formula_string == 'BASELINE("optimised", [revenue])'

    def test_hasbaseline_returns_boolean(self):
        from daitum_model import DataType, Formula

        result = formulas.HASBASELINE("optimised")
        assert isinstance(result, Formula)
        assert result.data_type == DataType.BOOLEAN
        assert result.formula_string == 'HASBASELINE("optimised")'


class TestCoordinateFormulas:
    def _fields(self):
        table = ModelBuilder().add_data_table("T")
        return (
            table.add_data_field("Lat", DataType.DECIMAL),
            table.add_data_field("Lng", DataType.DECIMAL),
            table.add_data_field("Lats", DataType.DECIMAL_ARRAY),
        )

    def test_coordinate_returns_coordinate(self):
        lat, lng, _ = self._fields()
        result = formulas.COORDINATE(lat, lng)
        assert isinstance(result, Formula)
        assert result.data_type == DataType.COORDINATE
        assert result.formula_string == "COORDINATE([Lat], [Lng])"

    def test_coordinate_propagates_array(self):
        _, lng, lats = self._fields()
        result = formulas.COORDINATE(lats, lng)
        assert result.data_type == DataType.COORDINATE_ARRAY

    def test_coordinate_rejects_non_numeric(self):
        import pytest

        table = ModelBuilder().add_data_table("T")
        name = table.add_data_field("Name", DataType.STRING)
        lng = table.add_data_field("Lng", DataType.DECIMAL)
        with pytest.raises(ValueError):
            formulas.COORDINATE(name, lng)

    def test_latitude_longitude_return_decimal(self):
        coord = formulas.COORDINATE(-33.87, 151.21)
        assert formulas.LATITUDE(coord).data_type == DataType.DECIMAL
        assert formulas.LONGITUDE(coord).data_type == DataType.DECIMAL

    def test_component_propagates_array(self):
        _, lng, lats = self._fields()
        coord = formulas.COORDINATE(lats, lng)
        assert formulas.LATITUDE(coord).data_type == DataType.DECIMAL_ARRAY

    def test_component_rejects_non_coordinate(self):
        import pytest

        with pytest.raises(ValueError):
            formulas.LATITUDE(1.0)


class TestRoutingFormulas:
    def _fields(self):
        table = ModelBuilder().add_data_table("T")
        return (
            table.add_data_field("Loc", DataType.COORDINATE),
            table.add_data_field("Locs", DataType.COORDINATE_ARRAY),
            table.add_data_field("Prof", DataType.STRING),
        )

    def test_route_scalar_returns_decimal(self):
        loc, _, _ = self._fields()
        result = formulas.ROUTE_DISTANCE(loc, loc)
        assert isinstance(result, Formula)
        assert result.data_type == DataType.DECIMAL
        assert result.formula_string == "ROUTE_DISTANCE([Loc], [Loc])"

    def test_route_array_argument_returns_array(self):
        loc, locs, _ = self._fields()
        assert formulas.ROUTE_DURATION(loc, locs).data_type == DataType.DECIMAL_ARRAY

    def test_route_profile_omitted_is_not_rendered(self):
        loc, _, _ = self._fields()
        assert "car" not in formulas.ROUTE_DISTANCE(loc, loc).formula_string

    def test_route_profile_rendered_when_given(self):
        loc, _, _ = self._fields()
        assert formulas.ROUTE_DISTANCE(loc, loc, "bike").formula_string == (
            'ROUTE_DISTANCE([Loc], [Loc], "bike")'
        )

    def test_route_rejects_non_coordinate(self):
        import pytest

        loc, _, _ = self._fields()
        with pytest.raises(ValueError):
            formulas.ROUTE_DISTANCE(1.0, loc)

    def test_path_returns_scalar_decimal(self):
        _, locs, _ = self._fields()
        result = formulas.PATH_DISTANCE(locs)
        assert result.data_type == DataType.DECIMAL
        assert result.formula_string == "PATH_DISTANCE([Locs])"

    def test_path_rejects_scalar_coordinate(self):
        import pytest

        loc, _, _ = self._fields()
        with pytest.raises(ValueError):
            formulas.PATH_DURATION(loc)

    def test_path_rejects_array_profile(self):
        import pytest

        _, locs, _ = self._fields()
        with pytest.raises(ValueError):
            formulas.PATH_DISTANCE(locs, locs)


class TestCoordinateCollectionSupport:
    """Coordinates flow through the generic-type collection/logical functions (matching the
    platform), while arithmetic/reducer functions keep rejecting them."""

    def _coords(self):
        table = ModelBuilder().add_data_table("T")
        return (
            table.add_data_field("Loc", DataType.COORDINATE),
            table.add_data_field("Locs", DataType.COORDINATE_ARRAY),
            table.add_data_field("Flags", DataType.BOOLEAN_ARRAY),
        )

    def test_accepted_collection_functions(self):
        loc, locs, flags = self._coords()
        assert formulas.DISTINCT(locs).data_type == DataType.COORDINATE_ARRAY
        assert formulas.FILTER(locs, flags).data_type == DataType.COORDINATE_ARRAY
        assert formulas.INDEX(locs, 1).data_type == DataType.COORDINATE
        assert formulas.SIZE(locs).data_type == DataType.INTEGER
        assert formulas.CONTAINS(locs, loc).data_type == DataType.BOOLEAN
        assert formulas.COUNT(locs, loc).data_type == DataType.INTEGER
        assert formulas.UNION(False, locs, locs).data_type == DataType.COORDINATE_ARRAY

    def test_accepted_logical_and_text(self):
        loc, locs, _ = self._coords()
        flag = ModelBuilder().add_data_table("U").add_data_field("F", DataType.BOOLEAN)
        assert formulas.IF(flag, loc, loc).data_type == DataType.COORDINATE
        assert formulas.IFBLANK(loc, loc).data_type == DataType.COORDINATE
        assert formulas.ISBLANK(loc).data_type == DataType.BOOLEAN
        assert formulas.TEXT(loc).data_type == DataType.STRING

    def test_arithmetic_still_rejects_coordinates(self):
        import pytest

        loc, locs, _ = self._coords()
        for build in (
            lambda: formulas.ABS(loc),
            lambda: formulas.SUM(locs),
            lambda: formulas.AVERAGE(locs),
            lambda: formulas.ROUND(loc),
        ):
            with pytest.raises(ValueError):
                build()
