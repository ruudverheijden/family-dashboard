"""Planner contracts, independent of SQLite, HTTP, and the current date."""

import pytest

from app import validation
from app.errors import DomainError
from app.services import planner


@pytest.fixture
def validate(monkeypatch):
    monkeypatch.setattr(validation, "entities", lambda *_: [{"id": "alex"}, {"id": "sam"}])

    def check(kind, **changes):
        data = dict(
            title="Ochtend",
            date="2024-02-29",
            members=["alex"],
            weekdays=[3],
            start_time="07:00",
            end_time="08:00",
            steps=[{"text": "Opstaan"}],
            mode="individual",
            repeat="weekly",
        )
        return validation.validate(kind, data | changes, None)

    return check


@pytest.mark.parametrize(
    "kind,repeat,day,expected",
    [
        ("tasks", "once", "2024-02-28", []),
        ("tasks", "once", "2024-02-29", ["alex", "sam"]),
        ("tasks", "once", "2024-03-01", []),
        ("tasks", "daily", "2024-03-01", ["alex", "sam"]),
        ("tasks", "weekly", "2024-03-01", []),
        ("tasks", "weekly", "2024-03-07", ["alex", "sam"]),
        ("routines", None, "2024-03-01", []),
        ("routines", None, "2024-03-07", ["alex", "sam"]),
    ],
)
def test_occurrences_across_leap_day(validate, kind, repeat, day, expected):
    template = validate(kind, members=["alex", "sam"], repeat=repeat)
    assert planner.scheduled_members(kind, template, day) == expected


def test_shared_task_archiving_and_member_deduplication(validate):
    template = validate("tasks", mode="shared", members=["alex", "sam", "alex"])
    assert template["members"] == ["alex", "sam"]
    assert planner.scheduled_members("tasks", template, "2024-02-29") == ["shared"]
    assert planner.scheduled_members("tasks", template | {"archived": True}, "2024-02-29") == []


@pytest.mark.parametrize(
    "kind,changes",
    [
        ("tasks", {"members": []}),
        ("tasks", {"members": ["removed"]}),
        ("tasks", {"weekdays": [True]}),
        ("tasks", {"weekdays": [7]}),
        ("tasks", {"date": "2023-02-29"}),
        ("tasks", {"archived": "false"}),
        ("tasks", {"points": True}),
        ("tasks", {"points": -1}),
        ("tasks", {"points": 10001}),
        ("routines", {"steps": []}),
        ("routines", {"steps": [{"text": "a"}] * 31}),
        ("routines", {"steps": ["Opstaan"]}),
        ("routines", {"steps": [{"text": "  "}]}),
        ("routines", {"start_time": "24:00"}),
        ("routines", {"start_time": ""}),
        ("routines", {"end_time": ""}),
        ("routines", {"end_time": "07:00"}),
        ("routines", {"end_time": "06:59"}),
    ],
)
def test_reject_invalid_templates(validate, kind, changes):
    with pytest.raises(DomainError) as error:
        validate(kind, **changes)
    assert error.value.status_code == 422


def test_normalize_date_before_scheduling(validate):
    for value in ["20240229", "2024-W09-4"]:
        template = validate("tasks", repeat="once", date=value)
        assert template["date"] == "2024-02-29"
        assert planner.scheduled_members("tasks", template, "2024-02-29") == ["alex"]


def test_inclusive_limits_and_step_order(validate):
    assert validate("tasks", points=10000)["points"] == 10000
    steps = [{"text": f"  Stap {i} "} for i in range(30)]
    routine = validate("routines", steps=steps, start_time="00:00", end_time="23:59")
    assert [s["text"] for s in routine["steps"]] == [f"Stap {i}" for i in range(30)]


def test_routine_without_time_window_still_follows_weekdays(validate):
    routine = validate("routines", start_time="", end_time="")
    assert routine["start_time"] == routine["end_time"] == ""
    assert planner.scheduled_members("routines", routine, "2024-02-29") == ["alex"]
    assert planner.scheduled_members("routines", routine, "2024-03-01") == []
