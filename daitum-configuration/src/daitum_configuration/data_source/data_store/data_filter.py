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
Abstract :class:`DataFilter` base class for row-level :class:`DataStoreConfig` filters.

Concrete subclasses declare their ``@type`` discriminator via the
``@json_type_info`` decorator, and implement :attr:`type`.
"""

from abc import ABC, abstractmethod

from typeguard import typechecked

from daitum_configuration._buildable import Buildable
from daitum_configuration.data_source.data_store.data_filter_type import DataFilterType


@typechecked
class DataFilter(Buildable, ABC):
    """Abstract base for typed data-store row filters."""

    @property
    @abstractmethod
    def type(self) -> DataFilterType:
        """The :class:`DataFilterType` discriminator for this filter."""
