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

""":class:`OutputMatrix` and :class:`Metric` for :class:`DistanceMatrixConfig` outputs."""

from enum import Enum

from typeguard import typechecked

from daitum_configuration._buildable import Buildable


class Metric(Enum):
    """Distance-matrix output metric."""

    DRIVING_DISTANCE = "DRIVING_DISTANCE"
    """Driving distance along the route."""

    DRIVING_TIME = "DRIVING_TIME"
    """Driving time along the route."""


# pylint: disable=too-few-public-methods
@typechecked
class OutputMatrix(Buildable):
    """
    Where one metric of a :class:`DistanceMatrixConfig` is written.

    Args:
        sheet_name: Target sheet name for the output matrix.
        named_range: Named range within the sheet receiving the values.
        metric: Which :class:`Metric` this output records.
    """

    def __init__(self, sheet_name: str, named_range: str, metric: Metric):
        self.sheet_name = sheet_name
        self.named_range = named_range
        self.metric = metric
