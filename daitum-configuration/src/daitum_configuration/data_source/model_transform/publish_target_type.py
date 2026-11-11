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

""":class:`PublishTargetType` — how a :class:`PublishConfig` names its data store."""

from enum import Enum


class PublishTargetType(Enum):
    """Identifies how a publish entry's ``data_store_key`` names its target store.

    DATA_STORE
        ``data_store_key`` is a data store path (organisation specific).
    DATA_STORE_INTERFACE
        ``data_store_key`` is an interface mapping key, resolved through the publishing
        user's organisation, so one config works for every organisation.
    """

    DATA_STORE = "DATA_STORE"
    DATA_STORE_INTERFACE = "DATA_STORE_INTERFACE"
