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
Builder library for the Daitum platform's model-configuration JSON.

A :class:`ConfigurationBuilder` composes an algorithm, a model configuration
(decision variables, objectives, constraints), data sources, schedule, and
report/model properties; :meth:`ConfigurationBuilder.write_to_file` emits
``model-configuration.json``.
"""

from .algorithm_configuration.cmaes_algorithm import CMAESAlgorithm
from .algorithm_configuration.genetic_algorithm import (
    ComparatorType,
    DistanceMetricType,
    GeneticAlgorithm,
    Mutation,
    MutationType,
    RecombinatorType,
    SamplingMethodType,
    Selection,
    SelectionType,
)
from .algorithm_configuration.numeric_expression import NumericExpression
from .algorithm_configuration.vns_algorithm import VariableNeighbourhoodSearch
from .configuration import ConfigurationBuilder
from .data_source.batched_data_source.batch_data_source_type import BatchDataSourceType
from .data_source.batched_data_source.batched_data_source_config import BatchedDataSourceConfig
from .data_source.batched_data_source.data_source_info import DataSourceInfo
from .data_source.data_store.data_store_config import DataStoreConfig
from .data_source.data_store.equality_data_filter import EqualityDataFilter
from .data_source.data_store.inequality_data_filter import InequalityDataFilter
from .data_source.data_store.regex_data_filter import RegexDataFilter
from .data_source.data_store.set_data_filter import SetDataFilter
from .data_source.data_store.wildcard_data_filter import WildcardDataFilter
from .data_source.distance_matrix.distance_matrix_config import DistanceMatrixConfig
from .data_source.distance_matrix.output_matrix import Metric, OutputMatrix
from .data_source.excel_transform.excel_transform_config import ExcelTransformConfig
from .data_source.excel_transform.import_option_overrides import ImportOptionOverrides
from .data_source.geo_location_config import GeoLocationConfig
from .data_source.model_transform.model_transform import ModelTransform
from .data_source.model_transform.model_transform_config import ModelTransformConfig
from .data_source.set_features_config import SetFeaturesConfig
from .model_configuration.constraint import ConstraintType
from .model_configuration.decision_variable import DVType
from .model_configuration.external_configuration import (
    ExternalModelConfiguration,
    InputDataMapping,
    OutputDataMapping,
    ParameterMapping,
)
from .model_configuration.model_configuration import ModelConfiguration
from .model_configuration.priority import Priority
from .model_configuration.stochastic_configuration import (
    MetricCombinationRule,
    StochasticConfiguration,
)
from .model_property.model_import_options import ModelImportOptions
from .model_property.overlay_config import OverlayConfig
from .report_property.report_data import ReportData
from .report_property.report_export_format import ReportExportFormat
from .schedule_configuration.step_configuration import StepConfiguration
from .schedule_configuration.step_type import StepType

__all__ = [
    "ConfigurationBuilder",
    "GeneticAlgorithm",
    "RecombinatorType",
    "ComparatorType",
    "MutationType",
    "SelectionType",
    "DistanceMetricType",
    "SamplingMethodType",
    "Mutation",
    "Selection",
    "CMAESAlgorithm",
    "NumericExpression",
    "ConstraintType",
    "DVType",
    "Priority",
    "MetricCombinationRule",
    "StochasticConfiguration",
    "ModelConfiguration",
    "ModelImportOptions",
    "OverlayConfig",
    "ReportExportFormat",
    "ReportData",
    "StepType",
    "StepConfiguration",
    "ExcelTransformConfig",
    "ImportOptionOverrides",
    "ModelTransform",
    "ModelTransformConfig",
    "DataStoreConfig",
    "EqualityDataFilter",
    "InequalityDataFilter",
    "RegexDataFilter",
    "SetDataFilter",
    "WildcardDataFilter",
    "BatchedDataSourceConfig",
    "DataSourceInfo",
    "BatchDataSourceType",
    "DistanceMatrixConfig",
    "OutputMatrix",
    "Metric",
    "GeoLocationConfig",
    "SetFeaturesConfig",
    "VariableNeighbourhoodSearch",
    "ExternalModelConfiguration",
    "InputDataMapping",
    "OutputDataMapping",
    "ParameterMapping",
]
