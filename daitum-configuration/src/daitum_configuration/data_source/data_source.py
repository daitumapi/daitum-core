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
:class:`DataSource` — wraps a :class:`DataSourceConfig` with metadata (display name,
visibility, behaviour flags).
"""

from typeguard import typechecked

from daitum_configuration._buildable import Buildable
from daitum_configuration.data_source.data_source_config import DataSourceConfig


# pylint: disable=too-few-public-methods
@typechecked
class DataSource(Buildable):
    """
    Wraps a :class:`DataSourceConfig` with display metadata and behaviour flags.

    ``ConfigurationBuilder.add_*`` methods construct this wrapper for you and
    return it so you can chain ``set_*`` methods to customise behaviour.
    """

    # Class-level static counter for assigning ``temp_export_id``.
    _temp_export_id_counter = 0

    def __init__(
        self,
        name: str,
        config: DataSourceConfig,
    ):
        self.name = name
        self.config = config
        self.hidden: bool = False
        self.temp_export_id = DataSource._temp_export_id_counter
        DataSource._temp_export_id_counter += 1
        self.post_optimise: bool = False
        self.notify_on_new_data: bool = False
        self.update_new_data: bool = False

    def set_hidden(self, hidden: bool) -> "DataSource":
        """Hide this data source from the UI's data menu."""
        self.hidden = hidden
        return self

    def set_post_optimise(self, post_optimise: bool) -> "DataSource":
        """The data source will run automatically after optimisation has completed."""
        self.post_optimise = post_optimise
        return self

    def set_notify_on_new_data(self, notify_on_new_data: bool) -> "DataSource":
        """Send a UI notification when new data arrives."""
        self.notify_on_new_data = notify_on_new_data
        return self

    def set_update_new_data(self, update_new_data: bool) -> "DataSource":
        """Auto-apply incoming updates without operator confirmation."""
        self.update_new_data = update_new_data
        return self
