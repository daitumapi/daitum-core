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
Decoders for the named-value types (:class:`Calculation`, :class:`Parameter`).

These are routed through the owning model's factory methods (``add_calculation`` /
``add_parameter``) so the decoded objects are registered and back-pointed. The ``id`` of
each named value is recorded in the load context so formulas and references that mention it
resolve.

A :class:`Calculation` derives its data type from its formula, so the redundant
``dataType`` key is ignored on the way in. A :class:`Parameter`'s value lives in the
separate ``named-values.json`` files rather than ``model-definition.json``; when decoding
a model definition alone the value is left unset and patched in later by the model decoder
if those files were loaded.
"""

from __future__ import annotations

from typing import Any

from daitum_model._decoders.data_types import decode_data_type
from daitum_model._decoders.formula import defer_formula, placeholder_formula
from daitum_model.decoding import LoadContext, LoadError, optional, register_decoder
from daitum_model.named_values import Calculation, Parameter


def decode_calculation(data: dict[str, Any], ctx: LoadContext) -> Calculation:
    """Reconstruct a :class:`Calculation` via the model's ``add_calculation`` factory.

    The formula is parsed in phase 2 (deferred); the calculation is created now with a typed
    placeholder, and the parsed tree replaces it once every symbol is registered.
    """
    if ctx.model is None:
        raise LoadError("Cannot decode a Calculation without a model in the load context")
    placeholder = placeholder_formula(data["formula"], ctx)
    calc = ctx.model.add_calculation(
        data["id"], placeholder, model_level=optional(data, "modelLevel", False)
    )
    defer_formula(data["formula"], ctx, None, lambda f: setattr(calc, "formula", f))
    if data.get("dependsOnDecision") is not None:
        calc.set_depends_on_decision(data["dependsOnDecision"])
    if data.get("requiredByOutput") is not None:
        calc.set_required_by_output(data["requiredByOutput"])
    if data.get("trackingGroups"):
        calc.set_tracking_groups(data["trackingGroups"])
    return calc


def decode_parameter(data: dict[str, Any], ctx: LoadContext) -> Parameter:
    """Reconstruct a :class:`Parameter` via the model's ``add_parameter`` factory."""
    if ctx.model is None:
        raise LoadError("Cannot decode a Parameter without a model in the load context")
    data_type = decode_data_type(data["dataType"], ctx)
    param = ctx.model.add_parameter(
        data["id"], data_type, None, model_level=optional(data, "modelLevel", False)
    )
    if data.get("importFormat") is not None:
        param.set_import_format(data["importFormat"])
    if data.get("trackingGroups"):
        param.set_tracking_groups(data["trackingGroups"])
    return param


def register() -> None:
    """Register the named-value decoders."""
    register_decoder(Calculation, decode_calculation)
    register_decoder(Parameter, decode_parameter)
