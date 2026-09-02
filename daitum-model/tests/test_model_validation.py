"""
Tests for the model-structure validation framework (:mod:`daitum_model.validation`).

Covers the three recurring defects the platform rejects — circular dependencies, invalid
field references, and missing source fields — plus the aggregate-reporting contract and the
non-raising ``validate()`` entry point.
"""

from __future__ import annotations

import pytest
from fixtures import invalid_models

from daitum_model import (
    CircularDependencyError,
    FieldReferenceError,
    MissingSourceFieldError,
    ModelValidationError,
    TableReferenceError,
)
from daitum_model.validation.engine import RULES


class TestTableCycles:
    def test_cycle_via_object_reference(self):
        report = invalid_models.table_cycle_via_reference().validate()
        assert not report.ok
        issues = [i for i in report if isinstance(i, CircularDependencyError)]
        assert len(issues) == 1
        assert "A -> B -> A" in issues[0].render()

    def test_cycle_via_formula_across_tables(self):
        # B is derived from A and a calculated field on A reads a column of B.
        report = invalid_models.table_cycle_via_formula().validate()
        cycles = [i for i in report if isinstance(i, CircularDependencyError)]
        assert len(cycles) == 1
        assert "A" in cycles[0].location and "B" in cycles[0].location

    def test_build_raises_on_cycle(self):
        with pytest.raises(ModelValidationError, match="[Cc]ircular"):
            invalid_models.table_cycle_via_reference().build()

    def test_cycle_path_ignores_self_edges(self):
        # A self-referencing calculated field adds a self-edge on A; the reported cycle path
        # must still be the real A -> B -> A loop, not a spurious "A -> A".
        report = invalid_models.table_cycle_with_self_edge().validate()
        cycles = [i for i in report if isinstance(i, CircularDependencyError)]
        assert len(cycles) == 1
        assert "A -> B -> A" in cycles[0].render()


class TestNamedValueCycles:
    def test_mutually_referencing_calculations(self):
        report = invalid_models.named_value_cycle().validate()
        cycles = [i for i in report if isinstance(i, CircularDependencyError)]
        assert len(cycles) == 1
        assert "C1 -> C2 -> C1" in cycles[0].render()


class TestFieldCycles:
    def test_plain_calculated_field_cycle_is_invalid(self):
        report = invalid_models.field_cycle_plain_calculated().validate()
        cycles = [
            i
            for i in report
            if isinstance(i, CircularDependencyError)
            and i.rule_id == "no-circular-field-dependencies"
        ]
        assert len(cycles) == 1
        assert "A -> B -> A" in cycles[0].render()

    def test_combo_pair_with_opposite_flags_is_allowed(self):
        # Only one side of a T/F combo pair is ever calculated, so the cycle never resolves.
        report = invalid_models.field_cycle_combo_opposite_flags().validate()
        assert report.by_rule("no-circular-field-dependencies") == []

    def test_combo_pair_with_same_flag_is_invalid(self):
        report = invalid_models.field_cycle_combo_same_flag().validate()
        assert report.by_rule("no-circular-field-dependencies")


class TestFieldReferences:
    def test_calculated_field_missing_reference(self):
        report = invalid_models.calculated_field_missing_reference().validate()
        issues = [i for i in report if isinstance(i, FieldReferenceError)]
        assert len(issues) == 1
        message = issues[0].render()
        assert "Val" in message
        # Reuses the "available fields" wording from Table.get_field.
        assert "available fields" in message


class TestMissingSourceFields:
    def test_derived_sort_field_not_on_source(self):
        report = invalid_models.derived_sort_field_missing().validate()
        issues = [i for i in report if isinstance(i, MissingSourceFieldError)]
        assert len(issues) == 1
        assert "sort field" in issues[0].render()
        assert "NotOnSource" in issues[0].render()


class TestTableReferences:
    def test_object_field_unknown_target_table(self):
        report = invalid_models.object_reference_unknown_table().validate()
        issues = [i for i in report if isinstance(i, TableReferenceError)]
        assert any("Ghost" in i.render() for i in issues)


class TestReportAggregation:
    def test_all_problems_reported_at_once(self):
        report = invalid_models.three_distinct_problems().validate()
        assert len(report) == 3

    def test_build_raises_single_error_listing_every_problem(self):
        with pytest.raises(ModelValidationError) as excinfo:
            invalid_models.three_distinct_problems().build()
        assert len(excinfo.value.issues) == 3

    def test_issue_order_is_deterministic(self):
        first = str(invalid_models.three_distinct_problems().validate().issues)
        second = str(invalid_models.three_distinct_problems().validate().issues)
        assert first == second


class TestStandaloneValidate:
    def test_validate_does_not_raise(self):
        report = invalid_models.named_value_cycle().validate()
        assert report.ok is False  # populated, but no exception

    def test_by_rule_filters_issues(self):
        report = invalid_models.named_value_cycle().validate()
        assert report.by_rule("no-circular-named-value-dependencies")
        assert report.by_rule("does-not-exist") == []


class TestValidModelPasses:
    def test_valid_model_has_empty_report(self):
        assert invalid_models.valid_model().validate().ok

    def test_valid_model_builds(self):
        model = invalid_models.valid_model()
        built = model.build()
        assert "Items" in built["tableDefinitions"]


class TestBuildHookGuardsWrite:
    def test_write_to_file_writes_nothing_for_invalid_model(self, tmp_path):
        with pytest.raises(ModelValidationError):
            invalid_models.named_value_cycle().write_to_file(tmp_path)
        assert not any(tmp_path.iterdir())


class TestRuleRegistry:
    def test_all_rule_ids_are_unique(self):
        ids = [r.id for r in RULES]
        assert len(ids) == len(set(ids))

    def test_registry_is_non_empty(self):
        assert RULES
