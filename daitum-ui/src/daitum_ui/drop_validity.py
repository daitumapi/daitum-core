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
Drag feedback shared by views that support drag and drop.

While an item is dragged, the platform judges each possible drop as **Recommended**,
**Allowed** or **Not allowed**. These classes choose which of those outcomes are drawn, and
where:

- `DropValidity` colours things that travel with the drag. ``timeline_drag`` is the anchor
  line, time pill, dashed landing shadow and callout; ``card`` is the outline on the card a
  dragged item is dropped onto.
- `DropValidityOverlay` shades areas of the view while dragging. ``rows`` shades the row under
  the pointer, ``columns`` shades whole columns (roster only) and ``canvas`` shades the whole
  view with where the dragged item may be dropped.

Each part is a `DropOutcomes`. A part left as ``None`` is switched off; an outcome set to
``False`` is drawn in a neutral colour rather than hidden, except Recommended, which is drawn as
Allowed (a Recommended drop is also allowed). Which parts a view accepts is decided by the view
itself (for example `SchedulerView.set_drop_validity`).

Classes:
    - `DropOutcomes`: Which of the three outcomes a part paints.
    - `DropValidity`: Feedback that travels with the drag.
    - `DropValidityOverlay`: Shading of view areas while dragging.
"""

from dataclasses import dataclass

from typeguard import typechecked

from daitum_ui._buildable import Buildable


@dataclass
@typechecked
class DropOutcomes(Buildable):
    """
    The outcomes a drag-feedback part paints in their own colour.

    An outcome set to ``False`` is still judged (a Not allowed drop is still refused); it is
    only drawn in a neutral colour. ``recommended=False`` draws Recommended drops as Allowed
    instead, since a Recommended drop is also allowed. At least one outcome must be ``True`` — to
    switch a part off, leave it as ``None`` on its `DropValidity` or `DropValidityOverlay` instead.

    Attributes:
        recommended: Paint Recommended drops (green).
        allowed: Paint Allowed drops (blue).
        not_allowed: Paint Not allowed drops (red).

    Raises:
        ValueError: If all three outcomes are ``False``.
    """

    recommended: bool = True
    allowed: bool = True
    not_allowed: bool = True

    def __post_init__(self) -> None:
        if not self.shows_any():
            raise ValueError(
                "DropOutcomes shows no outcome; leave the part as None to switch it off."
            )

    def shows_any(self) -> bool:
        """Whether at least one outcome is painted."""
        return self.recommended or self.allowed or self.not_allowed


@dataclass
@typechecked
class DropValidity(Buildable):
    """
    Drag feedback that travels with the dragged item.

    Attributes:
        timeline_drag:
            The anchor line, time pill, dashed landing shadow and callout drawn while a task is
            moved or placed on a timeline. ``None`` switches them off.
        card:
            The outline on the card a dragged item would be dropped onto (for example the task
            a resource is allocated to). ``None`` switches it off.
    """

    timeline_drag: DropOutcomes | None = None
    card: DropOutcomes | None = None


@dataclass
@typechecked
class DropValidityOverlay(Buildable):
    """
    Shading of view areas while an item is dragged.

    Attributes:
        rows:
            Shades the row under the pointer, split into Recommended, Allowed and Not allowed
            stretches. ``None`` switches it off.
        columns:
            Shades whole columns (roster views only). ``None`` switches it off.
        canvas:
            Shades the whole view with where the dragged item may be dropped. A place it may not
            go to at all is Not allowed throughout; everywhere else is split into Recommended,
            Allowed and Not allowed stretches of time, including time blocked for that place.
            ``None`` switches it off.
    """

    rows: DropOutcomes | None = None
    columns: DropOutcomes | None = None
    canvas: DropOutcomes | None = None


def drop_feedback_problems(
    path: str,
    validity: DropValidity | None,
    overlay: DropValidityOverlay | None,
    supported: frozenset[str],
    source: str,
) -> list[tuple[str, str]]:
    """
    Check drag-feedback settings against the parts a drag source can draw.

    Mirrors the platform's validation so problems surface while building rather than at upload.

    Args:
        path: Path prefix of the owning object (``""`` for the view itself).
        validity: The source's `DropValidity`, if any.
        overlay: The source's `DropValidityOverlay`, if any.
        supported: Built part names the source can draw (``timelineDrag``, ``card``, ``rows``,
            ``columns``, ``canvas``).
        source: Human-readable name of the source, used in messages.

    Returns:
        ``(path, problem)`` pairs; empty when the settings are valid.
    """
    prefix = f"{path}." if path else ""
    parts: list[tuple[str, str, DropOutcomes | None]] = []
    if validity is not None:
        parts += [
            ("dropValidity", "timelineDrag", validity.timeline_drag),
            ("dropValidity", "card", validity.card),
        ]
    if overlay is not None:
        parts += [
            ("dropValidityOverlay", "rows", overlay.rows),
            ("dropValidityOverlay", "columns", overlay.columns),
            ("dropValidityOverlay", "canvas", overlay.canvas),
        ]
    problems: list[tuple[str, str]] = []
    for owner, name, outcomes in parts:
        if outcomes is None:
            continue
        part_path = f"{prefix}{owner}.{name}"
        if name not in supported:
            problems.append((part_path, f"not supported by {source}"))
        elif not outcomes.shows_any():
            problems.append((part_path, f"shows no outcome; leave {name} out to switch it off"))
    return problems
