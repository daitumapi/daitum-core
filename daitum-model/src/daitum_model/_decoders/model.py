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
Top-level model decoder: reconstruct a live :class:`ModelBuilder` from the output of
:meth:`ModelBuilder.build`.

``ModelBuilder.build()`` emits domain-named top-level keys
(``calculationDefinitions``, ``parameterDefinitions``, ``tableDefinitions``,
``optimisationCheckNamedValue``, ``partialEvaluationAllowed``) rather than the generic
attribute walk, so it needs a hand decoder that owns the load ordering and symbol-table
population.

Ordering matters because fields, formulas, and named values reference ids defined earlier:

1. Build tables in dependency order — each table (and its fields) is fully reconstructed
   before any table built from it, because derived/joined/union construction reads its
   sources' fields. The order is computed by dependency, not definition order, so the
   ``sort_keys=True`` on-disk layout makes no difference.
2. Decode parameters, then calculations (calculations may reference parameters and fields).
3. Set the optimisation-check named value and the partial-evaluation flag.

Calculation/parameter ``build()`` output omits the ``id`` (it keys the parent map), so the
id is injected from the map key before dispatch.
"""

from __future__ import annotations

from typing import Any

from daitum_model._decoders.named_values import decode_calculation, decode_parameter
from daitum_model._decoders.tables import build_table, dependency_order
from daitum_model.decoding import LoadContext, LoadError, optional, optional_map, optional_seq
from daitum_model.model import ModelBuilder
from daitum_model.tracking import AutoCapture

#: The exact top-level keys ``ModelBuilder.build()`` emits.
_MODEL_KEYS = {
    "calculationDefinitions",
    "parameterDefinitions",
    "tableDefinitions",
    "optimisationCheckNamedValue",
    "partialEvaluationAllowed",
    "trackingGroupDefinitions",
    "baselineDefinitions",
}


def decode_model(data: dict[str, Any], ctx: LoadContext) -> ModelBuilder:
    """Reconstruct a live :class:`ModelBuilder` from a built model-definition dict."""
    extra = set(data) - _MODEL_KEYS
    if extra:
        raise LoadError(f"Model definition: unmapped key(s) {sorted(extra)!r}")

    model = ModelBuilder()
    ctx.model = model

    # Tracking groups and baselines are declared first so tracked elements decoded below resolve
    # their group names against a fully-populated model. The ``name`` inside each definition
    # defaults to the map key when absent.
    for group_name, group_data in optional_map(data, "trackingGroupDefinitions").items():
        model.add_tracking_group(optional(group_data, "name", group_name))
    for baseline_name, baseline_data in optional_map(data, "baselineDefinitions").items():
        model.add_baseline(
            optional(baseline_data, "name", baseline_name),
            list(optional_seq(baseline_data, "trackingGroups")),
            AutoCapture(optional(baseline_data, "autoCapture", AutoCapture.NONE.value)),
        )

    table_defs: dict[str, Any] = optional_map(data, "tableDefinitions")

    # Build each table fully (construct + fields + field-id registration) in dependency order,
    # so a derived/joined/union table is built only after every source it reads is complete.
    for table_id in dependency_order(table_defs):
        build_table(table_id, table_defs[table_id], model, ctx)

    # Parameters before calculations: calculations may reference parameters.
    for param_id, param_data in optional_map(data, "parameterDefinitions").items():
        param = decode_parameter({**param_data, "id": param_id}, ctx)
        ctx.register(param_id, param)

    for calc_id, calc_data in optional_map(data, "calculationDefinitions").items():
        calc = decode_calculation({**calc_data, "id": calc_id}, ctx)
        ctx.register(calc_id, calc)

    optimisation_check = data.get("optimisationCheckNamedValue")
    if optimisation_check is not None:
        model.set_data_validation_rule(ctx.resolve(optimisation_check))

    model.set_partial_evaluation_allowed(optional(data, "partialEvaluationAllowed", True))

    # Phase 2: now every table, field and named value is registered, parse the deferred formula
    # strings into their structured trees. A formula that cannot be faithfully decoded raises
    # LoadError (invalid output — no silent degradation).
    ctx.resolve_deferred_formulas()
    return model
