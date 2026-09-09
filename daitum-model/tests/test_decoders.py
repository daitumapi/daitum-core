# Copyright 2026 Daitum
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
Structural round-trip tests for the model decoder layer (``daitum_model._decoders``).

Each test follows the contract ``decode(x.build()).build() == x.build()``, building
fixtures from real builder construction so they never drift from ``build()`` output.
"""

import daitum_model.formulas as formulas
import pytest
from daitum_model import (
    AggregationMethod,
    Calculation,
    DataType,
    JoinCondition,
    JoinType,
    MapDataType,
    ModelBuilder,
    ModelValidationError,
    ObjectDataType,
    Parameter,
    SortDirection,
)
from daitum_model._decoders.data_types import decode_data_type
from daitum_model._decoders.model import decode_model
from daitum_model._decoders.named_values import decode_calculation, decode_parameter
from daitum_model.decoding import LoadContext, LoadError, decode_into
from daitum_model.fields import CalculatedField, ComboField, DataField, Field
from daitum_model.formula import Formula
from daitum_model.tables import DataTable, Table


class TestDataTypeCoercion:
    def test_primitive_string_round_trips(self):
        for dt in (DataType.INTEGER, DataType.DECIMAL, DataType.STRING, DataType.DATE_ARRAY):
            built = dt.value
            decoded = decode_data_type(built, LoadContext())
            assert decoded is dt

    def test_object_data_type_round_trips(self):
        model = ModelBuilder()
        table = model.add_data_table("People")
        table.add_data_field("Name", DataType.STRING)
        ctx = LoadContext()
        ctx.register("People", table)
        original = ObjectDataType(table)
        decoded = decode_data_type(original.build(), ctx)
        assert isinstance(decoded, ObjectDataType)
        assert decoded.build() == original.build()
        assert decoded.is_array() is False

    def test_object_array_data_type_round_trips(self):
        model = ModelBuilder()
        table = model.add_data_table("People")
        ctx = LoadContext()
        ctx.register("People", table)
        original = ObjectDataType(table, is_array=True)
        decoded = decode_data_type(original.build(), ctx)
        assert isinstance(decoded, ObjectDataType)
        assert decoded.is_array() is True
        assert decoded.build() == original.build()

    def test_map_data_type_round_trips(self):
        model = ModelBuilder()
        table = model.add_data_table("People")
        ctx = LoadContext()
        ctx.register("People", table)
        original = MapDataType(DataType.DECIMAL, table)
        decoded = decode_data_type(original.build(), ctx)
        assert isinstance(decoded, MapDataType)
        assert decoded.data_type is DataType.DECIMAL
        assert decoded.build() == original.build()


class TestFormula:
    def test_primitive_formula_round_trips(self):
        model = ModelBuilder()
        table = model.add_data_table("Items")
        cost = table.add_data_field("Cost", DataType.DECIMAL)
        ctx = LoadContext()
        ctx.register("Items", table)
        original = formulas.SUM(cost)
        decoded = decode_into(Formula, original.build(), ctx)
        assert isinstance(decoded, Formula)
        assert decoded.data_type is DataType.DECIMAL
        assert decoded.build() == original.build()

    def test_object_typed_formula_round_trips(self):
        model = ModelBuilder()
        table = model.add_data_table("People")
        table.add_data_field("Age", DataType.INTEGER)
        ctx = LoadContext()
        ctx.register("People", table)
        # A bare table used as an operand renders as its id and is OBJECT_ARRAY-typed.
        original = formulas.ROWS(table)
        decoded = decode_into(Formula, original.build(), ctx)
        assert decoded.build() == original.build()

    def test_decoded_formula_regains_structure_and_dependencies(self):
        """End-state payoff: a decoded formula is a structured tree, not a string leaf, so it
        reports the reference leaves it uses."""
        model = ModelBuilder()
        table = model.add_data_table("Jobs")
        cost = table.add_data_field("Cost", DataType.DECIMAL)
        qty = table.add_data_field("Qty", DataType.INTEGER)
        ctx = LoadContext()
        ctx.register("Jobs", table)
        ctx.register("Cost", cost)
        ctx.register("Qty", qty)

        original = formulas.SUM(cost, qty)
        decoded = decode_into(Formula, original.build(), ctx)

        assert decoded.build() == original.build()
        assert {d.to_string() for d in decoded.dependencies()} == {"[Cost]", "[Qty]"}

    def test_bare_reference_formula_round_trips(self):
        """A calculated field may just alias another field or named value — its formula is a bare
        ``[field]`` / id reference, not a compound expression. The builder wraps that in a Constant,
        so the decoder must too (parse_formula resolves it to the referenced operand), rather than
        rejecting it as "not a formula"."""
        model = ModelBuilder()
        table = model.add_data_table("T")
        table.add_data_field("ExpirationDate", DataType.DATE)
        table.add_calculated_field("Alias", table.get_field("ExpirationDate"))
        param = model.add_parameter("Threshold", DataType.INTEGER, 5, model_level=True)
        table.add_calculated_field("AliasParam", param)

        built = model.build()
        fields = built["tableDefinitions"]["T"]["fieldDefinitions"]
        assert fields["Alias"]["formula"]["formulaString"] == "[ExpirationDate]"
        assert fields["AliasParam"]["formula"]["formulaString"] == "Threshold"

        decoded = decode_model(built, LoadContext())
        assert decoded.build() == built

    def test_nested_blank_in_formula_round_trips(self):
        """A nested ``BLANK()`` (the fallback of an ``IFERROR`` inside an array-typed formula) must
        decode as untyped NULL, not re-typed to the whole formula's array type — otherwise IFERROR's
        branch-type check rejects it and the formula fails to decode. Mirrors the reported
        ``ARRAY(TRUE, IFERROR(LOOKUP(...), BLANK()))`` shape."""
        model = ModelBuilder()
        table = model.add_data_table("T")
        table.add_data_field("Qty", DataType.INTEGER)
        table.add_calculated_field(
            "X", formulas.ARRAY(True, formulas.IFERROR(table["Qty"], formulas.BLANK()))
        )
        built = model.build()
        formula = built["tableDefinitions"]["T"]["fieldDefinitions"]["X"]["formula"]
        assert formula["formulaString"] == "ARRAY(TRUE, IFERROR(T[Qty], BLANK()))"
        assert formula["dataType"] == "INTEGER_ARRAY"

        decoded = decode_model(built, LoadContext())
        assert decoded.build() == built

    def test_formula_with_escaped_quote_string_literal_round_trips(self):
        """A string literal may contain an escaped quote (``\\"``). The tokeniser must not treat it
        as the literal's end, and the renderer must re-emit it — mirrors the reported
        ``TEXTJOIN(..., "\\"", ...)`` formula that builds a JSON-like string."""
        from daitum_model.formula import CONST

        model = ModelBuilder()
        table = model.add_data_table("T")
        table.add_data_field("Name", DataType.STRING)
        table.add_calculated_field("X", formulas.TEXTJOIN(CONST('"'), True, table["Name"]))
        built = model.build()
        assert (
            built["tableDefinitions"]["T"]["fieldDefinitions"]["X"]["formula"]["formulaString"]
            == 'TEXTJOIN("\\"", TRUE, T[Name])'
        )

        decoded = decode_model(built, LoadContext())
        assert decoded.build() == built

    def test_foreign_unparenthesised_formula_normalises(self):
        """A formula generated elsewhere may omit the canonical per-operation brackets and rely on
        standard precedence. The decoder accepts it and normalises it to the canonical rendering
        (the parse is verified faithful by the fixed-point check, not byte-identity)."""
        model = ModelBuilder()
        table = model.add_data_table("T")
        for fid in ("A", "B", "C"):
            table.add_data_field(fid, DataType.INTEGER)
        table.add_calculated_field("X", table["A"])
        built = model.build()
        formula = built["tableDefinitions"]["T"]["fieldDefinitions"]["X"]["formula"]
        formula["formulaString"] = "T[A] - T[B] + 28 * T[C]"
        formula["dataType"] = "INTEGER_ARRAY"

        decoded = decode_model(built, LoadContext())
        rebuilt = decoded.get_table("T").get_field("X").build()["formula"]["formulaString"]
        assert rebuilt == "((T[A] - T[B]) + (28 * T[C]))"

    def test_library_rendered_formula_round_trips_byte_for_byte(self):
        """A formula this library produced is already canonical, so it decodes to a byte-identical
        string — the exactness guarantee for our own output is preserved."""
        model = ModelBuilder()
        table = model.add_data_table("T")
        for fid in ("A", "B", "C"):
            table.add_data_field(fid, DataType.INTEGER)
        table.add_calculated_field("Y", table["A"] - table["B"] + 28 * table["C"])
        built = model.build()
        original = built["tableDefinitions"]["T"]["fieldDefinitions"]["Y"]["formula"][
            "formulaString"
        ]

        decoded = decode_model(built, LoadContext())
        rebuilt = decoded.get_table("T").get_field("Y").build()["formula"]["formulaString"]
        assert rebuilt == original

    def test_corrupt_formula_still_fails_loudly(self):
        """An unparseable formula string is rejected with a LoadError — the decoder never fabricates
        a degraded result."""
        import pytest

        model = ModelBuilder()
        table = model.add_data_table("T")
        table.add_data_field("A", DataType.INTEGER)
        table.add_calculated_field("X", table["A"])
        built = model.build()
        built["tableDefinitions"]["T"]["fieldDefinitions"]["X"]["formula"][
            "formulaString"
        ] = "T[A] + + )"
        with pytest.raises(LoadError):
            decode_model(built, LoadContext())

    def test_loaded_model_calculations_are_structured(self):
        """A model loaded from file has fully structured formulas, so its calculated fields report
        real dependencies (every formula is parsed into a tree — the decode fails otherwise)."""
        from pathlib import Path

        model_dir = Path(__file__).resolve().parents[2] / "model-files"
        if not (model_dir / "model-definition.json").exists():
            import pytest

            pytest.skip("golden model-files not present")
        loaded = ModelBuilder.read_from_file(model_dir)
        formula_fields = [
            fld
            for table in loaded.get_tables()
            for fld in table.get_fields()
            if hasattr(fld, "formula")
        ]
        assert formula_fields, "expected the golden model to contain calculated fields"
        # Every calculated field exposes a structured dependency set (possibly empty for a constant).
        for fld in formula_fields:
            assert isinstance(fld.dependencies(), set)


class TestFields:
    def test_data_field_round_trips(self):
        model = ModelBuilder()
        table = model.add_data_table("Jobs")
        field = table.add_data_field("Cost", DataType.DECIMAL).set_unique(True)
        built = field.build()
        ctx = LoadContext()
        ctx.register("Jobs", table)
        decoded = decode_into(Field, built, ctx)
        assert isinstance(decoded, DataField)
        assert decoded.data_type is DataType.DECIMAL
        assert decoded.unique is True
        assert decoded.build() == built

    def test_data_field_with_default_and_format(self):
        model = ModelBuilder()
        table = model.add_data_table("Jobs")
        field = (
            table.add_data_field("Start", DataType.DATE)
            .set_default_value([2026, 1, 1])
            .set_import_format("yyyy-MM-dd")
            .set_nullable(True)
        )
        built = field.build()
        ctx = LoadContext()
        ctx.register("Jobs", table)
        decoded = decode_into(Field, built, ctx)
        assert decoded.build() == built

    def test_calculated_field_round_trips(self):
        model = ModelBuilder()
        table = model.add_data_table("Jobs")
        table.add_data_field("Qty", DataType.INTEGER)
        field = table.add_calculated_field("Doubled", table["Qty"])
        built = field.build()
        ctx = LoadContext()
        ctx.register("Jobs", table)
        decoded = decode_into(Field, built, ctx)
        assert isinstance(decoded, CalculatedField)
        assert decoded.build() == built

    def test_combo_field_round_trips(self):
        model = ModelBuilder()
        table = model.add_data_table("Jobs")
        table.add_data_field("Qty", DataType.INTEGER)
        field = table.add_combo_field("Cmb", table["Qty"], True)
        built = field.build()
        ctx = LoadContext()
        ctx.register("Jobs", table)
        decoded = decode_into(Field, built, ctx)
        assert isinstance(decoded, ComboField)
        assert decoded.calculate_in_optimiser is True
        assert decoded.build() == built

    def test_object_reference_field_round_trips(self):
        model = ModelBuilder()
        people = model.add_data_table("People")
        people.add_data_field("Name", DataType.STRING)
        jobs = model.add_data_table("Jobs")
        field = jobs.add_object_reference_field("Owner", people)
        built = field.build()
        ctx = LoadContext()
        ctx.register("People", people)
        ctx.register("Jobs", jobs)
        decoded = decode_into(Field, built, ctx)
        assert isinstance(decoded.data_type, ObjectDataType)
        assert decoded.build() == built


class TestNamedValues:
    # build() omits the id (it keys the parent map), so named values are decoded with the id
    # injected and a model in the load context, exactly as the model decoder does it.
    def test_calculation_round_trips(self):
        model = ModelBuilder()
        table = model.add_data_table("Items")
        table.add_data_field("Cost", DataType.DECIMAL)
        calc = (
            model.add_calculation("TOTAL", formulas.SUM(table["Cost"]), model_level=True)
            .set_depends_on_decision(True)
            .set_required_by_output(True)
        )
        built = calc.build()
        decoded = decode_calculation({**built, "id": "TOTAL"}, LoadContext(model=ModelBuilder()))
        assert isinstance(decoded, Calculation)
        assert decoded.build() == built

    def test_parameter_round_trips(self):
        model = ModelBuilder()
        param = model.add_parameter("BUDGET", DataType.DECIMAL, 100.0, model_level=True)
        param.set_import_format("yyyy")
        built = param.build()
        decoded = decode_parameter({**built, "id": "BUDGET"}, LoadContext(model=ModelBuilder()))
        assert isinstance(decoded, Parameter)
        assert decoded.build() == built


class TestTables:
    def _round_trip_table(self, table: Table, ctx: LoadContext) -> Table:
        built = table.build()
        decoded = decode_into(Table, built, ctx)
        assert decoded.build() == built
        return decoded

    def test_data_table_round_trips(self):
        model = ModelBuilder()
        table = model.add_data_table("Items")
        table.set_key_column("Name")
        table.add_data_field("Name", DataType.STRING)
        table.add_data_field("Qty", DataType.INTEGER)
        table.add_calculated_field("Doubled", table["Qty"])
        ctx = LoadContext()
        ctx.register("Items", table)
        decoded = self._round_trip_table(table, ctx)
        assert isinstance(decoded, DataTable)

    def test_derived_table_round_trips(self):
        model = ModelBuilder()
        items = model.add_data_table("Items")
        items.add_data_field("Cat", DataType.STRING)
        items.add_data_field("Qty", DataType.INTEGER)
        derived = model.add_derived_table("ByCat", items)
        derived.group_by(items.get_field("Cat"))
        derived.add_source_fields([items.get_field("Cat")])
        derived.add_aggregated_field("TotQty", items.get_field("Qty"), AggregationMethod.SUM)
        derived.add_sort_key(items.get_field("Cat"), SortDirection.ASCENDING)
        ctx = LoadContext()
        ctx.register("Items", items)
        ctx.register("ByCat", derived)
        from daitum_model.derived_table import DerivedTable

        built = derived.build()
        decoded = decode_into(Table, built, ctx)
        assert isinstance(decoded, DerivedTable)
        assert decoded.build() == built

    def test_pivot_table_round_trips(self):
        model = ModelBuilder()
        source = model.add_data_table("Source")
        source.add_data_field("Location", DataType.STRING)
        source.add_data_field("Hour", DataType.INTEGER)
        source.add_data_field("Value", DataType.DECIMAL)
        report = model.add_derived_table("Report", source)
        report.group_by(source.get_field("Location"))
        report.add_source_fields([source.get_field("Location")])
        report.add_aggregated_field("Total", source.get_field("Value"), AggregationMethod.SUM)
        pivot = report.add_pivot(source.get_field("Hour"), source.get_field("Value"))
        pivot.add_column("H0", 0).add_column("H1", 1)
        ctx = LoadContext()
        ctx.register("Source", source)
        ctx.register("Report", report)
        from daitum_model.derived_table import DerivedTable

        built = report.build()
        # Pivot columns serialise as keyed aggregated fields, not a separate ``pivots`` block.
        assert built["groupingConfiguration"]["aggregatedFields"] == [
            {"aggregatedFieldId": "Total", "sourceFieldId": "Value", "aggregationMethod": "SUM"},
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
        assert "pivots" not in built["groupingConfiguration"]
        decoded = decode_into(Table, built, ctx)
        assert isinstance(decoded, DerivedTable)
        assert decoded.build() == built

    def test_derived_table_decodes_with_null_optional_collections(self):
        # An exported model may serialise optional collection keys as an explicit ``null``
        # rather than omitting them. ``dict.get(key, default)`` returns that ``null`` verbatim,
        # so iterating it raised ``TypeError: 'NoneType' object is not iterable``. Decoding must
        # treat missing and null the same (empty).
        model = ModelBuilder()
        items = model.add_data_table("Items")
        items.add_data_field("Cat", DataType.STRING)
        derived = model.add_derived_table("ByCat", items)
        derived.group_by(items.get_field("Cat"))
        derived.add_source_fields([items.get_field("Cat")])
        ctx = LoadContext()
        ctx.register("Items", items)
        ctx.register("ByCat", derived)
        from daitum_model.derived_table import DerivedTable

        built = derived.build()
        built["sortKeys"] = None
        decoded = decode_into(Table, built, ctx)
        assert isinstance(decoded, DerivedTable)

    def test_joined_table_round_trips(self):
        # Joined tables are built from their sources' fields, so they round-trip through the
        # whole-model decoder (which knows each table id from its map key) rather than the
        # standalone Table decoder, which has no id for a join-only table with no own fields.
        model = ModelBuilder()
        items = model.add_data_table("Items")
        items.set_key_column("Name")
        items.add_data_field("Name", DataType.STRING)
        other = model.add_data_table("Other")
        other.set_key_column("Name")
        other.add_data_field("Name", DataType.STRING)
        condition = JoinCondition(
            items, other, JoinType.INNER, items.get_field("Name"), other.get_field("Name")
        )
        joined = model.add_joined_table("J", [condition])
        joined.add_table_reference(items)
        from daitum_model.joined_table import JoinedTable

        built = model.build()
        decoded = decode_model(built, LoadContext())
        assert isinstance(decoded.get_table("J"), JoinedTable)
        assert decoded.build() == built

    def test_union_table_round_trips(self):
        model = ModelBuilder()
        items = model.add_data_table("Items")
        items.add_data_field("Name", DataType.STRING)
        other = model.add_data_table("Other")
        other.add_data_field("Name", DataType.STRING)
        union = model.add_union_table("U", [items, other])
        union.add_field("Name", DataType.STRING)
        union.add_field_mapping(items, "Name", items.get_field("Name"))
        union.set_filter_field(union.get_field("Name"))
        ctx = LoadContext()
        ctx.register("Items", items)
        ctx.register("Other", other)
        ctx.register("U", union)
        from daitum_model.union_table import UnionTable

        built = union.build()
        decoded = decode_into(Table, built, ctx)
        assert isinstance(decoded, UnionTable)
        assert decoded.build() == built

    def test_folded_table_round_trips(self):
        model = ModelBuilder()
        roster = model.add_data_table("Roster")
        roster.add_data_field("Employee", DataType.STRING)
        roster.add_data_field("Day1Wages", DataType.DECIMAL)
        roster.add_data_field("Day2Wages", DataType.DECIMAL)
        folded = model.add_folded_table("Long", roster)
        folded.add_column("Day", DataType.INTEGER)
        folded.add_column("Wages", DataType.DECIMAL)
        folded.carry(roster.get_field("Employee"))
        folded.fold(Day=1, Wages=roster.get_field("Day1Wages"))
        folded.fold(Day=2, Wages=roster.get_field("Day2Wages"))
        ctx = LoadContext()
        ctx.register("Roster", roster)
        ctx.register("Long", folded.table)
        from daitum_model.union_table import UnionTable

        built = folded.table.build()
        decoded = decode_into(Table, built, ctx)
        assert isinstance(decoded, UnionTable)
        assert decoded.build() == built

    def test_table_type_dispatch_ignores_null_structural_keys(self):
        # A model generated elsewhere may emit *every* structural key, null for the ones that do
        # not apply. A union table then carries "joinConditions": null / "sourceTableId": null
        # beside its real "sourceTables". Dispatch must key on the value being non-null, else the
        # union is misclassified (as a joined table) and silently degrades — the reported bug where
        # a union decoded to a data table with no sources and produced 0 rows.
        from daitum_model._decoders.tables import resolve_table_type
        from daitum_model.derived_table import DerivedTable
        from daitum_model.joined_table import JoinedTable
        from daitum_model.tables import DataTable
        from daitum_model.union_table import UnionTable

        def platform(**overrides):
            base = {
                "groupingConfiguration": None,
                "sortKeys": None,
                "sourceTableId": None,
                "joinConditions": None,
                "sourceTables": None,
            }
            base.update(overrides)
            return base

        assert resolve_table_type(platform()) is DataTable
        assert resolve_table_type(platform(sourceTableId="Base")) is DerivedTable
        assert (
            resolve_table_type(platform(joinConditions=[{"leftTableId": "A", "rightTableId": "B"}]))
            is JoinedTable
        )
        assert (
            resolve_table_type(platform(sourceTables=[{"sourceTableId": "A", "mappingKey": "A"}]))
            is UnionTable
        )
        # The deprecated union shape lists sources as a flat sourceTableIds array (no sourceTables).
        assert resolve_table_type(platform(sourceTableIds=["A", "B"])) is UnionTable

    def test_union_decodes_deprecated_source_table_ids_shape(self):
        # A union may serialise its sources the deprecated way: a flat "sourceTableIds" list of ids
        # (no "sourceTables" objects), with mapping keys implied by the fieldMappings keys. The
        # decoder must recognise and reconstruct it, not degrade the union to a data table.
        from daitum_model.union_table import UnionTable

        def data_field(fid, tid, dt="STRING"):
            return {
                "@type": "data",
                "id": fid,
                "tableId": tid,
                "dataType": dt,
                "unique": False,
                "nullable": False,
                "defaultValue": None,
                "importFormat": None,
                "orderIndex": None,
                "description": None,
            }

        def table(tid, fields, **extra):
            base = {
                "fieldDefinitions": fields,
                "modelLevel": False,
                "idField": None,
                "filterField": None,
                "exportAsKeyColumn": False,
                "keyColumnField": None,
            }
            base.update(extra)
            return base

        definition = {
            "tableDefinitions": {
                "All_Flights": table(
                    "All_Flights",
                    {
                        "ID": data_field("ID", "All_Flights", "INTEGER"),
                        "Flight Type": data_field("Flight Type", "All_Flights"),
                    },
                ),
                "Activities": table("Activities", {"Type": data_field("Type", "Activities")}),
                "Roster": table(
                    "Roster",
                    {
                        "ID": data_field("ID", "Roster", "INTEGER"),
                        "Type": data_field("Type", "Roster"),
                    },
                    keyColumnField="ID",
                    exportAsKeyColumn=True,
                    sourceTableIds=["All_Flights", "Activities"],
                    fieldMappings={
                        "All_Flights": {"ID": "ID", "Type": "Flight Type"},
                        "Activities": {"Type": "Type"},
                    },
                ),
            },
            "calculationDefinitions": {},
            "parameterDefinitions": {},
            "optimisationCheckNamedValue": None,
            "partialEvaluationAllowed": True,
        }
        decoded = decode_model(definition, LoadContext())
        union = decoded.get_table("Roster")
        assert isinstance(union, UnionTable)
        rebuilt = union.build()
        # Re-built in the modern sourceTables shape, with mapping keys == source table ids.
        assert rebuilt["sourceTables"] == [
            {"sourceTableId": "All_Flights", "mappingKey": "All_Flights"},
            {"sourceTableId": "Activities", "mappingKey": "Activities"},
        ]
        assert rebuilt["fieldMappings"] == {
            "All_Flights": {"ID": "ID", "Type": "Flight Type"},
            "Activities": {"Type": "Type"},
        }

    def test_union_decodes_from_platform_style_all_keys_present(self):
        # End-to-end: a union whose JSON carries all structural keys (null where inapplicable) and
        # platform-only field metadata (userEditable/derivedField/...) must decode as a UnionTable
        # with its sources and mappings intact, not degrade to an empty data table.
        from daitum_model.union_table import UnionTable

        def data_field(fid, tid):
            return {
                "@type": "data",
                "id": fid,
                "tableId": tid,
                "importFormat": None,
                "orderIndex": None,
                "dataType": "STRING",
                "unique": False,
                "nullable": False,
                "defaultValue": None,
                "userEditable": True,
                "derivedField": False,
                "aggregatedField": False,
            }

        def table(tid, fields, **extra):
            base = {
                "fieldDefinitions": fields,
                "modelLevel": False,
                "groupingConfiguration": None,
                "sortKeys": None,
                "sourceTableId": None,
                "keyColumnField": None,
                "filterField": None,
                "idField": None,
                "transientData": False,
                "exportAsKeyColumn": False,
                "joinConditions": None,
                "sourceTableIds": None,
                "sourceTables": None,
                "fieldMappings": None,
                "derived": False,
                "union": False,
                "join": False,
            }
            base.update(extra)
            return base

        definition = {
            "tableDefinitions": {
                "A": table("A", {"AType": data_field("AType", "A")}),
                "B": table("B", {"BType": data_field("BType", "B")}),
                "U": table(
                    "U",
                    {"Type": data_field("Type", "U")},
                    union=True,
                    sourceTableIds=["A", "B"],
                    sourceTables=[
                        {"sourceTableId": "A", "mappingKey": "A"},
                        {"sourceTableId": "B", "mappingKey": "B"},
                    ],
                    fieldMappings={"A": {"Type": "AType"}, "B": {"Type": "BType"}},
                ),
            },
            "calculationDefinitions": {},
            "parameterDefinitions": {},
            "optimisationCheckNamedValue": None,
            "partialEvaluationAllowed": True,
        }
        decoded = decode_model(definition, LoadContext())
        union = decoded.get_table("U")
        assert isinstance(union, UnionTable)
        rebuilt = union.build()
        assert [s["sourceTableId"] for s in rebuilt["sourceTables"]] == ["A", "B"]
        assert rebuilt["fieldMappings"] == {"A": {"Type": "AType"}, "B": {"Type": "BType"}}


class TestModelRoundTrip:
    def _example_model(self) -> ModelBuilder:
        model = ModelBuilder()
        items = model.add_data_table("Items")
        items.set_key_column("Name")
        items.add_data_field("Name", DataType.STRING)
        items.add_data_field("Unit Cost", DataType.DECIMAL)
        items.add_data_field("Quantity", DataType.INTEGER)
        items.add_calculated_field(
            "Row Cost", items.get_field("Unit Cost") * items.get_field("Quantity")
        )
        model.add_parameter("BUDGET", DataType.DECIMAL, 100.0, model_level=True)
        model.add_calculation("TOTAL_COST", formulas.SUM(items["Row Cost"]), model_level=True)
        return model

    def test_full_model_round_trips(self):
        model = self._example_model()
        built = model.build()
        decoded = decode_model(built, LoadContext())
        assert decoded.build() == built

    def test_model_decodes_with_null_optional_scalars(self):
        # A model generated by other tooling may serialise optional scalar keys as an explicit
        # ``null`` rather than omitting them. ``dict.get(key, default)`` returns that ``null``
        # verbatim, so a null flag reached the constructor as ``None`` instead of its default.
        # Decoding must treat missing and null the same (fall back to the default).
        built = self._example_model().build()
        built["optimisationCheckNamedValue"] = None
        built["partialEvaluationAllowed"] = None
        for calc in built["calculationDefinitions"].values():
            calc["modelLevel"] = None
        decoded = decode_model(built, LoadContext())
        assert decoded._partial_evaluation_allowed is True  # noqa: SLF001
        assert all(not c.model_level for c in decoded._calculations)  # noqa: SLF001

    def test_decoded_model_is_re_editable(self):
        model = self._example_model()
        built = model.build()
        decoded = decode_model(built, LoadContext())
        decoded.add_parameter("EXTRA", DataType.INTEGER, 5, model_level=True)
        assert "EXTRA" in decoded.build()["parameterDefinitions"]

    def test_model_with_derived_and_joined_tables_round_trips(self):
        # Decode through the whole-model path (not the standalone Table decoder with
        # pre-registered live sources), so derived/joined construction must resolve source
        # fields that only exist after the source table is fully built.
        model = ModelBuilder()
        items = model.add_data_table("Items")
        items.set_key_column("Cat")
        items.add_data_field("Cat", DataType.STRING)
        items.add_data_field("Qty", DataType.INTEGER)
        items.add_data_field("Keep", DataType.BOOLEAN)

        other = model.add_data_table("Other")
        other.set_key_column("Cat")
        other.add_data_field("Cat", DataType.STRING)

        derived = model.add_derived_table("ByCat", items)
        derived.group_by(items.get_field("Cat"))
        derived.set_filter_field(items.get_field("Keep"))
        derived.add_source_fields([items.get_field("Cat")])
        derived.add_aggregated_field("TotQty", items.get_field("Qty"), AggregationMethod.SUM)
        derived.add_sort_key(items.get_field("Cat"), SortDirection.ASCENDING)

        condition = JoinCondition(
            items, other, JoinType.INNER, items.get_field("Cat"), other.get_field("Cat")
        )
        model.add_joined_table("Joined", [condition])

        built = model.build()
        decoded = decode_model(built, LoadContext())
        assert decoded.build() == built

    def test_joined_reference_field_does_not_shadow_a_same_named_source_table(self):
        # add_table_reference names the object-reference field after its source table, so a
        # field id ("Items") can equal a table id. A later union sourced from "Items" must
        # still resolve the table, not the shadowing field.
        model = ModelBuilder()
        items = model.add_data_table("Items")
        items.set_key_column("Cat")
        items.add_data_field("Cat", DataType.STRING)
        other = model.add_data_table("Other")
        other.set_key_column("Cat")
        other.add_data_field("Cat", DataType.STRING)

        condition = JoinCondition(
            items, other, JoinType.INNER, items.get_field("Cat"), other.get_field("Cat")
        )
        joined = model.add_joined_table("Joined", [condition])
        joined.add_table_reference(items)  # creates a field with id "Items"

        union = model.add_union_table("U", [items, other])
        union.add_field("Cat", DataType.STRING)
        union.add_field_mapping(items, "Cat", items.get_field("Cat"))

        built = model.build()
        decoded = decode_model(built, LoadContext())
        assert decoded.build() == built

    def test_object_reference_resolves_table_not_a_same_named_field(self):
        # Tables and fields share the load's symbol table. A field elsewhere in the model may
        # reuse a table's id (here a calculated field "Staff" on another table). An object
        # reference to table "Staff" must resolve the table, not the shadowing field — otherwise
        # composite data-type decoding raised "resolved to a CalculatedField, not a table".
        model = ModelBuilder()
        staff = model.add_data_table("Staff")
        staff.set_key_column("Id")
        staff.add_data_field("Id", DataType.STRING)

        # "Aaa" decodes before "Zzz" and registers a field named "Staff", shadowing the table.
        aaa = model.add_data_table("Aaa")
        aaa.set_key_column("K")
        aaa.add_data_field("K", DataType.STRING)
        aaa.add_calculated_field("Staff", aaa["K"])

        zzz = model.add_data_table("Zzz")
        zzz.set_key_column("K")
        zzz.add_data_field("K", DataType.STRING)
        zzz.add_object_reference_field("Ref", staff)

        built = model.build()
        decoded = decode_model(built, LoadContext())
        assert decoded.build() == built

    def test_formula_column_access_resolves_table_not_a_same_named_field(self):
        # A formula's column access ``Table[Field]`` resolves the table through the load's symbol
        # table, which fields also populate. A field named after the table (here a field
        # "Role_Specifications" on another table) must not mask it, or phase-2 formula parsing
        # raised "unresolved table 'Role_Specifications'".
        model = ModelBuilder()
        roles = model.add_data_table("Role_Specifications")
        roles.add_data_field("UI_Display", DataType.INTEGER)

        people = model.add_data_table("People")
        people.add_data_field("Role", DataType.STRING)
        people.add_data_field("Role_Specifications", DataType.STRING)  # shadows the table id
        people.add_calculated_field("Total", formulas.SUM(roles["UI_Display"]))

        built = model.build()
        decoded = decode_model(built, LoadContext())
        assert decoded.build() == built
        total = decoded.get_table("People").get_field("Total")
        assert total.build()["formula"]["formulaString"] == "SUM(Role_Specifications[UI_Display])"

    def test_calculated_fields_on_derived_join_and_union_tables_round_trip(self):
        # Every table type supports calculated fields (unlike data/combo fields, which only
        # exist on data tables). The derived/join/union field populators used to treat every
        # non-aggregated field as a source-field copy, so a calculated field defined on the
        # table itself was either looked up in the wrong table (raising) or rebuilt as a plain
        # data copy, losing its formula. Each must decode via its ``@type`` discriminator.
        from daitum_model.formula import CONST

        model = ModelBuilder()
        items = model.add_data_table("Items")
        items.set_key_column("Cat")
        items.add_data_field("Cat", DataType.STRING)
        items.add_data_field("Qty", DataType.INTEGER)
        other = model.add_data_table("Other")
        other.set_key_column("Cat")
        other.add_data_field("Cat", DataType.STRING)

        derived = model.add_derived_table("ByCat", items)
        derived.group_by(items.get_field("Cat"))
        derived.add_source_fields([items.get_field("Cat")])
        derived.add_aggregated_field("TotQty", items.get_field("Qty"), AggregationMethod.SUM)
        derived.add_calculated_field("Doubled", derived.get_field("TotQty") * 2)

        condition = JoinCondition(
            items, other, JoinType.INNER, items.get_field("Cat"), other.get_field("Cat")
        )
        joined = model.add_joined_table("Joined", [condition])
        joined.add_table_reference(items)
        joined.add_calculated_field("Answer", CONST(42))

        union = model.add_union_table("U", [items, other])
        union.add_field("Cat", DataType.STRING)
        union.add_calculated_field("CatConst", CONST("x"))

        built = model.build()
        decoded = decode_model(built, LoadContext())
        assert decoded.build() == built
        # The calculated fields keep their @type and formula, not degraded to data copies.
        for table_id, field_id in [("ByCat", "Doubled"), ("Joined", "Answer"), ("U", "CatConst")]:
            field = decoded.get_table(table_id).build()["fieldDefinitions"][field_id]
            assert field["@type"] == "calculated"
            assert "formula" in field

    def test_model_table_decode_is_independent_of_definition_order(self):
        # write_to_file emits tableDefinitions with sort_keys=True, so a dependent table can
        # appear before its source. Decoding must order by dependency, not dict order.
        model = ModelBuilder()
        source = model.add_data_table("Zebra")  # sorts after its dependent "Alpha"
        source.set_key_column("K")
        source.add_data_field("K", DataType.STRING)
        model.add_derived_table("Alpha", source).group_by(source.get_field("K"))

        built = model.build()
        # Reproduce the on-disk alphabetical ordering write_to_file would produce.
        reordered = dict(built)
        reordered["tableDefinitions"] = dict(
            sorted(built["tableDefinitions"].items(), key=lambda kv: kv[0])
        )
        assert list(reordered["tableDefinitions"]) == ["Alpha", "Zebra"]
        decoded = decode_model(reordered, LoadContext())
        assert decoded.build() == built

    def test_forward_object_reference_field_round_trips(self):
        # An object/map reference field names a table in its dataType. That table must be
        # built before this one, even though the reference is a field dataType rather than a
        # structural source. Here the referrer "Aaa" sorts before its referent "Zzz".
        model = ModelBuilder()
        referrer = model.add_data_table("Aaa")
        referent = model.add_data_table("Zzz")
        referent.add_data_field("Name", DataType.STRING)
        referrer.add_object_reference_field("Ref", referent)
        referrer.add_map_field("M", DataType.INTEGER, referent)

        built = model.build()
        reordered = dict(built)
        reordered["tableDefinitions"] = dict(
            sorted(built["tableDefinitions"].items(), key=lambda kv: kv[0])
        )
        assert list(reordered["tableDefinitions"]) == ["Aaa", "Zzz"]
        decoded = decode_model(reordered, LoadContext())
        assert decoded.build() == built

    def test_self_referential_object_field_round_trips(self):
        # A table whose object field references itself must not be treated as depending on
        # itself (it is registered before its own fields are decoded).
        model = ModelBuilder()
        node = model.add_data_table("Node")
        node.add_data_field("Name", DataType.STRING)
        node.add_object_reference_field("Parent", node)

        built = model.build()
        decoded = decode_model(built, LoadContext())
        assert decoded.build() == built

    def test_mutually_referencing_tables_are_rejected_as_a_cycle_at_build(self):
        # Daitum forbids circular table dependencies, including through object references: a
        # model where A references B and B references A is invalid. Model validation now
        # rejects this at build time (before serialisation) rather than only on decode.
        model = ModelBuilder()
        a = model.add_data_table("A")
        a.add_data_field("AID", DataType.STRING)
        a.set_key_column("AID")
        b = model.add_data_table("B")
        b.add_data_field("BID", DataType.STRING)
        b.set_key_column("BID")
        a.add_object_reference_field("toB", b)
        b.add_object_reference_field("toA", a)

        with pytest.raises(ModelValidationError, match="[Cc]ircular"):
            model.build()

    def test_decoder_rejects_cyclic_table_json(self):
        # The decoder keeps its own cycle guard for JSON assembled outside the builder (where
        # build-time validation never ran). Feed it hand-built cyclic table definitions.
        cyclic = {
            "calculationDefinitions": {},
            "parameterDefinitions": {},
            "optimisationCheckNamedValue": None,
            "partialEvaluationAllowed": True,
            "tableDefinitions": {
                "A": {
                    "@type": "data",
                    "id": "A",
                    "keyColumnField": "AID",
                    "fieldDefinitions": {
                        "AID": {"@type": "data", "id": "AID", "dataType": "STRING"},
                        "toB": {
                            "@type": "data",
                            "id": "toB",
                            "dataType": {"type": "OBJECT", "tableId": "B"},
                        },
                    },
                },
                "B": {
                    "@type": "data",
                    "id": "B",
                    "keyColumnField": "BID",
                    "fieldDefinitions": {
                        "BID": {"@type": "data", "id": "BID", "dataType": "STRING"},
                        "toA": {
                            "@type": "data",
                            "id": "toA",
                            "dataType": {"type": "OBJECT", "tableId": "A"},
                        },
                    },
                },
            },
        }
        with pytest.raises(LoadError, match="[Cc]ycl"):
            decode_model(cyclic, LoadContext())

    def test_optimisation_check_named_value_round_trips(self):
        model = ModelBuilder()
        model.add_parameter("OK", DataType.BOOLEAN, True, model_level=True)
        model.set_data_validation_rule(model.get_named_value("OK"))
        built = model.build()
        decoded = decode_model(built, LoadContext())
        rebuilt = decoded.build()
        assert rebuilt["optimisationCheckNamedValue"] == "OK"
        assert rebuilt == built

    def test_partial_evaluation_flag_round_trips(self):
        model = ModelBuilder()
        model.set_partial_evaluation_allowed(False)
        built = model.build()
        decoded = decode_model(built, LoadContext())
        assert decoded.build()["partialEvaluationAllowed"] is False


class TestReadFromFile:
    def test_read_from_file_round_trips(self, tmp_path):
        model = TestModelRoundTrip()._example_model()
        original = model.build()
        model.write_to_file(tmp_path)
        loaded = ModelBuilder.read_from_file(tmp_path)
        assert loaded.build() == original
        assert "TOTAL_COST" in loaded.load_context.symbols


class TestErrors:
    def test_table_with_no_discriminating_keys_decodes_as_data_table(self):
        # A table with no join/union/source keys decodes as a DataTable.
        data = {
            "exportAsKeyColumn": False,
            "modelLevel": False,
            "fieldDefinitions": {
                "X": {
                    "@type": "data",
                    "id": "X",
                    "tableId": "T",
                    "dataType": "STRING",
                    "nullable": False,
                    "unique": False,
                }
            },
        }
        decoded = decode_into(Table, data, LoadContext())
        assert isinstance(decoded, DataTable)

    def test_unmapped_field_key_raises(self):
        with pytest.raises(LoadError):
            decode_into(
                Field,
                {"@type": "data", "id": "X", "tableId": "T", "dataType": "STRING", "bogus": 1},
                LoadContext(),
            )
