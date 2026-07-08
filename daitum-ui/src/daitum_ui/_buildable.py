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
UI serialisation base, extending the shared serialisation core.

The model and configuration packages use :class:`daitum_model.serialisation.Buildable`
directly. The UI package adds one extra serialisation rule — ``TemplateBindingKey``
instances serialise via ``to_string()`` — so it subclasses the core ``Buildable`` and
overrides the ``_convert_special`` hook. ``snake_to_camel`` and ``json_type_info`` are
re-exported unchanged.
"""

from typing import Any

from daitum_model.serialisation import (
    Buildable as _CoreBuildable,
    BuildableValue,
    json_type_info,
    snake_to_camel,
)

from daitum_ui.template_binding_key import TemplateBindingKey

__all__ = [
    "Buildable",
    "BuildableValue",
    "TemplateBindingKey",
    "json_type_info",
    "snake_to_camel",
]


class Buildable(_CoreBuildable):
    """UI ``Buildable`` — serialises ``TemplateBindingKey`` values via ``to_string()``."""

    def _convert_special(self, obj: Any) -> Any:
        if isinstance(obj, TemplateBindingKey):
            return obj.to_string()
        return NotImplemented
