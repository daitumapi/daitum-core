"""
Baseline change-tracking framework tests.

Covers the model-level declarations (tracking groups, baselines, ``set_tracking_groups``,
``set_id_field``), the ``build()`` output, the build-time validation rules, and a full
encode -> decode -> rebuild round-trip of a tracked model — the surface introduced when the
baseline framework met the rewritten formula/decoder architecture.
"""

import pytest
from daitum_model import AutoCapture, Baseline, DataType, ModelBuilder, TrackingGroup, formulas


def _tracked_model() -> ModelBuilder:
    model = ModelBuilder()
    edits = model.add_tracking_group("edits")
    model.add_baseline("optimised", [edits], auto_capture=AutoCapture.OPTIMISATION_COMPLETED)
    sales = model.add_data_table("Sales")
    sales.set_id_field("id")
    sales.add_data_field("id", DataType.STRING)
    sales.add_data_field("revenue", DataType.DECIMAL).set_tracking_groups([edits])
    return model


class TestDeclarations:
    def test_add_tracking_group_returns_group(self):
        model = ModelBuilder()
        group = model.add_tracking_group("edits")
        assert isinstance(group, TrackingGroup)
        assert group.name == "edits"

    def test_duplicate_tracking_group_raises(self):
        model = ModelBuilder()
        model.add_tracking_group("edits")
        with pytest.raises(ValueError, match="already exists"):
            model.add_tracking_group("edits")

    def test_add_baseline_returns_baseline(self):
        model = ModelBuilder()
        group = model.add_tracking_group("edits")
        baseline = model.add_baseline("optimised", [group])
        assert isinstance(baseline, Baseline)
        assert baseline.tracking_groups == ["edits"]
        assert baseline.auto_capture is AutoCapture.NONE

    def test_duplicate_baseline_raises(self):
        model = ModelBuilder()
        group = model.add_tracking_group("edits")
        model.add_baseline("optimised", [group])
        with pytest.raises(ValueError, match="already exists"):
            model.add_baseline("optimised", [group])

    def test_baseline_accepts_group_names_or_objects(self):
        model = ModelBuilder()
        model.add_tracking_group("a")
        b = model.add_tracking_group("b")
        baseline = model.add_baseline("base", ["a", b])
        assert baseline.tracking_groups == ["a", "b"]


class TestBuildOutput:
    def test_emits_definitions_when_declared(self):
        built = _tracked_model().build()
        assert built["trackingGroupDefinitions"] == {"edits": {"name": "edits"}}
        assert built["baselineDefinitions"]["optimised"] == {
            "name": "optimised",
            "trackingGroups": ["edits"],
            "autoCapture": "OPTIMISATION_COMPLETED",
        }

    def test_field_emits_tracking_groups(self):
        model = _tracked_model()
        field = model.get_table("Sales").get_field("revenue")
        assert field.build()["trackingGroups"] == ["edits"]

    def test_untracked_model_emits_no_tracking_keys(self):
        model = ModelBuilder()
        model.add_data_table("T").add_data_field("x", DataType.DECIMAL)
        built = model.build()
        assert "trackingGroupDefinitions" not in built
        assert "baselineDefinitions" not in built

    def test_set_tracking_groups_clears_on_empty_list(self):
        model = ModelBuilder()
        group = model.add_tracking_group("edits")
        field = model.add_data_table("T").add_data_field("x", DataType.DECIMAL)
        field.set_tracking_groups([group])
        assert field.tracking_groups == ["edits"]
        field.set_tracking_groups([])
        assert field.tracking_groups is None


class TestValidation:
    def test_element_references_undeclared_group_raises(self):
        model = ModelBuilder()
        table = model.add_data_table("T")
        table.set_id_field("id")
        table.add_data_field("id", DataType.STRING)
        table.add_data_field("x", DataType.DECIMAL).set_tracking_groups(["ghost"])
        with pytest.raises(ValueError, match="undeclared tracking group"):
            model.build()

    def test_baseline_references_undeclared_group_raises(self):
        model = ModelBuilder()
        model.add_baseline("base", ["ghost"])
        with pytest.raises(ValueError, match="undeclared tracking group"):
            model.build()

    def test_tracked_field_without_id_field_raises(self):
        model = ModelBuilder()
        group = model.add_tracking_group("edits")
        model.add_baseline("base", [group])
        table = model.add_data_table("T")
        table.add_data_field("x", DataType.DECIMAL).set_tracking_groups([group])
        with pytest.raises(ValueError, match="id_field"):
            model.build()

    def test_group_captured_by_no_baseline_warns(self):
        model = ModelBuilder()
        group = model.add_tracking_group("orphan")
        table = model.add_data_table("T")
        table.set_id_field("id")
        table.add_data_field("id", DataType.STRING)
        table.add_data_field("x", DataType.DECIMAL).set_tracking_groups([group])
        with pytest.warns(UserWarning, match="not captured by any baseline"):
            model.build()

    def test_tracked_calculation_and_parameter_validate(self):
        model = ModelBuilder()
        group = model.add_tracking_group("g")
        model.add_baseline("base", [group])
        calc = model.add_calculation("C", formulas.CONST(1)).set_tracking_groups([group])
        param = model.add_parameter("P", DataType.DECIMAL, 1.0).set_tracking_groups([group])
        assert calc.tracking_groups == ["g"]
        assert param.tracking_groups == ["g"]
        # Builds without error: both groups are captured and need no id_field (named values).
        model.build()


class TestRoundTrip:
    def test_tracked_model_round_trips(self):
        model = _tracked_model()
        # A calculated field that reads the baseline, to exercise BASELINE decode too. This lives
        # on Sales (a per-row context) so the bare ``revenue`` reference resolves locally — a
        # calculation has no table and could not reference the field directly.
        sales = model.get_table("Sales")
        revenue = sales.get_field("revenue")
        sales.add_calculated_field("delta", revenue - formulas.BASELINE("optimised", revenue))
        built = model.build()
        reloaded = ModelBuilder.read_from_dict(built)
        assert reloaded.build() == built

    def test_baseline_formula_in_calculated_field_round_trips(self):
        model = ModelBuilder()
        group = model.add_tracking_group("edits")
        model.add_baseline("optimised", [group])
        sales = model.add_data_table("Sales")
        sales.set_id_field("id")
        sales.add_data_field("id", DataType.STRING)
        revenue = sales.add_data_field("revenue", DataType.DECIMAL).set_tracking_groups([group])
        sales.add_calculated_field(
            "changed",
            formulas.IF(revenue.not_equal_to(formulas.BASELINE("optimised", revenue)), 1, 0),
        )
        built = model.build()
        reloaded = ModelBuilder.read_from_dict(built)
        assert reloaded.build() == built
