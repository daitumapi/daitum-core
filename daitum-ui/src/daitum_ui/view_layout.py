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
Named layouts a view offers in its toolbar Layout menu.

A view with more than one layout shows a Layout menu; picking a layout swaps the card templates
(and other view-specific presentation settings) the view uses. Each view type subclasses
`ViewLayout` with the settings it can swap — for example `SchedulerLayout`.

Classes:
    - `ViewLayout`: The shared base: a layout's unique ``name``.
"""

from collections.abc import Sequence

from typeguard import typechecked

from daitum_ui._buildable import Buildable


@typechecked
class ViewLayout(Buildable):
    """
    One entry in a view's Layout menu.

    Attributes:
        name: Shown in the Layout menu; unique within the view.
    """

    def __init__(self, name: str):
        """
        Args:
            name: Shown in the Layout menu; must be non-blank and unique within the view.

        Raises:
            ValueError: If ``name`` is blank.
        """
        if not name.strip():
            raise ValueError("A layout name is required.")
        self.name = name


def layout_problems(
    layouts: Sequence[ViewLayout | None], default_layout: str | None
) -> list[tuple[str, str]]:
    """
    Check a view's layouts and default layout, mirroring the platform's validation.

    Args:
        layouts: The view's layouts, in menu order.
        default_layout: The name of the layout the view opens with, if set.

    Returns:
        ``(path, problem)`` pairs; empty when the layouts are valid.
    """
    problems: list[tuple[str, str]] = []
    names: set[str] = set()
    for index, layout in enumerate(layouts):
        path = f"layouts[{index}]"
        if layout is None:
            problems.append((path, "is null"))
        elif not layout.name or not layout.name.strip():
            problems.append((f"{path}.name", "is required"))
        elif layout.name in names:
            problems.append((f"{path}.name", f"'{layout.name}' is used by another layout"))
        else:
            names.add(layout.name)
    if default_layout is not None and default_layout not in names:
        problems.append(("defaultLayout", f"'{default_layout}' does not name a layout"))
    return problems
