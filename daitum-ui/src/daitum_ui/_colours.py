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

from daitum_model import Severity

VALIDATION_COLOURS = {
    Severity.INFO: "blue",
    Severity.WARNING: "orange",
    Severity.ERROR: "red",
    Severity.CRITICAL: "red",
}

VALIDATION_BACKGROUND_COLOURS = {
    Severity.INFO: "#E2ECFA",
    Severity.WARNING: "#FFEBB7",
    Severity.ERROR: "#FFEAEA",
    Severity.CRITICAL: "#FFEAEA",
}
