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
Leaf decoders for the UI package's nested value types (fields, conditions, values, ...).

Every ``Buildable`` subclass in the package that carries a ``@type`` discriminator is
auto-discovered and made decodable by ``@type``, so polymorphic nested values
(``hiddenConditions``, ``formElements``, value objects) resolve to the right class. Leaves
are decoded through the template machinery — typed, never replayed.
"""

from __future__ import annotations

import importlib
import inspect
import pkgutil
from collections.abc import Callable
from typing import Any

from daitum_model.decoding import LoadContext
from daitum_model.serialisation import Buildable

from daitum_ui._decoders._template import decode_by_template

#: ``@type`` discriminator -> concrete Buildable class, auto-discovered across the package.
_AT_TYPE: dict[str, type] = {}

#: Concrete leaf class -> its decoder callable. Populated for every discovered Buildable so
#: nested typed values decode through the template machinery rather than the generic walk.
LEAF_DECODERS: dict[type, Callable[[dict[str, Any], LoadContext], Any]] = {}


def resolve_at_type(discriminator: str) -> type | None:
    """Return the concrete class for a ``@type`` discriminator, or ``None`` if unknown."""
    return _AT_TYPE.get(discriminator)


def _discover() -> None:
    """Populate the ``@type`` map and leaf-decoder table from the daitum_ui package."""
    import daitum_ui

    for _, name, _ in pkgutil.walk_packages(daitum_ui.__path__, daitum_ui.__name__ + "."):
        if "._decoders" in name:
            continue
        try:
            module = importlib.import_module(name)
        except ImportError:
            # A genuinely optional/unavailable module — skip it. Any other error (e.g. a
            # SyntaxError or a module-scope failure) is a real defect and propagates.
            continue
        for _, obj in inspect.getmembers(module, inspect.isclass):
            if (
                issubclass(obj, Buildable)
                and obj is not Buildable
                and obj.__module__.startswith("daitum_ui")
                and not getattr(obj, "__abstractmethods__", None)
            ):
                _register_leaf(obj)


def _register_leaf(cls: type) -> None:
    from daitum_ui.base_view import BaseView

    discriminator = getattr(cls, "_type_name", None)
    # Views are decoded as top-level envelopes through the BaseView @type registry, never as
    # nested leaf values, so they are excluded from the leaf @type map. This keeps a shared
    # discriminator (e.g. "card", used by both CardView and the Card element) unambiguous here.
    if discriminator is not None and not issubclass(cls, BaseView):
        _AT_TYPE.setdefault(discriminator, cls)

    def decode(data: dict[str, Any], ctx: LoadContext, _cls: type = cls) -> Any:
        return decode_by_template(_cls, data, ctx)

    LEAF_DECODERS.setdefault(cls, decode)


def register() -> None:
    """Discover and register every UI leaf decoder. Idempotent."""
    if not _AT_TYPE:
        _discover()
