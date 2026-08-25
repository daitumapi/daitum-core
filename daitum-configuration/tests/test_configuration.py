"""
Tests for daitum_configuration: Buildable serialisation, fluent builders, and edge cases.

The suite is split into:
    1. Imports — all public symbols are reachable.
    2. Snapshots — golden-output assertions for every class's ``build()``.
    3. Fluent builder chains — verifies ``set_*``/``add_*`` return the right object.
    4. Edge cases — None handling, enum extraction, idempotency, instance storage.
"""

import json

import pytest
from daitum_model import DataType, ModelBuilder
from daitum_model.formula import CONST

import daitum_configuration
from daitum_configuration import (
    BatchDataSourceType,
    BatchedDataSourceConfig,
    CMAESAlgorithm,
    ComparatorType,
    ConfigurationBuilder,
    ConstraintType,
    DataStoreConfig,
    DistanceMatrixConfig,
    DVType,
    EqualityDataFilter,
    ExcelTransformConfig,
    ExternalModelConfiguration,
    GeneticAlgorithm,
    GeoLocationConfig,
    ImportOptionOverrides,
    InequalityDataFilter,
    InputDataMapping,
    Metric,
    MetricCombinationRule,
    ModelConfiguration,
    ModelImportOptions,
    ModelTransform,
    ModelTransformConfig,
    NumericExpression,
    OutputDataMapping,
    OutputMatrix,
    OverlayConfig,
    ParameterMapping,
    Priority,
    RecombinatorType,
    RegexDataFilter,
    ReportData,
    ReportExportFormat,
    ScheduleConfiguration,
    Selection,
    SelectionType,
    SetDataFilter,
    SetFeaturesConfig,
    SteepestDynamicLocalSearch,
    StepConfiguration,
    StepType,
    StochasticConfiguration,
    VariableNeighbourhoodSearch,
    WildcardDataFilter,
)
from daitum_configuration.report_property.report_property import ReportProperty

# ----------------------------------------------------------------------------------------
# Imports
# ----------------------------------------------------------------------------------------


class TestImports:
    def test_package_importable(self):
        assert daitum_configuration is not None

    def test_top_level_classes(self):
        for cls in (
            ConfigurationBuilder,
            GeneticAlgorithm,
            CMAESAlgorithm,
            VariableNeighbourhoodSearch,
            SteepestDynamicLocalSearch,
            ModelConfiguration,
            ExcelTransformConfig,
            DataStoreConfig,
            DistanceMatrixConfig,
            GeoLocationConfig,
            SetFeaturesConfig,
            BatchedDataSourceConfig,
            ModelTransformConfig,
            StochasticConfiguration,
            ExternalModelConfiguration,
            StepConfiguration,
        ):
            assert cls is not None


# ----------------------------------------------------------------------------------------
# Helpers
# ----------------------------------------------------------------------------------------


def _make_calculation(model: ModelBuilder, name: str, datatype: DataType = DataType.DECIMAL):
    """Build a tiny calculation usable as an objective/constraint target."""
    if datatype == DataType.DECIMAL:
        return model.add_calculation(name, CONST(1.0))
    return model.add_calculation(name, CONST(1))


# ----------------------------------------------------------------------------------------
# Snapshots — leaf classes
# ----------------------------------------------------------------------------------------


class TestLeafSnapshots:
    def test_overlay_config(self):
        assert OverlayConfig().build() == {
            "showDecisionOverlay": False,
            "showLockOverlay": False,
            "showObjectiveOverlay": False,
            "showConstraintOverlay": False,
        }

    def test_overlay_config_all_set(self):
        assert OverlayConfig(True, True, True, True).build() == {
            "showDecisionOverlay": True,
            "showLockOverlay": True,
            "showObjectiveOverlay": True,
            "showConstraintOverlay": True,
        }

    def test_model_import_options_defaults_skip_nones(self):
        result = ModelImportOptions().build()
        assert result == {
            "matchColumnCount": True,
            "expectedColumnCount": 0,
            "matchColumnHeaders": True,
            "preserveOrdering": False,
            "matchExistingRows": False,
            "clearSheet": True,
            "resetDecisions": False,
            "closeOnSuccess": True,
            "skipPreProcessors": False,
        }

    def test_model_import_options_with_optionals(self):
        opts = (
            ModelImportOptions().set_key_column("ID").set_locale_key("en_AU").set_sync_key("sync-1")
        )
        out = opts.build()
        assert out["keyColumn"] == "ID"
        assert out["localeKey"] == "en_AU"
        assert out["syncKey"] == "sync-1"

    def test_import_option_overrides(self):
        assert ImportOptionOverrides(True, True, True, True).build() == {
            "matchColumnCount": True,
            "matchColumnHeaders": True,
            "matchExistingRows": True,
            "preserveOrdering": True,
            "clearSheet": False,
            "resetDecisions": False,
        }

    def test_output_matrix(self):
        assert OutputMatrix("Sheet1", "Distances", Metric.DRIVING_DISTANCE).build() == {
            "sheetName": "Sheet1",
            "namedRange": "Distances",
            "metric": "DRIVING_DISTANCE",
        }

    def test_report_data(self):
        rd = ReportData(required_sheets={"Summary"}, requires_monte_carlo=True)
        out = rd.build()
        assert out["requiredSheets"] == ["Summary"]
        assert out["requiresMonteCarlo"] is True
        assert out["requiresScenarioComparison"] is False


# ----------------------------------------------------------------------------------------
# Snapshots — model property and report property
# ----------------------------------------------------------------------------------------


class TestPropertySnapshots:
    def test_model_property_minimal(self):
        from daitum_configuration.model_property.model_property import ModelProperty

        result = ModelProperty().build()
        assert result == {
            "calculateOnLoad": False,
            "calculationEnabled": True,
            "ignoreFormula": False,
        }

    def test_model_property_with_nested_buildables(self):
        from daitum_configuration.model_property.model_property import ModelProperty

        mp = ModelProperty(
            calculate_on_load=True,
            import_options=ModelImportOptions(),
            overlay_config=OverlayConfig(show_decision_overlay=True),
        )
        result = mp.build()
        assert result["calculateOnLoad"] is True
        assert result["importOptions"]["matchColumnCount"] is True
        assert result["overlayConfig"]["showDecisionOverlay"] is True

    def test_report_property_defaults(self):
        rp = ReportProperty(ReportExportFormat.XLSX, "iface")
        out = rp.build()
        assert out["exportCsv"] is False
        assert out["exportFormat"] == "XLSX"
        assert out["exportInterfaceKey"] == "iface"
        assert out["orderIndex"] == 0
        assert out["showInMenu"] is True

    def test_report_property_fluent(self):
        rp = (
            ReportProperty(ReportExportFormat.CSV)
            .set_name("My Report")
            .set_order_index(2)
            .set_visible_on_navigator(True)
            .set_export_csv(True)
        )
        out = rp.build()
        assert out["name"] == "My Report"
        assert out["orderIndex"] == 2
        assert out["visibleOnNavigator"] is True
        assert out["exportCsv"] is True

    def test_report_property_report_name_fallback(self):
        assert ReportProperty(ReportExportFormat.XLSX, "iface-key").report_name() == "iface-key"
        assert (
            ReportProperty(ReportExportFormat.XLSX, "iface-key").set_name("Display").report_name()
            == "Display"
        )


# ----------------------------------------------------------------------------------------
# Snapshots — data source configs
# ----------------------------------------------------------------------------------------


class TestDataSourceSnapshots:
    def test_excel_transform_default(self):
        cfg = ExcelTransformConfig("key", "file.xlsx", [("Source", "Target")])
        out = cfg.build()
        assert out["type"] == "EXCEL_TRANSFORM"
        assert out["fileKey"] == "key"
        assert out["fileName"] == "file.xlsx"
        assert out["sheetMapping"] == [{"sourceSheet": "Source", "targetSheet": "Target"}]
        assert out["sheetNames"] == []
        assert out["perSheetOverrides"] == {}
        assert out["trackChangesSupported"] is False

    def test_excel_transform_with_per_sheet_overrides(self):
        overrides = {"sheet_one": ImportOptionOverrides(match_column_count=True)}
        cfg = (
            ExcelTransformConfig("key", "f.xlsx", [("A", "B")])
            .set_debug_file(True)
            .set_per_sheet_overrides(overrides)
        )
        out = cfg.build()
        assert out["debugFile"] is True
        # Dict keys are preserved verbatim by Buildable.convert.
        assert "sheet_one" in out["perSheetOverrides"]
        assert out["perSheetOverrides"]["sheet_one"]["matchColumnCount"] is True

    def test_data_store_config(self):
        cfg = DataStoreConfig("my_store", {"Jobs": "jobs"})
        out = cfg.build()
        assert out["type"] == "DATA_STORE"
        assert out["dataStoreKey"] == "my_store"
        assert out["tables"] == {"Jobs": "jobs"}
        assert out["trackChangesSupported"] is True
        # No filter set → key omitted (None values skipped).
        assert "modelFilter" not in out

    def test_data_store_config_with_filter(self):
        model = ModelBuilder()
        param = model.add_parameter("STATUS", DataType.STRING, "Active")
        cfg = DataStoreConfig("store", {"Jobs": "jobs"}).set_model_filter(
            EqualityDataFilter(["status"], param)
        )
        out = cfg.build()
        assert out["modelFilter"]["@type"] == "equality"
        assert out["modelFilter"]["sourceKey"].startswith("!!!")

    def test_distance_matrix_config(self):
        cfg = DistanceMatrixConfig(
            "From", "FromLng", "FromLat", [OutputMatrix("Out", "Range", Metric.DRIVING_TIME)]
        ).set_to_sheet("To", "ToLng", "ToLat")
        out = cfg.build()
        assert out["type"] == "DISTANCE_MATRIX"
        assert out["fromSheetName"] == "From"
        assert out["toSheetName"] == "To"
        assert out["outputs"][0]["metric"] == "DRIVING_TIME"

    def test_geo_location_config(self):
        cfg = (
            GeoLocationConfig("Sites", "Address", "Lng", "Lat")
            .set_region("AU")
            .set_live_update(True)
        )
        out = cfg.build()
        assert out["type"] == "GEOLOCATION"
        assert out["sheetName"] == "Sites"
        assert out["region"] == "AU"
        assert out["liveUpdate"] is True

    def test_set_features_config(self):
        cfg = SetFeaturesConfig({"feature_a": True, "feature_b": False})
        out = cfg.build()
        assert out["type"] == "SET_FEATURES"
        assert out["featureSettings"] == {"feature_a": True, "feature_b": False}

    def test_run_report_via_configuration(self):
        cfg = ConfigurationBuilder()
        ds = cfg.add_report_data_source("Report DS", "MyReport")
        out = ds.build()
        assert out["config"]["type"] == "RUN_REPORT"
        assert out["config"]["reportName"] == "MyReport"

    def test_run_external_model_via_configuration(self):
        cfg = ConfigurationBuilder()
        ds = cfg.add_external_model_data_source("External DS")
        out = ds.build()
        assert out["config"]["type"] == "RUN_EXTERNAL_MODEL"

    def test_batched_data_source(self):
        inner = BatchedDataSourceConfig(run_after_import_sheet="Done")
        # Build a wrapping DataSource so we can pass it into the batched config.
        from daitum_configuration.data_source.data_source import DataSource

        ds = DataSource(
            "child",
            ExcelTransformConfig("k", "f.xlsx", [("A", "B")]),
        )
        inner.add_data_source(
            ds, order=0, batch_data_source_type=BatchDataSourceType.START_PARALLEL
        )
        out = inner.build()
        assert out["type"] == "BATCHED_DATA_SOURCE"
        assert out["runAfterImportSheet"] == "Done"
        assert out["dataSources"][0]["order"] == 0
        assert out["dataSources"][0]["type"] == "START_PARALLEL"
        assert isinstance(out["dataSources"][0]["dataSourceId"], int)

    def test_model_transform_config_with_typed_inputs(self):
        model = ModelBuilder()
        tz = model.add_parameter("TZ", DataType.STRING, "Australia/Sydney")
        cfg = (
            ModelTransformConfig("transform_key", "transform.json")
            .add_dynamic_values(tz)
            .add_direct_upload_input({"src": "tgt"})
        )
        out = cfg.build()
        assert out["type"] == "MODEL_TRANSFORM"
        assert out["fileKey"] == "transform_key"
        assert len(out["inputs"]) == 2
        assert out["inputs"][0]["sourceType"] == "DYNAMIC_VALUES"
        assert out["inputs"][0]["timezoneKey"] == "TZ"
        assert out["inputs"][1]["sourceType"] == "DIRECT_UPLOAD"
        assert out["inputs"][1]["tableMapping"] == {"src": "tgt"}


# ----------------------------------------------------------------------------------------
# Snapshots — data filters
# ----------------------------------------------------------------------------------------


class TestFilterSnapshots:
    def _make_param(self):
        m = ModelBuilder()
        return m, m.add_parameter("STATUS", DataType.STRING, "Active")

    def test_equality_data_filter(self):
        _, param = self._make_param()
        f = EqualityDataFilter(["status"], param, value="x")
        out = f.build()
        assert out["@type"] == "equality"
        assert out["path"] == ["status"]
        assert out["value"] == "x"
        assert out["sourceKey"] == f"!!!{param.to_string()}"

    def test_regex_data_filter_uses_to_string(self):
        # Verifies the bug-fix: the source_key is formatted via .to_string().
        _, param = self._make_param()
        f = RegexDataFilter(["pattern"], param)
        out = f.build()
        assert out["sourceKey"] == f"!!!{param.to_string()}"

    def test_wildcard_data_filter_uses_to_string(self):
        _, param = self._make_param()
        f = WildcardDataFilter(["pattern"], param, case_sensitive=True)
        out = f.build()
        assert out["sourceKey"] == f"!!!{param.to_string()}"
        assert out["caseSensitive"] is True

    def test_set_data_filter(self):
        m = ModelBuilder()
        p1 = m.add_parameter("P1", DataType.STRING, "a")
        p2 = m.add_parameter("P2", DataType.STRING, "b")
        f = SetDataFilter(["p"], [p1, p2], values={"x", "y"})
        out = f.build()
        assert out["@type"] == "set"
        # Set is converted to a list for JSON safety.
        assert isinstance(out["values"], list)
        assert sorted(out["sourceKey"]) == sorted([f"!!!{p1.to_string()}", f"!!!{p2.to_string()}"])

    def test_inequality_data_filter(self):
        m = ModelBuilder()
        lo = m.add_parameter("LO", DataType.DECIMAL, 0.0)
        hi = m.add_parameter("HI", DataType.DECIMAL, 10.0)
        f = InequalityDataFilter(["x"], lo, hi, lower=0.0, upper=10.0)
        out = f.build()
        assert out["@type"] == "inequality"
        assert out["lower"] == 0.0
        assert out["upper"] == 10.0
        assert out["lowerKey"] == f"!!!{lo.to_string()}"
        assert out["upperKey"] == f"!!!{hi.to_string()}"


# ----------------------------------------------------------------------------------------
# Snapshots — algorithms
# ----------------------------------------------------------------------------------------


class TestAlgorithmSnapshots:
    def test_genetic_algorithm_default_shape(self):
        out = GeneticAlgorithm().build()
        assert out["algorithmKey"] == "daitum-gga-single-objective"
        params = out["parameters"]
        assert params["Log info"] == {"@type": "quantitative", "value": False}
        assert params["Recombinator"] == {
            "@type": "qualitative",
            "value": "Uniform crossover",
            "parameters": {},
        }
        # Selection nests its own parameters.
        assert params["Selection"]["@type"] == "qualitative"
        assert params["Selection"]["parameters"]["Selection pool size"] == {
            "@type": "quantitative",
            "value": "2",
        }

    def test_genetic_algorithm_n_point_crossover(self):
        # Picking N-point crossover should auto-populate n_point_cuts to 2.
        ga = GeneticAlgorithm(recombinator=RecombinatorType.N_POINT_CROSSOVER)
        out = ga.build()
        assert out["parameters"]["N-point cuts"] == {"@type": "quantitative", "value": "2"}

    def test_genetic_algorithm_with_comparator(self):
        ga = GeneticAlgorithm(comparator=ComparatorType.LEXICOGRAPHIC_COMPARATOR)
        out = ga.build()
        assert out["parameters"]["Comparator"]["value"] == "Lexicographic comparator"

    def test_cmaes_algorithm_default_shape(self):
        out = CMAESAlgorithm().build()
        assert out["algorithmKey"] == "daitum-cmaes"
        params = out["parameters"]
        assert "Sigma" in params
        assert params["Sigma"]["@type"] == "quantitative"

    def test_vns_algorithm_default_shape(self):
        out = VariableNeighbourhoodSearch().build()
        assert out["algorithmKey"] == "daitum-vns-single-objective"
        params = out["parameters"]
        assert "Initial mutation rate" in params
        assert params["Mutation"]["@type"] == "qualitative"

    def test_vns_algorithm_population_and_selection(self):
        # Defaults: tau = 0.5 (lognormal learning rate); selection defaults to
        # fast tournament; population_size defaults to NUM_VARIABLES expression.
        vns = VariableNeighbourhoodSearch()
        params = vns.build()["parameters"]
        assert params["Mutation rate tau"]["value"] == "0.5"
        assert "Mutation rate up scale" not in params
        assert "Mutation rate down scale" not in params
        assert params["Selection"]["@type"] == "qualitative"
        assert params["Selection"]["value"] == SelectionType.FAST_TOURNAMENT_SELECTION.value
        assert "Population size" in params

        # Explicit configuration flows through.
        configured = VariableNeighbourhoodSearch(
            population_size=128,
            offspring_size=16,
            selection=Selection.selection(SelectionType.TOURNAMENT_SELECTION, pool_size=4),
        ).build()["parameters"]
        assert configured["Population size"]["value"] == "128"
        assert configured["Selection"]["value"] == SelectionType.TOURNAMENT_SELECTION.value
        assert configured["Selection"]["parameters"]["Selection pool size"]["value"] == "4"

    def test_algorithm_post_construction_mutation_reflected_in_build(self):
        # Building parameters lazily ensures attribute mutation flows through.
        ga = GeneticAlgorithm()
        ga.population_size = 200
        out = ga.build()
        assert out["parameters"]["Population size"] == {
            "@type": "quantitative",
            "value": "200",
        }

    def test_steepest_dynamic_local_search_default_shape(self):
        out = SteepestDynamicLocalSearch().build()
        assert out["algorithmKey"] == "daitum-steepest-dynamic-localsearch-single-objective"
        params = out["parameters"]
        assert params["Allow neutral walks"] == {"@type": "quantitative", "value": False}
        assert params["Integer step size"] == {"@type": "quantitative", "value": "10"}
        assert params["Decimal step size"] == {"@type": "quantitative", "value": "0.1"}
        assert params["Integer step change"] == {"@type": "quantitative", "value": "1"}
        assert params["Integer lowest step"] == {"@type": "quantitative", "value": "1"}
        assert params["Decimal step change"] == {"@type": "quantitative", "value": "0.001"}
        assert params["Decimal lowest step"] == {"@type": "quantitative", "value": "0.001"}
        # Base Algorithm parameters are emitted alongside the SDLS-specific ones.
        for key in (
            "Log info",
            "Evaluations",
            "Maximum evaluations without improvement",
            "Maximum time without improvement",
            "Minimum improvement",
            "Maximum restart count",
            "PRNG seed",
            "Time limit",
        ):
            assert key in params

    def test_steepest_dynamic_local_search_with_named_value(self):
        sdls = SteepestDynamicLocalSearch(integer_step_size=NumericExpression("NUM_VARIABLES"))
        params = sdls.build()["parameters"]
        assert params["Integer step size"] == {
            "@type": "quantitative",
            "value": "NUM_VARIABLES",
        }

    def test_steepest_dynamic_local_search_rejects_invalid_types(self):
        with pytest.raises(TypeError):
            SteepestDynamicLocalSearch(integer_step_size=0.5)  # float for an int param
        with pytest.raises(ValueError):
            SteepestDynamicLocalSearch(integer_step_size=-1)
        with pytest.raises(TypeError):
            SteepestDynamicLocalSearch(decimal_step_size=1)  # int for a float param
        with pytest.raises(ValueError):
            SteepestDynamicLocalSearch(decimal_lowest_step=-0.1)


class TestAlgorithmParameterWrapping:
    @pytest.mark.parametrize(
        "value,expected_value",
        [
            (True, True),
            (False, False),
            (None, None),
            (5, "5"),
            (3.14, "3.14"),
        ],
    )
    def test_quant_value_branch(self, value, expected_value):
        from daitum_configuration.algorithm_configuration.algorithm import Algorithm

        result = Algorithm._quant(value)
        assert result["@type"] == "quantitative"
        assert result["value"] == expected_value

    def test_quant_with_named_value(self):
        from daitum_configuration.algorithm_configuration.algorithm import Algorithm

        m = ModelBuilder()
        p = m.add_parameter("X", DataType.INTEGER, 1)
        result = Algorithm._quant(p)
        assert result == {"@type": "quantitative", "value": "!!!X"}

    def test_qual_with_string_value(self):
        from daitum_configuration.algorithm_configuration.algorithm import Algorithm

        result = Algorithm._qual("Hello", {"k": Algorithm._quant(1)})
        assert result["@type"] == "qualitative"
        assert result["value"] == "Hello"
        assert result["parameters"]["k"]["value"] == "1"


# ----------------------------------------------------------------------------------------
# Snapshots — model configuration objects
# ----------------------------------------------------------------------------------------


class TestModelConfigurationSnapshots:
    def test_decision_variable_with_parameter(self):
        m = ModelBuilder()
        p = m.add_parameter("DV", DataType.INTEGER, 0)
        from daitum_configuration.model_configuration.decision_variable import DecisionVariable

        dv = DecisionVariable(p, dv_type=DVType.RANGE).set_min(0).set_max(10)
        out = dv.build()
        assert out["cellReference"] == f"!!!{p.to_string()}"
        spec = out["specification"]
        assert spec["@type"] == "range"
        assert spec["minimumValue"] == 0
        assert spec["maximumValue"] == 10
        assert spec["minimumValueReference"] is None

    def test_decision_variable_tag_and_seed_sources(self):
        from daitum_configuration.model_configuration.decision_variable import DecisionVariable

        m = ModelBuilder()
        p = m.add_parameter("DV", DataType.INTEGER, 0)
        tag_param = m.add_parameter("Tags", DataType.STRING, "")
        seed_param = m.add_parameter("Seed", DataType.INTEGER, 0)

        # Defaults: both sources serialised as null when unset.
        dv = DecisionVariable(p, dv_type=DVType.RANGE)
        out = dv.build()
        assert out["tagSource"] is None
        assert out["specification"]["seedSource"] is None

        # After setting, both serialise as !!!-prefixed references matching
        # the cellReference format.
        assert dv.set_tag_source(tag_param) is dv
        assert dv.set_seed_source(seed_param) is dv
        out = dv.build()
        assert out["tagSource"] == f"!!!{tag_param.to_string()}"
        assert out["specification"]["seedSource"] == f"!!!{seed_param.to_string()}"

    def test_decision_variable_per_row_sources_use_table_field(self):
        from daitum_configuration.model_configuration.decision_variable import DecisionVariable

        m = ModelBuilder()
        items = m.add_data_table("Items")
        items.set_key_column("Name")
        items.add_data_field("Name", DataType.STRING)
        qty = items.add_data_field("Qty", DataType.INTEGER)
        tag_field = items.add_data_field("Tag", DataType.STRING)
        seed_field = items.add_data_field("SeedQty", DataType.INTEGER)

        dv = DecisionVariable(qty, dv_table=items, dv_type=DVType.RANGE)
        dv.set_tag_source(tag_field).set_seed_source(seed_field)
        out = dv.build()
        assert out["tagSource"] == f"!!!{items.id}[{tag_field.id}]"
        assert out["specification"]["seedSource"] == f"!!!{items.id}[{seed_field.id}]"

    def test_decision_variable_injective(self):
        from daitum_configuration.model_configuration.decision_variable import DecisionVariable

        m = ModelBuilder()
        jobs = m.add_data_table("Jobs")
        jobs.set_key_column("Name")
        jobs.add_data_field("Name", DataType.STRING)
        order = jobs.add_data_field("Order", DataType.INTEGER)
        allowed = jobs.add_data_field("Allowed", DataType.STRING)

        # Minimal form: no domain, both spec references null but present.
        dv = DecisionVariable(order, dv_table=jobs, dv_type=DVType.INJECTIVE)
        out = dv.build()
        assert out["cellReference"] == f"!!!{jobs.id}[{order.id}]"
        spec = out["specification"]
        assert spec["@type"] == "injective"
        assert spec["domainReference"] is None
        assert spec["seedSource"] is None
        assert "minimumValue" not in spec
        assert "scale" not in spec

        # With a domain column, domainReference is a !!!-prefixed table reference.
        assert dv.set_domain(allowed) is dv
        out = dv.build()
        assert out["specification"]["domainReference"] == f"!!!{jobs.id}[{allowed.id}]"

    def test_decision_variable_injective_rejects_invalid(self):
        from daitum_configuration.model_configuration.decision_variable import DecisionVariable

        m = ModelBuilder()
        p = m.add_parameter("DV", DataType.INTEGER, 0)
        # A model-level (parameter) injective DV is rejected.
        with pytest.raises(ValueError, match="Injective decision variables require a table"):
            DecisionVariable(p, dv_type=DVType.INJECTIVE)

        jobs = m.add_data_table("Jobs")
        jobs.set_key_column("Name")
        jobs.add_data_field("Name", DataType.STRING)
        order = jobs.add_data_field("Order", DataType.INTEGER)
        cost = jobs.add_data_field("Cost", DataType.DECIMAL)

        # A non-integer decision column is rejected.
        with pytest.raises(ValueError, match="not integer"):
            DecisionVariable(cost, dv_table=jobs, dv_type=DVType.INJECTIVE)

        # A non-string domain column is rejected.
        dv = DecisionVariable(order, dv_table=jobs, dv_type=DVType.INJECTIVE)
        with pytest.raises(ValueError, match="not string"):
            dv.set_domain(order)

        # set_domain on a non-injective DV is rejected.
        range_dv = DecisionVariable(order, dv_table=jobs, dv_type=DVType.RANGE)
        with pytest.raises(ValueError, match="only valid for DVType.INJECTIVE"):
            range_dv.set_domain(order)

    def test_objective(self):
        m = ModelBuilder()
        c = _make_calculation(m, "OBJ_COST")
        from daitum_configuration.model_configuration.objective import Objective

        obj = Objective(c, maximise=False, priority=Priority.HIGH, weight=2.5, name="cost")
        out = obj.build()
        assert out["cellReference"].startswith("!!!")
        assert out["maximise"] is False
        assert out["priority"] == "HIGH"
        assert out["weight"] == 2.5
        assert out["name"] == "cost"

    def test_constraint_inequality(self):
        m = ModelBuilder()
        c = _make_calculation(m, "C1")
        from daitum_configuration.model_configuration.constraint import Constraint

        cons = (
            Constraint(c)
            .set_type(ConstraintType.INEQUALITY)
            .set_lower_bound(0.0)
            .set_upper_bound(10.0)
            .set_name("range")
        )
        out = cons.build()
        spec = out["specification"]
        assert spec["@type"] == "inequality"
        assert spec["lowerBound"] == 0.0
        assert spec["upperBound"] == 10.0
        assert spec["lowerBoundReference"] is None
        assert out["name"] == "range"

    def test_constraint_with_calculation_bound(self):
        m = ModelBuilder()
        c = _make_calculation(m, "C2")
        ub = _make_calculation(m, "UB")
        from daitum_configuration.model_configuration.constraint import Constraint

        cons = Constraint(c).set_upper_bound(ub)
        out = cons.build()
        assert out["specification"]["upperBound"] is None
        assert out["specification"]["upperBoundReference"] == ub.to_string()

    def test_scenario_output_calculation(self):
        m = ModelBuilder()
        c = _make_calculation(m, "OUT")
        from daitum_configuration.model_configuration.scenario_output import ScenarioOutput

        so = ScenarioOutput("output", c)
        out = so.build()
        assert out["name"] == "output"
        assert out["cellReference"] == f"!!!{c.to_string()}"

    def test_model_configuration_full(self):
        m = ModelBuilder()
        cost = _make_calculation(m, "COST")
        cap = _make_calculation(m, "CAP")
        out = _make_calculation(m, "OUT")

        cfg = ModelConfiguration()
        cfg.add_objective(cost, maximise=False, name="cost")
        cfg.add_constraint(cap).set_upper_bound(100.0)
        cfg.add_scenario_output("out", out)
        cfg.set_validation_enabled(False).set_profiling(True)

        result = cfg.build()
        assert isinstance(result["objectives"], list)
        assert result["objectives"][0]["name"] == "cost"
        assert result["constraints"][0]["specification"]["upperBound"] == 100.0
        assert result["scenarioOutputs"][0]["name"] == "out"
        assert result["validationEnabled"] is False
        assert result["profiling"] is True
        # decisionVariables list is empty.
        assert result["decisionVariables"] == []

    def test_model_configuration_stores_instances_not_dicts(self):
        m = ModelBuilder()
        c = _make_calculation(m, "OBJ_DUP")
        cfg = ModelConfiguration()
        cfg.add_objective(c, name="x")
        # Verify the underlying state is an Objective, not a dict.
        from daitum_configuration.model_configuration.objective import Objective

        assert all(isinstance(o, Objective) for o in cfg.objectives)

    def test_scenario_output_duplicate_detection(self):
        m = ModelBuilder()
        c = _make_calculation(m, "OUT_DUP")
        cfg = ModelConfiguration()
        cfg.add_scenario_output("name", c)
        with pytest.raises(ValueError, match="already exists"):
            cfg.add_scenario_output("name", c)

    def test_external_model_configuration(self):
        m = ModelBuilder()
        p = m.add_parameter("P1", DataType.STRING, "a")
        ext = ExternalModelConfiguration().add_parameter_mapping(ParameterMapping("paramA", p))
        out = ext.build()
        assert out["requiresReload"] is True
        assert out["parameterMappings"] == [{"parameterName": "paramA", "location": "P1"}]
        assert out["inputDataMappings"] == []
        assert out["outputDataMappings"] == []


# ----------------------------------------------------------------------------------------
# Snapshots — stochastic configuration (camelCase migration + enum fix)
# ----------------------------------------------------------------------------------------


class TestStochasticConfiguration:
    def test_default(self):
        sc = StochasticConfiguration(runs=10, p=0.05, disable_evaluator_caching=False)
        out = sc.build()
        assert out == {
            "runs": 10,
            "p": 0.05,
            "disableEvaluatorCaching": False,
            "metricRules": {},
        }

    def test_metric_rules_enum_extraction(self):
        sc = (
            StochasticConfiguration(runs=5, p=0.1, disable_evaluator_caching=True)
            .add_metric_rule("metric1", MetricCombinationRule.MIN)
            .add_metric_rule("metric2", MetricCombinationRule.PVALUE_MAX)
        )
        out = sc.build()
        assert out["metricRules"] == {"metric1": "MIN", "metric2": "PVALUE_MAX"}
        # Round-trip through json.dumps proves enums no longer leak.
        json.dumps(out)


# ----------------------------------------------------------------------------------------
# Snapshots — schedule configuration
# ----------------------------------------------------------------------------------------


class TestScheduleSnapshots:
    def test_step_configuration_single(self):
        step = StepConfiguration(StepType.SINGLE, algorithm_config_key="algo_1")
        out = step.build()
        assert out["type"] == "SINGLE"
        assert out["algorithmConfigKey"] == "algo_1"

    def test_step_configuration_parallel(self):
        leaf1 = StepConfiguration(StepType.SINGLE, algorithm_config_key="a")
        leaf2 = StepConfiguration(StepType.SINGLE, algorithm_config_key="b")
        parent = StepConfiguration(StepType.PARALLEL)
        parent.add_step(leaf1).add_step(leaf2)
        out = parent.build()
        assert out["type"] == "PARALLEL"
        assert len(out["steps"]) == 2

    def test_step_configuration_defaults_omit_optional_fields(self):
        # With no extra configuration, optional None fields are omitted by
        # Buildable. The boolean flags default to False and ARE emitted.
        step = StepConfiguration(StepType.SINGLE, algorithm_config_key="algo_1")
        out = step.build()
        assert "includedTags" not in out
        assert "overrideParameters" not in out
        assert "splitValuesKey" not in out
        assert "disabledKey" not in out
        assert out["recalculateRanges"] is False
        assert out["deferred"] is False

    def test_step_configuration_subproblem_and_execution_fields(self):
        step = (
            StepConfiguration(StepType.SINGLE, algorithm_config_key="algo_1")
            .add_included_tag("phase1")
            .add_included_tag("phase2")
            .add_included_tag("phase1")  # duplicate is ignored
            .add_override_parameter("populationSize", "200")
            .add_override_parameter("maxEvaluations", "10000")
            .set_split_values_key("groups[partition]")
            .set_recalculate_ranges(True)
            .set_disabled_key("flags[abort]")
            .set_deferred(True)
        )
        out = step.build()
        assert out["includedTags"] == ["phase1", "phase2"]
        assert out["overrideParameters"] == {
            "populationSize": "200",
            "maxEvaluations": "10000",
        }
        assert out["splitValuesKey"] == "groups[partition]"
        assert out["recalculateRanges"] is True
        assert out["disabledKey"] == "flags[abort]"
        assert out["deferred"] is True

    def test_step_configuration_setters_return_self(self):
        step = StepConfiguration(StepType.SINGLE, algorithm_config_key="algo_1")
        assert step.add_included_tag("a") is step
        assert step.add_override_parameter("k", "v") is step
        assert step.set_split_values_key("s") is step
        assert step.set_recalculate_ranges(True) is step
        assert step.set_disabled_key("d") is step
        assert step.set_deferred(True) is step

    def test_schedule_configuration(self):
        ga = GeneticAlgorithm()
        root = StepConfiguration(StepType.SINGLE, algorithm_config_key="ga")
        sc = ScheduleConfiguration(root).add_algorithm("ga", ga)
        out = sc.build()
        assert "algorithmConfigurations" in out
        assert out["algorithmConfigurations"]["ga"]["algorithmKey"] == "daitum-gga-single-objective"
        assert out["scheduleRoot"]["type"] == "SINGLE"

    def test_schedule_configuration_global_parameters(self):
        root = StepConfiguration(StepType.SINGLE, algorithm_config_key="ga")
        sc = ScheduleConfiguration(root)
        # No global params by default.
        assert "globalParameters" not in sc.build()
        # Adder is fluent and accumulates entries; same key replaces.
        result = (
            sc.add_global_parameter("seed", "42")
            .add_global_parameter("threads", "8")
            .add_global_parameter("seed", "99")
        )
        assert result is sc
        assert sc.build()["globalParameters"] == {"seed": "99", "threads": "8"}


# ----------------------------------------------------------------------------------------
# Top-level ConfigurationBuilder end-to-end
# ----------------------------------------------------------------------------------------


class TestConfigurationEndToEnd:
    def test_default_configuration_serialises(self):
        cfg = ConfigurationBuilder()
        out = cfg.build()
        assert out["solutionViewAllowed"] is False
        assert out["solutionViewEnabled"] is False
        assert out["dataSources"] == []
        assert "algorithmConfiguration" not in out  # None values skipped

    def test_full_configuration(self):
        m = ModelBuilder()
        cost = _make_calculation(m, "TOTAL_COST")
        model_cfg = ModelConfiguration()
        model_cfg.add_objective(cost, name="cost")

        cfg = (
            ConfigurationBuilder()
            .set_algorithm(GeneticAlgorithm())
            .set_model_configuration(model_cfg)
            .set_solution_view_allowed(True)
        )
        cfg.add_excel_transform("Inputs", ExcelTransformConfig("k", "f.xlsx", [("A", "B")]))
        cfg.add_report_property(
            "summary", ReportProperty(ReportExportFormat.XLSX).set_name("Summary")
        )

        out = cfg.build()
        assert out["algorithmConfiguration"]["algorithmKey"] == "daitum-gga-single-objective"
        assert out["modelConfiguration"]["objectives"][0]["name"] == "cost"
        assert out["dataSources"][0]["name"] == "Inputs"
        assert out["reportProperties"]["summary"]["name"] == "Summary"
        assert out["solutionViewAllowed"] is True

    def test_write_to_file(self, tmp_path):
        cfg = ConfigurationBuilder().set_algorithm(GeneticAlgorithm())
        cfg.write_to_file(tmp_path)
        path = tmp_path / "model-configuration.json"
        assert path.exists()
        loaded = json.loads(path.read_text())
        assert loaded["algorithmConfiguration"]["algorithmKey"] == "daitum-gga-single-objective"

    def test_idempotent_build(self):
        cfg = (
            ConfigurationBuilder()
            .set_algorithm(GeneticAlgorithm())
            .set_model_configuration(ModelConfiguration())
        )
        assert cfg.build() == cfg.build()


# ----------------------------------------------------------------------------------------
# Fluent-builder chains
# ----------------------------------------------------------------------------------------


class TestFluentChains:
    def test_configuration_setters_chain(self):
        cfg = ConfigurationBuilder()
        ret = cfg.set_solution_view_allowed(True).set_solution_view_enabled(True)
        assert ret is cfg

    def test_data_source_setters_chain(self):
        m = ModelBuilder()
        p = m.add_parameter("STATUS", DataType.STRING, "Active")
        cfg = (
            DataStoreConfig("k", {"T": "t"})
            .set_debug_file(True)
            .set_using_interface(True)
            .set_direct_data_pull(True)
            .set_model_filter(EqualityDataFilter(["s"], p))
        )
        out = cfg.build()
        assert out["debugFile"] is True
        assert out["usingInterface"] is True
        assert out["directDataPull"] is True
        assert out["modelFilter"]["@type"] == "equality"

    def test_constraint_chain(self):
        m = ModelBuilder()
        c = _make_calculation(m, "CON_CHAIN")
        from daitum_configuration.model_configuration.constraint import Constraint

        cons = (
            Constraint(c)
            .set_type(ConstraintType.EQUALITY)
            .set_lower_bound(1.0)
            .set_upper_bound(2.0)
            .set_priority(Priority.LOW)
            .set_hard_score(5)
            .set_name("chain")
        )
        out = cons.build()
        assert out["specification"]["@type"] == "equality"
        assert out["specification"]["priority"] == "LOW"
        assert out["specification"]["hardScore"] == 5
        assert out["name"] == "chain"


# ----------------------------------------------------------------------------------------
# Edge cases
# ----------------------------------------------------------------------------------------


class TestEdgeCases:
    def test_none_skipped_in_output(self):
        # Default ModelImportOptions has key_column=None, locale_key=None, sync_key=None.
        out = ModelImportOptions().build()
        assert "keyColumn" not in out
        assert "localeKey" not in out
        assert "syncKey" not in out

    def test_empty_list_emitted(self):
        cfg = ModelConfiguration()
        out = cfg.build()
        assert out["decisionVariables"] == []
        assert out["objectives"] == []
        assert out["constraints"] == []
        assert out["scenarioOutputs"] == []

    def test_enum_extracted_to_value(self):
        # Stochastic config converts MetricCombinationRule enums to .value automatically.
        sc = StochasticConfiguration(1, 0.05, False).add_metric_rule(
            "k", MetricCombinationRule.PVALUE_MIN
        )
        assert sc.build()["metricRules"]["k"] == "PVALUE_MIN"

    def test_nested_buildable_recurses(self):
        m = ModelBuilder()
        cost = _make_calculation(m, "REC_COST")
        cfg = ModelConfiguration()
        cfg.add_objective(cost, name="x")
        config = ConfigurationBuilder().set_model_configuration(cfg)
        out = config.build()
        # ModelConfiguration is nested inside ConfigurationBuilder; recursion produces a dict.
        assert isinstance(out["modelConfiguration"], dict)
        assert isinstance(out["modelConfiguration"]["objectives"][0], dict)


# ----------------------------------------------------------------------------------------
# ModelTransform helper class (separate from typed inputs in ModelTransformConfig)
# ----------------------------------------------------------------------------------------


class TestModelTransformBuilder:
    def test_build_serialises(self):
        m = ModelBuilder()
        m.add_data_table("Jobs")
        mt = ModelTransform(m)
        out = mt.build()
        assert "modelDefinition" in out
        assert "parameterOutputs" in out
        assert "tableOutputs" in out


# ----------------------------------------------------------------------------------------
# Backward compat — InputDataMapping/OutputDataMapping smoke
# ----------------------------------------------------------------------------------------


class TestExternalMappings:
    def test_input_mapping_with_columns(self):
        m = ModelBuilder()
        table = m.add_data_table("Jobs")
        col = table.add_data_field("Name", DataType.STRING)
        mapping = InputDataMapping("entity", table)
        mapping.add_column_mapping("propA", col)
        out = mapping.build()
        assert out["entityName"] == "entity"
        assert out["tableName"] == "Jobs"
        assert out["columnMappings"] == [{"propertyName": "propA", "columnName": "Name"}]

    def test_output_mapping_extends_input(self):
        m = ModelBuilder()
        table = m.add_data_table("Jobs")
        mapping = OutputDataMapping(
            "entity", table, key_column="id", preserve_order=True, clear_existing=False
        )
        out = mapping.build()
        assert out["entityName"] == "entity"
        assert out["mapByProperty"] == "id"
        assert out["preserveOrder"] is True
        assert out["clearExisting"] is False


class TestTrackChangesSnapshots:
    def test_track_changes_capture_default(self):
        from daitum_configuration import TrackChangesConfig

        cfg = TrackChangesConfig("optimised")
        out = cfg.build()
        assert out["type"] == "TRACK_CHANGES"
        assert out["baseline"] == "optimised"
        assert out["mode"] == "CAPTURE"
        assert "trackingGroups" not in out

    def test_track_changes_revert_with_groups(self):
        from daitum_configuration import TrackChangesConfig, TrackChangesMode

        cfg = TrackChangesConfig(
            "optimised", mode=TrackChangesMode.REVERT, tracking_groups=["edits"]
        )
        out = cfg.build()
        assert out["mode"] == "REVERT"
        assert out["trackingGroups"] == ["edits"]

    def test_track_changes_via_configuration(self):
        from daitum_configuration import TrackChangesConfig

        cfg = ConfigurationBuilder()
        ds = cfg.add_track_changes("Snapshot", TrackChangesConfig("optimised"))
        out = ds.build()
        assert out["config"]["type"] == "TRACK_CHANGES"
        assert out["config"]["baseline"] == "optimised"
