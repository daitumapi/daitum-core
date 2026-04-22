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
    parts = k.split("_")
    return parts[0] + "".join(word.capitalize() for word in parts[1:])


def json_type_info(name: str):
    def decorator(cls):
        cls._type_name = name
        return cls

    return decorator


class Buildable:
    def build(self) -> dict[str, Any]:
        def convert(obj: BuildableValue):  # noqa: PLR0911
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

        type_name = getattr(self.__class__, "_type_name", None)
        if type_name is not None:
            result["@type"] = type_name

        for k, v in vars(self).items():
            if k.startswith("_") or v is None:
                continue

            key = snake_to_camel(k)
            result[key] = convert(v)

        return result
