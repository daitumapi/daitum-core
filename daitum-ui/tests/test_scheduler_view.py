"""
Tests for the Gantt scheduler view: its builder checks, whole-view validation, and decoding.

The validation rules mirror the platform's scheduler validator, so these tests pin the cases a
modeller is most likely to hit: settings that can never work (rejected as they are made) and
settings that only fail in combination or against the rest of the UI (reported by ``build``).
"""

import pytest
from daitum_model import DataType, ModelBuilder

from daitum_ui.context_variable import CVType
from daitum_ui.drop_validity import DropOutcomes
from daitum_ui.elements import Button, Card
from daitum_ui.model_event import ModelEvent
from daitum_ui.scheduler_view import (
    BackgroundEffect,
    SchedulerLineFilter,
    SchedulerPane,
    SchedulerScale,
    SchedulerSession,
    SchedulerStatistics,
    SchedulerTimeAxis,
    SchedulerValidationError,
    SchedulerView,
    StatisticFormat,
    Weekday,
    WorkingTime,
)
from daitum_ui.template_binding_key import TemplateBindingKey
from daitum_ui.ui_builder import UiBuilder


def _model():
    model = ModelBuilder()
    crews = model.add_data_table("Crews")
    crews.add_data_field("Name", DataType.STRING)
    crews.add_data_field("Summary", DataType.STRING)
    people = model.add_data_table("People")
    people.add_data_field("Name", DataType.STRING)
    jobs = model.add_data_table("Jobs")
    jobs.set_id_field("ID")
    for name, data_type in (
        ("ID", DataType.STRING),
        ("Start", DataType.DATETIME),
        ("End", DataType.DATETIME),
        ("Minutes", DataType.INTEGER),
        ("Kind", DataType.STRING),
        ("Open From", DataType.DATETIME_ARRAY),
        ("Open To", DataType.DATETIME_ARRAY),
    ):
        jobs.add_data_field(name, data_type)
    jobs.add_object_reference_field("Crew", crews)
    jobs.add_object_reference_field("Allowed Crews", crews, is_array=True)
    jobs.add_object_reference_field("Person", people)
    jobs.add_calculated_field("Planned Start", jobs.get_field("Start"))
    load = model.add_data_table("Load")
    for name, data_type in (
        ("From", DataType.DATETIME),
        ("To", DataType.DATETIME),
        ("Value", DataType.DECIMAL),
        ("Status", DataType.STRING),
    ):
        load.add_data_field(name, data_type)
    sessions = model.add_data_table("Sessions")
    for name, data_type in (
        ("Label", DataType.STRING),
        ("From", DataType.TIME),
        ("To", DataType.TIME),
        ("Date", DataType.DATE),
        ("Weekday", DataType.STRING),
    ):
        sessions.add_data_field(name, data_type)
    return model, jobs, crews, people, load


def _scheduler(ui=None):
    """A minimal valid scheduler: card, task, one crew level, a week/day axis."""
    model, jobs, crews, people, load = _model()
    ui = ui or UiBuilder()
    view = ui.add_scheduler_view(jobs, display_name="Schedule")
    view.add_card_template("job", Card())
    view.set_task(jobs.get_field("Start"), jobs.get_field("End"), "job")
    view.add_level(jobs.get_field("Crew")).set_label_field(crews.get_field("Name"))
    view.set_time_axis(SchedulerTimeAxis([SchedulerScale.WEEK, SchedulerScale.DAY]))
    return model, ui, view, (jobs, crews, people, load)


def _problems(ui):
    with pytest.raises(SchedulerValidationError) as raised:
        ui.build()
    return raised.value.problems


def _sessions(model):
    sessions = model.get_table("Sessions")
    return SchedulerSession(
        sessions,
        sessions.get_field("Label"),
        sessions.get_field("From"),
        sessions.get_field("To"),
        date_field=sessions.get_field("Date"),
        day_of_week_field=sessions.get_field("Weekday"),
    )


def _committing_event():
    event = ModelEvent()
    event.add_commit_transaction()
    return event


class TestBuild:
    def test_minimal_scheduler_builds(self):
        _, ui, view, _ = _scheduler()
        built = next(v for v in ui.build()["views"] if v["id"] == view.id)["viewDefinition"]
        assert built["@type"] == "scheduler"
        assert built["task"]["startField"] == "Start"
        assert built["levels"][0]["field"] == "Crew"
        assert built["timeAxis"]["defaultScale"] == "WEEK"
        assert built["timeAxis"]["showNowLine"] is False

    def test_field_card_template_is_bracketed(self):
        _, ui, view, (jobs, *_) = _scheduler()
        view.set_task(jobs.get_field("Start"), jobs.get_field("End"), jobs.get_field("Kind"))
        assert view.task.card_template == "[Kind]"
        ui.build()

    def test_full_scheduler_round_trips_with_typed_values(self):
        model, ui, view, (jobs, crews, people, load) = _scheduler()
        view.add_card_template("person", Card()).add_card_template("loose", Card())
        view.task.set_allow_move(on_move=_committing_event()).add_background(
            jobs.get_field("Open From"), jobs.get_field("Open To"), BackgroundEffect.ALLOW
        )
        view.task.set_default_background(BackgroundEffect.BLOCK)
        view.levels[0].set_summary(crews.get_field("Summary")).set_show_lines(
            SchedulerLineFilter.ALL
        ).set_allowed_values_field(jobs.get_field("Allowed Crews")).set_allow_move_across()
        view.set_time_axis(
            SchedulerTimeAxis(
                [SchedulerScale.WEEK, SchedulerScale.WORK_DAY],
                show_now_line=True,
                working_time=WorkingTime([Weekday.MONDAY, Weekday.TUESDAY], "08:00", "17:00"),
            ).set_sessions(_sessions(model))
        )
        view.set_total_row(
            "Total",
            statistics=SchedulerStatistics(
                load,
                load.get_field("From"),
                load.get_field("To"),
                load.get_field("Value"),
                load.get_field("Status"),
            ),
        )
        view.set_resource_pane(people, "person", jobs.get_field("Person")).set_drop_validity(
            DropOutcomes(recommended=False)
        )
        view.set_unscheduled_pane("loose", jobs.get_field("Minutes"))
        view.set_default_pane(SchedulerPane.UNSCHEDULED)
        view.set_drop_validity_overlay(rows=DropOutcomes())
        view.add_layout("Detailed")
        view.add_layout("Compact", resource_card_template_key="person", hide_level_summaries=True)
        view.set_default_layout("Compact")

        built = ui.build()
        decoded_ui = UiBuilder.read_from_dict(built, model)
        assert decoded_ui.build() == built

        decoded = next(v for v in decoded_ui.get_views() if isinstance(v, SchedulerView))
        assert decoded.time_axis.scales == [SchedulerScale.WEEK, SchedulerScale.WORK_DAY]
        assert decoded.time_axis.working_time.days == [Weekday.MONDAY, Weekday.TUESDAY]
        assert decoded.levels[0].show_lines is SchedulerLineFilter.ALL
        assert decoded.task.default_background is BackgroundEffect.BLOCK
        assert decoded.default_pane is SchedulerPane.UNSCHEDULED
        assert isinstance(decoded.task.on_move, ModelEvent)
        assert decoded.validate(decoded_ui) == []


class TestSetterChecks:
    def test_level_field_must_be_on_the_task_table(self):
        _, _, view, (_, crews, *_) = _scheduler()
        with pytest.raises(ValueError, match="must be a field of table 'Jobs'"):
            view.add_level(crews.get_field("Name"))

    def test_reference_only_option_on_a_value_level(self):
        _, _, view, (jobs, crews, *_) = _scheduler()
        level = view.add_level(jobs.get_field("Kind"))
        with pytest.raises(ValueError, match="needs an object reference level field"):
            level.set_label_field(crews.get_field("Name"))

    def test_list_level_cannot_move_across(self):
        _, _, view, (jobs, *_) = _scheduler()
        level = view.add_level(jobs.get_field("Allowed Crews"))
        with pytest.raises(ValueError, match="list level"):
            level.set_allow_move_across()

    def test_card_template_must_be_registered_first(self):
        _, _, view, (jobs, *_) = _scheduler()
        with pytest.raises(ValueError, match="call add_card_template first"):
            view.set_task(jobs.get_field("Start"), jobs.get_field("End"), "missing")

    def test_change_event_may_not_begin_a_transaction(self):
        _, ui, view, _ = _scheduler()
        modal = ui.add_modal(ui.add_form_view(display_name="Confirm"))
        event = ModelEvent()
        event.add_show_modal_action(modal.id)  # transactional=True adds TRANSACTION BEGIN
        with pytest.raises(ValueError, match="transactional=False"):
            view.task.set_allow_move(on_move=event)

    def test_time_task_needs_a_day_only_axis(self):
        model = ModelBuilder()
        shifts = model.add_data_table("Shifts")
        shifts.add_data_field("From", DataType.TIME)
        shifts.add_data_field("To", DataType.TIME)
        view = UiBuilder().add_scheduler_view(shifts)
        view.add_card_template("shift", Card())
        view.set_task(shifts.get_field("From"), shifts.get_field("To"), "shift")
        with pytest.raises(ValueError, match=r"must be exactly \[DAY\]"):
            view.set_time_axis(SchedulerTimeAxis([SchedulerScale.WEEK]))

    def test_period_label_on_a_time_task(self):
        model = ModelBuilder()
        shifts = model.add_data_table("Shifts")
        shifts.add_data_field("From", DataType.TIME)
        shifts.add_data_field("To", DataType.TIME)
        view = UiBuilder().add_scheduler_view(shifts)
        view.add_card_template("shift", Card())
        view.set_task(shifts.get_field("From"), shifts.get_field("To"), "shift")
        view.set_time_axis(SchedulerTimeAxis([SchedulerScale.DAY], period_label=""))
        assert view.time_axis.build()["periodLabel"] == ""

    def test_period_label_needs_a_time_task(self):
        _, _, view, _ = _scheduler()
        with pytest.raises(ValueError, match="periodLabel: only applies when the task fields"):
            view.set_time_axis(SchedulerTimeAxis([SchedulerScale.DAY], period_label="Shifts"))

    def test_time_axis_rules(self):
        with pytest.raises(ValueError, match="is not one of timeAxis.scales"):
            SchedulerTimeAxis([SchedulerScale.WEEK], SchedulerScale.DAY)
        with pytest.raises(ValueError, match="WORK_WEEK and WORK_DAY"):
            SchedulerTimeAxis([SchedulerScale.WORK_DAY])
        with pytest.raises(ValueError, match="not a time in HH:mm"):
            WorkingTime([Weekday.MONDAY], "8am", "17:00")

    def test_statistics_format_needs_a_baseline(self):
        *_, load = _model()
        with pytest.raises(ValueError, match="needs a baseline_field"):
            SchedulerStatistics(
                load,
                load.get_field("From"),
                load.get_field("To"),
                load.get_field("Value"),
                load.get_field("Status"),
                format=StatisticFormat.VALUE_OF_BASELINE,
            )

    def test_table_background_cannot_recommend(self):
        _, _, view, (*_, load) = _scheduler()
        with pytest.raises(ValueError, match="only allowed on task backgrounds"):
            view.add_background(
                load, load.get_field("From"), load.get_field("To"), BackgroundEffect.RECOMMEND
            )

    def test_drop_outcomes_must_show_something(self):
        with pytest.raises(ValueError, match="leave the part as None"):
            DropOutcomes(recommended=False, allowed=False, not_allowed=False)


class TestSessions:
    def test_builds_with_every_field(self):
        model, ui, view, _ = _scheduler()
        view.time_axis.set_sessions(_sessions(model))
        assert view.time_axis.build()["sessions"] == {
            "sourceTable": "Sessions",
            "labelField": "Label",
            "startField": "From",
            "endField": "To",
            "dateField": "Date",
            "dayOfWeekField": "Weekday",
        }

    def test_start_must_be_a_time(self):
        model, *_ = _scheduler()
        sessions = model.get_table("Sessions")
        with pytest.raises(ValueError, match="must be a TIME field"):
            SchedulerSession(
                sessions,
                sessions.get_field("Label"),
                sessions.get_field("Date"),
                sessions.get_field("To"),
            )

    def test_fields_must_be_on_the_source_table(self):
        model, _, _, (jobs, *_) = _scheduler()
        sessions = model.get_table("Sessions")
        with pytest.raises(ValueError, match="must be a field of table 'Sessions'"):
            SchedulerSession(
                sessions,
                jobs.get_field("Kind"),
                sessions.get_field("From"),
                sessions.get_field("To"),
            )

    def test_satisfies_must_fit_session(self):
        model, ui, view, _ = _scheduler()
        view.set_time_axis(
            SchedulerTimeAxis(
                [SchedulerScale.DAY], sessions=_sessions(model), must_fit_session=True
            )
        )
        ui.build()

    def test_must_fit_session_needs_sessions(self):
        with pytest.raises(ValueError, match="needs timeAxis.sessions"):
            SchedulerTimeAxis([SchedulerScale.DAY], must_fit_session=True)


class TestBuildValidation:
    def test_missing_parts_are_listed_together(self):
        _, jobs, *_ = _model()
        ui = UiBuilder()
        ui.add_scheduler_view(jobs, display_name="Empty")
        problems = _problems(ui)
        assert "Empty: Scheduler task: is required" in problems
        assert "Empty: Scheduler timeAxis: is required" in problems
        assert "Empty: Scheduler levels: needs at least one level" in problems

    def test_task_table_needs_an_id_field(self):
        model = ModelBuilder()
        jobs = model.add_data_table("Jobs")
        jobs.add_data_field("Start", DataType.DATETIME)
        jobs.add_data_field("End", DataType.DATETIME)
        ui = UiBuilder()
        view = ui.add_scheduler_view(jobs)
        view.add_card_template("job", Card())
        view.set_task(jobs.get_field("Start"), jobs.get_field("End"), "job")
        view.add_level(jobs.get_field("Start"))
        view.set_time_axis(SchedulerTimeAxis([SchedulerScale.DAY]))
        assert any("needs an idField" in p for p in _problems(ui))

    def test_moving_a_calculated_start_needs_an_edit_override(self):
        _, ui, view, (jobs, *_) = _scheduler()
        view.set_task(
            jobs.get_field("Planned Start"), jobs.get_field("End"), "job"
        ).set_allow_move()
        assert any(
            "'Planned Start' is not editable; add startEditOverride" in p for p in _problems(ui)
        )
        view.task.set_start_edit_override(jobs.get_field("Start"))
        ui.build()

    def test_on_add_needs_context_variables_on_every_level_above(self):
        _, ui, view, (jobs, *_) = _scheduler()
        kind = ui.add_context_variable("kind", CVType.STRING)
        view.add_level(jobs.get_field("Kind")).set_on_add(_committing_event()).set_context_variable(
            kind
        )
        assert any(
            "levels[0].contextVariable: is required because levels[1] has onAdd" in p
            for p in _problems(ui)
        )

    def test_context_variable_must_be_registered(self):
        from daitum_ui.context_variable import ContextVariable

        _, ui, view, _ = _scheduler()
        view.levels[0].set_context_variable(ContextVariable("stray", CVType.STRING))
        assert any("'stray' is not a context variable" in p for p in _problems(ui))

    def test_modal_close_button_must_end_the_transaction(self):
        _, ui, view, _ = _scheduler()
        modal = ui.add_modal(ui.add_form_view(display_name="Confirm"))
        modal.add_close_button(on_click=ModelEvent())
        event = ModelEvent()
        event.add_show_modal_action(modal.id, transactional=False)
        view.task.set_allow_move(on_move=event)
        assert any("whose closeButton never ends the transaction" in p for p in _problems(ui))

    def test_pane_double_click_events_build_and_round_trip(self):
        model, ui, view, (jobs, crews, people, load) = _scheduler()
        view.add_card_template("person", Card()).add_card_template("loose", Card())
        modal = ui.add_modal(ui.add_form_view(display_name="Edit"))
        edit = ModelEvent()
        edit.add_show_modal_action(modal.id)
        view.set_resource_pane(people, "person", jobs.get_field("Person")).set_on_double_click(edit)
        view.set_unscheduled_pane("loose", jobs.get_field("Minutes")).set_on_double_click(edit)

        built = ui.build()
        definitions = [v["viewDefinition"] for v in built["views"]]
        definition = next(d for d in definitions if d.get("@type") == "scheduler")
        assert definition["resourcePane"]["onDoubleClick"]["actions"]
        assert definition["unscheduledPane"]["onDoubleClick"]["actions"]
        decoded_ui = UiBuilder.read_from_dict(built, model)
        assert decoded_ui.build() == built
        decoded = next(v for v in decoded_ui.get_views() if isinstance(v, SchedulerView))
        assert isinstance(decoded.resource_pane.on_double_click, ModelEvent)
        assert isinstance(decoded.unscheduled_pane.on_double_click, ModelEvent)

    def test_pane_double_click_that_begins_a_transaction_must_end_it(self):
        _, ui, view, (jobs, *_) = _scheduler()
        view.add_card_template("loose", Card())
        event = ModelEvent()
        event.add_begin_transaction()
        view.set_unscheduled_pane("loose", jobs.get_field("Minutes")).set_on_double_click(event)
        problems = _problems(ui)
        assert any(
            "unscheduledPane.onDoubleClick: never ends the transaction" in p for p in problems
        )

    def test_block_default_needs_an_allowing_background(self):
        _, ui, view, _ = _scheduler()
        view.task.set_default_background(BackgroundEffect.BLOCK)
        assert any("BLOCK needs an ALLOW or RECOMMEND task background" in p for p in _problems(ui))

    def test_card_click_keys_need_event_mappings(self):
        _, ui, view, _ = _scheduler()
        view.card_templates["job"].add_element(
            Button(text_value="Open", on_click_key=TemplateBindingKey("open"))
        )
        assert any("onClickKey 'open' is not a key" in p for p in _problems(ui))
        view.task.add_model_event_mapping("open", _committing_event())
        ui.build()

    def test_statistics_level_columns_must_match_the_levels(self):
        _, ui, view, (*_, load) = _scheduler()
        statistics = SchedulerStatistics(
            load,
            load.get_field("From"),
            load.get_field("To"),
            load.get_field("Value"),
            load.get_field("Status"),
        )
        view.levels[0].set_statistics(statistics)
        assert any("has level columns [] but levels[0] needs ['Crew']" in p for p in _problems(ui))

    def test_sync_group_needs_identical_time_axes(self):
        ui = UiBuilder()
        _, _, first, _ = _scheduler(ui)
        _, _, second, _ = _scheduler(ui)
        first.set_time_axis(SchedulerTimeAxis([SchedulerScale.DAY], sync_group="plan"))
        second.set_time_axis(SchedulerTimeAxis([SchedulerScale.WEEK], sync_group="plan"))
        assert any("whose timeAxis differs" in p for p in _problems(ui))


def _crew_lines(model, *, with_kind=False):
    """A line table for the Crew level (or Crew › Kind), with a summary and an always-show flag."""
    lines = model.add_data_table("Crew_Lines" if not with_kind else "Crew_Kind_Lines")
    lines.add_object_reference_field("Crew", model.get_table("Crews"))
    if with_kind:
        lines.add_data_field("Kind", DataType.STRING)
    lines.add_data_field("Summary", DataType.STRING)
    lines.add_data_field("Pin", DataType.BOOLEAN)
    return lines


class TestLineTablesAndResourceCards:
    def test_line_table_carries_the_summary_and_round_trips(self):
        model, ui, view, _ = _scheduler()
        lines = _crew_lines(model)
        view.levels[0].set_line_table(lines).set_summary(lines.get_field("Summary"))
        view.levels[0].set_always_show_field(lines.get_field("Pin"))
        view.levels[0].set_show_lines(SchedulerLineFilter.ALL)
        built = ui.build()
        level = next(v for v in built["views"] if v["id"] == view.id)["viewDefinition"]["levels"][0]
        assert level["lineTable"] == "Crew_Lines"
        assert level["summaryField"] == "Summary"
        assert level["alwaysShowField"] == "Pin"
        decoded_ui = UiBuilder.read_from_dict(built, model)
        assert decoded_ui.build() == built
        decoded = next(v for v in decoded_ui.get_views() if isinstance(v, SchedulerView))
        assert decoded.validate(decoded_ui) == []

    def test_summary_must_be_on_the_line_table(self):
        model, _, view, (_, crews, *_) = _scheduler()
        view.levels[0].set_line_table(_crew_lines(model))
        with pytest.raises(ValueError, match="must be a field of table 'Crew_Lines'"):
            view.levels[0].set_summary(crews.get_field("Summary"))

    def test_line_table_comes_before_the_summary(self):
        model, _, view, (_, crews, *_) = _scheduler()
        view.levels[0].set_summary(crews.get_field("Summary"))
        with pytest.raises(ValueError, match="before the summary"):
            view.levels[0].set_line_table(_crew_lines(model))

    def test_value_level_takes_summaries_and_all_lines_from_a_line_table(self):
        model, ui, view, (jobs, *_) = _scheduler()
        lines = _crew_lines(model, with_kind=True)
        level = view.add_level(jobs.get_field("Kind"))
        with pytest.raises(ValueError, match="or a line table"):
            level.set_summary(lines.get_field("Summary"))
        level.set_line_table(lines).set_summary(lines.get_field("Summary"))
        level.set_show_lines(SchedulerLineFilter.ALL)
        ui.build()

    def test_line_table_columns_must_match_the_levels(self):
        model, ui, view, (jobs, *_) = _scheduler()
        view.add_level(jobs.get_field("Kind")).set_line_table(_crew_lines(model))
        assert any(
            "levels[1].lineTable: 'Crew_Lines' has level columns ['Crew'] but levels[1] needs "
            "['Crew', 'Kind']" in p
            for p in _problems(ui)
        )

    def test_resource_pane_over_a_derived_table(self):
        model, ui, view, (jobs, crews, *_) = _scheduler()
        cards = model.add_data_table("Crew_Cards")
        cards.add_object_reference_field("Crew", crews)
        cards.add_data_field("Hours", DataType.DECIMAL)
        view.add_card_template("crew", Card())
        pane = view.set_resource_pane(
            cards, "crew", jobs.get_field("Crew"), resource_reference_field=cards.get_field("Crew")
        )
        pane.set_allowed_resources_field(jobs.get_field("Allowed Crews"))
        pane.set_drag_label_field(cards.get_field("Hours"))
        assert pane.resource_table == "Crews"
        built = ui.build()
        definition = next(v for v in built["views"] if v["id"] == view.id)["viewDefinition"]
        assert definition["resourcePane"]["sourceTable"] == "Crew_Cards"
        assert definition["resourcePane"]["resourceReferenceField"] == "Crew"
        decoded_ui = UiBuilder.read_from_dict(built, model)
        assert decoded_ui.build() == built
        decoded = next(v for v in decoded_ui.get_views() if isinstance(v, SchedulerView))
        assert decoded.resource_pane.resource_table == "Crews"
        assert decoded.validate(decoded_ui) == []

    def test_resource_reference_field_rules(self):
        model, _, view, (jobs, crews, *_) = _scheduler()
        cards = model.add_data_table("Crew_Cards")
        cards.add_object_reference_field("Crew", crews)
        cards.add_data_field("Hours", DataType.DECIMAL)
        view.add_card_template("crew", Card())
        with pytest.raises(ValueError, match="must be a OBJECT field"):
            view.set_resource_pane(
                cards,
                "crew",
                jobs.get_field("Crew"),
                resource_reference_field=cards.get_field("Hours"),
            )
        with pytest.raises(ValueError, match="must be an object reference to 'Crew_Cards'"):
            view.set_resource_pane(cards, "crew", jobs.get_field("Crew"))


def test_scheduler_templates_match_real_instances():
    """The decoder's bare templates must carry exactly the attributes the classes set."""
    from daitum_ui._decoders.views import SCHEDULER_TEMPLATE_DEFAULTS

    model, ui, view, (jobs, crews, people, load) = _scheduler()
    view.add_card_template("person", Card()).add_card_template("loose", Card())
    view.task.add_background(
        jobs.get_field("Open From"), jobs.get_field("Open To"), BackgroundEffect.ALLOW
    )
    view.set_time_axis(
        SchedulerTimeAxis(
            [SchedulerScale.WORK_DAY],
            working_time=WorkingTime([Weekday.MONDAY], "08:00", "17:00"),
        ).set_sessions(_sessions(model))
    )
    statistics = SchedulerStatistics(
        load,
        load.get_field("From"),
        load.get_field("To"),
        load.get_field("Value"),
        load.get_field("Status"),
    )
    instances = [
        view.task,
        view.levels[0],
        view.time_axis,
        view.time_axis.working_time,
        view.time_axis.sessions,
        statistics,
        view.task.backgrounds[0],
        view.add_background(load, load.get_field("From"), load.get_field("To")),
        view.set_resource_pane(people, "person", jobs.get_field("Person")),
        view.set_unscheduled_pane("loose", jobs.get_field("Minutes")),
    ]
    for instance in instances:
        defaults = SCHEDULER_TEMPLATE_DEFAULTS[type(instance)]
        assert set(defaults) == set(vars(instance)), type(instance).__name__
