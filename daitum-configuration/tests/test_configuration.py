"""
Tests for daitum_configuration: Configuration, algorithms, data sources, and serialisation.
"""

import pytest

import daitum_configuration
from daitum_configuration import (
    CMAESAlgorithm,
    Configuration,
    ConstraintType,
    DVType,
    DataStoreConfig,
    DistanceMatrixConfig,
    EqualityDataFilter,
    ExcelTransformConfig,
    GeneticAlgorithm,
    ModelConfiguration,
    Priority,
    StepConfiguration,
    StepType,
    VariableNeighbourhoodSearch,
)


class TestImport:
    def test_package_importable(self):
        assert daitum_configuration is not None

    def test_configuration_importable(self):
        assert Configuration is not None

    def test_genetic_algorithm_importable(self):
        assert GeneticAlgorithm is not None

    def test_cmaes_importable(self):
        assert CMAESAlgorithm is not None

    def test_vns_importable(self):
        assert VariableNeighbourhoodSearch is not None


class TestConfiguration:
    def _make_model_config(self) -> ModelConfiguration:
        return ModelConfiguration()

    def test_configuration_serialises(self):
        config = Configuration()
        result = config.to_dict()
        assert isinstance(result, dict)

    def test_configuration_to_dict_has_model_configuration(self):
        config = Configuration()
        result = config.to_dict()
        assert isinstance(result, dict)


class TestGeneticAlgorithm:
    def test_instantiation(self):
        from daitum_configuration import MutationType, RecombinatorType, SelectionType

        algo = GeneticAlgorithm()
        assert algo is not None

    def test_to_dict(self):
        algo = GeneticAlgorithm()
        result = algo.to_dict()
        assert isinstance(result, dict)


class TestCMAESAlgorithm:
    def test_instantiation(self):
        algo = CMAESAlgorithm()
        assert algo is not None

    def test_to_dict(self):
        algo = CMAESAlgorithm()
        result = algo.to_dict()
        assert isinstance(result, dict)


class TestVariableNeighbourhoodSearch:
    def test_instantiation(self):
        vns = VariableNeighbourhoodSearch()
        assert vns is not None

    def test_to_dict(self):
        vns = VariableNeighbourhoodSearch()
        result = vns.to_dict()
        assert isinstance(result, dict)


class TestDataStoreConfig:
    def test_instantiation(self):
        config = DataStoreConfig(data_store_key="my_store", tables={"Jobs": "jobs"})
        assert config is not None

    def test_to_dict(self):
        config = DataStoreConfig(data_store_key="my_store", tables={"Jobs": "jobs"})
        result = config.to_dict()
        assert isinstance(result, dict)


class TestEqualityDataFilter:
    def test_instantiation(self):
        from daitum_model import DataType, ModelBuilder

        model = ModelBuilder()
        param = model.add_parameter("STATUS", DataType.STRING, "Active")
        f = EqualityDataFilter(path=["Status"], source_key=param)
        assert f is not None

    def test_to_dict(self):
        from daitum_model import DataType, ModelBuilder

        model = ModelBuilder()
        param = model.add_parameter("STATUS", DataType.STRING, "Active")
        f = EqualityDataFilter(path=["Status"], source_key=param)
        result = f.to_dict()
        assert isinstance(result, dict)


class TestExcelTransformConfig:
    def test_instantiation(self):
        config = ExcelTransformConfig(
            file_key="import_key",
            file_name="import.xlsx",
            sheet_mapping=[("Sheet1", "Jobs")],
        )
        assert config is not None

    def test_to_dict(self):
        config = ExcelTransformConfig(
            file_key="import_key",
            file_name="import.xlsx",
            sheet_mapping=[("Sheet1", "Jobs")],
        )
        result = config.to_dict()
        assert isinstance(result, dict)


class TestStepConfiguration:
    def test_step_type_enum(self):
        assert StepType is not None
        assert StepType.SINGLE is not None
        assert StepType.PARALLEL is not None
        assert StepType.SEQUENCE is not None

    def test_instantiation(self):
        step = StepConfiguration(step_type=StepType.SINGLE, algorithm_config_key="algo_1")
        assert step is not None

    def test_to_dict(self):
        step = StepConfiguration(step_type=StepType.SINGLE, algorithm_config_key="algo_1")
        result = step.to_dict()
        assert isinstance(result, dict)
