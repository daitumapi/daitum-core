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
Decoders for :class:`ModelConfiguration` and its decision variables, objectives,
constraints, and scenario outputs.

These reconstruct each object through the live model object resolved from its
``cellReference``, then restore the exact stored state (tracking ids, bounds, spec
fields) so ``build()`` reproduces the original JSON byte-for-byte.
"""

from __future__ import annotations

import contextlib
from collections.abc import Iterator
from typing import Any

from daitum_model.decoding import LoadContext, decode_into, register_decoder, require
from daitum_model.references import REFERENCE_PREFIX

from daitum_configuration._decoders._references import resolve_table, resolve_value, strip_prefix
from daitum_configuration.model_configuration.constraint import Constraint, ConstraintType
from daitum_configuration.model_configuration.decision_variable import DecisionVariable, DVType
from daitum_configuration.model_configuration.external_configuration import (
    ExternalModelConfiguration,
)
from daitum_configuration.model_configuration.model_configuration import ModelConfiguration
from daitum_configuration.model_configuration.objective import Objective
from daitum_configuration.model_configuration.priority import Priority
from daitum_configuration.model_configuration.scenario_output import ScenarioOutput
from daitum_configuration.model_configuration.stochastic_configuration import (
    StochasticConfiguration,
)


def _unref(rendered: str | None) -> str | None:
    """Strip a leading ``!!!`` from a stored reference string, preserving None."""
    return strip_prefix(rendered) if rendered is not None else None


def decode_decision_variable(data: dict[str, Any], ctx: LoadContext) -> DecisionVariable:
    """Reconstruct a :class:`DecisionVariable` from its built dict."""
    spec = require(data, "specification", "DecisionVariable")
    cell = require(data, "cellReference", "DecisionVariable")
    target = resolve_value(cell, ctx)
    table = resolve_table(cell, ctx)
    dv = DecisionVariable(target, table, DVType(spec["@type"]))

    dv._dv_string = strip_prefix(cell)
    dv._tracking_id = data["trackingId"]
    dv._scale = spec["scale"]
    dv._dv_min_value = _spec_bound(spec, "minimumValue", "minimumValueReference")
    dv._dv_max_value = _spec_bound(spec, "maximumValue", "maximumValueReference")
    dv._seed_source_string = _unref(spec["seedSource"])
    dv._tag_source_string = _unref(data["tagSource"])
    dv._disabled = data["disabled"]
    dv._disabled_if_invalid = data["disabledIfInvalid"]
    return dv


def _spec_bound(spec: dict[str, Any], literal_key: str, reference_key: str) -> Any:
    literal = spec[literal_key]
    if literal is not None:
        return literal
    reference = spec[reference_key]
    if reference is not None:
        return strip_prefix(reference)
    return None


def decode_objective(data: dict[str, Any], ctx: LoadContext) -> Objective:
    """Reconstruct an :class:`Objective` from its built dict."""
    objective = resolve_value(require(data, "cellReference", "Objective"), ctx)
    obj = Objective(
        objective,
        maximise=require(data, "maximise", "Objective"),
        priority=Priority(require(data, "priority", "Objective")),
        weight=require(data, "weight", "Objective"),
        name=require(data, "name", "Objective"),
    )
    obj.tracking_id = data["trackingId"]
    return obj


def decode_constraint(data: dict[str, Any], ctx: LoadContext) -> Constraint:
    """Reconstruct a :class:`Constraint` from its built dict."""
    spec = require(data, "specification", "Constraint")
    constraint = resolve_value(require(data, "cellReference", "Constraint"), ctx)
    con = Constraint(constraint)
    con._tracking_id = data["trackingId"]
    con._constraint_type = ConstraintType(spec["@type"])
    con._lower_bound = _constraint_bound(spec, "lowerBound", "lowerBoundReference", ctx)
    con._upper_bound = _constraint_bound(spec, "upperBound", "upperBoundReference", ctx)
    con._lower_bound_inclusive = spec["lowerBoundInclusive"]
    con._upper_bound_inclusive = spec["upperBoundInclusive"]
    con._priority = Priority(spec["priority"])
    con._hard_score = spec["hardScore"]
    con._name = data["name"]
    return con


def _constraint_bound(
    spec: dict[str, Any], literal_key: str, reference_key: str, ctx: LoadContext
) -> Any:
    literal = spec[literal_key]
    if literal is not None:
        return literal
    reference = spec[reference_key]
    if reference is not None:
        # Constraint bound references are stored bare (no !!! prefix); resolve to the object.
        return resolve_value(reference, ctx)
    return None


def decode_scenario_output(data: dict[str, Any], ctx: LoadContext) -> ScenarioOutput:
    """Reconstruct a :class:`ScenarioOutput` from its built dict."""
    cell = require(data, "cellReference", "ScenarioOutput")
    target = resolve_value(cell, ctx)
    table = resolve_table(cell, ctx)
    scenario_output = ScenarioOutput(require(data, "name", "ScenarioOutput"), target, table)
    scenario_output.cell_reference = f"{REFERENCE_PREFIX}{strip_prefix(cell)}"
    scenario_output.tracking_id = data["trackingId"]
    return scenario_output


#: Classes whose constructors bump a class-level ``_tracking_counter``. Decoding reconstructs
#: them through those constructors but restores each object's real tracking id, so the counter
#: bump is an unwanted side effect — :func:`_preserve_tracking_counters` undoes it.
_TRACKED = (DecisionVariable, Objective, Constraint, ScenarioOutput)


@contextlib.contextmanager
def _preserve_tracking_counters() -> Iterator[None]:
    """Leave each tracked class's ``_tracking_counter`` unchanged across a decode."""
    saved = {cls: cls._tracking_counter for cls in _TRACKED}
    try:
        yield
    finally:
        for cls, value in saved.items():
            cls._tracking_counter = value


def decode_model_configuration(data: dict[str, Any], ctx: LoadContext) -> ModelConfiguration:
    """Reconstruct a :class:`ModelConfiguration` from its built dict.

    Decoding is side-effect-free: the decision-variable/objective/constraint/scenario-output
    constructors bump class-level tracking counters, but each object's real tracking id is
    restored from the data and the counters are reset, so loading a configuration does not
    perturb the ids a subsequently *built* object would receive.
    """
    with _preserve_tracking_counters():
        return _decode_model_configuration(data, ctx)


def _decode_model_configuration(data: dict[str, Any], ctx: LoadContext) -> ModelConfiguration:
    config = ModelConfiguration()
    config.decision_variables = [
        decode_decision_variable(d, ctx) for d in data.get("decisionVariables", [])
    ]
    config.objectives = [decode_objective(d, ctx) for d in data.get("objectives", [])]
    config.constraints = [decode_constraint(d, ctx) for d in data.get("constraints", [])]
    config.scenario_outputs = [
        decode_scenario_output(d, ctx) for d in data.get("scenarioOutputs", [])
    ]
    config.disable_seed_solution = data.get("disableSeedSolution", config.disable_seed_solution)
    config.calculated_seed = data.get("calculatedSeed", config.calculated_seed)
    config.validation_enabled = data.get("validationEnabled", config.validation_enabled)
    config.profiling = data.get("profiling", config.profiling)
    config.hide_objective_when_infeasible = data.get(
        "hideObjectiveWhenInfeasible", config.hide_objective_when_infeasible
    )

    stochastic = data.get("stochasticConfiguration")
    if stochastic is not None:
        config.stochastic_configuration = decode_into(StochasticConfiguration, stochastic, ctx)

    external = data.get("externalConfiguration")
    if external is not None:
        config.external_configuration = decode_into(ExternalModelConfiguration, external, ctx)

    config.using_custom_evaluator = data.get("usingCustomEvaluator", config.using_custom_evaluator)
    config.custom_evaluator_version = data.get(
        "customEvaluatorVersion", config.custom_evaluator_version
    )
    config.custom_evaluator_key = data.get("customEvaluatorKey", config.custom_evaluator_key)
    return config


def register() -> None:
    """Register the model-configuration decoders."""
    register_decoder(DecisionVariable, decode_decision_variable)
    register_decoder(Objective, decode_objective)
    register_decoder(Constraint, decode_constraint)
    register_decoder(ScenarioOutput, decode_scenario_output)
    register_decoder(ModelConfiguration, decode_model_configuration)
