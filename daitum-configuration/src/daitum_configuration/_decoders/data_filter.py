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
Decoders for the :class:`DataFilter` family (``@type``-discriminated).

Each filter stores its source key(s) as a :class:`Reference`, but its constructor takes the
raw ``Parameter``/``Calculation`` (or a numeric literal) and wraps it. So we recover the
referenced value from the ``!!!`` string and call the constructor, which re-wraps it — giving
a byte-identical round-trip without touching private state.
"""

from __future__ import annotations

from typing import Any

from daitum_model.decoding import LoadContext, register_decoder, register_type, require
from daitum_model.references import is_reference, reference_number

from daitum_configuration._decoders._references import resolve_value
from daitum_configuration.data_source.data_store.data_filter import DataFilter
from daitum_configuration.data_source.data_store.data_filter_type import DataFilterType
from daitum_configuration.data_source.data_store.equality_data_filter import EqualityDataFilter
from daitum_configuration.data_source.data_store.inequality_data_filter import InequalityDataFilter
from daitum_configuration.data_source.data_store.regex_data_filter import RegexDataFilter
from daitum_configuration.data_source.data_store.set_data_filter import SetDataFilter
from daitum_configuration.data_source.data_store.wildcard_data_filter import WildcardDataFilter


def _key(rendered: Any, ctx: LoadContext) -> Any:
    """Recover a filter key from its rendered form.

    A filter key builds to a ``!!!`` reference whose body is either a *numeric literal*
    (a plain bound, e.g. ``"!!!5.0"``) or a named-value/field identifier. A non-reference
    value passes through unchanged.
    """
    if not is_reference(rendered):
        return rendered
    number = reference_number(rendered)
    if number is not None:
        return number
    # An identifier body: resolve through the shared reference forms (id / table[field] / …).
    return resolve_value(rendered, ctx)


def _decode_equality(data: dict[str, Any], ctx: LoadContext) -> EqualityDataFilter:
    return EqualityDataFilter(
        require(data, "path", "EqualityDataFilter"),
        _key(require(data, "sourceKey", "EqualityDataFilter"), ctx),
        data.get("value"),
    )


def _decode_regex(data: dict[str, Any], ctx: LoadContext) -> RegexDataFilter:
    return RegexDataFilter(
        require(data, "path", "RegexDataFilter"),
        _key(require(data, "sourceKey", "RegexDataFilter"), ctx),
        data.get("value"),
    )


def _decode_wildcard(data: dict[str, Any], ctx: LoadContext) -> WildcardDataFilter:
    return WildcardDataFilter(
        require(data, "path", "WildcardDataFilter"),
        _key(require(data, "sourceKey", "WildcardDataFilter"), ctx),
        data.get("value"),
        data.get("caseSensitive", False),
    )


def _decode_set(data: dict[str, Any], ctx: LoadContext) -> SetDataFilter:
    source_keys = [_key(k, ctx) for k in require(data, "sourceKey", "SetDataFilter")]
    values = data.get("values")
    return SetDataFilter(
        require(data, "path", "SetDataFilter"),
        source_keys,
        set(values) if values is not None else None,
    )


def _decode_inequality(data: dict[str, Any], ctx: LoadContext) -> InequalityDataFilter:
    return InequalityDataFilter(
        require(data, "path", "InequalityDataFilter"),
        _key(require(data, "lowerKey", "InequalityDataFilter"), ctx),
        _key(require(data, "upperKey", "InequalityDataFilter"), ctx),
        data.get("lower"),
        data.get("upper"),
    )


def register() -> None:
    """Register the five data filters under the ``DataFilter`` ``@type`` registry."""
    mapping = {
        DataFilterType.EQUALITY.value: (EqualityDataFilter, _decode_equality),
        DataFilterType.INEQUALITY.value: (InequalityDataFilter, _decode_inequality),
        DataFilterType.SET.value: (SetDataFilter, _decode_set),
        DataFilterType.WILDCARD.value: (WildcardDataFilter, _decode_wildcard),
        DataFilterType.REGEX.value: (RegexDataFilter, _decode_regex),
    }
    for type_value, (cls, decoder) in mapping.items():
        register_type(DataFilter, type_value, cls)
        register_decoder(cls, decoder)
