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
This module defines the RunReportConfig class.

Classes:
    RunReportConfig: Represents configuration for running a report as a data source.
"""

from typeguard import typechecked

from daitum_configuration.data_source.data_source_config import DataSourceConfig
from daitum_configuration.data_source.data_source_type import DataSourceType


@typechecked
class RunReportConfig(DataSourceConfig):
    """
    Configuration class for running reports as a data source.
    """

    def __init__(
        self,
        report_name: str,
    ):
        self._report_name = report_name
        super().__init__()

    @property
    def type(self) -> DataSourceType:
        """
        Returns the type identifier for this data source configuration.
        """
        return DataSourceType.RUN_REPORT

    def to_dict(self) -> dict:
        """
        Serializes the instance into a dictionary representation for RunReportConfig.

        Returns:
            dict: A dictionary representation of the RunReportConfig instance.
        """
        return {"type": self.type.value, "reportName": self._report_name}
