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
Decoders for the schedule family.

:class:`StepConfiguration` is a recursive tree (its ``steps`` are more steps) and
:class:`ScheduleConfiguration` holds a named map of :class:`Algorithm` instances that decode
through the existing algorithm decoder. Both populate their state through ``add_*``/``set_*``
after construction, so they decode via ``decode_with_state``.
"""

from __future__ import annotations

from typing import Any

from daitum_model.decoding import LoadContext, decode_into, register_decoder, require
from daitum_model.serialisation import camel_to_snake as _camel_to_snake

from daitum_configuration._decoders._state import DictOf, decode_with_state
from daitum_configuration.algorithm_configuration.algorithm import Algorithm
from daitum_configuration.schedule_configuration.schedule_configuration import ScheduleConfiguration
from daitum_configuration.schedule_configuration.step_configuration import (
    StepConfiguration,
    StepType,
)


def decode_step_configuration(data: dict[str, Any], ctx: LoadContext) -> StepConfiguration:
    """Decode a :class:`StepConfiguration` (recursively decoding its child steps).

    The built ``type`` key maps to the ``step_type`` constructor parameter, and the
    constructor validates the ``type``/``algorithm_config_key`` pairing — so the two are
    passed as constructor arguments and the remaining flat fields (plus nested ``steps``) are
    restored afterwards.
    """
    step = StepConfiguration(
        StepType(require(data, "type", "StepConfiguration")),
        algorithm_config_key=data.get("algorithmConfigKey"),
    )
    for camel_key, value in data.items():
        if camel_key in ("type", "algorithmConfigKey"):
            continue
        snake = _camel_to_snake(camel_key)
        if camel_key == "steps":
            step.steps = [decode_into(StepConfiguration, s, ctx) for s in value]
        else:
            setattr(step, snake, value)
    return step


def decode_schedule_configuration(data: dict[str, Any], ctx: LoadContext) -> ScheduleConfiguration:
    """Decode a :class:`ScheduleConfiguration`, reusing the algorithm decoder for its map."""
    schedule: ScheduleConfiguration = decode_with_state(
        ScheduleConfiguration,
        data,
        ctx,
        ctor_args=("schedule_root",),
        elements={"algorithm_configurations": DictOf(Algorithm)},
    )
    return schedule


def register() -> None:
    """Register the schedule and step decoders."""
    register_decoder(StepConfiguration, decode_step_configuration)
    register_decoder(ScheduleConfiguration, decode_schedule_configuration)
