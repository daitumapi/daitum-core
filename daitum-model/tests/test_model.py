"""
Tests for daitum_model: ModelBuilder, Table, Field, Formula, validators, and named values.
"""

import daitum_model
import pytest
from daitum_model import (
    DataType,
    Formula,
    JoinCondition,
    JoinType,
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

    def test_group_by_and_set_filter_field_are_chainable(self):
        model = ModelBuilder()
        src = model.add_data_table("Src")
        cat = src.add_data_field("Cat", DataType.STRING)
        keep = src.add_data_field("Keep", DataType.BOOLEAN)
        derived = model.add_derived_table("D", src)
        assert derived.group_by(cat) is derived
        assert derived.set_filter_field(keep) is derived
        assert derived.grouping_configuration.group_by_fields == ["Cat"]
        assert derived.filter_field == "Keep"

    def test_group_by_with_no_fields_collapses_to_single_row(self):
        model = ModelBuilder()
        src = model.add_data_table("Src")
        src.add_data_field("Cat", DataType.STRING)
        derived = model.add_derived_table("D", src).group_by()
        assert derived.grouping_configuration.group_by_fields == []

    def test_set_filter_field_rejects_non_boolean(self):
        model = ModelBuilder()
        src = model.add_data_table("Src")
        cat = src.add_data_field("Cat", DataType.STRING)
        derived = model.add_derived_table("D", src)
        with pytest.raises(ValueError, match="Cannot filter on field"):
            derived.set_filter_field(cat)

    def test_add_pivot_synthesises_columns_and_serialises(self):
        model = ModelBuilder()
        src = model.add_data_table("Src")
        src.add_data_field("Loc", DataType.STRING)
        hour = src.add_data_field("Hour", DataType.INTEGER)
        value = src.add_data_field("Value", DataType.DECIMAL)
        derived = model.add_derived_table("Report", src).group_by(src.get_field("Loc"))
        pivot = derived.add_pivot(hour, value)
        assert pivot.add_column("H0", 0) is pivot
        pivot.add_column("H1", 1)

        field_ids = [f.id for f in derived.get_fields()]
        assert "H0" in field_ids and "H1" in field_ids
        assert derived.get_field("H0").data_type == DataType.DECIMAL

        # Each pivot column serialises as a keyed aggregated field.
        aggregated = derived.build()["groupingConfiguration"]["aggregatedFields"]
        assert aggregated == [
            {
                "aggregatedFieldId": "H0",
                "sourceFieldId": "Value",
                "aggregationMethod": "FIRST",
                "keyField": "Hour",
                "keyValue": 0,
            },
            {
                "aggregatedFieldId": "H1",
                "sourceFieldId": "Value",
                "aggregationMethod": "FIRST",
                "keyField": "Hour",
                "keyValue": 1,
            },
        ]

    def test_add_pivot_requires_grouping(self):
        model = ModelBuilder()
        src = model.add_data_table("Src")
        hour = src.add_data_field("Hour", DataType.INTEGER)
        value = src.add_data_field("Value", DataType.DECIMAL)
        derived = model.add_derived_table("Report", src)
        with pytest.raises(ValueError, match="no grouped fields"):
            derived.add_pivot(hour, value)

    def test_add_pivot_rejects_reference(self):
        from daitum_model import AggregationMethod

        model = ModelBuilder()
        src = model.add_data_table("Src")
        hour = src.add_data_field("Hour", DataType.INTEGER)
        value = src.add_data_field("Value", DataType.DECIMAL)
        derived = model.add_derived_table("Report", src).group_by()
        with pytest.raises(ValueError, match="REFERENCE"):
            derived.add_pivot(hour, value, AggregationMethod.REFERENCE)

    def test_deprecated_kwargs_still_work_and_warn(self):
        model = ModelBuilder()
        src = model.add_data_table("Src")
        cat = src.add_data_field("Cat", DataType.STRING)
        keep = src.add_data_field("Keep", DataType.BOOLEAN)
        with pytest.warns(UserWarning, match="deprecated.*group_by"):
            derived = model.add_derived_table("D", src, group_by=[cat])
        with pytest.warns(UserWarning, match="deprecated.*set_filter_field"):
            model.add_derived_table("D2", src, filter_field=keep)
        assert derived.grouping_configuration.group_by_fields == ["Cat"]


class TestFoldedTable:
    def _roster(self):
        model = ModelBuilder()
        roster = model.add_data_table("Roster")
        roster.add_data_field("Employee", DataType.STRING)
        roster.add_data_field("Day1Wages", DataType.DECIMAL)
        roster.add_data_field("Day2Wages", DataType.DECIMAL)
        return model, roster

    def test_fold_with_literal_labels(self):
        model, roster = self._roster()
        folded = model.add_folded_table("Long", roster)
        folded.add_column("Day", DataType.INTEGER)
        folded.add_column("Wages", DataType.DECIMAL)
        folded.carry(roster.get_field("Employee"))
        folded.fold(Day=1, Wages=roster.get_field("Day1Wages"))
        folded.fold(Day=2, Wages=roster.get_field("Day2Wages"))

        built = folded.table.build()
        assert list(built["fieldDefinitions"]) == ["Day", "Wages", "Employee"]
        mappings = built["fieldMappings"]
        assert len(mappings) == 2
        first = mappings["Roster#0"]
        assert first["Wages"] == "Day1Wages"
        assert first["Employee"] == "Employee"
        # literal label folded in as a synthesised constant field on the source
        assert first["Day"].startswith("__fold__")

    def test_fold_with_source_label_columns_does_not_mutate_source(self):
        model, roster = self._roster()
        roster.add_data_field("Day1Label", DataType.STRING)
        roster.add_data_field("Day2Label", DataType.STRING)
        folded = model.add_folded_table("Long", roster)
        folded.add_column("Day", DataType.STRING)
        folded.add_column("Wages", DataType.DECIMAL)
        folded.carry(roster.get_field("Employee"))
        folded.fold(Day=roster.get_field("Day1Label"), Wages=roster.get_field("Day1Wages"))
        folded.fold(Day=roster.get_field("Day2Label"), Wages=roster.get_field("Day2Wages"))

        mappings = folded.table.build()["fieldMappings"]
        assert mappings["Roster#0"]["Day"] == "Day1Label"
        assert not [f for f in roster.field_definitions if f.startswith("__fold")]

    def test_fold_rejects_missing_unknown_and_carried_columns(self):
        model, roster = self._roster()
        folded = model.add_folded_table("Long", roster)
        folded.add_column("Day", DataType.INTEGER)
        folded.add_column("Wages", DataType.DECIMAL)
        folded.carry(roster.get_field("Employee"))
        with pytest.raises(ValueError, match="missing"):
            folded.fold(Wages=roster.get_field("Day1Wages"))
        with pytest.raises(ValueError, match="Unknown"):
            folded.fold(Day=1, Wages=roster.get_field("Day1Wages"), Bogus=2)
        with pytest.raises(ValueError, match="Carried"):
            folded.fold(
                Employee=roster.get_field("Employee"),
                Day=1,
                Wages=roster.get_field("Day1Wages"),
            )

    def test_folded_table_registered_on_model(self):
        model, roster = self._roster()
        folded = model.add_folded_table("Long", roster)
        assert folded.table is model.get_table("Long")


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


class TestUnionTable:
    def _make_union(self):
        model = ModelBuilder()
        t1 = model.add_data_table("TableA")
        t1.add_data_field("Cost", DataType.DECIMAL)
        t1.add_data_field("Name", DataType.STRING)
        t2 = model.add_data_table("TableB")
        t2.add_data_field("Cost", DataType.DECIMAL)
        t2.add_data_field("Name", DataType.INTEGER)  # incompatible with union field
        union = model.add_union_table("Union", [t1, t2])
        union.add_field("Cost", DataType.DECIMAL)
        union.add_field("Name", DataType.STRING)
        return union, t1, t2

    def test_add_field_mapping_compatible_type_succeeds(self):
        union, t1, t2 = self._make_union()
        union.add_field_mapping(t1, "Cost", t1.get_field("Cost"))

    def test_add_field_mapping_incompatible_type_raises(self):
        union, t1, t2 = self._make_union()
        # TableB.Name is INTEGER but UnionTable.Name is STRING — must be rejected
        with pytest.raises(ValueError, match="Data type mismatch"):
            union.add_field_mapping(t2, "Name", t2.get_field("Name"))

    def test_add_field_mapping_unknown_union_field_raises(self):
        union, t1, _ = self._make_union()
        with pytest.raises(ValueError, match="does not exist in the UnionTable"):
            union.add_field_mapping(t1, "NonExistent", t1.get_field("Cost"))

    def test_add_field_mapping_unregistered_table_raises(self):
        union, _, _ = self._make_union()
        model = ModelBuilder()
        outsider = model.add_data_table("Outsider")
        outsider.add_data_field("Cost", DataType.DECIMAL)
        with pytest.raises(ValueError, match="does not appear in the UnionTable"):
            union.add_field_mapping(outsider, "Cost", outsider.get_field("Cost"))

    def test_direct_field_mapping_compatible_types_succeeds(self):
        model = ModelBuilder()
        t1 = model.add_data_table("TableA")
        t1.add_data_field("Cost", DataType.DECIMAL)
        t2 = model.add_data_table("TableB")
        t2.add_data_field("Cost", DataType.DECIMAL)
        union = model.add_union_table("Union", [t1, t2])
        union.add_field("Cost", DataType.DECIMAL)
        union.direct_field_mapping()  # should not raise

    def test_direct_field_mapping_incompatible_type_raises(self):
        union, t1, t2 = self._make_union()
        # t2.Name is INTEGER but union.Name is STRING — auto-mapping must raise
        with pytest.raises(ValueError, match="Data type mismatch"):
            union.direct_field_mapping()


class TestJoinedTable:
    def _make_tables(self):
        model = ModelBuilder()
        orders = model.add_data_table("Orders")
        orders.add_data_field("CustomerId", DataType.STRING)
        customers = model.add_data_table("Customers")
        customers.add_data_field("Id", DataType.STRING)
        return model, orders, customers

    def test_matching_join_with_fields_succeeds(self):
        _, orders, customers = self._make_tables()
        condition = JoinCondition(
            orders,
            customers,
            JoinType.INNER,
            left_field=orders.get_field("CustomerId"),
            right_field=customers.get_field("Id"),
        )
        built = condition.build()
        assert built["joinType"] == "INNER"
        assert built["leftTableField"] == "CustomerId"
        assert built["rightTableField"] == "Id"

    def test_matching_join_without_fields_raises(self):
        _, orders, customers = self._make_tables()
        with pytest.raises(ValueError, match="requires both left_field and right_field"):
            JoinCondition(orders, customers, JoinType.LEFT)

    def test_cross_join_without_fields_succeeds(self):
        _, orders, customers = self._make_tables()
        condition = JoinCondition(orders, customers, JoinType.CROSS)
        built = condition.build()
        assert built["joinType"] == "CROSS"
        # No match fields should be serialised for a CROSS join.
        assert "leftTableField" not in built
        assert "rightTableField" not in built
        assert condition.left_field is None
        assert condition.right_field is None

    def test_cross_join_with_fields_raises(self):
        _, orders, customers = self._make_tables()
        with pytest.raises(ValueError, match="CROSS join.*no match fields"):
            JoinCondition(
                orders,
                customers,
                JoinType.CROSS,
                left_field=orders.get_field("CustomerId"),
                right_field=customers.get_field("Id"),
            )

    def test_cross_join_with_single_field_raises(self):
        _, orders, customers = self._make_tables()
        with pytest.raises(ValueError, match="CROSS join.*no match fields"):
            JoinCondition(
                orders,
                customers,
                JoinType.CROSS,
                left_field=orders.get_field("CustomerId"),
            )


class TestTracking:
    def test_tracking_groups_and_baselines_serialise(self):
        from daitum_model import AutoCapture

        model = ModelBuilder()
        edits = model.add_tracking_group("edits")
        model.add_baseline("optimised", [edits], auto_capture=AutoCapture.OPTIMISATION_COMPLETED)
        table = model.add_data_table("Sales")
        table.set_id_field("id")
        table.add_data_field("id", DataType.STRING)
        table.add_data_field("revenue", DataType.DECIMAL).set_tracking_groups([edits])

        out = model.build()
        assert out["trackingGroupDefinitions"] == {"edits": {"name": "edits"}}
        assert out["baselineDefinitions"]["optimised"] == {
            "name": "optimised",
            "trackingGroups": ["edits"],
            "autoCapture": "OPTIMISATION_COMPLETED",
        }
        revenue = out["tableDefinitions"]["Sales"]["fieldDefinitions"]["revenue"]
        assert revenue["trackingGroups"] == ["edits"]

    def test_untracked_model_omits_tracking_keys(self):
        model = ModelBuilder()
        model.add_data_table("Jobs").add_data_field("Cost", DataType.DECIMAL)
        out = model.build()
        assert "trackingGroupDefinitions" not in out
        assert "baselineDefinitions" not in out

    def test_set_tracking_groups_accepts_names(self):
        model = ModelBuilder()
        model.add_tracking_group("edits")
        model.add_baseline("b", ["edits"])
        table = model.add_data_table("Sales")
        table.set_id_field("id")
        table.add_data_field("id", DataType.STRING)
        field = table.add_data_field("revenue", DataType.DECIMAL).set_tracking_groups(["edits"])
        assert field.tracking_groups == ["edits"]

    def test_tracked_field_without_id_field_raises(self):
        model = ModelBuilder()
        edits = model.add_tracking_group("edits")
        model.add_baseline("b", [edits])
        table = model.add_data_table("Sales")
        table.add_data_field("revenue", DataType.DECIMAL).set_tracking_groups([edits])
        with pytest.raises(ValueError, match="id_field"):
            model.build()

    def test_undeclared_group_on_element_raises(self):
        model = ModelBuilder()
        table = model.add_data_table("Sales")
        table.set_id_field("id")
        table.add_data_field("id", DataType.STRING)
        table.add_data_field("revenue", DataType.DECIMAL).set_tracking_groups(["ghost"])
        with pytest.raises(ValueError, match="undeclared tracking group"):
            model.build()

    def test_baseline_with_undeclared_group_raises(self):
        model = ModelBuilder()
        model.add_baseline("b", ["ghost"])
        with pytest.raises(ValueError, match="undeclared tracking group"):
            model.build()

    def test_uncaptured_group_warns(self):
        model = ModelBuilder()
        lonely = model.add_tracking_group("lonely")
        table = model.add_data_table("Sales")
        table.set_id_field("id")
        table.add_data_field("id", DataType.STRING)
        table.add_data_field("x", DataType.DECIMAL).set_tracking_groups([lonely])
        with pytest.warns(UserWarning, match="not captured by any baseline"):
            model.build()

    def test_duplicate_tracking_group_raises(self):
        model = ModelBuilder()
        model.add_tracking_group("edits")
        with pytest.raises(ValueError, match="already exists"):
            model.add_tracking_group("edits")

    def test_duplicate_baseline_raises(self):
        model = ModelBuilder()
        model.add_baseline("b", [])
        with pytest.raises(ValueError, match="already exists"):
            model.add_baseline("b", [])
