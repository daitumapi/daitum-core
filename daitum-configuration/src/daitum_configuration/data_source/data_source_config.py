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
Abstract :class:`DataSourceConfig` base class for typed data-source configurations.

Each concrete subclass corresponds to a :class:`DataSourceType` value and is
serialised with a ``type`` discriminator key.
"""

from abc import ABC, abstractmethod
from typing import Any

from daitum_configuration._buildable import Buildable
from daitum_configuration.data_source.data_source_type import DataSourceType


class DataSourceConfig(Buildable, ABC):
    """
    Abstract base for typed data-source configurations.

    Args:
        track_changes_supported: Whether the data source supports
            change-detection between imports.
    """

    def __init__(self, track_changes_supported: bool = False):
        self.track_changes_supported = track_changes_supported

    @property
    @abstractmethod
    def type(self) -> DataSourceType:
        """The :class:`DataSourceType` discriminator for this configuration."""

    def build(self) -> dict[str, Any]:
        """Serialise to a JSON-compatible dict with a leading ``type`` key."""
        result = {"type": self.type.value}
        result.update(super().build())
        return result
