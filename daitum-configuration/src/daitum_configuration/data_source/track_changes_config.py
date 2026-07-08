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

""":class:`TrackChangesConfig` — capture/revert a baseline as a data source."""

from enum import Enum

from daitum_model import Baseline, TrackingGroup
from daitum_model.tracking import normalise_tracking_groups
from typeguard import typechecked

from daitum_configuration.data_source.data_source_config import DataSourceConfig
from daitum_configuration.data_source.data_source_type import DataSourceType


class TrackChangesMode(Enum):
    """Whether a :class:`TrackChangesConfig` captures or reverts its baseline."""

    CAPTURE = "CAPTURE"
    REVERT = "REVERT"


@typechecked
class TrackChangesConfig(DataSourceConfig):
    """
    Captures or reverts a baseline when the data source runs.

    Usable as a step in a batched data source or as a ``post_optimise`` data source.

    Args:
        baseline: The baseline to capture or revert, or its name.
        mode: Whether to capture (the default) or revert the baseline.
        tracking_groups: Restrict to a subset of the baseline's tracking groups (objects
            or names). Omit (or leave empty) to act on all of them.
    """

    def __init__(
        self,
        baseline: Baseline | str,
        mode: TrackChangesMode = TrackChangesMode.CAPTURE,
        tracking_groups: list[str | TrackingGroup] | None = None,
    ):
        self.baseline = baseline.name if isinstance(baseline, Baseline) else baseline
        self.mode = mode
        self.tracking_groups = (
            normalise_tracking_groups(tracking_groups) if tracking_groups else None
        )
        super().__init__()

    @property
    def type(self) -> DataSourceType:
        return DataSourceType.TRACK_CHANGES
