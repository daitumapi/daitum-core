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
Baseline change-tracking primitives.

A :class:`TrackingGroup` is a named set of elements (fields, parameters, and
calculations) that should be snapshotted together. A :class:`Baseline` is a
named point in time that captures one or more tracking groups; it can be
captured manually (via UI events or model changes) or automatically when a
platform milestone such as optimisation completion occurs.

Both are declared on the :class:`~daitum_model.ModelBuilder` and referenced by
elements (via ``set_tracking_groups``) and by the ``BASELINE`` / ``HASBASELINE``
formula functions.
"""

from enum import Enum

from ._helpers import _validate_name
from .serialisation import Buildable


class AutoCapture(Enum):
    """When the platform should capture a baseline automatically."""

    NONE = "NONE"
    OPTIMISATION_COMPLETED = "OPTIMISATION_COMPLETED"


class TrackingGroup(Buildable):
    """
    A named set of tracked elements.

    Fields, parameters, and calculations reference a tracking group by name to
    opt into change tracking. A group only ever has an effect once a
    :class:`Baseline` captures it.
    """

    def __init__(self, name: str):
        _validate_name(name, "tracking group name")
        self.name = name


class Baseline(Buildable):
    """
    A named point in time that snapshots one or more tracking groups.

    Args:
        name: Unique identifier for the baseline.
        tracking_groups: The tracking groups this baseline captures.
        auto_capture: Platform milestone that triggers an automatic capture, or
            :attr:`AutoCapture.NONE` (the default) for manual capture only.
    """

    def __init__(
        self,
        name: str,
        tracking_groups: "list[str | TrackingGroup]",
        auto_capture: AutoCapture = AutoCapture.NONE,
    ):
        _validate_name(name, "baseline name")
        self.name = name
        self.tracking_groups = normalise_tracking_groups(tracking_groups)
        self.auto_capture = auto_capture


def normalise_tracking_groups(groups: "list[str | TrackingGroup]") -> list[str]:
    """Resolve a mix of :class:`TrackingGroup` objects and names to a list of names."""
    return [group.name if isinstance(group, TrackingGroup) else group for group in groups]
