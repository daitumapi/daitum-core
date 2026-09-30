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
Behaviour of the ``validationListTable`` key :meth:`ModelBuilder.build` emits, and of the
:meth:`ModelBuilder.set_validation_table` entry point that produces the table it names.

The key exists so the platform learns *which* table aggregates a model's validation errors.
``set_validation_table`` records the id when it builds the table, and ``build`` emits what was
recorded, so these tests pin the two halves that have to stay in step: the key names the table
once one exists, is ``None`` on a model that never asks for one (it is always emitted, so the
platform can read it unconditionally), survives a model with no validated fields at all, and
round-trips through ``build()``/``read_from_dict()`` -- which only holds because the decoder
records the id it loaded rather than dropping it. The idempotency check covers the second half:
two callers (a model transform's log table and a validation list view) legitimately ask for the
same table, and the second ask must return the first one rather than rebuild it.
"""

from __future__ import annotations

import pytest
from daitum_model import (
    VALIDATION_LIST_SORTED_TABLE,
    DataType,
    ModelBuilder,
    NonBlankValidator,
    Severity,
)
from daitum_model.decoding import LoadError


def _model_with_validated_field() -> ModelBuilder:
    """A minimal model that contributes one row to the validation list."""
    model = ModelBuilder()
    table = model.add_data_table("T")
    table.set_id_field("K")
    table.set_validation_group("G")
    table.add_data_field("K", DataType.STRING)
    table.add_data_field("V", DataType.INTEGER).add_validator(NonBlankValidator(Severity.ERROR))
    return model


def _model_without_validated_fields() -> ModelBuilder:
    model = ModelBuilder()
    table = model.add_data_table("T")
    table.set_id_field("K")
    table.add_data_field("K", DataType.STRING)
    return model


class TestValidationListTableKey:
    def test_key_is_null_until_the_table_is_built(self):
        # The key is always present, so the platform can read it unconditionally; it names a
        # table only once one exists.
        model = _model_with_validated_field()
        assert model.build()["validationListTable"] is None

    def test_emits_the_table_id_for_the_platform(self):
        model = _model_with_validated_field()
        table = model.set_validation_table()

        assert table is not None
        assert table.id == VALIDATION_LIST_SORTED_TABLE
        assert model.build()["validationListTable"] == VALIDATION_LIST_SORTED_TABLE

    def test_second_call_returns_the_first_table_without_rebuilding(self):
        # Rebuilding would re-add the ValidationList union table and raise on the duplicate id.
        model = _model_with_validated_field()
        first = model.set_validation_table()
        table_count = len(model.get_tables())

        assert model.set_validation_table() is first
        assert len(model.get_tables()) == table_count

    def test_model_without_validated_fields_emits_null(self):
        # ``_ValidationListBuilder.build()`` returns None here, so there is no table to name.
        model = _model_without_validated_fields()

        assert model.set_validation_table() is None
        assert model.build()["validationListTable"] is None


class TestValidationListTableRoundTrip:
    def test_id_survives_build_and_decode(self):
        model = _model_with_validated_field()
        model.set_validation_table()
        definition = model.build()

        decoded = ModelBuilder.read_from_dict(definition)

        assert decoded.build() == definition

    def test_decoded_model_does_not_rebuild_the_table(self):
        model = _model_with_validated_field()
        model.set_validation_table()

        decoded = ModelBuilder.read_from_dict(model.build())
        table_count = len(decoded.get_tables())

        assert decoded.set_validation_table() is decoded.get_table(VALIDATION_LIST_SORTED_TABLE)
        assert len(decoded.get_tables()) == table_count

    def test_decode_rejects_an_id_naming_no_table(self):
        model = _model_with_validated_field()
        model.set_validation_table()
        definition = model.build()
        definition["validationListTable"] = "NotATable"

        with pytest.raises(LoadError, match="validationListTable"):
            ModelBuilder.read_from_dict(definition)
