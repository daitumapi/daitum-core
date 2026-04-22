"""
Tests for daitum_model: ModelBuilder, Table, Field, Formula, validators, and named values.
"""

import pytest

import daitum_model
from daitum_model import (
    DataType,
    Formula,
    LengthValidator,
    ListValidator,
    ModelBuilder,
    NonBlankValidator,
    RangeValidator,
    Severity,
    UniqueValidator,
)
from daitum_model.formula import CONST


class TestImport:
    def test_package_importable(self):
        assert daitum_model is not None

    def test_model_builder_importable(self):
        assert ModelBuilder is not None

    def test_data_type_importable(self):
        assert DataType is not None

    def test_formula_importable(self):
        assert Formula is not None


class TestModelBuilder:
    def test_instantiation(self):
        model = ModelBuilder()
        assert model is not None

    def test_add_data_table(self):
        model = ModelBuilder()
        table = model.add_data_table("Jobs")
        table.set_key_column("ID")
        assert table is not None
        assert table.id == "Jobs"

    def test_duplicate_table_raises(self):
        model = ModelBuilder()
        model.add_data_table("Jobs")
        with pytest.raises(ValueError, match="already exists"):
            model.add_data_table("Jobs")

    def test_add_calculation(self):
        model = ModelBuilder()
        calc = model.add_calculation("TOTAL_COST", CONST(0.0))
        assert calc is not None
        assert calc.id == "TOTAL_COST"

    def test_add_parameter(self):
        model = ModelBuilder()
        param = model.add_parameter("START_TIME", DataType.INTEGER, 0)
        assert param is not None
        assert param.id == "START_TIME"

    def test_get_table(self):
        model = ModelBuilder()
        model.add_data_table("Jobs")
        table = model.get_table("Jobs")
        assert table.id == "Jobs"

    def test_get_missing_table_raises(self):
        model = ModelBuilder()
        with pytest.raises(ValueError, match="does not exist"):
            model.get_table("NonExistent")

    def test_to_dict_structure(self):
        model = ModelBuilder()
        model.add_data_table("Jobs")
        model.add_calculation("COST", CONST(1.0))
        result = model.build()
        assert "tableDefinitions" in result
        assert "calculationDefinitions" in result
        assert "parameterDefinitions" in result
        assert "Jobs" in result["tableDefinitions"]
        assert "COST" in result["calculationDefinitions"]


class TestTable:
    def test_add_data_field(self):
        model = ModelBuilder()
        table = model.add_data_table("Jobs")
        field = table.add_data_field("Cost", DataType.DECIMAL)
        assert field is not None
        assert field.id == "Cost"

    def test_add_calculated_field(self):
        from daitum_model import formulas

        model = ModelBuilder()
        table = model.add_data_table("Jobs")
        cost = table.add_data_field("Cost", DataType.DECIMAL)
        calc_field = table.add_calculated_field("Is Valid", formulas.NOT(formulas.ISBLANK(cost)))
        assert calc_field is not None

    def test_table_to_dict(self):
        model = ModelBuilder()
        table = model.add_data_table("Jobs")
        table.set_key_column("ID")
        table.add_data_field("ID", DataType.STRING)
        result = table.build()
        assert "ID" in str(result)

    def test_derived_table(self):
        model = ModelBuilder()
        jobs = model.add_data_table("Jobs")
        jobs.add_data_field("Cost", DataType.DECIMAL)
        ui_jobs = model.add_derived_table("UiJobs", jobs)
        assert ui_jobs.id == "UiJobs"


class TestValidators:
    def test_range_validator_attach(self):
        model = ModelBuilder()
        table = model.add_data_table("Jobs")
        cost = table.add_data_field("Cost", DataType.DECIMAL)
        validator = RangeValidator(Severity.ERROR, 0.0, None).set_allow_blank(True)
        cost.add_validator(validator)
        ids = [f.id for f in table.get_fields()]
        assert "Cost__invalid__Error" in ids

    def test_non_blank_validator_attach(self):
        model = ModelBuilder()
        table = model.add_data_table("Jobs")
        name = table.add_data_field("Name", DataType.STRING)
        validator = NonBlankValidator(Severity.ERROR)
        name.add_validator(validator)
        ids = [f.id for f in table.get_fields()]
        assert "Name__invalid__Error" in ids

    def test_unique_validator_attach(self):
        model = ModelBuilder()
        table = model.add_data_table("Jobs")
        id_field = table.add_data_field("ID", DataType.STRING)
        validator = UniqueValidator(Severity.ERROR)
        id_field.add_validator(validator)
        ids = [f.id for f in table.get_fields()]
        assert "ID__invalid__Error" in ids

    def test_list_validator_attach(self):
        model = ModelBuilder()
        table = model.add_data_table("Jobs")
        status = table.add_data_field("Status", DataType.STRING)
        validator = ListValidator(Severity.WARNING, ["Active", "Inactive"])
        status.add_validator(validator)
        ids = [f.id for f in table.get_fields()]
        assert "Status__invalid__Warning" in ids

    def test_length_validator_attach(self):
        model = ModelBuilder()
        table = model.add_data_table("Jobs")
        tags = table.add_data_field("Tags", DataType.STRING_ARRAY)
        validator = LengthValidator(Severity.INFO, 3)
        tags.add_validator(validator)
        ids = [f.id for f in table.get_fields()]
        assert "Tags__invalid__Info" in ids

    def test_list_validator_empty_raises(self):
        with pytest.raises(ValueError, match="must not be empty"):
            ListValidator(Severity.ERROR, [])

    def test_length_validator_negative_raises(self):
        with pytest.raises(ValueError, match="non-negative"):
            LengthValidator(Severity.ERROR, -1)
