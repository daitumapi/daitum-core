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
Module for defining and managing configuration components.

This module provides a foundation for building a configuration file for models.
The configuration is serialised and written to a JSON file.

Key Classes:
    - `Configuration`: Represents the overall configuration object, currently including the
       algorithm configuration and designed for future expansion.
    - `Algorithm`: A class that provides common parameters and functionality for
       all optimisation algorithms. This class should be inherited by specific
       algorithm implementations.
    - `ModelConfiguration`: A class that stores the configuration of an optimisation model,
       including its decision variables, objectives, constraints, and other model parameters.
    - `ScheduleConfiguration`: A class which represent the building blocks of algorithm execution
       schedules.
    - `ReportProperty`: A class which encapsulates all metadata and configuration related to
       exporting a report
    - `ModelProperty`: A container for storing arbitrary properties that should be tracked
       at a model level, including calculation flags and configurations.
    - `DataSource`: A class used to encapsulate information and configuration related to a data
       source for optimisation.
"""

import json
import os
from typing import Any

from typeguard import typechecked

from daitum_configuration.algorithm_configuration.algorithm import Algorithm
from daitum_configuration.data_source.batched_data_source.batched_data_source_config import (
    BatchedDataSourceConfig,
)
from daitum_configuration.data_source.data_source import DataSource
from daitum_configuration.data_source.data_store.data_store_config import DataStoreConfig
from daitum_configuration.data_source.distance_matrix.distance_matrix_config import (
    DistanceMatrixConfig,
)
from daitum_configuration.data_source.excel_transform.excel_transform_config import (
    ExcelTransformConfig,
)
from daitum_configuration.data_source.geo_location_config import GeoLocationConfig
from daitum_configuration.data_source.model_transform.model_transform_config import (
    ModelTransformConfig,
)
from daitum_configuration.data_source.run_report.run_report_config import RunReportConfig
from daitum_configuration.data_source.set_features_config import SetFeaturesConfig
from daitum_configuration.model_configuration.model_configuration import ModelConfiguration
from daitum_configuration.model_property.model_import_options import ModelImportOptions
from daitum_configuration.model_property.model_property import ModelProperty
from daitum_configuration.model_property.overlay_config import OverlayConfig
from daitum_configuration.report_property.report_property import ReportProperty
from daitum_configuration.schedule_configuration.schedule_configuration import (
    ScheduleConfiguration,
)
from daitum_configuration.schedule_configuration.step_configuration import StepConfiguration


# pylint: disable=too-few-public-methods
# pylint: disable=too-many-instance-attributes
@typechecked
class Configuration:
    """
    Represents the overall configuration for a model setup.

    Currently, supports only the algorithm configuration and model configuration.
    """

    def __init__(self):
        """
        Initialises the Configuration object.
        """
        self._algorithm = None
        self._model_configuration = None
        self._data_sources: list[DataSource] = []
        self._schedule_configuration = None
        self._solution_view_allowed = False
        self._solution_view_enabled = False
        self._report_properties: dict[str, dict[str, Any]] | None = None
        self._model_property: dict[str, Any] | None = None
        self._model_topic_mapping: list = []
        self._tooltips: list = []

    def set_algorithm(self, algorithm: Algorithm) -> None:
        """
        Sets the algorithm configuration to include.

        Args:
            algorithm (Algorithm): The algorithm configuration to include.
        """
        self._algorithm = algorithm

    def set_model_configuration(self, model_configuration: ModelConfiguration) -> None:
        """
        Sets the model configuration to include.

        Args:
            model_configuration (ModelConfiguration): The model configuration to include.
        """
        self._model_configuration = model_configuration

    def set_schedule_configuration(
        self,
        algorithm_configurations: dict[str, Algorithm] | None = None,
        schedule_root: StepConfiguration | None = None,
    ) -> None:
        """
        Sets the schedule configuration to include.

        Args:
            algorithm_configurations: Optional dictionary of algorithm configurations.
                Keys are algorithm keys and values are Algorithm instances.
                Defaults to an empty dictionary.
            schedule_root: Optional root step configuration that defines the
                execution schedule hierarchy. Defaults to None.
        """
        self._schedule_configuration = ScheduleConfiguration(
            algorithm_configurations, schedule_root
        )

    def add_report_property(self, key: str, report_property: ReportProperty) -> None:
        """
        Adds the report property to the dictionary.

        Args:
            key (str): The key for the report property.
            report_property (ReportProperty): The pre-built report property to add.
        """
        if self._report_properties is None:
            self._report_properties = {}
        self._report_properties[key] = report_property.to_dict()

    def set_model_property(
        self,
        calculate_on_load: bool = False,
        calculation_enabled: bool = True,
        ignore_formula: bool = False,
        import_options: ModelImportOptions | None = None,
        overlay_config: OverlayConfig | None = None,
    ):
        """
        Data model representing model-level properties and configurations.

        Args:
            calculate_on_load (bool): Whether to calculate on load. Default False.
            calculation_enabled (bool): Whether calculation is enabled. Default True.
            ignore_formula (bool): Whether to ignore formulas. Default False.
            import_options (Optional[ModelImportOptions]): Import configuration options.
            overlay_config (Optional[OverlayConfig]): Spreadsheet overlay configuration.
        """
        model_property = ModelProperty(
            calculate_on_load, calculation_enabled, ignore_formula, import_options, overlay_config
        )
        self._model_property = model_property.to_dict()

    def add_excel_transform(
        self,
        name: str,
        config: ExcelTransformConfig,
    ) -> DataSource:
        """
        Adds a new Excel-based data source to the configuration.

        Args:
            name (str): Display name of the data source.
            config (ExcelTransformConfig): Configuration object specifying how to import
                and transform the Excel file.

        Returns:
            DataSource: The created data source instance, for further configuration via
                chained setter calls (e.g. ``set_hidden``, ``set_post_optimise``).
        """
        data_source = DataSource(name, config)
        self._data_sources.append(data_source)
        return data_source

    def add_model_transform(
        self,
        name: str,
        config: ModelTransformConfig,
    ) -> DataSource:
        """
        Adds a new ModelTransformConfig data source to the configuration.

        Args:
            name (str): Display name of the data source.
            config (ModelTransformConfig): Configuration class for model transforms,
                transformation of model data using the v3 modelling language and data
                store integration.

        Returns:
            DataSource: The created data source instance, for further configuration via
                chained setter calls (e.g. ``set_hidden``, ``set_post_optimise``).
        """
        data_source = DataSource(name, config)
        self._data_sources.append(data_source)
        return data_source

    def add_data_store(
        self,
        name: str,
        config: DataStoreConfig,
    ) -> DataSource:
        """
        Adds a new DataStoreConfig data source to the configuration.

        Args:
            name (str): Display name of the data source.
            config (DataStoreConfig): Configuration class for data stores, enabling structured
                serialisation and supporting optional filtering and debug options.

        Returns:
            DataSource: The created data source instance, for further configuration via
                chained setter calls (e.g. ``set_hidden``, ``set_post_optimise``).
        """
        data_source = DataSource(name, config)
        self._data_sources.append(data_source)
        return data_source

    def add_batched_data_source(
        self,
        name: str,
        config: BatchedDataSourceConfig,
    ) -> DataSource:
        """
        Adds a new BatchedDataSourceConfig data source to the configuration.

        Args:
            name (str): Display name of the data source.
            config (BatchedDataSourceConfig): Represents a configuration for a batched data
                source composed of multiple individual data sources.

        Returns:
            DataSource: The created data source instance, for further configuration via
                chained setter calls (e.g. ``set_hidden``, ``set_post_optimise``).
        """
        data_source = DataSource(name, config)
        self._data_sources.append(data_source)
        return data_source

    def add_report_data_source(
        self,
        name: str,
        report_name: str,
    ) -> DataSource:
        """
        Adds a new RunReport data source to the configuration.

        Args:
            name (str): Display name of the data source.
            report_name (str): The name of the report to be run.

        Returns:
            DataSource: The created data source instance, for further configuration via
                chained setter calls (e.g. ``set_hidden``, ``set_post_optimise``).
        """
        data_source = DataSource(name, RunReportConfig(report_name))
        self._data_sources.append(data_source)
        return data_source

    def add_distance_matrix(
        self,
        name: str,
        config: DistanceMatrixConfig,
    ) -> DataSource:
        """
        Adds a new DistanceMatrixConfig data source to the configuration.

        Args:
            name (str): Display name of the data source.
            config (DistanceMatrixConfig): Represents a configuration model for a distance
                matrix data source.

        Returns:
            DataSource: The created data source instance, for further configuration via
                chained setter calls (e.g. ``set_hidden``, ``set_post_optimise``).
        """
        data_source = DataSource(name, config)
        self._data_sources.append(data_source)
        return data_source

    def add_set_features(
        self,
        name: str,
        config: SetFeaturesConfig,
    ) -> DataSource:
        """
        Adds a new SetFeaturesConfig data source to the configuration.

        Args:
            name (str): Display name of the data source.
            config (SetFeaturesConfig): A configuration class that holds boolean feature flags
                for enabling or disabling specific functionalities.

        Returns:
            DataSource: The created data source instance, for further configuration via
                chained setter calls (e.g. ``set_hidden``, ``set_post_optimise``).
        """
        data_source = DataSource(name, config)
        self._data_sources.append(data_source)
        return data_source

    def add_geo_location(
        self,
        name: str,
        config: GeoLocationConfig,
    ) -> DataSource:
        """
        Adds a new GeoLocationConfig data source to the configuration.

        Args:
            name (str): Display name of the data source.
            config (GeoLocationConfig): A configuration class that represents a geolocation
                configuration for address-to-coordinate transformation.

        Returns:
            DataSource: The created data source instance, for further configuration via
                chained setter calls (e.g. ``set_hidden``, ``set_post_optimise``).
        """
        data_source = DataSource(name, config)
        self._data_sources.append(data_source)
        return data_source

    def to_dict(self) -> dict[str, Any]:
        """
        Converts the `Configuration` object to a dictionary representation for JSON serialisation.

        Returns:
            dict[str, Any]: A dictionary representation of the configuration.
        """
        return {
            "algorithmConfiguration": self._algorithm.to_dict() if self._algorithm else None,
            "modelConfiguration": (
                self._model_configuration.to_dict() if self._model_configuration else None
            ),
            "dataSources": [ds.to_dict() for ds in self._data_sources],
            "scheduleConfiguration": (
                self._schedule_configuration.to_dict() if self._schedule_configuration else None
            ),
            "solutionViewAllowed": self._solution_view_allowed,
            "solutionViewEnabled": self._solution_view_enabled,
            "reportProperties": self._report_properties,
            "modelProperties": self._model_property,
            "modelTopicMapping": self._model_topic_mapping,
            "tooltips": self._tooltips,
        }

    def write_to_file(self, file_name: str):
        """
        Serialises the configuration and writes it to a JSON file.

        Args:
            file_name (str): The path to the file where the model will be saved.
        """
        directory = os.path.dirname(file_name)
        if directory and not os.path.exists(directory):
            os.makedirs(directory)
        with open(file_name, "w", encoding="utf-8") as fp:
            json.dump(self.to_dict(), fp, indent=4, sort_keys=False)
