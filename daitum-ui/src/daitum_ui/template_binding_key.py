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

from dataclasses import dataclass

from typeguard import typechecked


@dataclass
@typechecked
class TemplateBindingKey:
    """
    Represents a binding key used inside a UI template.

    A TemplateBindingKey corresponds to a placeholder that appears in
    template definitions.

    Attributes:
        key (str):
            The raw identifier of the placeholder (without formatting).
            For example, for the placeholder "${employeeName}", the key
            would be "employeeName".
    """

    key: str

    def to_string(self):
        return self.key
