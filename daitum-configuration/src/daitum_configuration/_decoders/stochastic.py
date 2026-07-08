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

"""Decoder for :class:`StochasticConfiguration` (a metric-rule map set after construction)."""

from __future__ import annotations

from typing import Any

from daitum_model.decoding import LoadContext, register_decoder

from daitum_configuration._decoders._state import DictOf, decode_with_state
from daitum_configuration.model_configuration.stochastic_configuration import (
    MetricCombinationRule,
    StochasticConfiguration,
)


def decode_stochastic_configuration(
    data: dict[str, Any], ctx: LoadContext
) -> StochasticConfiguration:
    """Reconstruct a :class:`StochasticConfiguration`, restoring its metric-rule enum map."""
    config: StochasticConfiguration = decode_with_state(
        StochasticConfiguration,
        data,
        ctx,
        ctor_args=("runs", "p", "disable_evaluator_caching"),
        elements={"metric_rules": DictOf(MetricCombinationRule)},
    )
    return config


def register() -> None:
    """Register the stochastic-configuration decoder."""
    register_decoder(StochasticConfiguration, decode_stochastic_configuration)
