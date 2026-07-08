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
Decoder for the top-level :class:`ConfigurationBuilder`.

``ConfigurationBuilder.build()`` is a default attribute walk, but several of its nested
values (the algorithm, the model configuration) are irregular and have their own
registered decoders. This decoder dispatches those nested values explicitly and copies
the flat scalar flags through.
"""

from __future__ import annotations

from typing import Any

from daitum_model.decoding import LoadContext, decode_into, register_decoder

from daitum_configuration.algorithm_configuration.algorithm import Algorithm
from daitum_configuration.configuration import ConfigurationBuilder
from daitum_configuration.data_source.data_source import DataSource
from daitum_configuration.model_configuration.model_configuration import ModelConfiguration
from daitum_configuration.model_property.model_property import ModelProperty
from daitum_configuration.report_property.report_property import ReportProperty
from daitum_configuration.schedule_configuration.schedule_configuration import ScheduleConfiguration


def decode_configuration(data: dict[str, Any], ctx: LoadContext) -> ConfigurationBuilder:
    """Reconstruct a :class:`ConfigurationBuilder` from its built dict."""
    builder = ConfigurationBuilder()

    algorithm = data.get("algorithmConfiguration")
    if algorithm is not None:
        builder.algorithm_configuration = decode_into(Algorithm, algorithm, ctx)

    model_configuration = data.get("modelConfiguration")
    if model_configuration is not None:
        builder.model_configuration = decode_into(ModelConfiguration, model_configuration, ctx)

    data_sources = data.get("dataSources")
    if data_sources:
        builder.data_sources = [decode_into(DataSource, d, ctx) for d in data_sources]

    schedule = data.get("scheduleConfiguration")
    if schedule is not None:
        builder.schedule_configuration = decode_into(ScheduleConfiguration, schedule, ctx)

    model_properties = data.get("modelProperties")
    if model_properties is not None:
        builder.model_properties = decode_into(ModelProperty, model_properties, ctx)

    report_properties = data.get("reportProperties")
    if report_properties:
        builder.report_properties = {
            key: decode_into(ReportProperty, rp, ctx) for key, rp in report_properties.items()
        }

    builder.solution_view_allowed = data.get("solutionViewAllowed", builder.solution_view_allowed)
    builder.solution_view_enabled = data.get("solutionViewEnabled", builder.solution_view_enabled)
    return builder


def register() -> None:
    """Register the configuration-builder decoder."""
    register_decoder(ConfigurationBuilder, decode_configuration)
