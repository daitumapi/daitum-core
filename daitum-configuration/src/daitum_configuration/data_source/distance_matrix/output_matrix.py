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
This module defines the OutputMatrix class and the Metric enumeration used to
configure and represent distance or duration matrices in a spreadsheet-based
distance matrix configuration.

Classes:
    - OutputMatrix: Represents a single output definition (e.g., driving distance or time)
      associated with a sheet and named range.

Enums:
    Metric: Enumeration of supported metrics for the distance matrix output.
"""

from enum import Enum

from typeguard import typechecked


class Metric(Enum):
    """
    Enumeration of possible distance matrix metrics.

    Attributes:
        DRIVING_DISTANCE: Represents distance traveled.
        DRIVING_TIME: Represents travel time.
    """

    DRIVING_DISTANCE = "DRIVING_DISTANCE"
    DRIVING_TIME = "DRIVING_TIME"


# pylint: disable=too-few-public-methods
@typechecked
class OutputMatrix:
    """
    Represents a single output matrix configuration.

    Each OutputMatrix instance defines how a particular metric (distance or time)
    will be stored in a spreadsheet, including the sheet name and the named range
    where the output will be placed.
    """

    def __init__(self, sheet_name: str, named_range: str, metric: Metric):
        """
        Initializes an OutputMatrix instance.

        Args:
            sheet_name (str): Target sheet name for the matrix.
            named_range (str): Named range in the sheet to output values.
            metric (Metric): Metric type to output.
        """
        self._sheet_name = sheet_name
        self._named_range = named_range
        self._metric = metric

    def to_dict(self) -> dict:
        """
        Serializes the OutputMatrix instance into a dictionary format.

        This is typically used for exporting configuration to JSON or
        other serializable formats.

        Returns:
            dict: Dictionary representation of the OutputMatrix instance.
        """
        return {
            "sheetName": self._sheet_name,
            "namedRange": self._named_range,
            "metric": self._metric.value,
        }
