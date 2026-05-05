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
Shared serialisation utilities for all Daitum UI objects.

Provides the ``Buildable`` base class and helper utilities used across the UI package
to convert Python objects into JSON-serialisable dicts.
"""

from datetime import date, datetime, time
from enum import Enum
from typing import TYPE_CHECKING, Union

from daitum_ui.template_binding_key import TemplateBindingKey

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
    "TemplateBindingKey",
    list["BuildableValue"],
    dict[str, "BuildableValue"],
]


def snake_to_camel(k: str) -> str:
    """Convert a snake_case string to camelCase."""
    parts = k.split("_")
    return parts[0] + "".join(word.capitalize() for word in parts[1:])


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
    as the ``@type`` discriminator field.  ``TemplateBindingKey`` instances are serialised
    via ``to_string()``.
    """

    def build(self):
        """
        Serialise this object to a JSON-compatible dict.

        Converts public, non-``None`` instance attributes to camelCase keys.
        Recursively builds nested ``Buildable`` objects and handles ``Enum``,
        ``TemplateBindingKey``, and date/time types.

        Returns:
            dict: The serialised representation.

        Raises:
            TypeError: If an attribute value is of an unsupported type.
        """

        def convert(obj: BuildableValue):  # noqa: PLR0911
            if isinstance(obj, Buildable):
                # Delegate to obj.build() so subclass overrides are respected
                return obj.build()
            elif isinstance(obj, TemplateBindingKey):
                return obj.to_string()
            elif isinstance(obj, Enum):
                return obj.value
            elif isinstance(obj, list):
                return [convert(i) for i in obj]
            elif isinstance(obj, dict):
                return {
                    (snake_to_camel(k) if isinstance(k, str) else k): convert(v)
                    for k, v in obj.items()
                }
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

        type_name = getattr(self.__class__, "_type_name", None)
        if type_name is not None:
            result["@type"] = type_name

        for k, v in vars(self).items():
            if k.startswith("_") or v is None:
                continue

            key = snake_to_camel(k)
            result[key] = convert(v)

        return result
