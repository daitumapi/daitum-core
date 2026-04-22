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
This module defines the DataSource class used to encapsulate information and
configuration related to a data source for optimisation.
It includes tracking fields for metadata like visibility, post-processing,
data update notifications, and a temporary export ID for internal use.

Classes:
    DataSource: Represents a configured data source with serialisation support.
"""

from typeguard import typechecked

from daitum_configuration.data_source.data_source_config import DataSourceConfig


# pylint: disable=too-few-public-methods
@typechecked
class DataSource:
    """
    Represents a data source configuration with relevant metadata and control flags.
    """

    # Class-level static variable for tracking ID
    _temp_export_id = 0

    def __init__(
        self,
        name: str,
        config: DataSourceConfig,
    ):
        """
        Initialises a new instance of DataSource.

        Args:
            name (str): Name of the data source.
            config (DataSourceConfig): Configuration object.
        """
        self._temp_export_id = DataSource._temp_export_id
        DataSource._temp_export_id += 1
        self._name = name
        self._config = config
        self._hidden: bool = False
        self._post_optimise: bool = False
        self._notify_on_new_data: bool = False
        self._update_new_data: bool = False

    def set_hidden(self, hidden: bool) -> "DataSource":
        """
        Sets whether the data source is hidden.

        Args:
            hidden (bool): If True, the data source will be marked as hidden.

        Returns:
            DataSource: self, for method chaining.
        """
        self._hidden = hidden
        return self

    def set_post_optimise(self, post_optimise: bool) -> "DataSource":
        """
        Sets whether post-optimisation is triggered after data import.

        Args:
            post_optimise (bool): If True, triggers post-optimisation after data import.

        Returns:
            DataSource: self, for method chaining.
        """
        self._post_optimise = post_optimise
        return self

    def set_notify_on_new_data(self, notify_on_new_data: bool) -> "DataSource":
        """
        Sets whether notifications are sent when new data is detected.

        Args:
            notify_on_new_data (bool): If True, notifications will be sent when new data
                is detected.

        Returns:
            DataSource: self, for method chaining.
        """
        self._notify_on_new_data = notify_on_new_data
        return self

    def set_update_new_data(self, update_new_data: bool) -> "DataSource":
        """
        Sets whether updates are triggered when new data is available.

        Args:
            update_new_data (bool): If True, updates will be triggered when new data
                is available.

        Returns:
            DataSource: self, for method chaining.
        """
        self._update_new_data = update_new_data
        return self

    def to_dict(self) -> dict:
        """
        Serialises the instance into a dictionary representation for data source.

        Returns:
            dict: A dictionary formatted for use in data source.
        """
        return {
            "name": self._name,
            "config": self._config.to_dict(),
            "hidden": self._hidden,
            "tempExportId": self._temp_export_id,
            "postOptimise": self._post_optimise,
            "notifyOnNewData": self._notify_on_new_data,
            "updateNewData": self._update_new_data,
        }
