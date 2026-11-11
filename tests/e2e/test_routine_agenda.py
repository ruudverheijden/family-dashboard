"""Routines in the agenda use the same dated executions as the routine overview."""

import re
import uuid
from datetime import date, datetime, timedelta, timezone
from zoneinfo import ZoneInfo

import pytest
from conftest import PASSWORD, section
from playwright.sync_api import expect

HEAD = {"X-Family-Request": "1"}


def create(page, kind, body):
    entity_id = str(uuid.uuid4())
    response = page.request.post(
        page.url + "api/entities/" + kind,
        headers=HEAD,
        data={
            "id": entity_id,
            "version": 0,
            "request_id": str(uuid.uuid4()),
            "action": "save",
            "body": body,
        },
    )
    assert response.ok, response.text()
    return entity_id


@pytest.fixture
def routines(dashboard):
    p = dashboard
    response = p.request.post(p.url + "api/login", headers=HEAD, data={"password": PASSWORD})
    assert response.ok
    day = date.fromisoformat(p.request.get(p.url + "api/state").json()["day"])
    monday = day - timedelta(days=day.weekday())
    alex = create(p, "members", {"name": "Alex", "color": "#aa7755"})
    sam = create(p, "members", {"name": "Sam", "color": "#5577aa"})
    body = {
        "title": "Ochtendritme",
        "icon": "☀️",
        "date": monday.isoformat(),
        "members": [alex, sam],
        "weekdays": list(range(7)),
        "points": 5,
        "start_time": "07:00",
        "end_time": "07:30",
        "steps": [{"text": "Poetsen", "icon": "✓"}, {"text": "Aankleden", "icon": "✓"}],
    }
    timed_id = create(p, "routines", body)
    untimed_id = create(
        p,
        "routines",
        body | {"title": "Samen lezen", "members": [alex], "start_time": "", "end_time": ""},
    )
    p.reload()
    yield p, day, timed_id, untimed_id, alex, sam


def card(page, template, day):
    return page.locator(f'[data-open-routine="{template}"][data-routine-day="{day}"]')


@pytest.mark.parametrize("size", [(390, 664), (1440, 1000)])
@pytest.mark.parametrize("mode,count", [("Dag", 1), ("3 dagen", 3), ("Week", 7)])
def test_agenda_routines_in_all_views_with_overlapping_appointments(routines, mode, count, size):
    p, day, timed, untimed, alex, sam = routines
    p.set_viewport_size(dict(zip(("width", "height"), size)))

    def with_appointment(route):
        response = route.fetch()
        body = response.json()
        body["events"] = [
            {
                "title": "Afspraak",
                "start": datetime.combine(
                    day,
                    datetime.min.time().replace(hour=7, minute=15),
                    ZoneInfo("Europe/Amsterdam"),
                ).isoformat(),
                "end": datetime.combine(
                    day, datetime.min.time().replace(hour=8), ZoneInfo("Europe/Amsterdam")
                ).isoformat(),
                "member": "",
                "calendar": "Gezin",
                "all_day": False,
            }
        ]
        route.fulfill(response=response, json=body)

    p.route("**/api/state*", with_appointment)
    p.get_by_role("button", name=mode, exact=True).click()
    expect(p.locator(".day-timeline .agenda-routine")).to_have_count(count)
    expect(p.locator(".calendar-routine-row .agenda-routine")).to_have_count(count)
    timed_card = card(p, timed, day)
    expect(timed_card).to_contain_text("07:00–07:30")
    expect(timed_card).to_contain_text("Alex · 0 van 2 klaar")
    expect(timed_card).to_contain_text("Sam · 0 van 2 klaar")
    expect(card(p, untimed, day)).to_contain_text("Zonder tijdvenster")
    # Shared collision layout prevents the routine from covering the appointment.
    expect(p.locator(".timed-event.event")).to_have_count(1)
    boxes = p.locator(f'[data-timeline-day="{day}"]').evaluate("""column => {
      const rect = selector => {
        const box = column.querySelector(selector).getBoundingClientRect();
        return {x: box.x, width: box.width, height: box.height};
      };
      return {routine: rect('.agenda-routine'), event: rect('.event')};
    }""")
    routine_box, event_box = boxes["routine"], boxes["event"]
    assert (
        routine_box["x"] + routine_box["width"] <= event_box["x"] + 1
        or event_box["x"] + event_box["width"] <= routine_box["x"] + 1
    )
    assert routine_box["height"] >= 48 and routine_box["width"] >= 48
    assert p.evaluate("document.documentElement.scrollWidth <= innerWidth")
    # Filtering removes the other person's progress and untimed execution.
    p.locator(f'[data-member="{sam}"]').click()
    expect(timed_card).to_contain_text("Sam")
    expect(timed_card).not_to_contain_text("Alex")
    expect(p.locator(".calendar-routine-row")).to_have_count(0)


def test_agenda_panel_updates_shared_progress_and_preserves_other_days(routines, tmp_path):
    p, day, timed, untimed, alex, sam = routines
    p.set_viewport_size({"width": 390, "height": 664})
    p.get_by_role("button", name="Dag", exact=True).click()
    opener = card(p, timed, day)
    opener.click()
    panel = p.locator("#routine-dialog")
    expect(panel).to_be_visible()
    expect(panel).to_contain_text("Ochtendritme")
    expect(panel.locator("#routine-dialog-title")).to_contain_text(str(day.day))
    panel.get_by_role("button", name="Voltooi Poetsen voor Alex", exact=True).click()
    expect(
        panel.get_by_role("button", name="Heropen Poetsen voor Alex", exact=True)
    ).to_have_attribute("aria-pressed", "true")
    # The panel stays current after polling and a second completion uses the new version.
    panel.get_by_role("button", name="Voltooi Aankleden voor Alex", exact=True).click()
    expect(
        panel.get_by_role("button", name="Heropen Aankleden voor Alex", exact=True)
    ).to_be_visible()
    p.get_by_role("button", name="Viering sluiten").click()
    expect(
        panel.get_by_role("button", name="Voltooi Poetsen voor Sam", exact=True)
    ).to_have_attribute("aria-pressed", "false")
    p.screenshot(path=str(tmp_path / "routine-panel.png"))
    for button in panel.locator("button").all():
        box = button.bounding_box()
        assert box["width"] >= 48 - 0.001 and box["height"] >= 48 - 0.001
    p.keyboard.press("Escape")
    expect(panel).to_be_hidden()
    expect(opener).to_be_focused()
    expect(opener).to_contain_text("Alex · 2 van 2 klaar")
    p.screenshot(path=str(tmp_path / "routine-timeline.png"))
    section(p, "Routines")
    overview = p.locator(".routine-grid > .panel").filter(has_text="Ochtendritme")
    expect(
        overview.get_by_role("button", name="Heropen Poetsen voor Alex", exact=True)
    ).to_be_visible()
    p.get_by_role("button", name="Volgende dag", exact=True).click()
    expect(
        overview.get_by_role("button", name="Voltooi Poetsen voor Alex", exact=True)
    ).to_have_attribute("aria-pressed", "false")
    p.get_by_role("button", name="Vorige dag", exact=True).click()
    expect(
        overview.get_by_role("button", name="Heropen Poetsen voor Alex", exact=True)
    ).to_be_visible()
    section(p, "Agenda")
    opener.click()
    panel.get_by_role("button", name="Heropen Poetsen voor Alex", exact=True).click()
    expect(
        panel.get_by_role("button", name="Voltooi Poetsen voor Alex", exact=True)
    ).to_be_visible()
    panel.get_by_role("button", name="Sluiten", exact=True).click()
    # Complete the untimed routine: its calendar card stays visible as Klaar.
    card(p, untimed, day).click()
    panel.get_by_role("button", name="Voltooi Poetsen voor Alex", exact=True).click()
    expect(
        panel.get_by_role("button", name="Heropen Poetsen voor Alex", exact=True)
    ).to_be_visible()
    panel.get_by_role("button", name="Voltooi Aankleden voor Alex", exact=True).click()
    expect(
        panel.get_by_role("button", name="Heropen Aankleden voor Alex", exact=True)
    ).to_be_visible()
    p.get_by_role("button", name="Viering sluiten").click()
    panel.get_by_role("button", name="Sluiten", exact=True).click()
    expect(card(p, untimed, day)).to_contain_text("Klaar")
    p.reload()
    p.get_by_role("button", name="Dag", exact=True).click()
    expect(card(p, untimed, day)).to_contain_text("Klaar")
    p.screenshot(path=str(tmp_path / "routine-agenda.png"))


def test_routine_empty_day_links_next_scheduled_day_and_separate_management(dashboard):
    p = dashboard
    assert p.request.post(p.url + "api/login", headers=HEAD, data={"password": PASSWORD}).ok
    day = date.fromisoformat(p.request.get(p.url + "api/state").json()["day"])
    next_day = day + timedelta(days=3)
    alex = create(p, "members", {"name": "Alex", "color": "#aa7755"})
    create(
        p,
        "routines",
        {
            "title": "Weekendritme",
            "date": str(day),
            "members": [alex],
            "weekdays": [next_day.weekday()],
            "start_time": "09:00",
            "end_time": "10:00",
            "steps": [{"text": "Lezen"}],
        },
    )
    p.reload()
    section(p, "Routines")
    expect(p.locator(".routine-grid > section")).to_have_count(1)
    expect(p.locator(".routine-empty")).to_contain_text("Geen routines op")
    expect(p.locator(".routine-grid")).not_to_contain_text("Weekendritme")
    expect(p.locator(".routine-grid [data-run]")).to_have_count(0)
    expect(p.locator(f'.routine-empty [data-day="{next_day}"]')).to_be_visible()
    p.get_by_role("button", name=re.compile("^Bekijk ")).click()
    expect(p.get_by_role("button", name="Voltooi Lezen voor Alex", exact=True)).to_be_visible()
    section(p, "Agenda")
    p.get_by_role("button", name="Dag", exact=True).click()
    expect(p.locator(".day-heading.selected")).to_have_attribute("data-day", str(next_day))
    expect(p.locator(".agenda-routine")).to_have_count(1)
    section(p, "Routines")
    p.get_by_role("button", name="Routines beheren", exact=True).click()
    expect(p.locator("#dialog [data-template]")).to_contain_text("Weekendritme")
    expect(p.locator("#dialog [data-template]")).to_contain_text("09:00–10:00")


def test_panel_on_another_day_tracks_external_changes_and_recovers_from_save_failure(routines):
    p, day, timed, untimed, alex, sam = routines
    p.get_by_role("button", name="3 dagen", exact=True).click()
    other_day = day + timedelta(days=1)
    card(p, timed, other_day).click()
    panel = p.locator("#routine-dialog")
    expect(panel).to_be_visible()
    expect(p.locator(".day-heading.selected")).to_have_attribute("data-day", str(other_day))
    run = next(
        run
        for run in p.request.get(p.url + f"api/state?day={other_day}").json()["runs"]
        if run["template_id"] == timed and run["member"] == alex
    )
    response = p.request.post(
        p.url + "api/entities/runs",
        headers=HEAD,
        data={
            "id": run["id"],
            "version": run["version"],
            "request_id": str(uuid.uuid4()),
            "action": "save",
            "body": {"done": [0]},
        },
    )
    assert response.ok
    expect(
        panel.get_by_role("button", name="Heropen Poetsen voor Alex", exact=True)
    ).to_be_visible()
    p.route("**/api/entities/runs", lambda route: route.abort("failed"))
    panel.get_by_role("button", name="Voltooi Aankleden voor Alex", exact=True).click()
    expect(panel.locator("[role='alert']")).to_contain_text("Geen verbinding")
    expect(
        panel.get_by_role("button", name="Voltooi Aankleden voor Alex", exact=True)
    ).to_be_enabled()
    p.unroute("**/api/entities/runs")
    panel.get_by_role("button", name="Voltooi Aankleden voor Alex", exact=True).click()
    expect(
        panel.get_by_role("button", name="Heropen Aankleden voor Alex", exact=True)
    ).to_be_visible()
    p.get_by_role("button", name="Viering sluiten").click()
    panel.get_by_role("button", name="Sluiten", exact=True).click()
    section(p, "Routines")
    expect(p.get_by_role("button", name="Heropen Poetsen voor Alex", exact=True)).to_be_visible()
    original = p.request.get(p.url + f"api/state?day={day}").json()["runs"]
    assert all(run["done"] == [] for run in original)


@pytest.mark.parametrize("clear_fields", [False, True], ids=["toggle", "clear-fields"])
def test_create_routine_without_time_in_editor(routines, clear_fields):
    p, day, timed, untimed, alex, sam = routines
    section(p, "Routines")
    p.get_by_role("button", name="Nieuwe routine", exact=True).click()
    p.get_by_label("Titel", exact=True).fill("Vrije routine")
    p.get_by_label("Alex", exact=True).check()
    p.get_by_label("Titel stap 1", exact=True).fill("Vrij spelen")
    use_time = p.get_by_role("checkbox", name="Tijdvenster gebruiken", exact=True)
    if clear_fields:
        p.get_by_label("Vanaf", exact=True).fill("")
        p.get_by_label("Tot", exact=True).fill("")
    else:
        use_time.uncheck()
    expect(p.get_by_role("checkbox", name="Tijdvenster gebruiken", exact=True)).not_to_be_checked()
    expect(p.get_by_label("Vanaf", exact=True)).to_be_disabled()
    expect(p.get_by_label("Tot", exact=True)).to_be_disabled()
    use_time.check()
    expect(p.get_by_label("Vanaf", exact=True)).to_have_value("07:00")
    expect(p.get_by_label("Tot", exact=True)).to_have_value("09:00")
    use_time.uncheck()
    p.get_by_role("button", name="Opslaan", exact=False).click()
    expect(p.locator("#dialog")).to_be_hidden()
    section(p, "Agenda")
    p.get_by_role("button", name="Dag", exact=True).click()
    agenda = p.get_by_label("Dagagenda", exact=True)
    expect(agenda).to_be_visible()
    expect(
        agenda.locator(".calendar-routine-row .agenda-routine").filter(has_text="Vrije routine")
    ).to_be_visible()
    expect(
        agenda.locator(".day-timeline .agenda-routine").filter(has_text="Vrije routine")
    ).to_have_count(0)


def test_returning_from_daily_routines_loads_entire_agenda_period_without_polling(routines):
    p, day, timed, untimed, alex, sam = routines
    p.clock.install()
    p.clock.pause_at(datetime.now(timezone.utc) + timedelta(seconds=1))
    p.reload()
    p.get_by_role("button", name="Week", exact=True).click()
    expect(p.locator(".day-timeline .agenda-routine")).to_have_count(7)
    p.get_by_role("navigation", name="Gezinsplanner").get_by_role(
        "button", name="Routines", exact=True
    ).click()
    # The daily routine overview polls only the selected day. Freeze future polling
    # so returning to the agenda must load its own period immediately.
    with p.expect_response(
        lambda response: "/api/state?" in response.url and "period=" not in response.url
    ):
        p.clock.fast_forward(1600)
    expect(p.locator(".routine-grid [data-run]")).to_have_count(6)
    with p.expect_response(
        lambda response: "/api/state?" in response.url and "period=week" in response.url,
        timeout=5000,
    ):
        p.get_by_role("navigation", name="Gezinsplanner").get_by_role(
            "button", name="Agenda", exact=True
        ).click()
    expect(p.locator(".day-timeline .agenda-routine")).to_have_count(7)
    expect(p.locator(".calendar-routine-row .agenda-routine")).to_have_count(7)
    p.get_by_role("button", name="Volgende week", exact=True).click()
    expect(p.locator(".day-heading").first).to_have_attribute(
        "data-day", str(day - timedelta(days=day.weekday()) + timedelta(days=7))
    )
    expect(p.locator(".day-timeline .agenda-routine")).to_have_count(7)
    shown_days = p.locator(".day-heading").evaluate_all(
        "buttons => buttons.map(button => button.dataset.day)"
    )
    assert (
        p.locator(".day-timeline .agenda-routine").evaluate_all(
            "cards => cards.map(card => card.dataset.routineDay)"
        )
        == shown_days
    )


def test_daily_routine_starting_today_appears_on_future_days_not_before_start(dashboard):
    p = dashboard
    assert p.request.post(p.url + "api/login", headers=HEAD, data={"password": PASSWORD}).ok
    day = date.fromisoformat(p.request.get(p.url + "api/state").json()["day"])
    alex = create(p, "members", {"name": "Alex", "color": "#aa7755"})
    routine_id = create(
        p,
        "routines",
        {
            "title": "Elke avond",
            "date": str(day),
            "members": [alex],
            "weekdays": list(range(7)),
            "start_time": "18:30",
            "end_time": "19:30",
            "steps": [{"text": "Lezen"}],
        },
    )
    p.reload()
    p.get_by_role("button", name="Week", exact=True).click()
    expect(p.locator(".agenda-routine")).to_have_count(7 - day.weekday())
    p.get_by_role("button", name="3 dagen", exact=True).click()
    expect(p.locator(".agenda-routine")).to_have_count(3)
    for offset in range(3):
        expect(card(p, routine_id, day + timedelta(days=offset))).to_have_count(1)
    p.get_by_role("button", name="Week", exact=True).click()
    p.get_by_role("button", name="Volgende week", exact=True).click()
    expect(p.locator(".day-heading").first).to_have_attribute(
        "data-day", str(day - timedelta(days=day.weekday()) + timedelta(days=7))
    )
    expect(p.locator(".agenda-routine")).to_have_count(7)
    assert p.locator(".agenda-routine").evaluate_all(
        "cards => cards.map(card => card.dataset.routineDay)"
    ) == p.locator(".day-heading").evaluate_all(
        "buttons => buttons.map(button => button.dataset.day)"
    )


def test_late_daily_routine_response_cannot_replace_week_after_navigation(routines):
    p, day, timed, untimed, alex, sam = routines
    p.clock.install()
    p.clock.pause_at(datetime.now(timezone.utc) + timedelta(seconds=1))
    p.reload()
    p.get_by_role("button", name="Week", exact=True).click()
    expect(p.locator(".day-timeline .agenda-routine")).to_have_count(7)
    pending = []

    def hold_daily_response(route):
        if "period=" not in route.request.url:
            pending.append(route)
        else:
            route.continue_()

    p.route("**/api/state*", hold_daily_response)
    p.get_by_role("navigation", name="Gezinsplanner").get_by_role(
        "button", name="Routines", exact=True
    ).click()
    with p.expect_request(
        lambda request: "/api/state?" in request.url and "period=" not in request.url
    ):
        p.clock.fast_forward(1600)
    expect(p.locator(".routine-grid")).to_be_visible()
    try:
        assert len(pending) == 1
        with p.expect_response(
            lambda response: "/api/state?" in response.url and "period=week" in response.url,
            timeout=5000,
        ):
            p.get_by_role("navigation", name="Gezinsplanner").get_by_role(
                "button", name="Agenda", exact=True
            ).click()
            route = pending.pop()
            route.fulfill(response=route.fetch())
        expect(p.locator(".day-timeline .agenda-routine")).to_have_count(7)
        expect(p.locator(".calendar-routine-row .agenda-routine")).to_have_count(7)
    finally:
        for route in pending:
            route.abort()


def test_previously_viewed_future_week_updates_after_routine_is_renamed_and_rescheduled(dashboard):
    p = dashboard
    assert p.request.post(p.url + "api/login", headers=HEAD, data={"password": PASSWORD}).ok
    day = date.fromisoformat(p.request.get(p.url + "api/state").json()["day"])
    monday = day - timedelta(days=day.weekday())
    next_monday = monday + timedelta(days=7)
    alex = create(p, "members", {"name": "Alex", "color": "#aa7755"})
    original = {
        "title": "Ochtend",
        "date": str(monday),
        "members": [alex],
        "weekdays": [0, 1, 2, 3, 4],
        "start_time": "07:00",
        "end_time": "08:00",
        "steps": [{"text": "Opstaan"}],
    }
    routine_id = create(p, "routines", original)
    # Viewing next week used to freeze the old name, time and steps permanently.
    planned = p.request.get(p.url + f"api/state?day={next_monday}&period=week").json()["runs"]
    assert len(planned) == 5
    past_before = [
        run
        for run in p.request.get(p.url + f"api/state?day={monday}&period=week").json()["runs"]
        if run["day"] < str(day)
    ]
    response = p.request.post(
        p.url + "api/entities/routines",
        headers=HEAD,
        data={
            "id": routine_id,
            "version": 1,
            "request_id": str(uuid.uuid4()),
            "action": "save",
            "body": original
            | {
                "title": "Naar bed",
                "weekdays": list(range(7)),
                "start_time": "18:30",
                "end_time": "19:30",
                "steps": [{"text": "Tanden poetsen"}, {"text": "Boekje lezen"}],
            },
        },
    )
    assert response.ok
    p.reload()
    p.get_by_role("button", name="Week", exact=True).click()
    p.get_by_role("button", name="Volgende week", exact=True).click()
    expect(p.locator(".day-heading").first).to_have_attribute("data-day", str(next_monday))
    expect(p.locator(".agenda-routine")).to_have_count(7)
    assert all(
        "Naar bed" in text and "18:30–19:30" in text and "Ochtend" not in text
        for text in p.locator(".agenda-routine").all_text_contents()
    )
    card(p, routine_id, next_monday).click()
    panel = p.locator("#routine-dialog")
    expect(
        panel.get_by_role("button", name="Voltooi Boekje lezen voor Alex", exact=True)
    ).to_be_visible()
    expect(panel).not_to_contain_text("Opstaan")
    panel.get_by_role("button", name="Sluiten", exact=True).click()
    # Earlier dated occurrences keep their original snapshot.
    past_runs = p.request.get(p.url + f"api/state?day={monday}&period=week").json()["runs"]
    by_id = {run["id"]: run for run in past_runs}
    assert all(by_id[run["id"]] == run for run in past_before)


def test_changed_future_plan_and_started_snapshot_open_their_own_steps(dashboard):
    p = dashboard
    assert p.request.post(p.url + "api/login", headers=HEAD, data={"password": PASSWORD}).ok
    day = date.fromisoformat(p.request.get(p.url + "api/state").json()["day"])
    tomorrow = day + timedelta(days=1)
    alex = create(p, "members", {"name": "Alex", "color": "#aa7755"})
    sam = create(p, "members", {"name": "Sam", "color": "#5577aa"})
    original = {
        "title": "Ochtend",
        "date": str(day),
        "members": [alex, sam],
        "weekdays": list(range(7)),
        "start_time": "07:00",
        "end_time": "08:00",
        "steps": [{"text": "Opstaan"}],
    }
    routine_id = create(p, "routines", original)
    planned = p.request.get(p.url + f"api/state?day={tomorrow}").json()["runs"]
    alex_run = next(run for run in planned if run["member"] == alex)
    sam_run = next(run for run in planned if run["member"] == sam)
    assert p.request.post(
        p.url + "api/entities/runs",
        headers=HEAD,
        data={
            "id": alex_run["id"],
            "version": alex_run["version"],
            "request_id": str(uuid.uuid4()),
            "action": "save",
            "body": {"done": [0]},
        },
    ).ok
    assert p.request.post(
        p.url + "api/entities/routines",
        headers=HEAD,
        data={
            "id": routine_id,
            "version": 1,
            "request_id": str(uuid.uuid4()),
            "action": "save",
            "body": original
            | {
                "title": "Naar bed",
                "start_time": "18:30",
                "end_time": "19:30",
                "steps": [{"text": "Boekje lezen"}],
            },
        },
    ).ok
    p.reload()
    p.get_by_role("button", name="3 dagen", exact=True).click()
    old_card = p.locator(f'[data-routine-run="{alex_run["id"]}"]')
    new_card = p.locator(f'[data-routine-run="{sam_run["id"]}"]')
    expect(old_card).to_contain_text("Ochtend")
    expect(new_card).to_contain_text("Naar bed")
    new_card.click()
    panel = p.locator("#routine-dialog")
    expect(
        panel.get_by_role("button", name="Voltooi Boekje lezen voor Sam", exact=True)
    ).to_be_visible()
    expect(panel).not_to_contain_text("Opstaan")
    panel.get_by_role("button", name="Sluiten", exact=True).click()
    old_card.click()
    expect(
        panel.get_by_role("button", name="Heropen Opstaan voor Alex", exact=True)
    ).to_be_visible()
    expect(panel).not_to_contain_text("Boekje lezen")
