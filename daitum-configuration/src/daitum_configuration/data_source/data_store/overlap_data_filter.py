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

""":class:`OverlapDataFilter` — a :class:`DataFilter` matching rows by a time window."""

from datetime import timedelta
from enum import Enum

from daitum_model import Calculation, Parameter
from daitum_model.references import Reference
from daitum_model.serialisation import json_type_info
from typeguard import typechecked

from daitum_configuration.data_source.data_store.data_filter import DataFilter
from daitum_configuration.data_source.data_store.data_filter_type import DataFilterType


class OverlapMode(Enum):
    """How an :class:`OverlapDataFilter` compares a row's period with its window.

    OVERLAP
        Match rows whose ``[start, end)`` overlaps the (padded) window.
    START_WITHIN
        Match rows whose start lies within the window; padding is ignored.
    """

    OVERLAP = "OVERLAP"
    START_WITHIN = "START_WITHIN"


def iso_duration(duration: timedelta) -> str:
    """Render a non-negative :class:`timedelta` as an ISO-8601 duration, e.g. ``PT12H``."""
    if duration < timedelta(0):
        raise ValueError(f"Padding must not be negative, got {duration}")
    days = duration.days
    hours, remainder = divmod(duration.seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    seconds_part = f"{seconds}.{duration.microseconds:06d}".rstrip("0").rstrip(".")
    time = "".join(
        f"{value}{unit}"
        for value, unit in ((hours, "H"), (minutes, "M"), (seconds_part, "S"))
        if value not in (0, "0")
    )
    if days == 0 and not time:
        return "PT0S"
    return f"P{f'{days}D' if days else ''}{f'T{time}' if time else ''}"


# pylint: disable=too-many-positional-arguments
@json_type_info(DataFilterType.OVERLAP.value)
@typechecked
class OverlapDataFilter(DataFilter):
    """
    Match rows whose period overlaps the window ``[from_source, to_source)``.

    Window bounds and row values are ISO local date-times. A row without an end (or a filter
    without ``end_path``) is a point in time, so ``OVERLAP`` behaves as a padded
    ``START_WITHIN``. An unset bound leaves that side of the window open.

    Args:
        start_path: Field path to each row's period start.
        from_source: Model named value supplying the window start, or ``None`` for open.
        to_source: Model named value supplying the window end, or ``None`` for open.
        end_path: Field path to each row's period end; ``None`` treats rows as points in time.
        mode: Whether to match overlapping periods or periods starting within the window.
        pad_before: Widens the window start (``OVERLAP`` mode only).
        pad_after: Widens the window end (``OVERLAP`` mode only).
    """

    def __init__(  # noqa: PLR0913, PLR0917
        self,
        start_path: list[str],
        from_source: Parameter | Calculation | None,
        to_source: Parameter | Calculation | None,
        end_path: list[str] | None = None,
        mode: OverlapMode = OverlapMode.OVERLAP,
        pad_before: timedelta | None = None,
        pad_after: timedelta | None = None,
    ):
        if mode == OverlapMode.START_WITHIN and (pad_before is not None or pad_after is not None):
            raise ValueError("Padding only applies to OVERLAP mode")
        self.start_path = start_path
        self.end_path = end_path
        self.mode = mode
        self.from_source = Reference(from_source) if from_source is not None else None
        self.to_source = Reference(to_source) if to_source is not None else None
        self.pad_before = iso_duration(pad_before) if pad_before is not None else None
        self.pad_after = iso_duration(pad_after) if pad_after is not None else None

    @property
    def type(self) -> DataFilterType:
        return DataFilterType.OVERLAP
