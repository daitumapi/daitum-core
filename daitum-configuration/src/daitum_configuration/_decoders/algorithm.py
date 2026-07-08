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
Decoder for the :class:`Algorithm` family.

``Algorithm.build()`` emits ``{"algorithmKey": ..., "parameters": {<displayName>: envelope}}``
with no ``@type`` discriminator, wrapping each value in a ``_quant``/``_qual`` envelope and
stringifying numbers. The decoder dispatches on ``algorithmKey``, strips the envelopes,
recovers the original Python value (number, :class:`NumericExpression`, ``!!!`` reference,
bool, enum, or operator), and reconstructs the right subclass via a per-subclass map of
display name -> constructor keyword.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from daitum_model.decoding import LoadContext, LoadError, register_decoder, require
from daitum_model.references import is_reference

from daitum_configuration._decoders._references import resolve_value
from daitum_configuration.algorithm_configuration.algorithm import Algorithm
from daitum_configuration.algorithm_configuration.alns_algorithm import (
    AcceptanceCriterion,
    AcceptanceCriterionType,
    AdaptiveLargeNeighbourhoodSearch,
)
from daitum_configuration.algorithm_configuration.cmaes_algorithm import CMAESAlgorithm
from daitum_configuration.algorithm_configuration.genetic_algorithm import (
    ComparatorType,
    DistanceMetricType,
    GeneticAlgorithm,
    Mutation,
    MutationType,
    RecombinatorType,
    SamplingMethodType,
    Selection,
    SelectionType,
)
from daitum_configuration.algorithm_configuration.numeric_expression import NumericExpression
from daitum_configuration.algorithm_configuration.steepest_dynamic_local_search import (
    SteepestDynamicLocalSearch,
)
from daitum_configuration.algorithm_configuration.vns_algorithm import VariableNeighbourhoodSearch


def _decode_scalar(envelope: dict[str, Any], ctx: LoadContext) -> Any:
    """Recover a numeric/bool/None/reference value from a ``quantitative`` envelope."""
    value = envelope["value"]
    if value is None or isinstance(value, bool):
        return value
    if is_reference(value):
        return resolve_value(value, ctx)
    return _parse_number_or_expression(value)


def _parse_number_or_expression(text: str) -> Any:
    """Invert ``str(value)``: an int/float literal back to its number, else a NumericExpression."""
    try:
        return int(text)
    except ValueError:
        pass
    try:
        return float(text)
    except ValueError:
        return NumericExpression._from_expr(text)


def _decode_mutation(envelope: dict[str, Any], ctx: LoadContext) -> Mutation:
    params = {k: _decode_scalar(v, ctx) for k, v in (envelope.get("parameters") or {}).items()}
    return Mutation(name=MutationType(envelope["value"]), parameters=params)


def _decode_selection(envelope: dict[str, Any], ctx: LoadContext) -> Selection:
    params = {k: _decode_scalar(v, ctx) for k, v in (envelope.get("parameters") or {}).items()}
    return Selection(name=SelectionType(envelope["value"]), parameters=params)


def _decode_acceptance_criterion(envelope: dict[str, Any], ctx: LoadContext) -> AcceptanceCriterion:
    """Recover an :class:`AcceptanceCriterion` from its ``_qual`` envelope.

    The parameter keys are display names (e.g. ``"Initial temperature"``) emitted verbatim by
    ``build()``; preserving them as-is reproduces the original output byte-for-byte.
    """
    name = AcceptanceCriterionType(envelope["value"])
    params = {k: _decode_scalar(v, ctx) for k, v in (envelope.get("parameters") or {}).items()}
    return AcceptanceCriterion(name=name, parameters=params)


def _enum_decoder(enum_cls: type) -> Callable[[dict[str, Any], LoadContext], Any]:
    def decode(envelope: dict[str, Any], _ctx: LoadContext) -> Any:
        value = envelope["value"]
        return enum_cls(value) if value is not None else None

    return decode


# Per-subclass map: display name -> (constructor kwarg, value decoder).
# A value decoder takes (envelope, ctx) and returns the Python value.
_SCALAR = _decode_scalar

# Base stopping-criteria params shared by every subclass.
_BASE_PARAMS: dict[str, tuple[str, Callable[[dict[str, Any], LoadContext], Any]]] = {
    "Log info": ("log_info", _SCALAR),
    "Evaluations": ("evaluations", _SCALAR),
    "Maximum evaluations without improvement": ("max_evaluations_without_improvement", _SCALAR),
    "Maximum time without improvement": ("max_time_without_improvement", _SCALAR),
    "Minimum improvement": ("min_improvement", _SCALAR),
    "Maximum restart count": ("max_restart_count", _SCALAR),
    "PRNG seed": ("prng_seed", _SCALAR),
    "Time limit": ("time_limit", _SCALAR),
}

_GGA_PARAMS = {
    **_BASE_PARAMS,
    "Mutation rate": ("mutation_rate", _SCALAR),
    "Recombinator rate": ("recombinator_rate", _SCALAR),
    "Population size": ("population_size", _SCALAR),
    "Elitism": ("elitism", _SCALAR),
    "Mutation": ("mutation", _decode_mutation),
    "Recombinator": ("recombinator", _enum_decoder(RecombinatorType)),
    "N-point cuts": ("n_point_cuts", _SCALAR),
    "Selection": ("selection", _decode_selection),
    "Comparator": ("comparator", _enum_decoder(ComparatorType)),
    "Tiebreaker": ("tiebreaker", _SCALAR),
    "Distance Metric": ("distance_metric", _enum_decoder(DistanceMetricType)),
    "Sample Count": ("sample_count", _SCALAR),
    "Sampling Method": ("sampling_method", _enum_decoder(SamplingMethodType)),
}

_VNS_PARAMS = {
    **_BASE_PARAMS,
    "Initial mutation rate": ("initial_mutation_rate", _SCALAR),
    "Maximum mutation rate": ("maximum_mutation_rate", _SCALAR),
    "Minimum mutation rate": ("minimum_mutation_rate", _SCALAR),
    "Mutation rate tau": ("mutation_rate_tau", _SCALAR),
    "Offspring size": ("offspring_size", _SCALAR),
    "Population size": ("population_size", _SCALAR),
    "Mutation": ("mutation", _decode_mutation),
    "Selection": ("selection", _decode_selection),
}

_CMAES_PARAMS = {
    **_BASE_PARAMS,
    "Population size": ("population_size", _SCALAR),
    "Consistency check": ("consistency_check", _SCALAR),
    "CC": ("cc", _SCALAR),
    "CS": ("cs", _SCALAR),
    "Damps": ("damps", _SCALAR),
    "CCOV": ("ccov", _SCALAR),
    "CCOVSEP": ("ccovsep", _SCALAR),
    "Sigma": ("sigma", _SCALAR),
    "Diagonal iterations": ("diagonal_iterations", _SCALAR),
}

_ALNS_PARAMS = {
    **_BASE_PARAMS,
    "Candidates per iteration": ("candidates_per_iteration", _SCALAR),
    "Segment length": ("segment_length", _SCALAR),
    "Decay factor": ("decay_factor", _SCALAR),
    "New best reward": ("new_best_reward", _SCALAR),
    "Improving reward": ("improving_reward", _SCALAR),
    "Accepted reward": ("accepted_reward", _SCALAR),
    "Stagnation limit": ("stagnation_limit", _SCALAR),
    "Acceptance criterion": ("acceptance_criterion", _decode_acceptance_criterion),
}

_SDLS_PARAMS = {
    **_BASE_PARAMS,
    "Allow neutral walks": ("allow_neutral_walks", _SCALAR),
    "Integer step size": ("integer_step_size", _SCALAR),
    "Decimal step size": ("decimal_step_size", _SCALAR),
    "Integer step change": ("integer_step_change", _SCALAR),
    "Integer lowest step": ("integer_lowest_step", _SCALAR),
    "Decimal step change": ("decimal_step_change", _SCALAR),
    "Decimal lowest step": ("decimal_lowest_step", _SCALAR),
}

# algorithmKey -> (subclass, display-name map).
_ALGORITHMS: dict[str, tuple[type, dict[str, tuple[str, Any]]]] = {
    GeneticAlgorithm().key: (GeneticAlgorithm, _GGA_PARAMS),
    VariableNeighbourhoodSearch().key: (VariableNeighbourhoodSearch, _VNS_PARAMS),
    CMAESAlgorithm().key: (CMAESAlgorithm, _CMAES_PARAMS),
    AdaptiveLargeNeighbourhoodSearch().key: (AdaptiveLargeNeighbourhoodSearch, _ALNS_PARAMS),
    SteepestDynamicLocalSearch().key: (SteepestDynamicLocalSearch, _SDLS_PARAMS),
}


def decode_algorithm(data: dict[str, Any], ctx: LoadContext) -> Algorithm:
    """Reconstruct an :class:`Algorithm` subclass from its built dict."""
    key = require(data, "algorithmKey", "Algorithm")
    entry = _ALGORITHMS.get(key)
    if entry is None:
        raise LoadError(f"Unknown algorithmKey: {key!r}")
    cls, param_map = entry

    kwargs: dict[str, Any] = {}
    for display_name, envelope in require(data, "parameters", cls.__name__).items():
        mapping = param_map.get(display_name)
        if mapping is None:
            raise LoadError(f"{cls.__name__}: no field for parameter {display_name!r}")
        field_name, value_decoder = mapping
        kwargs[field_name] = value_decoder(envelope, ctx)

    # n_point_cuts is derived in __post_init__ from the recombinator; let it recompute.
    kwargs.pop("n_point_cuts", None)
    algorithm: Algorithm = cls(**kwargs)
    return algorithm


def register() -> None:
    """Register the algorithm decoder for the base class and every subclass.

    Registering on the abstract :class:`Algorithm` base lets ``decode_into(Algorithm, ...)``
    dispatch on ``algorithmKey`` (the family has no ``@type`` discriminator).
    """
    register_decoder(Algorithm, decode_algorithm)
    for cls, _ in _ALGORITHMS.values():
        register_decoder(cls, decode_algorithm)
