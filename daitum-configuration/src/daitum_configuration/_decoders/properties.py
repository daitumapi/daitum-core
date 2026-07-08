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
Decoders for the model- and report-property families.

These are regular containers: ``ModelProperty``/``OverlayConfig``/``ReportData`` are plain
attribute walks, while ``ModelImportOptions`` and ``ReportProperty`` populate their state
through ``set_*`` methods (so they decode via ``decode_with_state``). ``ReportData`` converts
a ``set`` to a ``list`` in its constructor, which the generic walk handles transparently.
"""

from __future__ import annotations

from typing import Any

from daitum_model.decoding import LoadContext, generic, register_decoder

from daitum_configuration._decoders._state import decode_with_state
from daitum_configuration.model_property.model_import_options import ModelImportOptions
from daitum_configuration.model_property.model_property import ModelProperty
from daitum_configuration.model_property.overlay_config import OverlayConfig
from daitum_configuration.report_property.report_data import ReportData
from daitum_configuration.report_property.report_property import ReportProperty


def decode_report_data(data: dict[str, Any], _ctx: LoadContext) -> ReportData:
    """Decode :class:`ReportData`, restoring the ``required_sheets`` set the constructor takes."""
    sheets = data.get("requiredSheets")
    report_data = ReportData(
        required_sheets=set(sheets) if sheets is not None else None,
        requires_monte_carlo=data.get("requiresMonteCarlo", False),
        requires_scenario_comparison=data.get("requiresScenarioComparison", False),
    )
    return report_data


def register() -> None:
    """Register the property decoders."""
    generic(ModelProperty)
    generic(OverlayConfig)
    register_decoder(ReportData, decode_report_data)

    # Setter-built: no (or few) constructor args; state restored from the built dict.
    register_decoder(
        ModelImportOptions, lambda data, ctx: decode_with_state(ModelImportOptions, data, ctx)
    )
    register_decoder(
        ReportProperty,
        lambda data, ctx: decode_with_state(
            ReportProperty,
            data,
            ctx,
            ctor_args=("export_format",),
            elements={"report_data": ReportData},
        ),
    )
