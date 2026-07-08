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
Decoder registrations for the configuration package.

Call :func:`register_all` to register every configuration decoder in the shared
``DECODER_REGISTRY``. ``daitum_configuration.__init__`` calls it once on import.
"""

from daitum_configuration._decoders import (
    algorithm,
    configuration,
    data_filter,
    data_source,
    external,
    model_configuration,
    model_transform,
    properties,
    schedule,
    stochastic,
)

_done: set[str] = set()


def register_all() -> None:
    """Register every configuration decoder. Idempotent — safe to call more than once."""
    if _done:
        return
    algorithm.register()
    external.register()
    stochastic.register()
    model_configuration.register()
    data_filter.register()
    model_transform.register()
    data_source.register()
    schedule.register()
    properties.register()
    configuration.register()
    _done.add("registered")


__all__ = [
    "algorithm",
    "configuration",
    "data_filter",
    "data_source",
    "external",
    "model_configuration",
    "model_transform",
    "properties",
    "register_all",
    "schedule",
    "stochastic",
]
