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
Key-level symmetry gate for the model decoders' unmapped-key guards.

Three hand decoders reject unexpected input by subtracting a key-set from the incoming dict:
``_MODEL_KEYS`` (``_decoders/model.py``), ``_KNOWN_KEYS`` (``_decoders/fields.py``) and
``_UNION_FIELD_KEYS`` (``_decoders/tables.py``). Each is a transcription of what the corresponding
``build()`` emits, so it can silently drift *looser* than the serialiser — if ``build()`` gains a
key the guard forgets, the guard accepts (and ignores) it, and the ``decode(x.build()).build() ==
x.build()`` round-trip tests do not necessarily catch that (a too-permissive guard rejects nothing).

This gate closes that gap. For every guard it builds a *maximal* fixture — one whose ``build()``
emits every key the guard is meant to accept — and asserts the built key-set is a subset of the
guard. A new ``build()`` key that a guard does not know about therefore fails CI here, loudly,
naming the drift. It is the counterpart to ``test_decoder_coverage.py``: that gate is class-level
(every ``Buildable`` has a decode path); this one is key-level (every guard accepts everything its
``build()`` emits).

The guards for the model and fields are now *derived* from a single shared vocabulary
(``MODEL_DEFINITION_KEYS``, ``FIELD_BUILD_KEYS``), so drift is already structurally prevented; this
gate additionally proves that vocabulary matches the real ``build()`` output, catching a stale
vocabulary as well as a stale guard.
"""

from __future__ import annotations

from typing import Any

import daitum_model.formulas as formulas
import pytest
from daitum_model import DataType, ModelBuilder
from daitum_model._decoders.fields import _KNOWN_KEYS
from daitum_model._decoders.model import _MODEL_KEYS
from daitum_model._decoders.tables import _UNION_FIELD_KEYS
from daitum_model.tracking import AutoCapture


def _maximal_model() -> ModelBuilder:
    """A model exercising every top-level ``build()`` key, including the tracking-only keys.

    The optimisation-check named value must be boolean, so the driving calculation compares a sum to
    a constant; tracking requires an ``id_field`` on any table carrying a tracked field.
    """
    model = ModelBuilder()
    table = model.add_data_table("T")
    table.set_id_field("K")
    table.add_data_field("K", DataType.STRING)
    tracked = table.add_data_field("V", DataType.INTEGER)

    model.add_tracking_group("G")
    tracked.set_tracking_groups(["G"])
    model.add_baseline("BL", ["G"], AutoCapture.NONE)

    check = model.add_calculation("CALC", formulas.SUM(table["V"]) > formulas.CONST(0))
    model.add_parameter("P", DataType.INTEGER, 5)
    model.set_data_validation_rule(check)
    return model


def _model_definition_keys() -> set[str]:
    return set(_maximal_model().build())


def _data_field_keys() -> set[str]:
    """A data field with every optional attribute set, so ``build()`` emits its full key surface."""
    model = ModelBuilder()
    table = model.add_data_table("T")
    field = table.add_data_field("D", DataType.INTEGER)
    field.set_default_value(1)
    field.set_import_format("#")
    field.set_unique(True)
    field.set_nullable(True)
    field.set_order_index(2)
    field.set_description("d")
    model.add_tracking_group("G")
    table.set_id_field("D")
    field.set_tracking_groups(["G"])
    return set(field.build())


def _calculated_field_keys() -> set[str]:
    model = ModelBuilder()
    table = model.add_data_table("T")
    source = table.add_data_field("D", DataType.INTEGER)
    field = table.add_calculated_field(
        "C", source + formulas.CONST(1), order_index=1, description="c"
    )
    model.add_tracking_group("G")
    table.set_id_field("D")
    field.set_tracking_groups(["G"])
    return set(field.build())


def _combo_field_keys() -> set[str]:
    model = ModelBuilder()
    table = model.add_data_table("T")
    source = table.add_data_field("D", DataType.INTEGER)
    field = table.add_combo_field("CO", source + formulas.CONST(1), True)
    field.set_default_value(0)
    field.set_import_format("#")
    field.set_order_index(3)
    field.set_description("co")
    return set(field.build())


def _union_field_keys() -> set[str]:
    """A union field with every optional attribute set. Union fields are plain data fields."""
    model = ModelBuilder()
    left = model.add_data_table("A")
    left.add_data_field("X", DataType.INTEGER)
    left.set_key_column("X")
    right = model.add_data_table("B")
    right.add_data_field("X", DataType.INTEGER)
    right.set_key_column("X")
    union = model.add_union_table("U", [left, right])
    field = union.add_field("X", DataType.INTEGER, order_index=1, description="x")
    return set(field.build())


#: (name, guard-set, maximal-key producer). Each producer returns the exact key set its ``build()``
#: emits when every accepted key is present; the guard must be a superset.
_GUARD_CASES: list[tuple[str, frozenset[str], Any]] = [
    ("model definition", frozenset(_MODEL_KEYS), _model_definition_keys),
    ("data field", frozenset(_KNOWN_KEYS), _data_field_keys),
    ("calculated field", frozenset(_KNOWN_KEYS), _calculated_field_keys),
    ("combo field", frozenset(_KNOWN_KEYS), _combo_field_keys),
    ("union field", frozenset(_UNION_FIELD_KEYS), _union_field_keys),
]


class TestGuardKeySymmetry:
    @pytest.mark.parametrize(
        ("name", "guard", "producer"), _GUARD_CASES, ids=[c[0] for c in _GUARD_CASES]
    )
    def test_guard_accepts_everything_build_emits(self, name, guard, producer):
        built_keys = producer()
        missing = built_keys - guard
        assert not missing, (
            f"{name}: build() emits key(s) {sorted(missing)!r} that the decoder guard does not "
            f"accept — the guard has drifted looser/staler than the serialiser"
        )

    def test_model_fixture_is_actually_maximal(self):
        # Guard against the gate silently weakening: the maximal model must exercise every
        # _MODEL_KEYS entry, otherwise a dropped key would go untested.
        assert _model_definition_keys() == set(_MODEL_KEYS)

    def test_field_fixtures_cover_the_whole_field_vocabulary(self):
        # Across the three field types, every _KNOWN_KEYS entry must be emitted by some fixture,
        # so no field key escapes the subset check above.
        covered = _data_field_keys() | _calculated_field_keys() | _combo_field_keys()
        assert covered == set(_KNOWN_KEYS)

    def test_union_guard_is_a_superset_of_the_emitted_union_keys(self):
        # Unlike the model/field vocabularies, the union guard is legitimately *broader* than what
        # this library's ``add_field`` emits: a union field is a data field, so the guard accepts
        # ``defaultValue``/``importFormat`` (which a platform-authored model may carry) even though
        # ``UnionTable.add_field`` never sets them. So this is a subset check, not equality — the
        # ``@type``/``id``/``tableId``/``dataType``/``orderIndex``/``description`` keys the builder
        # does emit must all be accepted, and the guard may accept more.
        assert _union_field_keys() <= set(_UNION_FIELD_KEYS)
