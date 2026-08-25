"""
Tests for the Reference value type (daitum_model.references).

Reference is the lever for collapsing the configuration package's "!!!<id>" build()
overrides; it must build and decode symmetrically, tested here in isolation.
"""

import pytest
from daitum_model import DataType, ModelBuilder
from daitum_model.decoding import LoadContext, LoadError
from daitum_model.references import Reference, is_reference


class TestReferenceBuild:
    def test_calculation_reference_builds_prefixed_id(self):
        from daitum_model import formulas

        model = ModelBuilder()
        table = model.add_data_table("Jobs")
        table.add_data_field("Cost", DataType.DECIMAL)
        calc = model.add_calculation("TOTAL_COST", formulas.SUM(table["Cost"]), model_level=True)

        ref = Reference(calc)
        assert ref.build() == "!!!TOTAL_COST"
        assert ref.id == "TOTAL_COST"

    def test_parameter_reference_builds_prefixed_id(self):
        model = ModelBuilder()
        param = model.add_parameter("RATE", DataType.DECIMAL, 0.1, model_level=True)
        ref = Reference(param)
        assert ref.build() == "!!!RATE"
        assert ref.id == "RATE"

    def test_field_reference_builds_prefixed_bracketed_id(self):
        model = ModelBuilder()
        table = model.add_data_table("Jobs")
        field = table.add_data_field("Cost", DataType.DECIMAL)
        ref = Reference(field)
        # Field.to_string() renders "[Cost]"; the platform reference keeps the brackets.
        assert ref.build() == "!!![Cost]"
        # The bare id strips both the prefix and the brackets.
        assert ref.id == "Cost"


class TestNumericReference:
    def test_numeric_target_builds_prefixed_number(self):
        assert Reference(1.5).build() == "!!!1.5"
        assert Reference(3).build() == "!!!3"

    def test_numeric_reference_decodes_to_number(self):
        assert Reference.decode("!!!1.5", LoadContext()).target == 1.5
        assert Reference.decode("!!!3", LoadContext()).target == 3

    def test_numeric_round_trip(self):
        for n in (1.5, 3, 2.5, 0):
            ref = Reference(n)
            assert Reference.decode(ref.build(), LoadContext()).build() == ref.build()


class TestReferenceDecode:
    def test_decode_resolves_via_context(self):
        model = ModelBuilder()
        param = model.add_parameter("RATE", DataType.DECIMAL, 0.1, model_level=True)

        ctx = LoadContext()
        ctx.register("RATE", param)

        decoded = Reference.decode("!!!RATE", ctx)
        assert isinstance(decoded, Reference)
        assert decoded.target is param

    def test_decode_field_reference_strips_brackets(self):
        model = ModelBuilder()
        table = model.add_data_table("Jobs")
        field = table.add_data_field("Cost", DataType.DECIMAL)

        ctx = LoadContext()
        ctx.register("Cost", field)

        decoded = Reference.decode("!!![Cost]", ctx)
        assert decoded.target is field

    def test_decode_unresolved_raises(self):
        with pytest.raises(LoadError):
            Reference.decode("!!!MISSING", LoadContext())

    def test_decode_non_reference_raises(self):
        with pytest.raises(ValueError):
            Reference.decode("RATE", LoadContext())


class TestReferenceRoundTrip:
    def test_build_then_decode_recovers_target(self):
        model = ModelBuilder()
        param = model.add_parameter("RATE", DataType.DECIMAL, 0.1, model_level=True)

        ref = Reference(param)
        built = ref.build()

        ctx = LoadContext()
        ctx.register("RATE", param)

        assert Reference.decode(built, ctx).build() == built


class TestHelpers:
    def test_is_reference(self):
        assert is_reference("!!!X")
        assert not is_reference("X")
        assert not is_reference(5)

    def test_equality_and_hash(self):
        model = ModelBuilder()
        p = model.add_parameter("RATE", DataType.DECIMAL, 0.1, model_level=True)
        assert Reference(p) == Reference(p)
        assert hash(Reference(p)) == hash(Reference(p))
