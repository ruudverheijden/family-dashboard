"""An open dashboard follows the configured local day without changing history."""

from datetime import date, datetime, time, timedelta
from zoneinfo import ZoneInfo

import pytest
from conftest import add_member, login, save, section
from playwright.sync_api import expect


@pytest.mark.parametrize("resume", [False, True], ids=["midnight", "resume"])
def test_child_day_rollover_resets_daily_runs_and_shows_date(dashboard, resume):
    p = dashboard
    p.set_viewport_size({"width": 390, "height": 664})
    login(p)
    add_member(p, "Alex")
    section(p, "Taken")
    p.get_by_role("button", name="Nieuwe taak", exact=True).click()
    p.get_by_label("Titel", exact=True).fill("Opruimen")
    p.get_by_label("Alex", exact=True).check()
    p.get_by_label("Herhaling").select_option("daily")
    save(p)
    section(p, "Routines")
    p.get_by_role("button", name="Nieuwe routine", exact=True).click()
    p.get_by_label("Titel", exact=True).fill("Dagritme")
    p.get_by_label("Alex", exact=True).check()
    p.get_by_label("Titel stap 1").fill("Tanden poetsen")
    save(p)

    initial = p.request.get(p.url + "api/state").json()
    day = date.fromisoformat(initial["day"])
    midnight = datetime.combine(
        day + timedelta(days=1), time(), ZoneInfo(initial["config"]["timezone"])
    )
    p.clock.install(time=midnight - timedelta(seconds=10))
    p.reload()
    p.get_by_role("button", name="Kindmodus voor Alex", exact=True).click()
    shown_date = p.locator(".child-welcome time")
    expect(shown_date).to_be_visible()
    expect(shown_date).to_have_attribute("datetime", day.isoformat())
    p.get_by_role("button", name="Voltooi Opruimen", exact=True).click()
    expect(p.get_by_role("button", name="Heropen Opruimen")).to_be_visible()
    p.get_by_role("button", name="Voltooi Tanden poetsen voor Alex").click()
    expect(p.get_by_role("button", name="Heropen Tanden poetsen voor Alex")).to_be_visible()
    p.locator(".routine-celebration-close").click()

    if resume:
        # A suspended tab gets no timer ticks until it becomes visible again.
        p.clock.set_fixed_time(midnight + timedelta(hours=8))
        p.evaluate("document.dispatchEvent(new Event('visibilitychange'))")
    else:
        p.clock.fast_forward(15_000)
    expect(shown_date).to_have_attribute("datetime", (day + timedelta(days=1)).isoformat())
    expect(p.get_by_role("button", name="Voltooi Opruimen", exact=True)).to_have_attribute(
        "aria-pressed", "false"
    )
    expect(p.get_by_role("button", name="Voltooi Tanden poetsen voor Alex")).to_have_attribute(
        "aria-pressed", "false"
    )
    assert p.evaluate("document.documentElement.scrollWidth <= innerWidth")
    old_runs = p.request.get(p.url + f"api/state?day={day}").json()["runs"]
    assert len(old_runs) == 2
    assert all(run["done"] == [0] for run in old_runs)
    p.get_by_role("navigation", name="Hoofdnavigatie").get_by_role(
        "button", name="Kalender", exact=True
    ).click()
    # The saved parent view was also showing today and must advance with it.
    expect(p.locator(".date-nav h2")).to_contain_text(str((day + timedelta(days=1)).day))


@pytest.mark.parametrize("historical", [False, True], ids=["today", "chosen-date"])
def test_parent_day_rollover_preserves_explicit_date(dashboard, historical):
    p = dashboard
    initial = p.request.get(p.url + "api/state").json()
    day = date.fromisoformat(initial["day"])
    midnight = datetime.combine(
        day + timedelta(days=1), time(), ZoneInfo(initial["config"]["timezone"])
    )
    p.clock.install(time=midnight - timedelta(seconds=10))
    p.reload()
    section(p, "Routines")
    if historical:
        p.get_by_role("button", name="Vorige dag", exact=True).click()
    selected = day - timedelta(days=1) if historical else day + timedelta(days=1)
    with p.expect_response(
        lambda response: "/api/state?" in response.url and f"day={selected}" in response.url
    ):
        p.clock.fast_forward(15_000)
    expect(p.locator(".date-nav h2")).to_contain_text(str(selected.day))


def test_parent_routine_follows_scheduled_days_and_keeps_completion_history(dashboard):
    p = dashboard
    initial = p.request.get(p.url + "api/state").json()
    day = date.fromisoformat(initial["day"])
    zone = ZoneInfo(initial["config"]["timezone"])
    midnight = datetime.combine(day + timedelta(days=1), time(), zone)
    p.clock.install(time=midnight - timedelta(seconds=10))
    p.reload()
    login(p)
    add_member(p, "Alex")
    section(p, "Routines")
    p.get_by_role("button", name="Nieuwe routine", exact=True).click()
    p.get_by_label("Titel", exact=True).fill("Gepland dagritme")
    p.get_by_label("Alex", exact=True).check()
    p.get_by_label("Titel stap 1").fill("Tanden poetsen")
    # Today and the day after tomorrow are scheduled; tomorrow is deliberately off.
    scheduled = {day.weekday(), (day + timedelta(days=2)).weekday()}
    for index in range(7):
        p.locator('input[name="weekdays"]').nth(index).set_checked(index in scheduled)
    save(p)
    p.get_by_role("button", name="Voltooi Tanden poetsen voor Alex", exact=True).click()
    expect(
        p.get_by_role("button", name="Heropen Tanden poetsen voor Alex", exact=True)
    ).to_be_visible()
    p.get_by_role("button", name="Viering sluiten").click()
    completed = p.request.get(p.url + f"api/state?day={day}").json()["runs"][0]
    history = p.request.get(p.url + "api/history").json()
    completion = [entry for entry in history if entry["entity_id"] == completed["id"]]
    assert len(completion) == 1 and completion[0]["at"]

    p.clock.fast_forward(15_000)
    expect(p.get_by_text("Geen routines op", exact=False)).to_be_visible()
    expect(p.locator("[data-run]")).to_have_count(0)
    assert not p.request.get(p.url + f"api/state?day={day + timedelta(days=1)}").json()["runs"]

    p.clock.set_fixed_time(midnight + timedelta(days=1, hours=8))
    p.evaluate("document.dispatchEvent(new Event('visibilitychange'))")
    expect(
        p.get_by_role("button", name="Voltooi Tanden poetsen voor Alex", exact=True)
    ).to_have_attribute("aria-pressed", "false")
    next_run = p.request.get(p.url + f"api/state?day={day + timedelta(days=2)}").json()["runs"][0]
    assert next_run["id"] != completed["id"] and next_run["done"] == []

    p.get_by_role("button", name="Vorige dag", exact=True).click()
    expect(p.get_by_text("Geen routines op", exact=False)).to_be_visible()
    p.get_by_role("button", name="Vorige dag", exact=True).click()
    expect(
        p.get_by_role("button", name="Heropen Tanden poetsen voor Alex", exact=True)
    ).to_have_attribute("aria-pressed", "true")
    assert p.request.get(p.url + f"api/state?day={day}").json()["runs"][0] == completed
    assert p.request.get(p.url + "api/history").json() == history
