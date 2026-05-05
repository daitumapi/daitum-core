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
Top-level :class:`ConfigurationBuilder` for assembling a Daitum model configuration.

A configuration ties an :class:`~daitum_configuration.algorithm_configuration.algorithm.Algorithm`
and a :class:`~daitum_configuration.ModelConfiguration` to the data sources, schedule, and
model/report properties that surround them. :meth:`ConfigurationBuilder.write_to_file`
serialises the result into ``model-configuration.json``.
"""

import json
import os
import pathlib
from typing import Any

from typeguard import typechecked

from daitum_configuration._buildable import Buildable
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


# pylint: disable=too-few-public-methods
# pylint: disable=too-many-instance-attributes
# pylint: disable=too-many-arguments,too-many-positional-arguments
@typechecked
class ConfigurationBuilder(Buildable):
    """
    Builder for a complete model configuration.

    Use ``set_*`` methods to attach the algorithm, model configuration, schedule,
    and model property; use ``add_*`` methods to register data sources and
    report properties; call :meth:`write_to_file` to emit
    ``model-configuration.json``.
    """

    def __init__(self):
        self.algorithm_configuration: Algorithm | None = None
        self.model_configuration: ModelConfiguration | None = None
        self.data_sources: list[DataSource] = []
        self.schedule_configuration: ScheduleConfiguration | None = None
        self.solution_view_allowed: bool = False
        self.solution_view_enabled: bool = False
        self.report_properties: dict[str, ReportProperty] | None = None
        self.model_properties: ModelProperty | None = None
        self.model_topic_mapping: list[Any] = []
        self.tooltips: list[Any] = []

    def set_algorithm(self, algorithm: Algorithm) -> "ConfigurationBuilder":
        """Set the top-level algorithm. Mutually exclusive with a schedule."""
        self.algorithm_configuration = algorithm
        return self

    def set_model_configuration(
        self, model_configuration: ModelConfiguration
    ) -> "ConfigurationBuilder":
        """Set the :class:`~daitum_configuration.ModelConfiguration` (decision variables,
        objectives, constraints)."""
        self.model_configuration = model_configuration
        return self

    def set_schedule_configuration(
        self, schedule_configuration: ScheduleConfiguration
    ) -> "ConfigurationBuilder":
        """Set a multi-step schedule. Mutually exclusive with a single algorithm."""
        self.schedule_configuration = schedule_configuration
        return self

    def set_solution_view_allowed(self, solution_view_allowed: bool) -> "ConfigurationBuilder":
        """Set whether the solution-view feature is permitted for this model."""
        self.solution_view_allowed = solution_view_allowed
        return self

    def set_solution_view_enabled(self, solution_view_enabled: bool) -> "ConfigurationBuilder":
        """Set whether the solution view is enabled by default when allowed."""
        self.solution_view_enabled = solution_view_enabled
        return self

    def set_model_topic_mapping(self, model_topic_mapping: list[Any]) -> "ConfigurationBuilder":
        """Set the model-topic mapping list emitted alongside the configuration."""
        self.model_topic_mapping = model_topic_mapping
        return self

    def set_tooltips(self, tooltips: list[Any]) -> "ConfigurationBuilder":
        """Set the tooltip definitions emitted alongside the configuration."""
        self.tooltips = tooltips
        return self

    def add_report_property(
        self, key: str, report_property: ReportProperty
    ) -> "ConfigurationBuilder":
        """Register a :class:`~daitum_configuration.report_property.report_property.ReportProperty`
        under the given key."""
        if self.report_properties is None:
            self.report_properties = {}
        self.report_properties[key] = report_property
        return self

    def set_model_property(
        self,
        calculate_on_load: bool = True,
        calculation_enabled: bool = True,
        ignore_formula: bool = False,
        import_options: ModelImportOptions | None = None,
        overlay_config: OverlayConfig | None = None,
    ) -> "ConfigurationBuilder":
        """Construct and attach a
        :class:`~daitum_configuration.model_property.model_property.ModelProperty` from
        the given flags and configurations."""
        self.model_properties = ModelProperty(
            calculate_on_load,
            calculation_enabled,
            ignore_formula,
            import_options,
            overlay_config,
        )
        return self

    def add_excel_transform(self, name: str, config: ExcelTransformConfig) -> DataSource:
        """Register an Excel-transform data source and return its
        :class:`~daitum_configuration.data_source.data_source.DataSource` wrapper for
        further customisation (e.g. ``set_post_optimise``)."""
        return self._add_data_source(DataSource(name, config))

    def add_model_transform(self, name: str, config: ModelTransformConfig) -> DataSource:
        """Register a model-transform data source. See :meth:`add_excel_transform` for the
        return value."""
        return self._add_data_source(DataSource(name, config))

    def add_data_store(self, name: str, config: DataStoreConfig) -> DataSource:
        """Register a data-store data source. See :meth:`add_excel_transform` for the
        return value."""
        return self._add_data_source(DataSource(name, config))

    def add_batched_data_source(self, name: str, config: BatchedDataSourceConfig) -> DataSource:
        """Register a batched data source bundling other data sources. See
        :meth:`add_excel_transform` for the return value."""
        return self._add_data_source(DataSource(name, config))

    def add_report_data_source(self, name: str, report_name: str) -> DataSource:
        """Register a data source that feeds rows from a previously-run report. See
        :meth:`add_excel_transform` for the return value."""
        return self._add_data_source(DataSource(name, RunReportConfig(report_name)))

    def add_distance_matrix(self, name: str, config: DistanceMatrixConfig) -> DataSource:
        """Register a distance-matrix data source. See :meth:`add_excel_transform` for the
        return value."""
        return self._add_data_source(DataSource(name, config))

    def add_set_features(self, name: str, config: SetFeaturesConfig) -> DataSource:
        """Register a feature-flag data source. See :meth:`add_excel_transform` for the
        return value."""
        return self._add_data_source(DataSource(name, config))

    def add_geo_location(self, name: str, config: GeoLocationConfig) -> DataSource:
        """Register a geocoding data source. See :meth:`add_excel_transform` for the
        return value."""
        return self._add_data_source(DataSource(name, config))

    def _add_data_source(self, data_source: DataSource) -> DataSource:
        self.data_sources.append(data_source)
        return data_source

    def write_to_file(self, model_directory: str | os.PathLike[str]) -> None:
        """Serialise this configuration into ``model-configuration.json`` under
        ``model_directory``, creating the directory if it does not exist."""
        path = pathlib.Path(model_directory) / "model-configuration.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", encoding="utf-8") as fp:
            json.dump(self.build(), fp, indent=4, sort_keys=False)
