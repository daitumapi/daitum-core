"""
Tests for daitum_model.formulas: formula functions, types, and serialisation.
"""

import pytest

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


class TestChangeCalculator:
    def test_change_calculator_importable(self):
        from daitum_model import change_calculator

        assert change_calculator is not None

    def test_difference_function_exists(self):
        from daitum_model.change_calculator import difference

        assert difference is not None
