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
Gantt scheduler view for the UI Generator framework.

A `SchedulerView` draws the rows of a task table as cards on a timeline. Tasks are grouped into
nested **levels** (for example Site → Team → Role); the last level's values are the lines the
cards sit on. Users drag cards to move or resize them, drag across lines to reassign them, drag
resources from a side pane onto tasks to allocate them, and drag unscheduled tasks onto the
timeline to place them.

A scheduler is composed of:
    - A **task definition** (`SchedulerTaskDefinition`): the start and end fields, the card
      template, which edits are allowed, the events fired on change, and per-task
      backgrounds that block or recommend time.
    - One or more **levels** (`SchedulerLevel`), each grouping tasks by a field.
    - A **time axis** (`SchedulerTimeAxis`): the zoom scales, working time and sessions.
    - Optional **statistics** strips (`SchedulerStatistics`), **table backgrounds**
      (`SchedulerTableBackground`), a **resource pane** (`SchedulerResourcePane`), an
      **unscheduled pane** (`SchedulerUnscheduledPane`), **layouts** (`SchedulerLayout`) and
      **drag feedback** (`DropValidity`, `DropValidityOverlay`).

Settings are checked as they are made: each ``set_*``/``add_*`` raises ``ValueError`` as soon
as a setting cannot be valid (a field on the wrong table, the wrong data type, an unknown card
template, ...). Rules that depend on several settings, or on the rest of the UI (context
variables, modals, filters, other schedulers), are checked by `SchedulerView.validate`, which
`UiBuilder.build` runs for every scheduler; a scheduler with problems raises
`SchedulerValidationError` listing all of them. The rules mirror the platform's own, so a model
that builds here uploads cleanly.

Example:
    >>> model = ModelBuilder()
    >>> crews = model.add_data_table("Crews")
    >>> crews.add_data_field("Name", DataType.STRING)
    >>> jobs = model.add_data_table("Jobs")
    >>> jobs.set_id_field("ID")
    >>> jobs.add_data_field("ID", DataType.STRING)
    >>> jobs.add_data_field("Start", DataType.DATETIME)
    >>> jobs.add_data_field("End", DataType.DATETIME)
    >>> jobs.add_object_reference_field("Crew", crews)
    >>>
    >>> ui = UiBuilder()
    >>> scheduler = ui.add_scheduler_view(jobs, display_name="Schedule")
    >>> scheduler.add_card_template("job", Card())
    >>> scheduler.set_task(jobs.get_field("Start"), jobs.get_field("End"), "job").set_allow_move()
    >>> scheduler.add_level(jobs.get_field("Crew")).set_label_field(crews.get_field("Name"))
    >>> scheduler.set_time_axis(
    ...     SchedulerTimeAxis([SchedulerScale.WEEK, SchedulerScale.DAY], SchedulerScale.WEEK)
    ... )
"""

import json
import re
from collections.abc import Sequence
from datetime import time
from enum import Enum
from typing import TYPE_CHECKING, Any

from daitum_model import DataType, Field, MapDataType, ObjectDataType, Table
from daitum_model.fields import ComboField, DataField
from typeguard import typechecked

from daitum_ui._buildable import Buildable, json_type_info
from daitum_ui._data import EditOverride
from daitum_ui._events import ActionType, ModelTransactionArgs, OpenModalArgs
from daitum_ui.base_view import BaseView
from daitum_ui.context_variable import ContextVariable, CVType
from daitum_ui.drop_validity import (
    DropOutcomes,
    DropValidity,
    DropValidityOverlay,
)
from daitum_ui.elements import Card
from daitum_ui.filter_component import FilterableView, FilterComponent
from daitum_ui.model_event import ModelEvent
from daitum_ui.template_binding_key import TemplateBindingKey
from daitum_ui.view_layout import ViewLayout

if TYPE_CHECKING:
    from daitum_ui.ui_builder import UiBuilder

Problems = list[tuple[str, str]]

# ---------------------------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------------------------


class SchedulerScale(Enum):
    """
    A zoom level of the time axis. Each scale fixes the period shown and the snap increment.

    Attributes:
        YEAR: A year, in months.
        MONTH: A month, in days.
        WEEK: A week of seven days.
        WORK_WEEK: The working days of a week (needs `WorkingTime`).
        DAY: A day, in hours.
        WORK_DAY: The working hours of a day (needs `WorkingTime`).
    """

    YEAR = "YEAR"
    MONTH = "MONTH"
    WEEK = "WEEK"
    WORK_WEEK = "WORK_WEEK"
    DAY = "DAY"
    WORK_DAY = "WORK_DAY"


class Weekday(Enum):
    """A day of the week, used by `WorkingTime`."""

    MONDAY = "MONDAY"
    TUESDAY = "TUESDAY"
    WEDNESDAY = "WEDNESDAY"
    THURSDAY = "THURSDAY"
    FRIDAY = "FRIDAY"
    SATURDAY = "SATURDAY"
    SUNDAY = "SUNDAY"


class SchedulerLineFilter(Enum):
    """
    Which values of a level are drawn as lines.

    Attributes:
        ALL: Every row of the level's referenced table, even with no tasks (object reference
            levels only).
        WITH_TASKS: Values that have at least one task.
        IN_PERIOD: Values that have a task in the period on screen.
    """

    ALL = "ALL"
    WITH_TASKS = "WITH_TASKS"
    IN_PERIOD = "IN_PERIOD"


class SchedulerPane(Enum):
    """The side pane a scheduler opens on."""

    RESOURCES = "RESOURCES"
    UNSCHEDULED = "UNSCHEDULED"


class BackgroundEffect(Enum):
    """
    What a background range does to drops that land on it.

    Attributes:
        NONE: Drawn only; drops are unaffected.
        BLOCK: Drops are Not allowed.
        RECOMMEND: Drops are Recommended (task backgrounds only).
        ALLOW: Drops are Allowed even when the task's default background is BLOCK (task
            backgrounds only).
    """

    NONE = "NONE"
    BLOCK = "BLOCK"
    RECOMMEND = "RECOMMEND"
    ALLOW = "ALLOW"


class StatisticFormat(Enum):
    """
    How a statistics tile shows its value.

    Attributes:
        VALUE: The value alone.
        VALUE_OF_BASELINE: ``value of baseline`` (needs a baseline field).
        VALUE_AND_DIFFERENCE: The value and its difference from the baseline.
        VALUE_OVER_BASELINE: ``value / baseline``.
    """

    VALUE = "VALUE"
    VALUE_OF_BASELINE = "VALUE_OF_BASELINE"
    VALUE_AND_DIFFERENCE = "VALUE_AND_DIFFERENCE"
    VALUE_OVER_BASELINE = "VALUE_OVER_BASELINE"


class StatisticAggregation(Enum):
    """How statistics rows are combined into one tile at the current scale."""

    MAX = "MAX"
    SUM = "SUM"
    AVERAGE = "AVERAGE"
    MIN = "MIN"


class SchedulerValidationError(ValueError):
    """
    Raised when a scheduler cannot be built because its settings break platform rules.

    Attributes:
        problems: One message per problem, each naming the setting at fault.
    """

    def __init__(self, problems: list[str]):
        self.problems = problems
        super().__init__("Scheduler settings are invalid:\n  - " + "\n  - ".join(problems))


# ---------------------------------------------------------------------------------------------
# Field and value helpers
# ---------------------------------------------------------------------------------------------

_TIME_PATTERN = re.compile(r"^([01]\d|2[0-3]):[0-5]\d$")
_NUMERIC = ("INTEGER", "DECIMAL")
_TIME_KINDS = ("DATETIME", "TIME")
_VIEW_DROP_PARTS = frozenset({"timelineDrag", "rows", "canvas"})
_RESOURCE_DROP_PARTS = frozenset({"card"})


def _kind(field: Field) -> str:
    """The platform base type name of ``field`` (``OBJECT``, ``STRING_ARRAY``, ...)."""
    data_type = field.to_data_type()
    if isinstance(data_type, ObjectDataType):
        return "OBJECT_ARRAY" if data_type.is_array() else "OBJECT"
    if isinstance(data_type, MapDataType):
        return data_type.type
    if isinstance(data_type, DataType):
        return data_type.name
    return str(data_type)


def _referenced_table(field: Field) -> str | None:
    data_type = field.to_data_type()
    return data_type.table_id if isinstance(data_type, ObjectDataType) else None


def _is_editable(field: Field) -> bool:
    return isinstance(field, DataField | ComboField)


def _bracketed(reference: str | None) -> str | None:
    """The field id inside a ``[Field]`` card-template reference, or ``None`` for a key."""
    min_length = 3
    if reference and len(reference) >= min_length and reference[0] == "[" and reference[-1] == "]":
        return reference[1:-1]
    return None


def _blank(value: str | None) -> bool:
    return value is None or not value.strip()


def _fields_of(table: Table | None) -> dict[str, Field] | None:
    """The table's fields by id, or ``None`` when unknown (e.g. a model-less decode stub)."""
    if table is None:
        return None
    try:
        return {field.id: field for field in table.get_fields()}
    except (AttributeError, KeyError):
        return None


def _hhmm(value: str | time, what: str) -> str:
    """Normalise a time of day to the platform's ``HH:mm`` form."""
    if isinstance(value, time):
        if value.second or value.microsecond:
            raise ValueError(f"{what} must be a whole minute; got {value}.")
        return value.strftime("%H:%M")
    if not _TIME_PATTERN.match(value):
        raise ValueError(f"{what} '{value}' is not a time in HH:mm.")
    return value


def _parse_hhmm(value: str | None) -> time | None:
    if value is None or not _TIME_PATTERN.match(value):
        return None
    return time(int(value[:2]), int(value[3:]))


def _raise_if(problems: Problems) -> None:
    if problems:
        raise ValueError("; ".join(f"{path}: {problem}" for path, problem in problems))


def _check_on_table(field: Field, table_id: str, what: str) -> None:
    if field.table_id != table_id:
        raise ValueError(
            f"{what} '{field.id}' must be a field of table '{table_id}', not '{field.table_id}'."
        )


def _check_kind(field: Field, what: str, *kinds: str) -> None:
    if _kind(field) not in kinds:
        expected = " or ".join(kinds)
        raise ValueError(f"{what} '{field.id}' must be a {expected} field; got {_kind(field)}.")


def _check_reference_to(field: Field, table_id: str, what: str, *, as_list: bool) -> None:
    expected = "OBJECT_ARRAY" if as_list else "OBJECT"
    if _kind(field) != expected or _referenced_table(field) != table_id:
        noun = "a list of object references" if as_list else "an object reference"
        raise ValueError(f"{what} '{field.id}' must be {noun} to '{table_id}'.")


def _edit_override(  # noqa: PLR0913, PLR0917
    displayed_table_id: str,
    target_field: Field,
    target_reference_field: Field | None,
    map_key_field: Field | None,
    required_reference_table: str | None,
    what: str,
) -> EditOverride:
    """
    Build an `EditOverride`, checking it writes somewhere the platform can write.

    ``target_reference_field`` (on the displayed table) points at the table holding
    ``target_field``; without it, ``target_field`` is on the displayed table itself.
    """
    target_table = displayed_table_id
    if target_reference_field is not None:
        _check_on_table(target_reference_field, displayed_table_id, f"{what} reference field")
        reference_table = _referenced_table(target_reference_field)
        if reference_table is None or _kind(target_reference_field) != "OBJECT":
            raise ValueError(
                f"{what} reference field '{target_reference_field.id}' must be an object reference."
            )
        target_table = reference_table
    _check_on_table(target_field, target_table, f"{what} target field")
    if not _is_editable(target_field):
        raise ValueError(
            f"{what} target field '{target_field.id}' is calculated, so it cannot be written."
        )
    if required_reference_table is not None and (
        _referenced_table(target_field) != required_reference_table
    ):
        raise ValueError(
            f"{what} target field '{target_field.id}' must be an object reference to "
            f"'{required_reference_table}'."
        )
    if map_key_field is not None:
        _check_on_table(map_key_field, displayed_table_id, f"{what} map key field")
    return EditOverride(
        target_reference_field.id if target_reference_field is not None else None,
        target_field.id,
        map_key_field.id if map_key_field is not None else None,
    )


def _actions(event: ModelEvent | None) -> list[Any]:
    return list(event.actions) if event is not None else []


def _transactions(event: ModelEvent | None) -> set[ActionType]:
    # Decoded events may carry the action type as its plain string value.
    return {
        ActionType(getattr(action.action_type, "value", action.action_type))
        for action in _actions(event)
        if isinstance(action, ModelTransactionArgs)
    }


def _modal_ids(event: ModelEvent | None) -> list[str]:
    return [a.modal_id for a in _actions(event) if isinstance(a, OpenModalArgs) and a.modal_id]


def _change_event_problems(path: str, event: ModelEvent | None) -> Problems:
    """
    Rules for events fired after the view has begun a transaction (move, resize, allocate, ...).

    The view begins the transaction itself, so the event must not, and something must end it:
    the event itself, or the close button of a modal it opens (checked with the UI).
    """
    if event is None:
        return []
    problems: Problems = []
    if ActionType.BEGIN in _transactions(event):
        problems.append(
            (
                path,
                "must not contain TRANSACTION BEGIN; the view begins the transaction itself "
                "(open modals with add_show_modal_action(..., transactional=False))",
            )
        )
    ends = {ActionType.COMMIT, ActionType.ROLLBACK} & _transactions(event)
    if not _modal_ids(event) and not ends:
        problems.append(
            (
                path,
                "never ends the transaction (add TRANSACTION COMMIT or ROLLBACK, or open a "
                "modal that does)",
            )
        )
    return problems


def _check_change_event(event: ModelEvent | None, what: str) -> None:
    _raise_if(_change_event_problems(what, event))


def _check_string_variable(variable: ContextVariable, what: str) -> None:
    if variable.type is not CVType.STRING or variable.is_array:
        raise ValueError(f"{what} '{variable.id}' must be a single STRING context variable.")


def _on_click_keys(card: Card) -> set[str]:
    """Every ``onClickKey`` used anywhere inside a card template."""
    keys: set[str] = set()

    def walk(node: Any) -> None:
        if isinstance(node, dict):
            for key, value in node.items():
                if key == "onClickKey" and isinstance(value, str):
                    keys.add(value)
                else:
                    walk(value)
        elif isinstance(node, list):
            for item in node:
                walk(item)

    walk(card.build())
    return keys


# ---------------------------------------------------------------------------------------------
# Time axis
# ---------------------------------------------------------------------------------------------


@typechecked
class SchedulerSession(Buildable):
    """
    The scheduler's sessions: named stretches of the day read from a model table, one per row,
    so they can differ by day.

    With sessions set, the DAY, WORK_DAY, WEEK and WORK_WEEK scales draw only the sessions,
    with a short gap between them, and label each one on a second header line. For each day
    the scheduler uses the rows whose ``date_field`` is that date if there are any, otherwise
    the rows whose ``day_of_week_field`` is that weekday, otherwise the rows with neither set.
    A day with no rows has no sessions.

    Attributes:
        source_table: Table of sessions.
        label_field: STRING session name shown on the time header.
        start_field: TIME session start.
        end_field: TIME session end; sessions cannot cross midnight.
        date_field: Optional DATE; the row applies to that date only.
        day_of_week_field: Optional STRING day of the week (``MONDAY`` to ``SUNDAY``); the row
            applies to that weekday.
    """

    def __init__(  # noqa: PLR0913
        self,
        source_table: Table,
        label_field: Field,
        start_field: Field,
        end_field: Field,
        *,
        date_field: Field | None = None,
        day_of_week_field: Field | None = None,
    ):
        """
        Args:
            source_table: Table of sessions.
            label_field: STRING session name on ``source_table``.
            start_field: TIME session start on ``source_table``.
            end_field: TIME session end on ``source_table``.
            date_field: Optional DATE field on ``source_table``.
            day_of_week_field: Optional STRING day-of-week field on ``source_table``.

        Raises:
            ValueError: If a field is not on ``source_table`` or has the wrong type.
        """
        table_id = source_table.id
        for what, field, kind in (
            ("Session label field", label_field, "STRING"),
            ("Session start field", start_field, "TIME"),
            ("Session end field", end_field, "TIME"),
            ("Session date field", date_field, "DATE"),
            ("Session day of week field", day_of_week_field, "STRING"),
        ):
            if field is not None:
                _check_on_table(field, table_id, what)
                _check_kind(field, what, kind)
        self._source_table: Table | None = source_table
        self.source_table = table_id
        self.label_field = label_field.id
        self.start_field = start_field.id
        self.end_field = end_field.id
        self.date_field = date_field.id if date_field is not None else None
        self.day_of_week_field = day_of_week_field.id if day_of_week_field is not None else None


@typechecked
class WorkingTime(Buildable):
    """
    The working days and hours of the week.

    Needed by the WORK_WEEK and WORK_DAY scales and by ``enforce_working_time``; otherwise it
    only shades non-working time. ``end`` at or before ``start`` means the working day ends the
    next day (for example 10:00 to 02:00).

    Attributes:
        days: The working days.
        start: Start of the working day, ``HH:mm``.
        end: End of the working day, ``HH:mm``.
    """

    def __init__(self, days: Sequence[Weekday], start: str | time, end: str | time):
        """
        Args:
            days: The working days; at least one.
            start: Start of the working day, as ``HH:mm`` or a ``datetime.time``.
            end: End of the working day, as ``HH:mm`` or a ``datetime.time``.

        Raises:
            ValueError: If ``days`` is empty or a time is not in ``HH:mm``.
        """
        if not days:
            raise ValueError("WorkingTime needs at least one day.")
        self.days: list[Weekday] = list(dict.fromkeys(days))
        self.start = _hhmm(start, "Working time start")
        self.end = _hhmm(end, "Working time end")


@typechecked
class SchedulerTimeAxis(Buildable):
    """
    The scheduler's time axis: its zoom scales, working time and sessions.

    Attributes:
        scales: Scales offered in the toolbar, in order; at least one, none repeated.
        default_scale: The scale the view opens on; one of ``scales``.
        show_navigation: Show the previous/next period controls.
        show_now_line: Draw a vertical line at the current time.
        period_label: Toolbar text shown in place of the date range on a single-day (TIME)
            scheduler; ``None`` shows "Daily times" and ``""`` hides it.
        working_time: Working days and hours (see `WorkingTime`).
        enforce_working_time: Refuse drops outside working time.
        sessions: Sessions read from a model table, so they can differ by day.
        must_fit_session: Refuse drops that do not fit inside one session.
        sync_group: Schedulers sharing a sync group scroll and zoom together; they need
            identical time axes.
    """

    def __init__(  # noqa: PLR0913
        self,
        scales: Sequence[SchedulerScale],
        default_scale: SchedulerScale | None = None,
        *,
        show_navigation: bool = False,
        show_now_line: bool = False,
        period_label: str | None = None,
        working_time: WorkingTime | None = None,
        enforce_working_time: bool = False,
        sessions: SchedulerSession | None = None,
        must_fit_session: bool = False,
        sync_group: str | None = None,
    ):
        """
        Args:
            scales: Scales offered in the toolbar; at least one, none repeated.
            default_scale: The scale the view opens on; defaults to the first of ``scales``.
            show_navigation: Show the previous/next period controls.
            show_now_line: Draw a vertical line at the current time.
            period_label: Toolbar text in place of the date range when the task times are TIME;
                ``None`` shows "Daily times" and ``""`` hides it. Only for TIME schedulers.
            working_time: Working days and hours. Required by WORK_WEEK, WORK_DAY and
                ``enforce_working_time``.
            enforce_working_time: Refuse drops outside working time.
            sessions: Read the sessions from a model table (see `SchedulerSession`).
            must_fit_session: Refuse drops that do not fit inside one session; needs
                ``sessions``.
            sync_group: Name shared by schedulers that scroll and zoom together.

        Raises:
            ValueError: If the settings break any of the rules above.
        """
        self.scales: list[SchedulerScale] = list(scales)
        self.default_scale = default_scale if default_scale is not None else _first(scales)
        self.show_navigation = show_navigation
        self.show_now_line = show_now_line
        self.period_label = period_label
        self.working_time = working_time
        self.enforce_working_time = enforce_working_time
        self.sessions = sessions
        self.must_fit_session = must_fit_session
        self.sync_group = sync_group
        _raise_if(self._problems("timeAxis"))

    def set_sessions(self, sessions: SchedulerSession) -> "SchedulerTimeAxis":
        """
        Read the sessions from a model table, so they can differ by day.

        Returns:
            This `SchedulerTimeAxis`, for fluent chaining.
        """
        self.sessions = sessions
        return self

    def _problems(self, path: str) -> Problems:
        problems: Problems = []
        scales = self.scales
        if not scales:
            problems.append((f"{path}.scales", "needs at least one scale"))
        elif len(set(scales)) != len(scales):
            problems.append((f"{path}.scales", f"must not repeat a scale {_names(scales)}"))
        if self.default_scale is None:
            problems.append((f"{path}.defaultScale", "is required"))
        elif scales and self.default_scale not in scales:
            problems.append(
                (
                    f"{path}.defaultScale",
                    f"{self.default_scale.value} is not one of timeAxis.scales {_names(scales)}",
                )
            )
        if self.working_time is None:
            if {SchedulerScale.WORK_WEEK, SchedulerScale.WORK_DAY} & set(scales):
                problems.append(
                    (f"{path}.workingTime", "is required by the WORK_WEEK and WORK_DAY scales")
                )
            if self.enforce_working_time:
                problems.append((f"{path}.workingTime", "is required by enforceWorkingTime"))
        else:
            problems += _working_time_problems(f"{path}.workingTime", self.working_time)
        if self.must_fit_session and self.sessions is None:
            problems.append((f"{path}.mustFitSession", "needs timeAxis.sessions"))
        return problems

    def _same_as(self, other: "SchedulerTimeAxis") -> bool:
        def key(axis: SchedulerTimeAxis) -> str:
            built = axis.build()
            built.pop("syncGroup", None)
            built.pop("periodLabel", None)
            working = built.get("workingTime")
            if working is not None:
                working["days"] = sorted(working.get("days", []))
            return json.dumps(built, sort_keys=True)

        return key(self) == key(other)


def _first(scales: Sequence[SchedulerScale]) -> SchedulerScale | None:
    return scales[0] if scales else None


def _names(scales: Sequence[SchedulerScale]) -> str:
    return "[" + ", ".join(scale.value for scale in scales) + "]"


def _working_time_problems(path: str, working_time: WorkingTime) -> Problems:
    problems: Problems = []
    if not working_time.days:
        problems.append((f"{path}.days", "needs at least one day"))
    for name in ("start", "end"):
        value = getattr(working_time, name)
        if _parse_hhmm(value) is None:
            problems.append((f"{path}.{name}", f"'{value}' is not a time in HH:mm"))
    return problems


# ---------------------------------------------------------------------------------------------
# Statistics and backgrounds
# ---------------------------------------------------------------------------------------------


@typechecked
class SchedulerStatistics(Buildable):
    """
    A strip of statistics tiles above the timeline, read from a time-bucketed table.

    Each row of ``source_table`` is one bucket of time with a value and a status. For a level's
    strip, the table also carries one column per level up to and including that level, named
    and typed like the task table's level fields (an object reference level is matched by an
    object reference to the same table); the total strip carries none.

    Attributes:
        source_table: Table of time buckets.
        bucket_start_field: Bucket start; same type as the task start (DATETIME or TIME).
        bucket_end_field: Bucket end; same type as the task start.
        value_field: Numeric value shown in the tile.
        baseline_field: Optional numeric baseline the value is compared with.
        status_field: STRING status colouring the tile (``OK``, ``WARNING``, ``ERROR``,
            ``INFO``).
        format: How the value is shown; anything but VALUE needs ``baseline_field``.
        aggregation: How buckets are combined into one tile at the current scale.
    """

    def __init__(  # noqa: PLR0913
        self,
        source_table: Table,
        bucket_start_field: Field,
        bucket_end_field: Field,
        value_field: Field,
        status_field: Field,
        *,
        baseline_field: Field | None = None,
        format: StatisticFormat | None = None,  # noqa: A002
        aggregation: StatisticAggregation | None = None,
    ):
        """
        Args:
            source_table: Table of time buckets.
            bucket_start_field: Bucket start field (DATETIME or TIME) on ``source_table``.
            bucket_end_field: Bucket end field, the same type as ``bucket_start_field``.
            value_field: Numeric value field on ``source_table``.
            status_field: STRING status field on ``source_table``.
            baseline_field: Optional numeric baseline field on ``source_table``.
            format: How the value is shown; anything but VALUE needs ``baseline_field``.
            aggregation: How buckets are combined into one tile.

        Raises:
            ValueError: If a field is not on ``source_table`` or has the wrong type, or
                ``format`` needs a baseline that is missing.
        """
        table_id = source_table.id
        for what, field in (
            ("Statistics bucket start field", bucket_start_field),
            ("Statistics bucket end field", bucket_end_field),
            ("Statistics value field", value_field),
            ("Statistics status field", status_field),
        ):
            _check_on_table(field, table_id, what)
        _check_kind(bucket_start_field, "Statistics bucket start field", *_TIME_KINDS)
        if _kind(bucket_end_field) != _kind(bucket_start_field):
            raise ValueError(
                f"Statistics bucket end field '{bucket_end_field.id}' must be "
                f"{_kind(bucket_start_field)}, like the bucket start field."
            )
        _check_kind(value_field, "Statistics value field", *_NUMERIC)
        _check_kind(status_field, "Statistics status field", "STRING")
        if baseline_field is not None:
            _check_on_table(baseline_field, table_id, "Statistics baseline field")
            _check_kind(baseline_field, "Statistics baseline field", *_NUMERIC)
        elif format not in (None, StatisticFormat.VALUE):
            raise ValueError(f"Statistics format {format.value} needs a baseline_field.")
        self._source_table: Table | None = source_table
        self.source_table = table_id
        self.bucket_start_field = bucket_start_field.id
        self.bucket_end_field = bucket_end_field.id
        self.value_field = value_field.id
        self.baseline_field = baseline_field.id if baseline_field is not None else None
        self.status_field = status_field.id
        self.format = format
        self.aggregation = aggregation


@typechecked
class SchedulerBackground(Buildable):
    """
    A task background: time ranges stored on each task that block, recommend or allow drops.

    The ranges are read from list fields on the task table, paired by position: the n-th start,
    end, label and status describe the n-th range. They apply while that task is dragged.
    Create these with `SchedulerTaskDefinition.add_background`.

    Attributes:
        start_field: DATETIME_ARRAY (or TIME_ARRAY) of range starts, matching the task start.
        end_field: List of range ends, the same type as ``start_field``.
        label_field: Optional STRING_ARRAY of range labels.
        status_field: Optional STRING_ARRAY of range statuses.
        effect: What the ranges do to drops.
    """

    def __init__(  # noqa: PLR0913
        self,
        start_field: Field,
        end_field: Field,
        effect: BackgroundEffect,
        *,
        label_field: Field | None = None,
        status_field: Field | None = None,
    ):
        """
        Args:
            start_field: List field of range starts on the task table.
            end_field: List field of range ends on the task table.
            effect: What the ranges do to drops.
            label_field: Optional STRING_ARRAY of range labels on the task table.
            status_field: Optional STRING_ARRAY of range statuses on the task table.

        Raises:
            ValueError: If the fields are not on one table or have the wrong types.
        """
        table_id = start_field.table_id
        _check_kind(start_field, "Task background start field", "DATETIME_ARRAY", "TIME_ARRAY")
        _check_on_table(end_field, table_id, "Task background end field")
        _check_kind(end_field, "Task background end field", _kind(start_field))
        for what, field in (
            ("Task background label field", label_field),
            ("Task background status field", status_field),
        ):
            if field is not None:
                _check_on_table(field, table_id, what)
                _check_kind(field, what, "STRING_ARRAY")
        self.start_field = start_field.id
        self.end_field = end_field.id
        self.label_field = label_field.id if label_field is not None else None
        self.status_field = status_field.id if status_field is not None else None
        self.effect = effect


@typechecked
class SchedulerTableBackground(SchedulerBackground):
    """
    A table background: time ranges from their own table, drawn behind the lines they match.

    Each row of ``source_table`` is one range. The table may carry columns for the first levels,
    in order, named and typed like the task table's level fields; a range then applies only to
    the matching lines. Only NONE and BLOCK are allowed here. Create these with
    `SchedulerView.add_background`.

    Attributes:
        source_table: Table of ranges.
        start_field: Range start; same type as the task start (DATETIME or TIME).
        end_field: Range end; same type as ``start_field``.
        label_field: Optional STRING label.
        status_field: Optional STRING status.
        effect: NONE (drawn only) or BLOCK (drops refused).
    """

    def __init__(  # noqa: PLR0913  # pylint: disable=super-init-not-called
        self,
        source_table: Table,
        start_field: Field,
        end_field: Field,
        effect: BackgroundEffect = BackgroundEffect.BLOCK,
        *,
        label_field: Field | None = None,
        status_field: Field | None = None,
    ):
        """
        Args:
            source_table: Table of ranges.
            start_field: Range start field (DATETIME or TIME) on ``source_table``.
            end_field: Range end field, the same type as ``start_field``.
            effect: NONE or BLOCK.
            label_field: Optional STRING label field on ``source_table``.
            status_field: Optional STRING status field on ``source_table``.

        Raises:
            ValueError: If ``effect`` is RECOMMEND or ALLOW, or a field is not on
                ``source_table`` or has the wrong type.
        """
        if effect in (BackgroundEffect.RECOMMEND, BackgroundEffect.ALLOW):
            raise ValueError(
                f"{effect.value} is only allowed on task backgrounds; use NONE or BLOCK here."
            )
        table_id = source_table.id
        _check_on_table(start_field, table_id, "Background start field")
        _check_kind(start_field, "Background start field", *_TIME_KINDS)
        _check_on_table(end_field, table_id, "Background end field")
        _check_kind(end_field, "Background end field", _kind(start_field))
        for what, field in (
            ("Background label field", label_field),
            ("Background status field", status_field),
        ):
            if field is not None:
                _check_on_table(field, table_id, what)
                _check_kind(field, what, "STRING")
        self._source_table: Table | None = source_table
        self.start_field = start_field.id
        self.end_field = end_field.id
        self.label_field = label_field.id if label_field is not None else None
        self.status_field = status_field.id if status_field is not None else None
        self.effect = effect
        self.source_table = table_id


# ---------------------------------------------------------------------------------------------
# Task definition
# ---------------------------------------------------------------------------------------------


@typechecked
class SchedulerTaskDefinition(Buildable):
    """
    How the task table's rows are drawn and edited. Create with `SchedulerView.set_task`.

    Attributes:
        start_field: Task start, DATETIME or TIME.
        end_field: Task end, the same type as ``start_field``.
        start_edit_override: Where a move or resize writes the start, when ``start_field``
            is calculated or lives on another table.
        end_edit_override: As ``start_edit_override``, for the end.
        card_template: A key of the view's card templates, or ``[Field]`` naming a STRING
            field holding the key per task.
        model_event_mappings: Events fired by ``on_click_key`` elements in the task cards.
        allow_move: Cards can be dragged in time and across lines.
        allow_resize: Card edges can be dragged.
        editable_field: Optional BOOLEAN field; only tasks where it is true can be dragged.
        on_move: Event fired after a move (the view begins the transaction).
        on_resize: Event fired after a resize (the view begins the transaction).
        on_double_click_row: Event fired by double-clicking an empty part of a line.
        double_click_time_context_variable: STRING context variable receiving the clicked time.
        backgrounds: Task backgrounds applied while a task is dragged.
        default_background: ALLOW (drops are allowed unless blocked) or BLOCK (drops are refused
            unless an ALLOW or RECOMMEND background covers them).
    """

    def __init__(self, start_field: Field, end_field: Field, card_template: str | Field):
        """
        Args:
            start_field: Task start field, DATETIME or TIME.
            end_field: Task end field on the same table, the same type as ``start_field``.
            card_template: A card template key, or a STRING field holding the key per task.

        Raises:
            ValueError: If the fields are on different tables or have the wrong types, or
                ``card_template`` is blank or a non-STRING field.
        """
        table_id = start_field.table_id
        _check_kind(start_field, "Task start field", *_TIME_KINDS)
        _check_on_table(end_field, table_id, "Task end field")
        _check_kind(end_field, "Task end field", _kind(start_field))
        self._table_id: str | None = table_id
        self._time_kind: str | None = _kind(start_field)
        self.start_field = start_field.id
        self.end_field = end_field.id
        self.start_edit_override: EditOverride | None = None
        self.end_edit_override: EditOverride | None = None
        self.card_template = _template_reference(card_template, table_id, "Task card template")
        self.model_event_mappings: dict[str, ModelEvent] = {}
        self.allow_move = False
        self.allow_resize = False
        self.editable_field: str | None = None
        self.on_move: ModelEvent | None = None
        self.on_resize: ModelEvent | None = None
        self.on_double_click_row: ModelEvent | None = None
        self.double_click_time_context_variable: str | None = None
        self.backgrounds: list[SchedulerBackground] = []
        self.default_background: BackgroundEffect | None = None

    def set_allow_move(
        self, allow: bool = True, on_move: ModelEvent | None = None
    ) -> "SchedulerTaskDefinition":
        """
        Let users drag cards in time and across lines.

        Args:
            allow: Whether cards can be moved.
            on_move: Optional event fired after a move, inside the transaction the view begins.
                It must not begin a transaction itself and must end it, directly or through
                the close button of a modal it opens.

        Returns:
            This `SchedulerTaskDefinition`, for fluent chaining.
        """
        _check_change_event(on_move, "task.onMove")
        self.allow_move = allow
        self.on_move = on_move
        return self

    def set_allow_resize(
        self, allow: bool = True, on_resize: ModelEvent | None = None
    ) -> "SchedulerTaskDefinition":
        """
        Let users drag card edges to change a task's start or end.

        Args:
            allow: Whether cards can be resized.
            on_resize: Optional event fired after a resize; the same rules as ``on_move``.

        Returns:
            This `SchedulerTaskDefinition`, for fluent chaining.
        """
        _check_change_event(on_resize, "task.onResize")
        self.allow_resize = allow
        self.on_resize = on_resize
        return self

    def set_start_edit_override(
        self,
        target_field: Field,
        target_reference_field: Field | None = None,
        map_key_field: Field | None = None,
    ) -> "SchedulerTaskDefinition":
        """
        Write moved and resized starts somewhere other than ``start_field``.

        Needed when ``start_field`` is calculated. Without ``target_reference_field``,
        ``target_field`` is another field on the task table; with it, ``target_field`` is on
        the table that reference points at.

        Returns:
            This `SchedulerTaskDefinition`, for fluent chaining.
        """
        self.start_edit_override = self._override(
            target_field, target_reference_field, map_key_field, "Task start edit override"
        )
        return self

    def set_end_edit_override(
        self,
        target_field: Field,
        target_reference_field: Field | None = None,
        map_key_field: Field | None = None,
    ) -> "SchedulerTaskDefinition":
        """
        Write moved and resized ends somewhere other than ``end_field``.

        See `set_start_edit_override`.

        Returns:
            This `SchedulerTaskDefinition`, for fluent chaining.
        """
        self.end_edit_override = self._override(
            target_field, target_reference_field, map_key_field, "Task end edit override"
        )
        return self

    def add_model_event_mapping(
        self, key: TemplateBindingKey | str, event: ModelEvent
    ) -> "SchedulerTaskDefinition":
        """
        Fire ``event`` when a task card element with ``on_click_key == key`` is clicked.

        Returns:
            This `SchedulerTaskDefinition`, for fluent chaining.
        """
        name = key.to_string() if isinstance(key, TemplateBindingKey) else key
        if _blank(name):
            raise ValueError("A model event mapping key is required.")
        self.model_event_mappings[name] = event
        return self

    def set_editable_field(self, field: Field) -> "SchedulerTaskDefinition":
        """
        Only let tasks be dragged where ``field`` (a BOOLEAN on the task table) is true.

        Returns:
            This `SchedulerTaskDefinition`, for fluent chaining.
        """
        self._check_task_field(field, "Task editable field")
        _check_kind(field, "Task editable field", "BOOLEAN")
        self.editable_field = field.id
        return self

    def set_on_double_click_row(
        self, event: ModelEvent, time_context_variable: ContextVariable
    ) -> "SchedulerTaskDefinition":
        """
        Fire ``event`` when an empty part of a line is double-clicked (for example to add a
        task there).

        Before the event fires, the clicked time is written to ``time_context_variable`` and
        each level's value to that level's context variable — so every level needs one (see
        `SchedulerLevel.set_context_variable`).

        Args:
            event: The event to fire.
            time_context_variable: A single STRING context variable receiving the time.

        Returns:
            This `SchedulerTaskDefinition`, for fluent chaining.
        """
        _check_string_variable(time_context_variable, "Double-click time context variable")
        self.on_double_click_row = event
        self.double_click_time_context_variable = time_context_variable.id
        return self

    def add_background(  # noqa: PLR0913
        self,
        start_field: Field,
        end_field: Field,
        effect: BackgroundEffect,
        *,
        label_field: Field | None = None,
        status_field: Field | None = None,
    ) -> SchedulerBackground:
        """
        Add a task background: per-task time ranges that block, recommend or allow drops.

        Args:
            start_field: List of range starts on the task table — DATETIME_ARRAY when the task
                times are DATETIME, TIME_ARRAY when they are TIME.
            end_field: List of range ends, the same type as ``start_field``.
            effect: What the ranges do to drops.
            label_field: Optional STRING_ARRAY of labels, paired with the times by position.
            status_field: Optional STRING_ARRAY of statuses, paired by position.

        Returns:
            The new `SchedulerBackground`.
        """
        self._check_task_field(start_field, "Task background start field")
        background = SchedulerBackground(
            start_field, end_field, effect, label_field=label_field, status_field=status_field
        )
        expected = self._list_time_kind()
        if expected is not None and _kind(start_field) != expected:
            raise ValueError(
                f"Task background start field '{start_field.id}' must be {expected}, a list of "
                "the task's start and end type."
            )
        self.backgrounds.append(background)
        return background

    def set_default_background(self, effect: BackgroundEffect) -> "SchedulerTaskDefinition":
        """
        Choose whether time is allowed or blocked unless a task background says otherwise.

        Args:
            effect: ALLOW, or BLOCK — which then needs an ALLOW or RECOMMEND task background,
                or no drop could ever pass (checked when the view is validated).

        Returns:
            This `SchedulerTaskDefinition`, for fluent chaining.
        """
        if effect not in (BackgroundEffect.ALLOW, BackgroundEffect.BLOCK):
            raise ValueError("The default task background must be ALLOW or BLOCK.")
        self.default_background = effect
        return self

    def _check_task_field(self, field: Field, what: str) -> None:
        if self._table_id is not None:
            _check_on_table(field, self._table_id, what)

    def _list_time_kind(self) -> str | None:
        time_kind = getattr(self, "_time_kind", None)
        return f"{time_kind}_ARRAY" if time_kind is not None else None

    def _override(
        self,
        target_field: Field,
        target_reference_field: Field | None,
        map_key_field: Field | None,
        what: str,
    ) -> EditOverride:
        table_id = self._table_id or target_field.table_id
        return _edit_override(
            table_id, target_field, target_reference_field, map_key_field, None, what
        )


def _template_reference(reference: str | Field, table_id: str, what: str) -> str:
    """A card-template key, or ``[Field]`` for a STRING field on ``table_id`` holding the key."""
    if isinstance(reference, Field):
        _check_on_table(reference, table_id, what)
        _check_kind(reference, what, "STRING")
        return reference.to_string()
    if _blank(reference):
        raise ValueError(f"{what} is required.")
    return reference


# ---------------------------------------------------------------------------------------------
# Levels
# ---------------------------------------------------------------------------------------------


@typechecked
class SchedulerLevel(Buildable):
    """
    One grouping of tasks by a field of the task table. Create with `SchedulerView.add_level`.

    The level field is either:

    - an **object reference** — lines are rows of the referenced table, which supply labels,
      summaries and the other reference-only options below;
    - a **list of object references** — a task appears on every line it lists (it cannot be
      moved across lines); or
    - a **single value** (STRING, INTEGER, ...) — lines are the distinct values.

    Summaries, their status and always-show come from the referenced table, which has one row
    per value whatever its parent lines. When they depend on the parent lines (a role's count
    within one site and team), or the level is a single value, give the level a line table
    (`set_line_table`): one row per line, joined by columns named after the level fields.

    Attributes:
        field: The task field the level groups by.
        edit_override: Where moving across lines writes the new value, when ``field`` is
            calculated or lives on another table.
        label_field: Field of the referenced table labelling each line (reference levels).
        line_table: Table with one row per line of this level, joined by columns named after
            the level fields up to and including this one; it carries the summary, status and
            always-show fields.
        summary_field: STRING field shown under the label, on ``line_table`` if set, otherwise
            on the referenced table.
        summary_status_field: STRING status colouring the summary.
        null_label: Label of the line holding tasks whose level value is blank.
        show_lines: Which values are drawn as lines.
        always_show_field: BOOLEAN field of ``line_table`` if set, otherwise of the referenced
            table; lines where it is true are always drawn.
        statistics: A statistics strip per line of this level.
        collapsible: Lines of this level can be collapsed.
        default_collapsed: Lines start collapsed.
        allow_move_across: Cards can be dragged onto another line of this level.
        allowed_values_field: OBJECT_ARRAY field of the task table listing the lines a task may
            be moved to (single reference levels).
        on_move_across: Event fired after a move across lines (the view begins the transaction).
        on_add: Event fired by the line's add button.
        context_variable: STRING context variable receiving this level's value before
            ``on_add`` or ``task.on_double_click_row`` fire.
    """

    def __init__(self, field: Field):
        """
        Args:
            field: The task field to group by: an object reference, a list of object
                references, or a single (non-list, non-map) value.

        Raises:
            ValueError: If ``field`` is a list of values or a map.
        """
        kind = _kind(field)
        if kind != "OBJECT_ARRAY" and (kind.endswith(("_ARRAY", "_MAP"))):
            raise ValueError(
                f"Level field '{field.id}' must be an object reference, a list of object "
                f"references or a single value; got {kind}."
            )
        self._kind: str | None = kind
        self._referenced: str | None = _referenced_table(field)
        self._task_table_id: str | None = field.table_id
        self.field = field.id
        self.edit_override: EditOverride | None = None
        self._line_table: Table | None = None
        self.label_field: str | None = None
        self.line_table: str | None = None
        self.summary_field: str | None = None
        self.summary_status_field: str | None = None
        self.null_label: str | None = None
        self.show_lines: SchedulerLineFilter | None = None
        self.always_show_field: str | None = None
        self.statistics: SchedulerStatistics | None = None
        self.collapsible = False
        self.default_collapsed = False
        self.allow_move_across = False
        self.allowed_values_field: str | None = None
        self.on_move_across: ModelEvent | None = None
        self.on_add: ModelEvent | None = None
        self.context_variable: str | None = None

    def set_label_field(self, field: Field) -> "SchedulerLevel":
        """Label each line with ``field`` of the referenced table. Returns self."""
        self._check_reference_field(field, "Level label field")
        self.label_field = field.id
        return self

    def set_line_table(self, table: Table) -> "SchedulerLevel":
        """
        Read this level's summary, status and always-show fields from ``table``.

        ``table`` has one row per line, joined by columns named after the level fields up to and
        including this one (as statistics tables are): a role line under site North and team
        Electrical is the row whose Site, Team and Role columns hold those values. Rows with a
        blank level column are ignored; when several rows match a line the first wins. With
        ``showLines`` ALL every row is drawn, and a drawn row also draws its parent lines.

        Call it before `set_summary` and `set_always_show_field`. Works on reference and
        single-value levels; not on a list level. Returns self.

        Raises:
            ValueError: On a list level, or when a summary or always-show field is already set.
        """
        if self._kind == "OBJECT_ARRAY":
            raise ValueError(f"Level '{self.field}' is a list level; it cannot have a line table.")
        if self.summary_field is not None or self.always_show_field is not None:
            raise ValueError(
                "Set the line table before the summary and always-show fields, which it carries."
            )
        self._line_table = table
        self.line_table = table.id
        return self

    def set_summary(
        self, summary_field: Field, status_field: Field | None = None
    ) -> "SchedulerLevel":
        """
        Show a STRING summary under each line's label, optionally coloured by a STRING status.

        Both fields belong to the line table if one is set, otherwise to the referenced table
        (which needs a reference level). Returns self.
        """
        self._check_line_field(summary_field, "Level summary field")
        _check_kind(summary_field, "Level summary field", "STRING")
        if status_field is not None:
            self._check_line_field(status_field, "Level summary status field")
            _check_kind(status_field, "Level summary status field", "STRING")
        self.summary_field = summary_field.id
        self.summary_status_field = status_field.id if status_field is not None else None
        return self

    def set_null_label(self, label: str) -> "SchedulerLevel":
        """Label the line holding tasks whose level value is blank. Returns self."""
        self.null_label = label
        return self

    def set_show_lines(self, show_lines: SchedulerLineFilter) -> "SchedulerLevel":
        """
        Choose which values are drawn as lines. ALL draws every line table row, or every
        referenced row without one; it needs a reference level or a line table. Returns self.
        """
        if show_lines is SchedulerLineFilter.ALL and self.line_table is None:
            self._require_reference("showLines ALL", " or a line table")
        self.show_lines = show_lines
        return self

    def set_always_show_field(self, field: Field) -> "SchedulerLevel":
        """
        Always draw lines where BOOLEAN ``field`` is true; ``field`` is on the line table if one
        is set, otherwise on the referenced table. Returns self.
        """
        self._check_line_field(field, "Level always-show field")
        _check_kind(field, "Level always-show field", "BOOLEAN")
        self.always_show_field = field.id
        return self

    def set_statistics(self, statistics: SchedulerStatistics) -> "SchedulerLevel":
        """Show a statistics strip on each line of this level. Returns self."""
        self.statistics = statistics
        return self

    def set_collapsible(
        self, collapsible: bool = True, default_collapsed: bool = False
    ) -> "SchedulerLevel":
        """Let lines of this level be collapsed, optionally starting collapsed. Returns self."""
        if default_collapsed and not collapsible:
            raise ValueError("A level can only start collapsed if it is collapsible.")
        self.collapsible = collapsible
        self.default_collapsed = default_collapsed
        return self

    def set_allow_move_across(
        self, allow: bool = True, on_move_across: ModelEvent | None = None
    ) -> "SchedulerLevel":
        """
        Let cards be dragged onto another line of this level.

        Not available on a list level: the view never writes a list. ``on_move_across`` fires
        after the move inside the transaction the view begins — it must not begin one and must
        end it, directly or through a modal's close button. Returns self.
        """
        if self._kind == "OBJECT_ARRAY" and (allow or on_move_across is not None):
            raise ValueError(
                f"Level '{self.field}' is a list level; the view never writes it, so cards "
                "cannot be moved across its lines."
            )
        _check_change_event(on_move_across, f"Level '{self.field}' onMoveAcross")
        self.allow_move_across = allow
        self.on_move_across = on_move_across
        return self

    def set_edit_override(
        self,
        target_field: Field,
        target_reference_field: Field | None = None,
        map_key_field: Field | None = None,
    ) -> "SchedulerLevel":
        """
        Write a move across lines somewhere other than the level field.

        For a reference level, ``target_field`` must reference the same table as the level
        field (the line's row is what gets written). Returns self.
        """
        self.edit_override = _edit_override(
            self._task_table_id or target_field.table_id,
            target_field,
            target_reference_field,
            map_key_field,
            self._referenced,
            "Level edit override",
        )
        return self

    def set_allowed_values_field(self, field: Field) -> "SchedulerLevel":
        """
        Restrict the lines a task may be moved to.

        ``field`` is an OBJECT_ARRAY on the task table listing rows of the referenced table;
        only for a single object reference level. Returns self.
        """
        self._require_reference("allowedValuesField")
        if self._kind == "OBJECT_ARRAY":
            raise ValueError(
                "allowedValuesField is only allowed on a single object reference level."
            )
        if self._task_table_id is not None:
            _check_on_table(field, self._task_table_id, "Level allowed values field")
        if self._referenced is not None:
            _check_reference_to(field, self._referenced, "Level allowed values field", as_list=True)
        self.allowed_values_field = field.id
        return self

    def set_on_add(self, event: ModelEvent) -> "SchedulerLevel":
        """
        Show an add button on each line of this level that fires ``event``.

        This level and every level above it need a context variable (see
        `set_context_variable`); they receive the line's values before the event fires.
        Returns self.
        """
        self.on_add = event
        return self

    def set_context_variable(self, variable: ContextVariable) -> "SchedulerLevel":
        """Write this level's value to a single STRING context variable before events fire."""
        _check_string_variable(variable, "Level context variable")
        self.context_variable = variable.id
        return self

    def _require_reference(self, option: str, alternative: str = "") -> None:
        if self._kind is not None and self._kind not in ("OBJECT", "OBJECT_ARRAY"):
            raise ValueError(
                f"{option} needs an object reference level field{alternative}; "
                f"'{self.field}' is {self._kind}."
            )

    def _check_line_field(self, field: Field, what: str) -> None:
        if self.line_table is not None:
            _check_on_table(field, self.line_table, what)
        else:
            self._require_reference(what, " or a line table")
            if self._referenced is not None:
                _check_on_table(field, self._referenced, what)

    def _check_reference_field(self, field: Field, what: str) -> None:
        self._require_reference(what)
        if self._referenced is not None:
            _check_on_table(field, self._referenced, what)


# ---------------------------------------------------------------------------------------------
# Panes and layouts
# ---------------------------------------------------------------------------------------------


@typechecked
class SchedulerResourcePane(Buildable):
    """
    A side pane listing resources that can be dragged onto tasks to allocate them.

    Create with `SchedulerView.set_resource_pane`. The pane lists ``source_table``: either the
    resource table itself, or — when a card needs values the resource table cannot hold, such as
    rollups over the tasks — a derived table whose rows point at the resources through
    ``resource_reference_field``.

    Attributes:
        title: Pane tab title.
        source_table: The table the pane lists.
        resource_reference_field: OBJECT field of ``source_table`` referencing the resource
            table, when ``source_table`` is not the resource table itself. Rows with no
            reference are not listed; the first row per resource wins.
        card_template_key: Card template drawing each resource; may not use ``on_click_key``.
        use_filter: Filter applied to the resource list.
        task_resource_field: OBJECT reference on the task table, to the resource table, written
            on allocation.
        allocate_edit_override: Where an allocation writes, when ``task_resource_field`` is
            calculated or lives on another table.
        allowed_resources_field: OBJECT_ARRAY on the task table listing the resources a task
            accepts.
        filter_on_selection: With a task selected, list only its allowed resources.
        drag_label_field: Field of ``source_table`` shown on the drag card.
        on_allocate: Event fired after an allocation (the view begins the transaction).
        on_double_click: Optional event fired on double-clicking a resource card, with the
            card's row in ``source_table`` as the active row; for example to open a modal that
            edits it. With ``resource_reference_field``, reach the resource through that field.
        drop_validity: Drag feedback; only ``card`` (the target task outline) is supported.
    """

    def __init__(
        self,
        source_table: Table,
        card_template_key: str,
        task_resource_field: Field,
        title: str | None = None,
        resource_reference_field: Field | None = None,
    ):
        """
        Args:
            source_table: The table the pane lists: the resources, or a table pointing at them.
            card_template_key: Card template drawing each resource.
            task_resource_field: OBJECT reference on the task table to the resource table.
            title: Pane tab title.
            resource_reference_field: OBJECT field of ``source_table`` referencing the resource
                table; omit when ``source_table`` is the resource table.

        Raises:
            ValueError: If ``card_template_key`` is blank, ``resource_reference_field`` is not
                an object reference on ``source_table``, or ``task_resource_field`` does not
                reference the resource table.
        """
        if _blank(card_template_key):
            raise ValueError("The resource pane card template key is required.")
        resource_table = source_table.id
        if resource_reference_field is not None:
            what = "Resource pane resource reference field"
            _check_on_table(resource_reference_field, source_table.id, what)
            _check_kind(resource_reference_field, what, "OBJECT")
            resource_table = _referenced_table(resource_reference_field) or source_table.id
        _check_reference_to(
            task_resource_field, resource_table, "Resource pane task resource field", as_list=False
        )
        self._source_table: Table | None = source_table
        self._resource_table_id: str | None = resource_table
        self._task_table_id: str | None = task_resource_field.table_id
        self.title = title
        self.source_table = source_table.id
        self.resource_reference_field = (
            resource_reference_field.id if resource_reference_field is not None else None
        )
        self.card_template_key = card_template_key
        self.use_filter: str | None = None
        self.task_resource_field = task_resource_field.id
        self.allocate_edit_override: EditOverride | None = None
        self.allowed_resources_field: str | None = None
        self.filter_on_selection = False
        self.drag_label_field: str | None = None
        self.on_allocate: ModelEvent | None = None
        self.on_double_click: ModelEvent | None = None
        self.drop_validity: DropValidity | None = None

    def set_use_filter(self, use_filter: FilterComponent) -> "SchedulerResourcePane":
        """Filter the resource list with a registered `FilterComponent`. Returns self."""
        self.use_filter = use_filter.filter_name
        return self

    def set_allocate_edit_override(
        self,
        target_field: Field,
        target_reference_field: Field | None = None,
        map_key_field: Field | None = None,
    ) -> "SchedulerResourcePane":
        """
        Write allocations somewhere other than ``task_resource_field``.

        ``target_field`` must reference the resource table. Returns self.
        """
        self.allocate_edit_override = _edit_override(
            self._task_table_id or target_field.table_id,
            target_field,
            target_reference_field,
            map_key_field,
            self.resource_table,
            "Allocate edit override",
        )
        return self

    def set_allowed_resources_field(self, field: Field) -> "SchedulerResourcePane":
        """Restrict allocations to the resources listed in an OBJECT_ARRAY task field."""
        if self._task_table_id is not None:
            _check_on_table(field, self._task_table_id, "Allowed resources field")
        _check_reference_to(field, self.resource_table, "Allowed resources field", as_list=True)
        self.allowed_resources_field = field.id
        return self

    @property
    def resource_table(self) -> str:
        """The table tasks reference: what ``resource_reference_field`` references, or else
        ``source_table``."""
        known: str | None = getattr(self, "_resource_table_id", None)
        if known is not None:
            return known
        fields = _fields_of(getattr(self, "_source_table", None)) or {}
        reference = fields.get(self.resource_reference_field or "")
        referenced = _referenced_table(reference) if reference is not None else None
        return referenced or self.source_table

    def set_filter_on_selection(self, filter_on_selection: bool = True) -> "SchedulerResourcePane":
        """With a task selected, list only its allowed resources. Returns self."""
        self.filter_on_selection = filter_on_selection
        return self

    def set_drag_label_field(self, field: Field) -> "SchedulerResourcePane":
        """Show ``field`` of ``source_table`` on the drag card. Returns self."""
        _check_on_table(field, self.source_table, "Resource pane drag label field")
        self.drag_label_field = field.id
        return self

    def set_on_allocate(self, event: ModelEvent | None) -> "SchedulerResourcePane":
        """
        Fire ``event`` after an allocation, inside the transaction the view begins.

        It must not begin a transaction and must end it, directly or through the close button
        of a modal it opens. Returns self.
        """
        _check_change_event(event, "resourcePane.onAllocate")
        self.on_allocate = event
        return self

    def set_on_double_click(self, event: ModelEvent | None) -> "SchedulerResourcePane":
        """
        Fire ``event`` when a resource card is double-clicked, with the card's row in
        ``source_table`` as the active row, for example to open a modal editing it. With
        ``resource_reference_field``, reach the resource through that field.

        Nothing begins a transaction for it: one it begins must be ended, directly or through
        the close button of a modal it opens. ``None`` removes it. Returns self.
        """
        self.on_double_click = event
        return self

    def set_drop_validity(self, card: DropOutcomes | None) -> "SchedulerResourcePane":
        """
        Choose the outcomes outlined on the task under a dragged resource.

        Without this call every outcome is outlined.

        Args:
            card: The outcomes to colour, e.g. ``DropOutcomes(recommended=False)``; ``None``
                switches the outline off.

        Returns:
            This `SchedulerResourcePane`, for fluent chaining.
        """
        self.drop_validity = DropValidity(card=card) if card is not None else DropValidity()
        return self


@typechecked
class SchedulerUnscheduledPane(Buildable):
    """
    A side pane listing tasks with no start, which can be dragged onto the timeline.

    Placing a task writes its start, end and level fields. Create with
    `SchedulerView.set_unscheduled_pane`.

    Attributes:
        title: Pane tab title.
        card_template_key: Card template drawing each unscheduled task.
        duration_field: Numeric task field giving the length, in minutes, of a placed task.
        drag_label_field: Task field shown on the drag card.
        on_place: Event fired after a placement (the view begins the transaction).
        on_double_click: Optional event fired on double-clicking an unscheduled task card, with
            that task's row as the active row.
    """

    def __init__(self, card_template_key: str, duration_field: Field, title: str | None = None):
        """
        Args:
            card_template_key: Card template drawing each unscheduled task.
            duration_field: Numeric task field: the placed task's length in minutes.
            title: Pane tab title.

        Raises:
            ValueError: If ``card_template_key`` is blank or ``duration_field`` is not numeric.
        """
        if _blank(card_template_key):
            raise ValueError("The unscheduled pane card template key is required.")
        _check_kind(duration_field, "Unscheduled pane duration field", *_NUMERIC)
        self._task_table_id: str | None = duration_field.table_id
        self.title = title
        self.card_template_key = card_template_key
        self.duration_field = duration_field.id
        self.drag_label_field: str | None = None
        self.on_place: ModelEvent | None = None
        self.on_double_click: ModelEvent | None = None

    def set_drag_label_field(self, field: Field) -> "SchedulerUnscheduledPane":
        """Show ``field`` of the task table on the drag card. Returns self."""
        if self._task_table_id is not None:
            _check_on_table(field, self._task_table_id, "Unscheduled pane drag label field")
        self.drag_label_field = field.id
        return self

    def set_on_place(self, event: ModelEvent | None) -> "SchedulerUnscheduledPane":
        """Fire ``event`` after a placement; the same rules as `set_on_allocate`."""
        _check_change_event(event, "unscheduledPane.onPlace")
        self.on_place = event
        return self

    def set_on_double_click(self, event: ModelEvent | None) -> "SchedulerUnscheduledPane":
        """
        Fire ``event`` when an unscheduled task card is double-clicked, with the task's row as
        the active row; the same rules as `SchedulerResourcePane.set_on_double_click`.
        """
        self.on_double_click = event
        return self


@typechecked
class SchedulerLayout(ViewLayout):
    """
    A named presentation in the scheduler's Layout menu. Create with `SchedulerView.add_layout`.

    Settings left as ``None`` keep the view's own.

    Attributes:
        name: Shown in the Layout menu; unique within the view.
        card_template: Task card template in this layout: a key, or ``[Field]`` naming a STRING
            task field holding the key.
        resource_card_template_key: Resource pane card template in this layout.
        unscheduled_card_template_key: Unscheduled pane card template in this layout.
        hide_level_summaries: Show level lines with their label only — no summary or status.
    """

    def __init__(
        self,
        name: str,
        *,
        card_template: str | None = None,
        resource_card_template_key: str | None = None,
        unscheduled_card_template_key: str | None = None,
        hide_level_summaries: bool = False,
    ):
        """
        Args:
            name: Shown in the Layout menu; unique within the view.
            card_template: Task card template key, or ``[Field]`` reference.
            resource_card_template_key: Resource pane card template key.
            unscheduled_card_template_key: Unscheduled pane card template key.
            hide_level_summaries: Hide level summaries and statuses.
        """
        super().__init__(name)
        self.card_template = card_template
        self.resource_card_template_key = resource_card_template_key
        self.unscheduled_card_template_key = unscheduled_card_template_key
        self.hide_level_summaries = hide_level_summaries


# ---------------------------------------------------------------------------------------------
# The view
# ---------------------------------------------------------------------------------------------


@typechecked
@json_type_info("scheduler")
class SchedulerView(BaseView, FilterableView):
    """
    Gantt scheduler: tasks drawn as cards on a timeline, grouped into levels of lines.

    Create with `UiBuilder.add_scheduler_view`, then at least:

    1. register the card templates (`add_card_template`);
    2. describe the tasks (`set_task`);
    3. add one or more levels (`add_level`);
    4. set the time axis (`set_time_axis`).

    The task table needs an ``id_field`` (`Table.set_id_field`), which identifies tasks across
    reloads.

    Attributes:
        source_table: The task table.
        card_templates: Card templates by key, used by the task, the panes and the layouts.
        layouts: Named presentations offered in the Layout menu.
        default_layout: Name of the layout the view opens with.
        task: How tasks are drawn and edited.
        levels: Groupings of tasks, outermost first; the last level's values are the lines.
        levels_title: Heading over the level column.
        time_axis: Zoom scales, working time and sessions.
        total_label: Label of the total row.
        total_summary: Text under the total row's label; ``${Name}`` inserts the value of a
            named value or calculation.
        total_statistics: Statistics strip on the total row.
        backgrounds: Table backgrounds drawn behind the lines.
        resource_pane: Side pane of resources to allocate.
        unscheduled_pane: Side pane of tasks to place.
        default_pane: The pane the view opens on.
        drop_validity: Drag feedback; only ``timeline_drag`` is supported.
        drop_validity_overlay: Drag shading; ``rows`` and ``canvas`` are supported.
    """

    def __init__(
        self,
        source_table: Table,
        display_name: str | None = None,
        hidden: bool = False,
    ):
        """
        Args:
            source_table: The task table; it needs an ``id_field``.
            display_name: Optional name shown for the view.
            hidden: Whether the view is hidden.
        """
        BaseView.__init__(self, hidden)
        if display_name is not None:
            self._display_name = display_name
        FilterableView.__init__(self)
        self._source_table: Table | None = source_table
        self.source_table = source_table.id
        self.card_templates: dict[str, Card] = {}
        self.layouts: list[SchedulerLayout] = []
        self.default_layout: str | None = None
        self.task: SchedulerTaskDefinition | None = None
        self.levels: list[SchedulerLevel] = []
        self.levels_title: str | None = None
        self.time_axis: SchedulerTimeAxis | None = None
        self.total_label: str | None = None
        self.total_summary: str | None = None
        self.total_statistics: SchedulerStatistics | None = None
        self.backgrounds: list[SchedulerTableBackground] = []
        self.resource_pane: SchedulerResourcePane | None = None
        self.unscheduled_pane: SchedulerUnscheduledPane | None = None
        self.default_pane: SchedulerPane | None = None
        self.drop_validity: DropValidity | None = None
        self.drop_validity_overlay: DropValidityOverlay | None = None

    def set_use_filter(self, use_filter: FilterComponent) -> "SchedulerView":
        """Filter the tasks with a registered `FilterComponent` and show its UI. Returns self."""
        self.use_filter = use_filter.filter_name
        self.show_filter = use_filter.filter_name
        return self

    def add_card_template(self, key: str, card: Card) -> "SchedulerView":
        """
        Register a card template under ``key``.

        Register templates before referring to them from `set_task`, `set_resource_pane`,
        `set_unscheduled_pane` or `add_layout`.

        Raises:
            ValueError: If ``key`` is blank or already registered.
        """
        if _blank(key):
            raise ValueError("A card template key is required.")
        if key in self.card_templates:
            raise ValueError(f"Card template '{key}' is already registered.")
        self.card_templates[key] = card
        return self

    def set_task(
        self, start_field: Field, end_field: Field, card_template: str | Field
    ) -> SchedulerTaskDefinition:
        """
        Describe the tasks: their start and end, and the card that draws them.

        Args:
            start_field: Task start field (DATETIME, or TIME for a single-day view).
            end_field: Task end field, the same type as ``start_field``.
            card_template: A registered card template key, or a STRING task field holding the
                key per task.

        Returns:
            The new `SchedulerTaskDefinition`, to configure editing and events.

        Raises:
            ValueError: If the fields are not on the task table, have the wrong types, or
                ``card_template`` names an unregistered template.
        """
        _check_on_table(start_field, self.source_table, "Task start field")
        task = SchedulerTaskDefinition(start_field, end_field, card_template)
        self._check_template_key(task.card_template, "Task card template")
        if self.time_axis is not None:
            _raise_if(_axis_problems_for(_kind(start_field), self.time_axis))
        self.task = task
        return task

    def add_level(self, field: Field) -> SchedulerLevel:
        """
        Add a level grouping the tasks by ``field``, inside the levels added before it.

        Args:
            field: Task field: an object reference, a list of object references, or a single
                value. Each field may be used by one level only.

        Returns:
            The new `SchedulerLevel`, to configure labels, summaries and moves.
        """
        _check_on_table(field, self.source_table, "Level field")
        if any(level.field == field.id for level in self.levels):
            raise ValueError(f"Level field '{field.id}' is already used by another level.")
        level = SchedulerLevel(field)
        self.levels.append(level)
        return level

    def set_levels_title(self, title: str) -> "SchedulerView":
        """Set the heading over the level column. Returns self."""
        self.levels_title = title
        return self

    def set_time_axis(self, time_axis: SchedulerTimeAxis) -> "SchedulerView":
        """
        Set the time axis.

        When the task times are TIME (a single-day view), the scales must be exactly
        ``[DAY]`` and navigation must be off; ``period_label`` is only allowed then.

        Returns:
            This `SchedulerView`, for fluent chaining.
        """
        _raise_if(_axis_problems_for(self._time_kind(), time_axis))
        self.time_axis = time_axis
        return self

    def set_total_row(
        self,
        label: str | None = None,
        summary: str | None = None,
        statistics: SchedulerStatistics | None = None,
    ) -> "SchedulerView":
        """
        Set the total row's label, summary text and statistics strip.

        ``summary`` may insert named values or calculations with ``${Name}``, e.g.
        ``"${Total Jobs} jobs"``. Returns self.
        """
        self.total_label = label
        self.total_summary = summary
        self.total_statistics = statistics
        return self

    def add_background(  # noqa: PLR0913
        self,
        source_table: Table,
        start_field: Field,
        end_field: Field,
        effect: BackgroundEffect = BackgroundEffect.BLOCK,
        *,
        label_field: Field | None = None,
        status_field: Field | None = None,
    ) -> SchedulerTableBackground:
        """
        Add a table background: time ranges from ``source_table`` drawn behind the lines.

        See `SchedulerTableBackground`.

        Returns:
            The new `SchedulerTableBackground`.
        """
        background = SchedulerTableBackground(
            source_table,
            start_field,
            end_field,
            effect,
            label_field=label_field,
            status_field=status_field,
        )
        self.backgrounds.append(background)
        return background

    def set_resource_pane(
        self,
        source_table: Table,
        card_template_key: str,
        task_resource_field: Field,
        title: str | None = None,
        resource_reference_field: Field | None = None,
    ) -> SchedulerResourcePane:
        """
        Add a pane of resources that can be dragged onto tasks to allocate them.

        Args:
            source_table: The table the pane lists: the resources themselves, or a table
                derived from them (e.g. one carrying per-resource rollups the resource table
                cannot calculate without a cycle) that points at them.
            card_template_key: Registered card template drawing each resource.
            task_resource_field: OBJECT reference on the task table to the resource table.
            title: Pane tab title.
            resource_reference_field: OBJECT field of ``source_table`` referencing the resource
                table; omit when ``source_table`` is the resource table.

        Returns:
            The new `SchedulerResourcePane`.
        """
        _check_on_table(task_resource_field, self.source_table, "Resource pane task resource field")
        self._check_template_key(card_template_key, "Resource pane card template")
        pane = SchedulerResourcePane(
            source_table, card_template_key, task_resource_field, title, resource_reference_field
        )
        self.resource_pane = pane
        return pane

    def set_unscheduled_pane(
        self, card_template_key: str, duration_field: Field, title: str | None = None
    ) -> SchedulerUnscheduledPane:
        """
        Add a pane of tasks with no start, which can be dragged onto the timeline.

        Placing writes the task's start, end and level fields, so they must be writable
        (data fields, or edit overrides).

        Args:
            card_template_key: Registered card template drawing each unscheduled task.
            duration_field: Numeric task field: the placed task's length in minutes.
            title: Pane tab title.

        Returns:
            The new `SchedulerUnscheduledPane`.
        """
        _check_on_table(duration_field, self.source_table, "Unscheduled pane duration field")
        self._check_template_key(card_template_key, "Unscheduled pane card template")
        pane = SchedulerUnscheduledPane(card_template_key, duration_field, title)
        self.unscheduled_pane = pane
        return pane

    def set_default_pane(self, pane: SchedulerPane) -> "SchedulerView":
        """Open on the given pane; it must have been added. Returns self."""
        if pane is SchedulerPane.RESOURCES and self.resource_pane is None:
            raise ValueError("The default pane RESOURCES needs a resource pane; add it first.")
        if pane is SchedulerPane.UNSCHEDULED and self.unscheduled_pane is None:
            raise ValueError(
                "The default pane UNSCHEDULED needs an unscheduled pane; add it first."
            )
        self.default_pane = pane
        return self

    def set_drop_validity(self, timeline_drag: DropOutcomes | None) -> "SchedulerView":
        """
        Choose the outcomes coloured on the anchor line, time pill, shadow and callout while a
        task is moved or placed.

        Without this call every outcome is coloured.

        Args:
            timeline_drag: The outcomes to colour; ``None`` switches the feedback off.

        Returns:
            This `SchedulerView`, for fluent chaining.
        """
        self.drop_validity = DropValidity(timeline_drag=timeline_drag)
        return self

    def set_drop_validity_overlay(
        self, rows: DropOutcomes | None = None, canvas: DropOutcomes | None = None
    ) -> "SchedulerView":
        """
        Shade the view while a task is moved or placed.

        Args:
            rows: Shade the row under the pointer with these outcomes.
            canvas: Shade the whole view with where the task may land, using these outcomes:
                lines it may not go to are Not allowed throughout.

        Returns:
            This `SchedulerView`, for fluent chaining.
        """
        if rows is None and canvas is None:
            self.drop_validity_overlay = None
        else:
            self.drop_validity_overlay = DropValidityOverlay(rows=rows, canvas=canvas)
        return self

    def add_layout(  # noqa: PLR0913
        self,
        name: str,
        *,
        card_template: str | Field | None = None,
        resource_card_template_key: str | None = None,
        unscheduled_card_template_key: str | None = None,
        hide_level_summaries: bool = False,
    ) -> SchedulerLayout:
        """
        Add a named layout to the Layout menu (shown when there are two or more).

        Templates must already be registered, and a pane template needs that pane.

        Args:
            name: Shown in the menu; unique within the view.
            card_template: Task card template key, or a STRING task field holding the key.
            resource_card_template_key: Resource pane card template key.
            unscheduled_card_template_key: Unscheduled pane card template key.
            hide_level_summaries: Show level lines with their label only.

        Returns:
            The new `SchedulerLayout`.
        """
        if any(layout.name == name for layout in self.layouts):
            raise ValueError(f"Layout '{name}' is already defined.")
        reference = None
        if card_template is not None:
            reference = _template_reference(
                card_template, self.source_table, "Layout card template"
            )
            self._check_template_key(reference, "Layout card template")
        for key, pane, what in (
            (resource_card_template_key, self.resource_pane, "resource"),
            (unscheduled_card_template_key, self.unscheduled_pane, "unscheduled"),
        ):
            if key is not None:
                if pane is None:
                    raise ValueError(
                        f"Layout '{name}' sets a {what} card template but there is no {what} "
                        "pane; add the pane first."
                    )
                self._check_template_key(key, f"Layout {what} card template")
        layout = SchedulerLayout(
            name,
            card_template=reference,
            resource_card_template_key=resource_card_template_key,
            unscheduled_card_template_key=unscheduled_card_template_key,
            hide_level_summaries=hide_level_summaries,
        )
        self.layouts.append(layout)
        return layout

    def set_default_layout(self, layout: SchedulerLayout | str) -> "SchedulerView":
        """Open with the given layout (by object or name). Returns self."""
        name = layout.name if isinstance(layout, SchedulerLayout) else layout
        if all(existing.name != name for existing in self.layouts):
            raise ValueError(f"Layout '{name}' is not defined; add it with add_layout first.")
        self.default_layout = name
        return self

    def validate(self, ui: "UiBuilder | None" = None) -> list[str]:
        """
        Check the rules the individual ``set_*``/``add_*`` calls cannot.

        Each setter already rejects its own invalid settings; this adds the rules that span
        several of them: that the required pieces are present (`set_task`, `set_time_axis`, a
        level, an ``id_field``), and that settings made in separate calls agree. `UiBuilder.build`
        runs it for every scheduler and raises `SchedulerValidationError` if anything is wrong.
        Pass the `UiBuilder` to also check references to the rest of the UI: context variables,
        modals, filters and other schedulers' sync groups.

        Returns:
            One message per problem; empty when the scheduler is valid.
        """
        name = self.display_name or self.id
        return [
            f"{name}: Scheduler {path}: {problem}"
            for path, problem in _SchedulerChecker(self, ui).problems()
        ]

    def _check_template_key(self, key: str, what: str) -> None:
        if _bracketed(key) is None and key not in self.card_templates:
            raise ValueError(
                f"{what} '{key}' is not a registered card template; call add_card_template first."
            )

    def _time_kind(self) -> str | None:
        if self.task is None:
            return None
        return getattr(self.task, "_time_kind", None)


def _axis_problems_for(time_kind: str | None, axis: SchedulerTimeAxis) -> Problems:
    """The time-axis rules that depend on whether the task times are TIME or DATETIME."""
    if time_kind == "TIME":
        return _time_only_problems(axis)
    if time_kind == "DATETIME" and axis.period_label is not None:
        return [("timeAxis.periodLabel", "only applies when the task fields are TIME")]
    return []


def _time_only_problems(axis: SchedulerTimeAxis) -> Problems:
    problems: Problems = []
    if axis.scales != [SchedulerScale.DAY]:
        problems.append(("timeAxis.scales", "must be exactly [DAY] when the task fields are TIME"))
    if axis.show_navigation:
        problems.append(("timeAxis.showNavigation", "must be false when the task fields are TIME"))
    sessions = axis.sessions
    if sessions is not None and (
        sessions.date_field is not None or sessions.day_of_week_field is not None
    ):
        problems.append(
            (
                "timeAxis.sessions",
                "dateField and dayOfWeekField need dates; they cannot be used when the task "
                "fields are TIME",
            )
        )
    return problems


# ---------------------------------------------------------------------------------------------
# Whole-view validation
# ---------------------------------------------------------------------------------------------


class _SchedulerChecker:  # pylint: disable=too-few-public-methods
    """
    Checks the rules a single ``set_*``/``add_*`` cannot: that the required pieces are present,
    that settings made in separate calls agree, and that references to the rest of the UI resolve.

    Everything a setter already guarantees (a field is on the right table, has the right type, a
    card template is registered, ...) is trusted here, not re-checked — the library validates at
    the point each setting is made and does not guard against later reaching past the API to
    change a public attribute.
    """

    def __init__(self, view: SchedulerView, ui: "UiBuilder | None"):
        self.view = view
        self.ui = ui
        self.out: Problems = []
        self.table_id = view.source_table
        self.fields: dict[str, Field] | None = None
        self.time_kind: str | None = None

    def problems(self) -> Problems:
        ready = self._view()
        if ready:
            self._templates()
            self._levels()
            self._writes()
            self._statistics()
            self._task_backgrounds()
        self._sync_group()
        self._events()
        return self.out

    # --- helpers -------------------------------------------------------------------------------

    def _add(self, path: str, problem: str) -> None:
        self.out.append((path, problem))

    def _task_field(self, field_id: str | None) -> Field | None:
        return (self.fields or {}).get(field_id or "") if field_id is not None else None

    # --- view: required pieces -----------------------------------------------------------------

    def _view(self) -> bool:
        """Report the pieces a scheduler cannot do without; ``True`` when its fields are known."""
        view = self.view
        table = getattr(view, "_source_table", None)
        if _blank(self.table_id):
            self._add("sourceTable", "is required")
        elif table is not None and _fields_of(table) is not None:
            if _blank(getattr(table, "id_field", None)):
                self._add(
                    "sourceTable",
                    f"'{self.table_id}' needs an idField, which identifies tasks across reloads",
                )
            else:
                self.fields = _fields_of(table)
        self._filter("useFilter", view.use_filter)
        if view.task is None:
            self._add("task", "is required")
        elif self.fields is not None:
            start = self._task_field(view.task.start_field)
            self.time_kind = _kind(start) if start is not None else None
        if view.time_axis is None:
            self._add("timeAxis", "is required")
        if not view.levels:
            self._add("levels", "needs at least one level")
        return view.task is not None and self.fields is not None

    def _filter(self, path: str, name: str | None) -> None:
        if name is None or self.ui is None:
            return
        if all(getattr(f, "filter_name", None) != name for f in self.ui.filters):
            self._add(path, f"'{name}' does not name a filter")

    # --- card templates: click keys need event mappings ----------------------------------------

    def _templates(self) -> None:
        view, task = self.view, self.view.task
        assert task is not None
        resource_keys = self._resource_template_keys()
        for key, card in view.card_templates.items():
            path = f"cardTemplates['{key}']"
            click_keys = sorted(_on_click_keys(card))
            if key in resource_keys:
                if click_keys:
                    self._add(
                        path,
                        f"is the resource pane's template and may not use onClickKey {click_keys}",
                    )
                continue
            for click_key in click_keys:
                if click_key not in task.model_event_mappings:
                    self._add(
                        path, f"onClickKey '{click_key}' is not a key in task.modelEventMappings"
                    )

    def _resource_template_keys(self) -> set[str]:
        pane = self.view.resource_pane
        if pane is None:
            return set()
        keys: set[str | None] = {pane.card_template_key}
        keys |= {layout.resource_card_template_key for layout in self.view.layouts if layout}
        return {key for key in keys if key is not None and not _blank(key)}

    # --- levels: context variables required by onAdd / onDoubleClickRow -------------------------

    def _levels(self) -> None:
        view = self.view
        assert view.task is not None
        double_click = view.task.on_double_click_row is not None
        last_add = max(
            (i for i, level in enumerate(view.levels) if level is not None and level.on_add),
            default=-1,
        )
        for index, level in enumerate(view.levels):
            if level is None or level.context_variable is not None:
                continue
            path = f"levels[{index}].contextVariable"
            if index <= last_add:
                self._add(path, f"is required because levels[{last_add}] has onAdd")
            elif double_click:
                self._add(path, "is required because task.onDoubleClickRow is set")

    # --- writes: fields the view edits must be editable ----------------------------------------

    def _writes(self) -> None:
        view, task = self.view, self.view.task
        assert task is not None
        if task.allow_move or task.allow_resize or view.unscheduled_pane is not None:
            self._writable(
                "task.startField",
                task.start_field,
                "task.startEditOverride",
                task.start_edit_override,
                None,
            )
            self._writable(
                "task.endField",
                task.end_field,
                "task.endEditOverride",
                task.end_edit_override,
                None,
            )
        for index, level in enumerate(view.levels):
            field = self._task_field(level.field) if level is not None else None
            if field is None or _kind(field) == "OBJECT_ARRAY":
                continue
            if level.allow_move_across or view.unscheduled_pane is not None:
                self._writable(
                    f"levels[{index}].field",
                    level.field,
                    f"levels[{index}].editOverride",
                    level.edit_override,
                    _referenced_table(field),
                )
        pane = view.resource_pane
        if pane is not None and pane.task_resource_field is not None:
            self._writable(
                "resourcePane.taskResourceField",
                pane.task_resource_field,
                "resourcePane.allocateEditOverride",
                pane.allocate_edit_override,
                pane.resource_table,
            )

    def _writable(  # noqa: PLR0913
        self,
        field_path: str,
        field_id: str | None,
        override_path: str,
        override: EditOverride | None,
        reference_table: str | None,
    ) -> None:
        if override is not None:
            for problem in self._override_problems(override, reference_table):
                self._add(override_path, problem)
            return
        field = self._task_field(field_id)
        if field is not None and not _is_editable(field):
            attribute = override_path.rsplit(".", 1)[-1]
            self._add(
                field_path,
                f"'{field_id}' is not editable; add {attribute} to say where the scheduler "
                "writes it",
            )

    def _override_problems(self, override: EditOverride, reference_table: str | None) -> list[str]:
        if _blank(override.target_field_id):
            return ["requires a targetFieldId"]
        fields = self.fields or {}
        target_table_id, target_fields = self.table_id, fields
        if override.target_reference_field is not None:
            reference = fields.get(override.target_reference_field)
            if reference is None:
                return [
                    f"targetReferenceField {override.target_reference_field} does not exist in "
                    f"table {self.table_id}"
                ]
            target_table_id = _referenced_table(reference) or ""
            if not target_table_id:
                return [
                    f"targetReferenceField {override.target_reference_field} is not an object "
                    "reference"
                ]
            found = _fields_of(getattr(reference.to_data_type(), "_source_table", None))
            if found is None:
                return []
            target_fields = found
        problems: list[str] = []
        target = target_fields.get(override.target_field_id)
        if target is None:
            problems.append(
                f"targetFieldId {override.target_field_id} does not exist in table "
                f"{target_table_id}"
            )
        elif not _is_editable(target):
            problems.append(
                f"targetFieldId {override.target_field_id} in table {target_table_id} "
                "is not editable"
            )
        elif reference_table is not None and _referenced_table(target) != reference_table:
            problems.append(
                f"targetFieldId {override.target_field_id} in table {target_table_id} must be an "
                f"object reference to {reference_table}"
            )
        if override.map_key_field is not None and override.map_key_field not in fields:
            problems.append(
                f"mapKeyField {override.map_key_field} does not exist in table {self.table_id}"
            )
        return problems

    # --- statistics and backgrounds: level columns must match the levels -----------------------

    def _statistics(self) -> None:
        self._level_columns_match("totalStatistics", self.view.total_statistics, 0)
        for index, level in enumerate(self.view.levels):
            if level is not None:
                self._level_columns_match(
                    f"levels[{index}].statistics", level.statistics, index + 1
                )
                self._line_table_columns(index, level)
        for index, background in enumerate(self.view.backgrounds):
            if background is None:
                continue
            table = getattr(background, "_source_table", None)
            if _fields_of(table) is None:
                continue
            columns = self._level_columns(
                f"backgrounds[{index}].sourceTable", _fields_of(table) or {}
            )
            if columns != self._level_fields(len(columns)):
                self._add(
                    f"backgrounds[{index}].sourceTable",
                    f"'{background.source_table}' has level columns {columns} but they must be "
                    f"the first levels in order, as in {self._level_fields(len(self.view.levels))}",
                )

    def _level_columns_match(
        self, path: str, statistics: SchedulerStatistics | None, level_count: int
    ) -> None:
        if statistics is None:
            return
        table = getattr(statistics, "_source_table", None)
        if _fields_of(table) is None:
            return
        found = self._level_columns(f"{path}.sourceTable", _fields_of(table) or {})
        expected = self._level_fields(level_count)
        if found != expected:
            needs = (
                "totalStatistics needs none"
                if level_count == 0
                else f"levels[{level_count - 1}] needs {expected}"
            )
            self._add(
                f"{path}.sourceTable",
                f"'{statistics.source_table}' has level columns {found} but {needs}",
            )

    def _line_table_columns(self, index: int, level: SchedulerLevel) -> None:
        table = getattr(level, "_line_table", None)
        fields = _fields_of(table)
        if level.line_table is None or fields is None:
            return
        path = f"levels[{index}].lineTable"
        found = self._level_columns(path, fields)
        expected = self._level_fields(index + 1)
        if found != expected:
            self._add(
                path,
                f"'{level.line_table}' has level columns {found} but levels[{index}] needs "
                f"{expected}",
            )

    def _level_columns(self, path: str, fields: dict[str, Field]) -> list[str]:
        """The level fields ``fields`` carries, checking each matches the task field's type."""
        found: list[str] = []
        for level in self.view.levels:
            if level is None or level.field is None or level.field in found:
                continue
            column = fields.get(level.field)
            task_field = self._task_field(level.field)
            if column is None or task_field is None:
                if column is not None:
                    found.append(level.field)
                continue
            found.append(level.field)
            task_kind = _kind(task_field)
            is_reference = task_kind in ("OBJECT", "OBJECT_ARRAY")
            expected_kind = "OBJECT" if is_reference else task_kind
            matches = _kind(column) == expected_kind and (
                not is_reference or _referenced_table(column) == _referenced_table(task_field)
            )
            if not matches:
                expected = (
                    f"an object reference to '{_referenced_table(task_field)}'"
                    if is_reference
                    else task_kind
                )
                self._add(
                    path,
                    f"level column '{level.field}' must be {expected}, to match the task field",
                )
        return found

    def _level_fields(self, count: int) -> list[str]:
        return [level.field for level in self.view.levels[:count] if level is not None]

    def _task_backgrounds(self) -> None:
        task = self.view.task
        assert task is not None
        allows_time = any(
            background is not None
            and background.effect in (BackgroundEffect.ALLOW, BackgroundEffect.RECOMMEND)
            for background in task.backgrounds
        )
        if task.default_background is BackgroundEffect.BLOCK and not allows_time:
            self._add(
                "task.defaultBackground",
                "BLOCK needs an ALLOW or RECOMMEND task background, or no drop could ever pass",
            )

    # --- time axis: schedulers sharing a sync group need identical axes -------------------------

    def _sync_group(self) -> None:
        axis = self.view.time_axis
        if axis is None or axis.sync_group is None or self.ui is None:
            return
        for other in self.ui.get_views():
            other_axis = getattr(other, "time_axis", None)
            if (
                other is self.view
                or not isinstance(other, SchedulerView)
                or other_axis is None
                or other_axis.sync_group != axis.sync_group
            ):
                continue
            if not axis._same_as(other_axis):  # noqa: SLF001
                self._add(
                    "timeAxis.syncGroup",
                    f"'{axis.sync_group}' is shared with view '{other.id}', whose timeAxis "
                    "differs; schedulers in a syncGroup need identical time axes",
                )

    # --- events, modals and context variables --------------------------------------------------

    def _events(self) -> None:
        change, custom = self._event_paths()
        for path, event in {**custom, **change}.items():
            if event is None:
                continue
            is_change = path in change
            if is_change:
                self.out += [
                    item for item in _change_event_problems(path, event) if "BEGIN" in item[1]
                ]
            if self.ui is None:
                if is_change and not _modal_ids(event):
                    self.out += [
                        item
                        for item in _change_event_problems(path, event)
                        if "never ends" in item[1]
                    ]
                continue
            modals_exist = self._modals_exist(path, event)
            begins = ActionType.BEGIN in _transactions(event)
            if (is_change or begins) and modals_exist:
                self._transaction_closes(path, event)
        self._event_context_variables()

    def _event_paths(self) -> tuple[dict[str, ModelEvent | None], dict[str, ModelEvent | None]]:
        view = self.view
        change: dict[str, ModelEvent | None] = {}
        custom: dict[str, ModelEvent | None] = {}
        if view.task is not None:
            for key, event in view.task.model_event_mappings.items():
                custom[f"task.modelEventMappings['{key}']"] = event
            change["task.onMove"] = view.task.on_move
            change["task.onResize"] = view.task.on_resize
            custom["task.onDoubleClickRow"] = view.task.on_double_click_row
        for index, level in enumerate(view.levels):
            if level is not None:
                change[f"levels[{index}].onMoveAcross"] = level.on_move_across
                custom[f"levels[{index}].onAdd"] = level.on_add
        if view.resource_pane is not None:
            change["resourcePane.onAllocate"] = view.resource_pane.on_allocate
            custom["resourcePane.onDoubleClick"] = view.resource_pane.on_double_click
        if view.unscheduled_pane is not None:
            change["unscheduledPane.onPlace"] = view.unscheduled_pane.on_place
            custom["unscheduledPane.onDoubleClick"] = view.unscheduled_pane.on_double_click
        return change, custom

    def _modals_exist(self, path: str, event: ModelEvent) -> bool:
        all_exist = True
        for modal_id in _modal_ids(event):
            if self._modal(modal_id) is None:
                self._add(path, f"opens modal '{modal_id}', which does not exist")
                all_exist = False
        return all_exist

    def _transaction_closes(self, path: str, event: ModelEvent) -> None:
        modal_ids = _modal_ids(event)
        if not modal_ids:
            if not {ActionType.COMMIT, ActionType.ROLLBACK} & _transactions(event):
                self._add(
                    path,
                    "never ends the transaction (add TRANSACTION COMMIT or ROLLBACK, or open a "
                    "modal that does)",
                )
            return
        for modal_id in modal_ids:
            modal = self._modal(modal_id)
            button = getattr(modal, "close_button", None)
            close = getattr(button, "on_click", None)
            if not {ActionType.COMMIT, ActionType.ROLLBACK} & _transactions(close):
                self._add(
                    path,
                    f"opens modal '{modal_id}' whose closeButton never ends the transaction "
                    "(add TRANSACTION ROLLBACK)",
                )

    def _modal(self, modal_id: str) -> Any:
        if self.ui is None:
            return None
        return next((m for m in self.ui.modals if getattr(m, "id", None) == modal_id), None)

    def _event_context_variables(self) -> None:
        """The STRING context variables levels and the task double-click write before events."""
        task = self.view.task
        if task is not None and task.on_double_click_row is not None:
            self._string_variable(
                "task.doubleClickTimeContextVariable",
                task.double_click_time_context_variable,
                "is required with onDoubleClickRow",
            )
        for index, level in enumerate(self.view.levels):
            if level is not None and level.context_variable is not None:
                self._string_variable(
                    f"levels[{index}].contextVariable", level.context_variable, None
                )

    def _string_variable(self, path: str, variable_id: str | None, missing: str | None) -> None:
        if _blank(variable_id):
            self._add(path, missing or "is required")
            return
        if self.ui is None:
            return
        variable = next(
            (v for v in self.ui.variables if getattr(v, "id", None) == variable_id), None
        )
        if variable is None:
            self._add(path, f"'{variable_id}' is not a context variable")
        elif variable.type is not CVType.STRING:
            self._add(path, f"'{variable_id}' must be a STRING context variable")
