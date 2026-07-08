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
Shared serialisation core for all Daitum objects.

This is the single source of truth for the :class:`Buildable` base class and the
``snake_case``/``camelCase`` key conventions used across the model, UI, and
configuration packages. The UI and configuration packages re-export ``Buildable``,
``snake_to_camel``, and ``json_type_info`` from their own ``_buildable`` modules for
backwards compatibility.

The base ``build()`` walk deliberately does **not** camelise dictionary string keys.
Every package keys dictionaries by domain identifiers — calculation names like
``TOTAL_COST``, field ids, context-variable ids, element ids — that must be emitted
verbatim. Camelising those keys would corrupt them (``start_date`` -> ``startDate``),
so attribute-name camelisation applies only to the top-level attribute keys.
"""

from datetime import date, datetime, time
from enum import Enum
from typing import TYPE_CHECKING, Any, Union

if TYPE_CHECKING:
    from typing import TypeVar

    BuildableType = TypeVar("BuildableType", bound="Buildable")

BuildableValue = Union[
    str,
    int,
    float,
    bool,
    None,
    Enum,
    date,
    time,
    "Buildable",
    list["BuildableValue"],
    dict[str, "BuildableValue"],
]


def snake_to_camel(k: str) -> str:
    """Convert a snake_case string to camelCase."""
    parts = k.split("_")
    return parts[0] + "".join(word.capitalize() for word in parts[1:])


def camel_to_snake(k: str) -> str:
    """Convert a camelCase string to snake_case (the inverse of :func:`snake_to_camel`).

    ``@type`` and any other key without internal capitals is returned unchanged.
    """
    out: list[str] = []
    for ch in k:
        if ch.isupper():
            out.append("_")
            out.append(ch.lower())
        else:
            out.append(ch)
    return "".join(out)


def json_type_info(name: str):
    """Class decorator that attaches a ``@type`` discriminator value for JSON serialisation."""

    def decorator(cls):
        cls._type_name = name
        return cls

    return decorator


class Buildable:
    """
    Base class for all objects that can be serialised to a JSON-compatible dict.

    Subclasses expose their public, non-None instance attributes as camelCase keys.
    An optional ``_type_name`` class attribute (set via ``@json_type_info``) is emitted
    as the ``@type`` discriminator field.

    Attributes listed in ``_always_emit`` (by snake_case attribute name) are emitted even
    when ``None`` — for platform keys whose schema requires the key to be present with a
    ``null`` value (e.g. an optional display ``name`` or ``mapByProperty``).
    """

    #: Snake_case attribute names emitted even when their value is ``None``.
    _always_emit: tuple[str, ...] = ()

    def _convert_special(self, obj: Any) -> Any:
        """Hook for subclasses to serialise types the base walk does not recognise.

        Return :data:`NotImplemented` to defer to the default handling. The UI package
        overrides this to serialise ``TemplateBindingKey`` via ``to_string()``.
        """
        return NotImplemented

    def build(self) -> dict[str, Any]:
        """
        Serialise this object to a JSON-compatible dict.

        Converts public, non-``None`` instance attributes to camelCase keys.
        Recursively builds nested ``Buildable`` objects, converts ``Enum`` values,
        and serialises ``date``/``time``/``datetime`` instances as lists of components.

        Returns:
            dict[str, Any]: The serialised representation.

        Raises:
            TypeError: If an attribute value is of an unsupported type.
        """

        def convert(obj: BuildableValue):  # noqa: PLR0911
            special = self._convert_special(obj)
            if special is not NotImplemented:
                return special
            if isinstance(obj, Buildable):
                return obj.build()
            elif isinstance(obj, Enum):
                return obj.value
            elif isinstance(obj, list):
                return [convert(i) for i in obj]
            elif isinstance(obj, dict):
                return {k: convert(v) for k, v in obj.items()}
            elif isinstance(obj, datetime):
                return [obj.year, obj.month, obj.day, obj.hour, obj.minute, obj.second]
            elif isinstance(obj, date):
                return [obj.year, obj.month, obj.day]
            elif isinstance(obj, time):
                return [obj.hour, obj.minute, obj.second]
            elif isinstance(obj, (str, int, float, bool)) or obj is None:
                return obj

            # Fallback: not allowed
            raise TypeError(f"Unsupported type in build: {type(obj).__name__} ({obj})")

        result = {}

        # ``_type_name`` may be set on the class (via @json_type_info) or, for hierarchies
        # with a dynamic discriminator, on the instance.
        type_name = getattr(self, "_type_name", None)
        if type_name is not None:
            result["@type"] = type_name

        always_emit = self._always_emit
        for k, v in vars(self).items():
            if k.startswith("_"):
                continue
            if v is None and k not in always_emit:
                continue

            key = snake_to_camel(k)
            result[key] = convert(v)

        return result
