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

""":class:`DataInputSourceType` discriminator enum for :class:`ModelTransformInput`."""

from enum import Enum


class DataInputSourceType(Enum):
    """Identifies the source of one input to a :class:`ModelTransformConfig`.

    Values:
        DATA_STORE: Rows pulled directly from a data store.
        DATA_STORE_INTERFACE: Rows pulled via a data-store interface.
        DYNAMIC_VALUES: Computed values such as the current time.
        DIRECT_UPLOAD: Rows from a CSV or zipped CSV upload.
    """

    DATA_STORE = "DATA_STORE"
    DATA_STORE_INTERFACE = "DATA_STORE_INTERFACE"
    DYNAMIC_VALUES = "DYNAMIC_VALUES"
    DIRECT_UPLOAD = "DIRECT_UPLOAD"
