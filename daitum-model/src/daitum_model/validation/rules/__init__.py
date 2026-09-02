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
Concrete validation rules.

Importing this package imports every rule module, which registers each rule on
:data:`daitum_model.validation.engine.RULES` via the ``@rule`` decorator. To add a rule,
create a new module here with a ``@rule``-decorated class and import it below.
"""

from __future__ import annotations

from . import (
    data_type_refs,
    derived_config,
    field_cycles,
    field_references,
    join_config,
    named_value_cycles,
    table_cycles,
    union_config,
)

__all__ = [
    "data_type_refs",
    "derived_config",
    "field_cycles",
    "field_references",
    "join_config",
    "named_value_cycles",
    "table_cycles",
    "union_config",
]
