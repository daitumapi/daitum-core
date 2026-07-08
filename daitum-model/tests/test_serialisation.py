"""
Tests for the shared serialisation core (daitum_model.serialisation).

These lock the behaviour unified out of the three former _buildable.py copies:
the build() walk, key conventions, and the camel_to_snake inverse the decoder relies on.
"""

from datetime import date, datetime, time
from enum import Enum

import pytest

from daitum_model.serialisation import (
    Buildable,
    camel_to_snake,
    json_type_info,
    snake_to_camel,
)


class _Colour(Enum):
    RED = "red"


class TestKeyConventions:
    @pytest.mark.parametrize(
        "snake,camel",
        [
            ("display_name", "displayName"),
            ("id", "id"),
            ("max_evaluations_without_improvement", "maxEvaluationsWithoutImprovement"),
            ("a_b_c", "aBC"),
        ],
    )
    def test_snake_to_camel(self, snake, camel):
        assert snake_to_camel(snake) == camel

    @pytest.mark.parametrize(
        "snake,camel",
        [
            ("display_name", "displayName"),
            ("id", "id"),
            ("max_evaluations_without_improvement", "maxEvaluationsWithoutImprovement"),
        ],
    )
    def test_camel_to_snake_inverts_snake_to_camel(self, snake, camel):
        assert camel_to_snake(camel) == snake
        assert snake_to_camel(camel_to_snake(camel)) == camel

    def test_camel_to_snake_leaves_at_type_untouched(self):
        assert camel_to_snake("@type") == "@type"


class TestBuildWalk:
    def test_attribute_keys_are_camelised(self):
        obj = Buildable()
        obj.display_name = "X"  # type: ignore[attr-defined]
        assert obj.build() == {"displayName": "X"}

    def test_private_and_none_attributes_skipped(self):
        obj = Buildable()
        obj.visible = True  # type: ignore[attr-defined]
        obj._hidden = "secret"  # type: ignore[attr-defined]
        obj.absent = None  # type: ignore[attr-defined]
        assert obj.build() == {"visible": True}

    def test_dict_keys_are_not_camelised(self):
        # Domain-keyed dicts (calc names, field ids) must be emitted verbatim.
        obj = Buildable()
        obj.definitions = {"TOTAL_COST": 1, "start_date": 2}  # type: ignore[attr-defined]
        assert obj.build() == {"definitions": {"TOTAL_COST": 1, "start_date": 2}}

    def test_enum_date_time_serialisation(self):
        obj = Buildable()
        obj.colour = _Colour.RED  # type: ignore[attr-defined]
        obj.d = date(2026, 6, 11)  # type: ignore[attr-defined]
        obj.t = time(9, 30, 0)  # type: ignore[attr-defined]
        obj.dt = datetime(2026, 6, 11, 9, 30, 0)  # type: ignore[attr-defined]
        built = obj.build()
        assert built["colour"] == "red"
        assert built["d"] == [2026, 6, 11]
        assert built["t"] == [9, 30, 0]
        assert built["dt"] == [2026, 6, 11, 9, 30, 0]

    def test_type_discriminator_emitted(self):
        @json_type_info("widget")
        class Widget(Buildable):
            pass

        w = Widget()
        w.size = 3  # type: ignore[attr-defined]
        assert w.build() == {"@type": "widget", "size": 3}

    def test_unsupported_type_raises(self):
        obj = Buildable()
        obj.bad = object()  # type: ignore[attr-defined]
        with pytest.raises(TypeError):
            obj.build()


class TestSharedBase:
    def test_model_and_config_use_the_core_buildable_directly(self):
        # The model and configuration packages import the shared base from
        # daitum_model.serialisation; there is no per-package re-export shim.
        from daitum_configuration.configuration import ConfigurationBuilder

        from daitum_model.tables import DataTable

        assert issubclass(DataTable, Buildable)
        assert issubclass(ConfigurationBuilder, Buildable)

    def test_ui_buildable_is_a_core_subclass(self):
        # The UI package keeps its own Buildable subclass (it adds TemplateBindingKey
        # serialisation), built on the shared core.
        from daitum_ui._buildable import Buildable as UiBuildable

        assert issubclass(UiBuildable, Buildable)
