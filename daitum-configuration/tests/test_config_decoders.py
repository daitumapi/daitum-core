"""
Tests for the configuration decoder layer (daitum_configuration._decoders).

Structural round-trip contract: decode(x.build()).build() == x.build(), driven from
per-class fixtures built via the builders.
"""

import daitum_model.formulas as formulas
import pytest
from daitum_model import DataType, ModelBuilder
from daitum_model.decoding import LoadContext, decode_into

from daitum_configuration import (
    CMAESAlgorithm,
    GeneticAlgorithm,
    VariableNeighbourhoodSearch,
)
from daitum_configuration.algorithm_configuration.algorithm import Algorithm
from daitum_configuration.algorithm_configuration.alns_algorithm import (
    AcceptanceCriterion,
    AdaptiveLargeNeighbourhoodSearch,
)
from daitum_configuration.algorithm_configuration.steepest_dynamic_local_search import (
    SteepestDynamicLocalSearch,
)
from daitum_configuration.model_configuration.constraint import Constraint, ConstraintType
from daitum_configuration.model_configuration.decision_variable import DecisionVariable, DVType
from daitum_configuration.model_configuration.objective import Objective
from daitum_configuration.model_configuration.priority import Priority
from daitum_configuration.model_configuration.scenario_output import ScenarioOutput


def _model_ctx(model) -> LoadContext:
    return LoadContext(symbols=dict(model["symbols"]), model=model["builder"])


@pytest.fixture
def model() -> dict:
    m = ModelBuilder()
    t = m.add_data_table("Items")
    t.set_key_column("Name")
    fields = {
        "Name": t.add_data_field("Name", DataType.STRING),
        "Quantity": t.add_data_field("Quantity", DataType.INTEGER),
        "MinQty": t.add_data_field("MinQty", DataType.INTEGER),
        "MaxQty": t.add_data_field("MaxQty", DataType.INTEGER),
        "Cost": t.add_data_field("Cost", DataType.DECIMAL),
    }
    calc = m.add_calculation("TOTAL_COST", formulas.SUM(t["Cost"]), model_level=True)
    budget = m.add_parameter("BUDGET", DataType.DECIMAL, 100.0, model_level=True)
    symbols = {"Items": t, "TOTAL_COST": calc, "BUDGET": budget, **fields}
    return {"builder": m, "symbols": symbols}


class TestAlgorithmRoundTrip:
    @pytest.mark.parametrize(
        "algorithm",
        [
            GeneticAlgorithm(),
            VariableNeighbourhoodSearch(),
            CMAESAlgorithm(),
            GeneticAlgorithm(evaluations=5000, population_size=50, elitism=2),
            AdaptiveLargeNeighbourhoodSearch(),
            AdaptiveLargeNeighbourhoodSearch(
                candidates_per_iteration=4, segment_length=50, decay_factor=0.9
            ),
            AdaptiveLargeNeighbourhoodSearch(acceptance_criterion=AcceptanceCriterion.greedy()),
            AdaptiveLargeNeighbourhoodSearch(
                acceptance_criterion=AcceptanceCriterion.simulated_annealing(
                    initial_temperature=50.0, cooling_rate=0.99
                )
            ),
            SteepestDynamicLocalSearch(),
            SteepestDynamicLocalSearch(
                allow_neutral_walks=True, integer_step_size=5, decimal_step_size=0.5
            ),
        ],
    )
    def test_round_trip(self, algorithm):
        built = algorithm.build()
        decoded = decode_into(Algorithm, built, LoadContext())
        assert type(decoded) is type(algorithm)
        assert decoded.build() == built


class TestReferenceResolution:
    def test_table_qualified_reference_disambiguates_duplicate_field_ids(self):
        # The shared symbol table is keyed by bare field id, so two tables with a same-named
        # field would collide. A "Table[field]" reference must resolve through its table.
        from daitum_configuration._decoders._references import resolve_value

        m = ModelBuilder()
        a = m.add_data_table("A")
        a_qty = a.add_data_field("Qty", DataType.INTEGER)
        b = m.add_data_table("B")
        b_qty = b.add_data_field("Qty", DataType.INTEGER)

        ctx = LoadContext(symbols={"A": a, "B": b, "Qty": b_qty}, model=m)
        assert resolve_value("!!!A[Qty]", ctx) is a_qty
        assert resolve_value("!!!B[Qty]", ctx) is b_qty

    def test_table_qualifier_resolves_table_not_a_same_named_field(self):
        # Tables and fields share the symbol table. A field named after a table (here a field
        # "Jobs" on another table) must not mask the "Jobs" table when resolving a "Jobs[Qty]"
        # reference — otherwise the qualifier resolves to the shadowing field and the wrong (or no)
        # field is returned.
        from daitum_configuration._decoders._references import resolve_table, resolve_value

        m = ModelBuilder()
        jobs = m.add_data_table("Jobs")
        qty = jobs.add_data_field("Qty", DataType.INTEGER)
        other = m.add_data_table("Other")
        shadow = other.add_data_field("Jobs", DataType.STRING)  # id == "Jobs" table id

        # The symbol table has the field "Jobs" overwriting the table "Jobs" (registration order).
        ctx = LoadContext(symbols={"Jobs": shadow, "Other": other, "Qty": qty}, model=m)
        assert resolve_value("!!!Jobs[Qty]", ctx) is qty
        assert resolve_table("!!!Jobs[Qty]", ctx) is jobs


class TestModelConfigurationRoundTrip:
    def test_decision_variable(self, model):
        t = model["symbols"]["Items"]
        field = model["symbols"]["Quantity"]
        mn = model["symbols"]["MinQty"]
        mx = model["symbols"]["MaxQty"]
        dv = DecisionVariable(field, dv_table=t, dv_type=DVType.RANGE).set_min(mn).set_max(mx)
        built = dv.build()
        decoded = decode_into(DecisionVariable, built, _model_ctx(model))
        assert decoded.build() == built

    def test_decision_variable_injective(self, model):
        t = model["symbols"]["Items"]
        field = model["symbols"]["Quantity"]
        domain = model["symbols"]["Name"]  # a STRING field, standing in for the allowed column
        dv = DecisionVariable(field, dv_table=t, dv_type=DVType.INJECTIVE).set_domain(domain)
        built = dv.build()
        decoded = decode_into(DecisionVariable, built, _model_ctx(model))
        assert decoded.build() == built

    def test_decision_variable_injective_no_domain(self, model):
        t = model["symbols"]["Items"]
        field = model["symbols"]["Quantity"]
        dv = DecisionVariable(field, dv_table=t, dv_type=DVType.INJECTIVE)
        built = dv.build()
        decoded = decode_into(DecisionVariable, built, _model_ctx(model))
        assert decoded.build() == built

    def test_objective(self, model):
        calc = model["symbols"]["TOTAL_COST"]
        obj = Objective(calc, maximise=False, priority=Priority.LOW, weight=1.0, name="Cost")
        built = obj.build()
        decoded = decode_into(Objective, built, _model_ctx(model))
        assert decoded.build() == built

    def test_constraint(self, model):
        calc = model["symbols"]["TOTAL_COST"]
        budget = model["symbols"]["BUDGET"]
        con = (
            Constraint(calc)
            .set_type(ConstraintType.INEQUALITY)
            .set_upper_bound(budget)
            .set_name("Budget")
        )
        built = con.build()
        decoded = decode_into(Constraint, built, _model_ctx(model))
        assert decoded.build() == built

    def test_constraint_literal_bound(self, model):
        calc = model["symbols"]["TOTAL_COST"]
        con = Constraint(calc).set_lower_bound(1.0).set_upper_bound(5.0)
        built = con.build()
        decoded = decode_into(Constraint, built, _model_ctx(model))
        assert decoded.build() == built

    def test_decoding_does_not_perturb_tracking_counters(self, model):
        # Decoding a ModelConfiguration reconstructs tracked objects through their counter-
        # bumping constructors, but must leave the global counters untouched so a later built
        # object gets the id it would have had.
        from daitum_configuration.model_configuration.model_configuration import ModelConfiguration

        t = model["symbols"]["Items"]
        field = model["symbols"]["Quantity"]
        cfg = ModelConfiguration()
        cfg.decision_variables = [DecisionVariable(field, dv_table=t, dv_type=DVType.RANGE)]
        cfg.objectives = [Objective(model["symbols"]["TOTAL_COST"], maximise=False)]
        built = cfg.build()

        before = {
            cls.__name__: cls._tracking_counter
            for cls in (DecisionVariable, Objective, Constraint, ScenarioOutput)
        }
        decode_into(ModelConfiguration, built, _model_ctx(model))
        after = {
            cls.__name__: cls._tracking_counter
            for cls in (DecisionVariable, Objective, Constraint, ScenarioOutput)
        }
        assert before == after

    def test_scenario_output(self, model):
        calc = model["symbols"]["TOTAL_COST"]
        so = ScenarioOutput("Total", calc)
        built = so.build()
        decoded = decode_into(ScenarioOutput, built, _model_ctx(model))
        assert decoded.build() == built


class TestDataSourceRoundTrip:
    """Each data-source config round-trips and decodes to its concrete typed class."""

    def _ctx(self, model) -> LoadContext:
        return _model_ctx(model)

    def test_data_store_config(self, model):
        from daitum_configuration import DataStoreConfig, EqualityDataFilter
        from daitum_configuration.data_source.data_source import DataSource

        budget = model["symbols"]["BUDGET"]
        cfg = DataStoreConfig("store_key", {"Items": "ItemsSheet"})
        cfg.set_model_filter(EqualityDataFilter(["a", "b"], budget, "x"))
        ds = DataSource("Store", cfg)
        built = ds.build()
        decoded = decode_into(DataSource, built, self._ctx(model))
        assert isinstance(decoded.config, DataStoreConfig)
        assert decoded.build() == built

    def test_track_changes_capture_config(self, model):
        from daitum_configuration import TrackChangesConfig
        from daitum_configuration.data_source.data_source import DataSource

        cfg = TrackChangesConfig("optimised")
        ds = DataSource("Snapshot", cfg)
        built = ds.build()
        decoded = decode_into(DataSource, built, self._ctx(model))
        assert isinstance(decoded.config, TrackChangesConfig)
        assert decoded.config.baseline == "optimised"
        assert decoded.build() == built

    def test_track_changes_revert_config_with_groups(self, model):
        from daitum_configuration import TrackChangesConfig, TrackChangesMode
        from daitum_configuration.data_source.data_source import DataSource

        cfg = TrackChangesConfig(
            "optimised", mode=TrackChangesMode.REVERT, tracking_groups=["edits", "review"]
        )
        ds = DataSource("Undo", cfg)
        built = ds.build()
        decoded = decode_into(DataSource, built, self._ctx(model))
        assert isinstance(decoded.config, TrackChangesConfig)
        assert decoded.config.mode is TrackChangesMode.REVERT
        assert decoded.config.tracking_groups == ["edits", "review"]
        assert decoded.build() == built

    def test_decoding_does_not_perturb_temp_export_counter(self, model):
        # DataSource's constructor bumps a class-level temp_export_id counter. Decoding
        # reconstructs through that constructor but restores the stored id, so loading a
        # config must not advance the counter a subsequently built DataSource would consume.
        from daitum_configuration import DataStoreConfig
        from daitum_configuration.data_source.data_source import DataSource

        cfg = DataStoreConfig("k", {"Items": "Sheet"})
        built = DataSource("Store", cfg).build()

        before = DataSource._temp_export_id_counter
        decode_into(DataSource, built, self._ctx(model))
        assert DataSource._temp_export_id_counter == before

    def test_inequality_filter_with_numeric_bounds_round_trips(self, model):
        # Numeric bounds build to numeric-bodied references ("!!!5.0"); the decoder must
        # recover the literal, not treat it as a symbol-table id.
        from daitum_configuration import InequalityDataFilter
        from daitum_configuration.data_source.data_store.data_filter import DataFilter

        f = InequalityDataFilter(["col"], 5.0, 10.0)
        built = f.build()
        decoded = decode_into(DataFilter, built, self._ctx(model))
        assert isinstance(decoded, InequalityDataFilter)
        assert decoded.build() == built

    def test_inequality_filter_with_reference_bounds_round_trips(self, model):
        from daitum_configuration import InequalityDataFilter
        from daitum_configuration.data_source.data_store.data_filter import DataFilter

        budget = model["symbols"]["BUDGET"]
        total = model["symbols"]["TOTAL_COST"]
        f = InequalityDataFilter(["col"], budget, total)
        built = f.build()
        decoded = decode_into(DataFilter, built, self._ctx(model))
        assert decoded.build() == built

    def test_excel_transform_config(self, model):
        from daitum_configuration import ExcelTransformConfig
        from daitum_configuration.data_source.data_source import DataSource

        cfg = ExcelTransformConfig("file_key", "file.xlsx", [("Src", "Tgt"), ("S2", "T2")])
        ds = DataSource("Excel", cfg)
        built = ds.build()
        decoded = decode_into(DataSource, built, self._ctx(model))
        assert isinstance(decoded.config, ExcelTransformConfig)
        assert decoded.build() == built

    def test_distance_matrix_config(self, model):
        from daitum_configuration import DistanceMatrixConfig
        from daitum_configuration.data_source.data_source import DataSource
        from daitum_configuration.data_source.distance_matrix.output_matrix import (
            Metric,
            OutputMatrix,
        )

        cfg = DistanceMatrixConfig(
            "From", "Lon", "Lat", [OutputMatrix("Out", "Range", Metric.DRIVING_DISTANCE)]
        )
        ds = DataSource("Distance", cfg)
        built = ds.build()
        decoded = decode_into(DataSource, built, self._ctx(model))
        assert isinstance(decoded.config, DistanceMatrixConfig)
        assert decoded.build() == built

    def test_geo_location_config(self, model):
        from daitum_configuration import GeoLocationConfig
        from daitum_configuration.data_source.data_source import DataSource

        cfg = GeoLocationConfig("Sheet", "Address", "Lon", "Lat")
        ds = DataSource("Geo", cfg)
        built = ds.build()
        decoded = decode_into(DataSource, built, self._ctx(model))
        assert isinstance(decoded.config, GeoLocationConfig)
        assert decoded.build() == built

    def test_run_report_and_external_configs(self, model):
        from daitum_configuration.data_source.data_source import DataSource
        from daitum_configuration.data_source.run_external_model.run_external_model_config import (
            RunExternalModelConfig,
        )
        from daitum_configuration.data_source.run_report.run_report_config import RunReportConfig

        for cfg in (RunReportConfig("MyReport"), RunExternalModelConfig()):
            ds = DataSource("S", cfg)
            built = ds.build()
            decoded = decode_into(DataSource, built, self._ctx(model))
            assert type(decoded.config) is type(cfg)
            assert decoded.build() == built

    def test_set_features_config(self, model):
        from daitum_configuration import SetFeaturesConfig
        from daitum_configuration.data_source.data_source import DataSource

        cfg = SetFeaturesConfig({"flagA": True, "flagB": False})
        ds = DataSource("Features", cfg)
        built = ds.build()
        decoded = decode_into(DataSource, built, self._ctx(model))
        assert isinstance(decoded.config, SetFeaturesConfig)
        assert decoded.build() == built

    def test_batched_data_source_config(self, model):
        from daitum_configuration import BatchedDataSourceConfig, SetFeaturesConfig
        from daitum_configuration.data_source.data_source import DataSource
        from daitum_configuration.data_source.run_report.run_report_config import RunReportConfig

        inner_a = DataSource("A", RunReportConfig("R"))
        inner_b = DataSource("B", SetFeaturesConfig({"f": True}))
        batched = BatchedDataSourceConfig()
        batched.add_data_source(inner_a, order=1).add_data_source(inner_b, order=2)
        ds = DataSource("Batch", batched)
        built = ds.build()
        decoded = decode_into(DataSource, built, self._ctx(model))
        assert isinstance(decoded.config, BatchedDataSourceConfig)
        assert decoded.build() == built

    def test_decodes_to_typed_config(self, model):
        from daitum_configuration import DataStoreConfig
        from daitum_configuration.data_source.data_source import DataSource

        ds = DataSource("Store", DataStoreConfig("k", {"T": "S"}))
        decoded = decode_into(DataSource, ds.build(), self._ctx(model))
        # The decoded data source must hold a genuinely typed config, not a replayed dict.
        assert isinstance(decoded, DataSource)
        assert isinstance(decoded.config, DataStoreConfig)
        assert decoded.build() == ds.build()


class TestModelTransformRoundTrip:
    """Model-transform inputs round-trip; ModelTransform recursively decodes its sub-model."""

    def test_model_transform_config_with_inputs(self, model):
        from daitum_configuration import ExcelTransformConfig  # noqa: F401  (ensure registered)
        from daitum_configuration.data_source.data_source import DataSource
        from daitum_configuration.data_source.model_transform.model_transform_config import (
            ModelTransformConfig,
        )
        from daitum_configuration.data_source.model_transform.model_transform_input import (
            DataStoreInput,
            DirectUploadInput,
            DynamicValuesInput,
        )

        budget = model["symbols"]["BUDGET"]
        cfg = ModelTransformConfig("file_key", "transform.dtm")
        cfg.inputs.append(DynamicValuesInput(budget))
        cfg.inputs.append(DataStoreInput("store", {"T": "S"}, None, True))
        cfg.inputs.append(DirectUploadInput({"T2": "S2"}))
        ds = DataSource("Transform", cfg)
        built = ds.build()
        decoded = decode_into(DataSource, built, _model_ctx(model))
        assert isinstance(decoded.config, ModelTransformConfig)
        assert {type(i) for i in decoded.config.inputs} == {
            DynamicValuesInput,
            DataStoreInput,
            DirectUploadInput,
        }
        assert decoded.build() == built

    def test_model_transform_embeds_sub_model(self):
        from daitum_model import DataType, ModelBuilder
        from daitum_model.decoding import LoadContext

        from daitum_configuration.data_source.model_transform.model_transform import ModelTransform

        sub = ModelBuilder()
        sub_table = sub.add_data_table("Sub")
        sub_table.add_data_field("ID", DataType.STRING)
        sub_table.set_key_column("ID")

        parent = ModelBuilder()
        parent_table = parent.add_data_table("Sub")
        parent_table.add_data_field("ID", DataType.STRING)
        parent_table.set_key_column("ID")

        transform = ModelTransform(sub)
        transform.add_data_source_table(sub_table, parent_table)
        built = transform.build()
        decoded = decode_into(ModelTransform, built, LoadContext())
        assert isinstance(decoded, ModelTransform)
        assert decoded.build() == built


class TestScheduleAndPropertyRoundTrip:
    def test_schedule_configuration(self, model):
        from daitum_configuration.schedule_configuration.schedule_configuration import (
            ScheduleConfiguration,
        )
        from daitum_configuration.schedule_configuration.step_configuration import (
            StepConfiguration,
            StepType,
        )

        leaf = StepConfiguration(StepType.SINGLE, algorithm_config_key="ga")
        root = StepConfiguration(StepType.SEQUENCE)
        root.add_step(leaf)
        schedule = (
            ScheduleConfiguration(root)
            .add_algorithm("ga", GeneticAlgorithm(evaluations=1000))
            .add_global_parameter("seed", "42")
        )
        built = schedule.build()
        decoded = decode_into(ScheduleConfiguration, built, LoadContext())
        assert isinstance(decoded.schedule_root, StepConfiguration)
        assert isinstance(decoded.algorithm_configurations["ga"], GeneticAlgorithm)
        assert decoded.build() == built

    def test_stochastic_configuration(self):
        from daitum_configuration.model_configuration.stochastic_configuration import (
            MetricCombinationRule,
            StochasticConfiguration,
        )

        sc = StochasticConfiguration(5, 0.9, True).add_metric_rule("m", MetricCombinationRule.MAX)
        built = sc.build()
        decoded = decode_into(StochasticConfiguration, built, LoadContext())
        assert decoded.metric_rules["m"] is MetricCombinationRule.MAX
        assert decoded.build() == built

    def test_model_and_report_properties(self):
        from daitum_configuration.model_property.model_import_options import ModelImportOptions
        from daitum_configuration.model_property.model_property import ModelProperty
        from daitum_configuration.report_property.report_data import ReportData
        from daitum_configuration.report_property.report_export_format import ReportExportFormat
        from daitum_configuration.report_property.report_property import ReportProperty

        opts = ModelImportOptions()
        opts.set_key_column("ID").set_expected_column_count(3)
        mp = ModelProperty(calculate_on_load=True, import_options=opts)
        mp_built = mp.build()
        assert decode_into(ModelProperty, mp_built, LoadContext()).build() == mp_built

        rp = ReportProperty(ReportExportFormat.XLSX)
        # A single-element set keeps the list order deterministic for the byte-identical check.
        rp.set_report_data(ReportData({"Sheet1"})).set_name("Report")
        rp_built = rp.build()
        decoded_rp = decode_into(ReportProperty, rp_built, LoadContext())
        assert isinstance(decoded_rp.report_data, ReportData)
        assert decoded_rp.build() == rp_built

    def test_external_configuration(self, model):
        from daitum_configuration.model_configuration.external_configuration import (
            ExternalModelConfiguration,
            InputDataMapping,
            OutputDataMapping,
            ParameterMapping,
        )

        table = model["symbols"]["Items"]
        field = model["symbols"]["Quantity"]
        budget = model["symbols"]["BUDGET"]

        ext = ExternalModelConfiguration(requires_reload=False)
        ext.add_parameter_mapping(ParameterMapping("budget", budget))
        ext.add_input_data_mapping(
            InputDataMapping("items", table).add_column_mapping("qty", field)
        )
        ext.add_output_data_mapping(
            OutputDataMapping("out", table, key_column="qty", clear_existing=False)
        )
        built = ext.build()
        decoded = decode_into(ExternalModelConfiguration, built, _model_ctx(model))
        assert decoded.build() == built


class TestFullConfigurationRoundTrip:
    """A configuration exercising data sources + schedule + properties round-trips and re-edits."""

    def _build_full_config(self, model_builder):
        from daitum_configuration import GeneticAlgorithm, SetFeaturesConfig
        from daitum_configuration.configuration import ConfigurationBuilder
        from daitum_configuration.report_property.report_export_format import ReportExportFormat
        from daitum_configuration.report_property.report_property import ReportProperty

        cfg = ConfigurationBuilder()
        cfg.set_algorithm(GeneticAlgorithm(evaluations=2000))
        cfg.add_report_data_source("ReportSource", "MyReport")
        cfg.add_set_features("Features", SetFeaturesConfig({"flag": True}))
        cfg.add_report_property("R", ReportProperty(ReportExportFormat.CSV))
        cfg.set_model_property(calculate_on_load=True)
        return cfg

    def test_full_config_round_trips_and_re_edits(self, tmp_path):
        from daitum_configuration.configuration import ConfigurationBuilder
        from daitum_configuration.data_source.run_report.run_report_config import RunReportConfig

        model = ModelBuilder()
        model.add_data_table("T").add_data_field("ID", DataType.STRING)
        model.get_table("T").set_key_column("ID")
        model.write_to_file(tmp_path)
        loaded_model = ModelBuilder.read_from_file(tmp_path)

        cfg = self._build_full_config(loaded_model)
        built = cfg.build()

        cfg.write_to_file(tmp_path)
        decoded = ConfigurationBuilder.read_from_file(tmp_path, loaded_model)
        assert decoded.build() == built

        # Genuinely typed and re-editable.
        assert len(decoded.data_sources) == len(built["dataSources"])
        assert isinstance(decoded.data_sources[0].config, RunReportConfig)
        decoded.set_solution_view_allowed(True)
        assert decoded.build()["solutionViewAllowed"] is True


class TestNegativeDecoding:
    """Malformed payloads fail loudly with a useful LoadError, never silently degrade."""

    def test_unknown_data_source_type_raises(self):
        from daitum_model.decoding import LoadError

        from daitum_configuration.data_source.data_source_config import DataSourceConfig

        with pytest.raises(LoadError, match="Unknown data-source type"):
            decode_into(DataSourceConfig, {"type": "NOT_A_REAL_TYPE"}, LoadContext())

    def test_unknown_algorithm_key_raises(self):
        from daitum_model.decoding import LoadError

        with pytest.raises(LoadError, match="Unknown algorithmKey"):
            decode_into(Algorithm, {"algorithmKey": "no-such-algorithm"}, LoadContext())

    def test_dangling_reference_raises(self, model):
        from daitum_model.decoding import LoadError

        obj = Objective(model["symbols"]["TOTAL_COST"], maximise=False)
        built = obj.build()
        # Resolve against an empty symbol table — the referenced calculation is absent.
        with pytest.raises(LoadError, match="Unresolved reference"):
            decode_into(Objective, built, LoadContext())

    def test_missing_required_key_raises_load_error_not_key_error(self, model):
        from daitum_model.decoding import LoadError

        # A payload missing a required build key must surface as the layer's LoadError (naming
        # the key and owner), not leak a bare KeyError from deep inside a decoder.
        obj = Objective(model["symbols"]["TOTAL_COST"], maximise=False)
        built = obj.build()
        del built["maximise"]
        ctx = LoadContext()
        ctx.register("TOTAL_COST", model["symbols"]["TOTAL_COST"])
        with pytest.raises(LoadError, match="Objective: missing required key 'maximise'"):
            decode_into(Objective, built, ctx)
