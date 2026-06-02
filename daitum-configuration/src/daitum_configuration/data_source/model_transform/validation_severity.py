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

""":class:`ValidationSeverity` — how header-validation issues are surfaced at upload time."""

from enum import Enum


class ValidationSeverity(Enum):
    """How a header-validation issue should be surfaced when running a model transform input.

    Used on every :class:`~daitum_configuration.data_source.model_transform.\
model_transform_input.ModelTransformInput` for both the *missing header* and
    *unexpected header* checks.
    """

    #: Treat as a hard error — block the file upload and surface in the validation dialog.
    ERROR = "ERROR"
    #: Surface in the validation dialog but allow the import to proceed.
    WARNING = "WARNING"
    #: Suppress entirely — neither block nor display.
    IGNORE = "IGNORE"
