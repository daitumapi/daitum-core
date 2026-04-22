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
This module defines the ReportExportFormat enumeration, which represents
the supported file formats for report exports.

Each export format is associated with its corresponding file extension.
"""

from enum import Enum


class ReportExportFormat(Enum):
    """
    Enumeration of supported report export formats.

    Each member represents a specific file format that can be used to export
    reports, along with its corresponding file extension.
    """

    XLSX = "XLSX"
    CSV = "CSV"
    JSON = "JSON"
    MSDOS = "MSDOS"
