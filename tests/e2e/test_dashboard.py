"""Requirement IDs identify acceptance coverage; integration responses are explicit fixtures."""

from concurrent.futures import ThreadPoolExecutor
from datetime import date, datetime, time, timedelta, timezone
from zoneinfo import ZoneInfo

import httpx
import pytest
from conftest import add_member, grocery, login, save, section
from playwright.sync_api import expect

# Bounding rectangles can report 48 CSS pixels as 47.99997 in Firefox.
MIN_TOUCH_TARGET = 48 - 0.001


def assert_touch_targets(page):
    undersized = page.evaluate(
        """(minimum) => Array.from(document.querySelectorAll('button')).flatMap(button => {
            const {width, height} = button.getBoundingClientRect();
            if (!width || !height || getComputedStyle(button).visibility !== 'visible') return [];
            return width < minimum || height < minimum
                ? [{label: button.getAttribute('aria-label') || button.textContent, width, height}]
                : [];
        })""",
        MIN_TOUCH_TARGET,
    )
    assert not undersized, undersized


def test_three_day_agenda_shows_today_and_next_two_days(dashboard):
    p = dashboard
    today = date.fromisoformat(p.request.get(p.url + "api/state").json()["day"])

    def calendar_with_events(route):
        response = route.fetch()
        body = response.json()
        start = today - timedelta(days=today.weekday())
        body["events"] = [
            {
                "title": f"Afspraak dag {offset + 1}",
                "start": f"{start + timedelta(days=offset)}T09:00:00+01:00",
                "end": f"{start + timedelta(days=offset)}T10:00:00+01:00",
                "member": "",
                "calendar": "Gezin",
                "all_day": False,
            }
            for offset in range(14)
        ]
        route.fulfill(response=response, json=body)

    p.route("**/api/state*", calendar_with_events)
    p.get_by_role("button", name="3 dagen", exact=True).click()
    expect(p.get_by_role("button", name="3 dagen", exact=True)).to_have_attribute(
        "aria-pressed", "true"
    )
    assert [
        date.fromisoformat(day)
        for day in p.locator(".calendar-day-headings .day-heading").evaluate_all(
            "(columns) => columns.map(column => column.dataset.day)"
        )
    ] == [today + timedelta(days=offset) for offset in range(3)]
    expect(p.locator(".calendar")).to_have_attribute("aria-label", "3-daagse agenda")
    expect(p.locator(".day-timeline")).to_have_count(3)
    expect(p.locator(".timed-event")).to_have_count(3)
    schedule_bounds = p.locator(".calendar-day-schedules").bounding_box()
    column_bounds = p.locator(".calendar-day-schedules").evaluate(
        '(schedule) => [".calendar-day-headings .day-heading", ".day-task-cell", ".day-timeline"].map(selector => [...document.querySelectorAll(selector)].map(column => {const {x, width} = column.getBoundingClientRect(); return {x, width}}))'
    )
    header_bounds, task_bounds, timeline_bounds = column_bounds
    for day_index in range(3):
        for bounds in (header_bounds, task_bounds):
            assert abs(bounds[day_index]["x"] - timeline_bounds[day_index]["x"]) < 1
            assert abs(bounds[day_index]["width"] - timeline_bounds[day_index]["width"]) < 1
    assert timeline_bounds[0]["x"] == pytest.approx(schedule_bounds["x"])
    assert (
        abs(
            timeline_bounds[-1]["x"]
            + timeline_bounds[-1]["width"]
            - schedule_bounds["x"]
            - schedule_bounds["width"]
        )
        < 1
    )
    next_three_day_title = f"Afspraak dag {today.weekday() + 4}"
    expect(p.locator(".timed-event").filter(has_text=next_three_day_title)).to_have_count(0)

    previous_range = p.locator(".date-nav h2").inner_text()
    p.get_by_role("button", name="Volgende 3 dagen").click()
    expect(p.locator(".date-nav h2")).not_to_have_text(previous_range)
    assert [
        date.fromisoformat(day)
        for day in p.locator(".calendar-day-headings .day-heading").evaluate_all(
            "(columns) => columns.map(column => column.dataset.day)"
        )
    ] == [today + timedelta(days=offset) for offset in range(3, 6)]
    expect(p.locator(".timed-event")).to_have_count(3)
    expect(p.locator(".timed-event").filter(has_text=next_three_day_title)).to_have_count(1)

    p.get_by_role("button", name="Week", exact=True).click()
    expect(p.locator(".day-timeline")).to_have_count(7)
    expect(p.locator(".timed-event")).to_have_count(7)


@pytest.mark.parametrize("size", [(390, 664), (750, 342), (768, 1024), (1024, 768), (1440, 1000)])
def test_navigation_responsive_UI01_09(dashboard, size):
    p = dashboard
    p.set_viewport_size(dict(zip(("width", "height"), size)))
    if size[0] >= 761:
        navigation = p.locator(".header-navigation").bounding_box()
        assert navigation["x"] + navigation["width"] / 2 == pytest.approx(size[0] / 2, abs=1)
        logo = p.locator(".brandmark").bounding_box()
        clock = p.locator("#analog-clock").bounding_box()
        assert clock["height"] == pytest.approx(logo["height"], abs=1)
        assert (
            p.locator("#clock-toggle").evaluate("element => getComputedStyle(element).marginRight")
            == "0px"
        )
    else:
        header = p.locator(".topbar").bounding_box()
        nav = p.locator(".main-tabs")
        nav_box = nav.bounding_box()
        gear = p.locator("#admin")
        assert nav.evaluate("(element) => getComputedStyle(element).position") == "static"
        assert nav_box["y"] >= header["y"]
        assert nav_box["y"] + nav_box["height"] <= header["y"] + header["height"]
        expect(p.locator(".brand")).to_be_hidden()
        expect(gear).to_be_visible()
        assert (
            gear.bounding_box()["x"] + gear.bounding_box()["width"] <= header["x"] + header["width"]
        )
    admin_button = p.locator("#admin").bounding_box()
    admin_icon = p.locator("#admin svg").bounding_box()
    assert admin_icon["x"] + admin_icon["width"] / 2 == pytest.approx(
        admin_button["x"] + admin_button["width"] / 2, abs=1
    )
    assert admin_icon["y"] + admin_icon["height"] / 2 == pytest.approx(
        admin_button["y"] + admin_button["height"] / 2, abs=1
    )
    p.get_by_role("button", name="Week", exact=True).click()
    expect(p.get_by_role("button", name="Week", exact=True)).to_have_attribute(
        "aria-pressed", "true"
    )
    previous = p.locator(".date-nav h2").inner_text()
    p.get_by_role("button", name="Volgende week").click()
    expect(p.locator(".date-nav h2")).not_to_have_text(previous)
    title = p.locator(".date-nav h2").inner_text()
    if size[0] <= 760:
        expect(p.locator(".day-task-cell").first).to_have_css("display", "flex")
        assert p.locator(".calendar").evaluate(
            "(calendar) => calendar.scrollWidth > calendar.clientWidth"
        )
        assert p.locator(".calendar-time-scroll").evaluate(
            "(timeline) => timeline.scrollWidth === timeline.clientWidth"
        )
    for tab in ["Spelletjes", "Home Assistant", "Immich", "Boodschappen", "Kalender"]:
        p.get_by_role("navigation", name="Hoofdnavigatie").get_by_role(
            "button", name=tab, exact=True
        ).click()
        clock_button = p.locator("#clock-toggle")
        clock_bounds = clock_button.bounding_box() if clock_button.is_visible() else None
        for button in p.locator(".main-tabs button:visible").all():
            expect(button).to_be_in_viewport()
            if clock_bounds:
                bounds = button.bounding_box()
                assert (
                    bounds["x"] + bounds["width"] <= clock_bounds["x"]
                    or clock_bounds["x"] + clock_bounds["width"] <= bounds["x"]
                    or bounds["y"] + bounds["height"] <= clock_bounds["y"]
                    or clock_bounds["y"] + clock_bounds["height"] <= bounds["y"]
                ), (tab, button.get_attribute("aria-label"), bounds, clock_bounds)
        assert p.evaluate("document.documentElement.scrollWidth <= innerWidth"), tab
    expect(p.locator(".date-nav h2")).to_have_text(title)
    expect(p.locator(".day-heading").first).to_contain_text("ma")
    for name in ["Taken", "Routines", "Boodschappen", "Beloningen", "Agenda"]:
        section(p, name)
        assert p.evaluate("document.documentElement.scrollWidth <= innerWidth")
    assert_touch_targets(p)


def test_shared_planner_date_and_groceries_top_level(dashboard):
    p = dashboard
    nav = p.get_by_role("navigation", name="Hoofdnavigatie")
    nav.get_by_role("button", name="Boodschappen", exact=True).click()
    expect(nav.get_by_role("button", name="Boodschappen", exact=True)).to_have_class("active")
    expect(p.locator(".planner-datebar")).to_have_count(0)
    expect(p.locator(".family-filter")).to_have_count(0)

    section(p, "Taken")
    expect(p.locator(".planner-datebar")).to_have_count(1)
    assert p.locator(".planner-datebar").evaluate(
        '(bar) => bar.getBoundingClientRect().bottom < document.querySelector(".family-filter").getBoundingClientRect().top'
    )
    initial_date = p.locator(".date-nav h2").inner_text()
    p.get_by_role("button", name="Vorige dag").click()
    expect(p.locator(".date-nav h2")).not_to_have_text(initial_date)
    selected_date = p.locator(".date-nav h2").inner_text()

    for name in ["Routines", "Beloningen"]:
        section(p, name)
        expect(p.locator(".date-nav h2")).to_have_text(selected_date)
        expect(p.locator(".planner-datebar")).to_have_count(1)

    nav.get_by_role("button", name="Boodschappen", exact=True).click()
    expect(p.locator(".planner-datebar")).to_have_count(0)
    section(p, "Taken")
    expect(p.locator(".date-nav h2")).to_have_text(selected_date)


@pytest.mark.parametrize("size", [(390, 664), (750, 342), (768, 1024), (1440, 1000)])
def test_calendar_date_stays_in_topbar_without_page_header(dashboard, size):
    p = dashboard
    p.set_viewport_size(dict(zip(("width", "height"), size)))
    if size[0] > 480:
        expect(p.locator("#calendar-date")).to_be_visible()
    else:
        expect(p.locator("#calendar-date")).to_be_hidden()
    expect(p.locator(".welcome")).to_have_count(0)
    if 480 < size[0] <= 1050:
        expect(p.locator("#calendar-date-compact")).to_be_visible()
    elif size[0] > 1050:
        expect(p.locator("#calendar-date-full")).to_be_visible()
    assert p.evaluate("document.documentElement.scrollWidth <= innerWidth")

    p.evaluate("window.scrollTo(0, document.body.scrollHeight)")
    expect(p.locator(".topbar")).to_be_in_viewport()
    if size[0] > 480:
        expect(p.locator("#calendar-date")).to_be_in_viewport()
    assert p.locator(".topbar").bounding_box()["y"] == pytest.approx(0, abs=1)


@pytest.mark.parametrize("size", [(320, 740), (390, 844), (750, 342), (768, 1024), (1440, 1000)])
def test_analog_clock_and_next_agenda_item_IM13(dashboard, size):
    p = dashboard
    now = datetime.now(timezone.utc).replace(microsecond=0)
    events = [
        {
            "title": "Verlopen afspraak",
            "start": (now - timedelta(hours=1)).isoformat(),
            "end": (now - timedelta(minutes=30)).isoformat(),
            "member": "",
            "calendar": "Gezin",
            "all_day": False,
        },
        {
            "title": "Eerstvolgende afspraak",
            "start": (now + timedelta(seconds=45)).isoformat(),
            "end": (now + timedelta(hours=1)).isoformat(),
            "member": "",
            "calendar": "Gezin",
            "all_day": False,
        },
        {
            "title": "Afspraak later",
            "start": (now + timedelta(hours=2)).isoformat(),
            "end": (now + timedelta(hours=3)).isoformat(),
            "member": "",
            "calendar": "Gezin",
            "all_day": False,
        },
    ]

    def calendar_with_events(route):
        response = route.fetch()
        body = response.json()
        body["events"] = events
        route.fulfill(response=response, json=body)

    p.clock.install(time=now)
    p.route("**/api/state*", calendar_with_events)
    p.set_viewport_size(dict(zip(("width", "height"), size)))
    p.reload()
    clock = p.get_by_role("img", name="Analoge klok")
    if size[0] <= 480:
        expect(clock).to_be_hidden()
        expect(p.locator("#calendar-date")).to_be_hidden()
        expect(p.locator("#next-agenda-item")).to_contain_text("Eerstvolgende afspraak")
        expect(p.locator("#next-agenda-item")).not_to_contain_text("Verlopen afspraak")
        assert p.evaluate("document.documentElement.scrollWidth <= innerWidth")
        return
    expect(clock).to_be_visible()
    assert p.locator("#calendar-date").locator("#analog-clock").count() == 0
    p.wait_for_function("""() => {
      const logo = document.querySelector('.brandmark');
      const style = getComputedStyle(logo);
      const logoHeight = logo.getBoundingClientRect().height ||
        Number.parseFloat(style.height) * new DOMMatrixReadOnly(style.transform).d;
      return Math.abs(
        document.querySelector('#analog-clock').getBoundingClientRect().height - logoHeight
      ) < 1;
    }""")
    clock_box = clock.bounding_box()
    date_box = p.locator("#calendar-date").bounding_box()
    assert 0 <= date_box["x"] - clock_box["x"] - clock_box["width"] <= 24
    logo_height = p.locator(".brandmark").evaluate("""element => {
      const style = getComputedStyle(element);
      return element.getBoundingClientRect().height ||
        Number.parseFloat(style.height) * new DOMMatrixReadOnly(style.transform).d;
    }""")
    assert clock_box["height"] == pytest.approx(logo_height, abs=1)
    expect(p.locator("#clock-numerals text")).to_have_count(12)
    assert set(p.locator("#clock-numerals text").all_text_contents()) == set(
        ["12", *map(str, range(1, 12))]
    )
    expect(p.locator("#next-agenda-item")).to_contain_text("Eerstvolgende afspraak")
    expect(p.locator("#next-agenda-item")).not_to_contain_text("Verlopen afspraak")
    assert p.evaluate("document.documentElement.scrollWidth <= innerWidth")

    initial_hand_position = p.locator("#clock-second-hand").get_attribute("transform")
    p.clock.fast_forward(90_000)
    assert p.locator("#clock-second-hand").get_attribute("transform") != initial_hand_position
    expect(p.locator("#next-agenda-item")).to_contain_text("Afspraak later")
    expect(p.locator("#next-agenda-item")).not_to_contain_text("Eerstvolgende afspraak")


def test_next_agenda_item_empty_state(dashboard):
    p = dashboard
    expect(p.locator("#next-agenda-item")).to_have_text("Geen volgende afspraak gepland")


@pytest.mark.parametrize("device", ["iPhone 13", "iPhone 13 landscape"])
def test_iphone13_touch_navigation_and_settings(browser, playwright, server, device):
    options = dict(playwright.devices[device])
    options.pop("default_browser_type")
    with browser.new_context(**options) as context:
        p = context.new_page()
        p.goto(server)
        if p.viewport_size["width"] <= 480:
            expect(p.locator("#calendar-date")).to_be_hidden()
        else:
            expect(p.locator("#calendar-date")).to_be_visible()
        if p.viewport_size["width"] <= 760:
            header = p.locator(".topbar").bounding_box()
            nav = p.locator(".main-tabs")
            nav_box = nav.bounding_box()
            assert nav.evaluate("(element) => getComputedStyle(element).position") == "static"
            assert nav_box["y"] >= header["y"]
            assert nav_box["y"] + nav_box["height"] <= header["y"] + header["height"]
            expect(p.locator(".brand")).to_be_hidden()
            expect(p.locator("#admin")).to_be_visible()
        for name in ["Spelletjes", "Home Assistant", "Immich", "Boodschappen", "Kalender"]:
            button = p.get_by_role("navigation", name="Hoofdnavigatie").get_by_role(
                "button", name=name, exact=True
            )
            button.tap()
            expect(button).to_be_in_viewport()
            assert p.evaluate("document.documentElement.scrollWidth <= innerWidth")
        for name in ["Taken", "Routines", "Boodschappen", "Beloningen", "Agenda"]:
            section(p, name)
            if name == "Boodschappen":
                p.get_by_role("navigation", name="Hoofdnavigatie").get_by_role(
                    "button", name=name, exact=True
                ).tap()
            else:
                p.get_by_role("navigation", name="Gezinsplanner").get_by_role(
                    "button", name=name
                ).tap()
            assert p.evaluate("document.documentElement.scrollWidth <= innerWidth")
        open_device_settings(p)
        expect(p.get_by_label("Na inactiviteit")).to_be_visible()
        assert p.locator("#dialog").evaluate("(el) => el.scrollWidth <= el.clientWidth")
        p.get_by_label("Na inactiviteit").fill("2")
        p.get_by_role("button", name="Opslaan op dit scherm").tap()
        expect(p.get_by_role("heading", name="Ons dashboard instellen")).to_be_visible()
        p.get_by_role("button", name="Sluiten", exact=True).click()


@pytest.mark.parametrize("size", [(390, 664), (1440, 1000)])
def test_profile_photos_fit_round_avatars(dashboard, size):
    p = dashboard
    p.set_viewport_size({"width": size[0], "height": size[1]})
    login(p)
    add_member(p)

    def assert_round_photos():
        images = p.locator(".avatar img:visible")
        assert images.count() > 0
        for image in images.all():
            expect(image).to_have_js_property("complete", True)
            assert image.evaluate("""img => {
                const avatar = img.parentElement;
                const style = getComputedStyle(avatar);
                const photo = getComputedStyle(img);
                const box = img.getBoundingClientRect();
                return img.naturalWidth > 0 && style.borderRadius === '50%'
                    && style.overflowX === 'hidden' && style.overflowY === 'hidden'
                    && photo.objectFit === 'cover'
                    && Math.abs(box.width - box.height) < 1
                    && Math.abs(box.width - avatar.clientWidth) < 1
                    && Math.abs(box.height - avatar.clientHeight) < 1;
            }""")

    # Family filter and header; settings list and upload preview; child welcome.
    assert_round_photos()
    p.get_by_role("button", name="Beheerinstellingen", exact=True).click()
    assert_round_photos()
    p.locator("[data-admin-member]").click()
    assert_round_photos()
    p.get_by_role("button", name="Sluiten", exact=True).click()
    p.locator("[data-child-profile]").click()
    expect(p.locator(".child-welcome .avatar img")).to_be_visible()
    assert_round_photos()


def test_admin_profile_lifecycle_GEZ01_05(dashboard):
    p = dashboard
    assert p.request.get(p.url + "api/admin/settings").status == 401
    p.get_by_role("button", name="Beheerinstellingen", exact=True).click()
    p.get_by_label("Beheerwachtwoord").fill("wrong-password")
    p.get_by_role("button", name="Ontgrendelen").click()
    expect(p.get_by_role("alert")).to_contain_text("wachtwoord klopt niet")
    p.get_by_label("Beheerwachtwoord").fill("fictional-playwright-password")
    p.get_by_role("button", name="Ontgrendelen").click()
    add_member(p)
    expect(
        p.locator("[data-member]").filter(has_text="Alex").locator(".avatar img")
    ).to_be_visible()
    p.get_by_role("button", name="Beheerinstellingen", exact=True).click()
    p.locator("[data-admin-member]").click()
    p.get_by_label("Naam", exact=True).fill("Robin")
    p.get_by_role("button", name="Opslaan", exact=True).click()
    expect(p.get_by_role("heading", name="Ons dashboard instellen")).to_be_visible()
    p.get_by_role("button", name="Sluiten", exact=True).click()
    expect(p.locator("[data-member]").filter(has_text="Robin")).to_be_visible()
    expect(
        p.locator("[data-member]").filter(has_text="Robin").locator(".avatar img")
    ).to_be_visible()
    p.get_by_role("button", name="Beheerinstellingen", exact=True).click()
    p.locator("[data-admin-member]").click()
    p.get_by_role("button", name="Foto verwijderen", exact=True).click()
    expect(p.locator("#member-avatar-preview img")).to_have_count(0)
    p.get_by_role("button", name="Opslaan", exact=True).click()
    expect(p.get_by_role("heading", name="Ons dashboard instellen")).to_be_visible()
    p.get_by_role("button", name="Sluiten", exact=True).click()
    expect(
        p.locator("[data-member]").filter(has_text="Robin").locator(".avatar img")
    ).to_have_count(0)
    p.get_by_role("button", name="Beheerinstellingen", exact=True).click()
    p.get_by_role("button", name="Vergrendelen").click()
    assert p.request.get(p.url + "api/admin/settings").status == 401
    grocery(p)


def test_dark_theme_toggle_persists_per_screen(dashboard):
    p = dashboard
    assert "blur(" in p.locator("#calendar-date").evaluate(
        "(element) => getComputedStyle(element).backdropFilter"
    )
    login(p)
    p.get_by_role("tab", name="Dit apparaat").click()
    toggle = p.get_by_role("switch", name="Donkere modus Alleen op dit scherm opgeslagen")
    expect(toggle).to_have_attribute("aria-checked", "false")
    toggle.click()
    expect(toggle).to_have_attribute("aria-checked", "true")
    assert p.locator("html").get_attribute("data-theme") == "dark"
    assert (
        p.locator("body").evaluate("(element) => getComputedStyle(element).backgroundColor")
        == "rgb(17, 20, 28)"
    )
    assert "blur(" in p.locator("#calendar-date").evaluate(
        "(element) => getComputedStyle(element).backdropFilter"
    )

    p.reload()
    assert p.locator("html").get_attribute("data-theme") == "dark"
    p.get_by_role("button", name="Beheerinstellingen", exact=True).click()
    p.get_by_role("tab", name="Dit apparaat").click()
    toggle = p.get_by_role("switch", name="Donkere modus Alleen op dit scherm opgeslagen")
    expect(toggle).to_have_attribute("aria-checked", "true")
    toggle.click()
    expect(toggle).to_have_attribute("aria-checked", "false")


def test_admin_tabs_preserve_unsaved_settings(dashboard):
    p = dashboard
    p.set_viewport_size({"width": 390, "height": 664})
    login(p)
    expect(p.locator("#screen-settings")).to_have_count(0)
    p.get_by_label("Tijdzone").fill("Europe/London")
    p.get_by_role("tab", name="Dit apparaat").click()
    expect(p.get_by_label("Tijdzone")).not_to_be_visible()
    p.get_by_label("Na inactiviteit").fill("4")
    p.get_by_role("tab", name="Algemeen", exact=True).click()
    expect(p.get_by_label("Tijdzone")).to_have_value("Europe/London")
    p.get_by_role("button", name="Instellingen opslaan", exact=True).click()
    expect(p.get_by_role("status").filter(has_text="Opgeslagen")).to_be_visible()
    expect(p.locator("#dialog")).to_be_visible()
    p.get_by_role("tab", name="Dit apparaat").click()
    expect(p.get_by_label("Na inactiviteit")).to_have_value("4")
    assert p.locator("#dialog").evaluate("(el) => el.scrollWidth <= el.clientWidth")
    p.get_by_role("button", name="Opslaan op dit scherm").click()
    expect(p.get_by_role("heading", name="Ons dashboard instellen")).to_be_visible()
    p.get_by_role("button", name="Sluiten", exact=True).click()
    assert p.evaluate("JSON.parse(localStorage.getItem('samen-screen')).idle") == 4


def test_branding_can_be_customized_from_admin(dashboard):
    p = dashboard
    login(p)
    p.get_by_label("Titel", exact=True).fill("Familie Jansen")
    p.get_by_label("Subtitel", exact=True).fill("Samen thuis")
    p.evaluate("""async () => {
        const canvas = document.createElement('canvas');
        canvas.width = canvas.height = 2;
        canvas.getContext('2d').fillRect(0, 0, 2, 2);
        const blob = await new Promise(resolve => canvas.toBlob(resolve, 'image/png'));
        const input = document.querySelector('#brand-image-file');
        const transfer = new DataTransfer();
        transfer.items.add(new File([blob], 'family.png', {type: 'image/png'}));
        input.files = transfer.files;
        input.dispatchEvent(new Event('change', {bubbles: true}));
    }""")
    expect(p.locator("#brand-image-preview img")).to_be_visible()
    p.get_by_role("button", name="Instellingen opslaan", exact=True).click()
    expect(p.locator("#brand-title")).to_have_text("Familie Jansen")
    expect(p.locator("#brand-caption")).to_have_text("Samen thuis")
    expect(p.locator(".brandmark img")).to_be_visible()
    assert p.locator(".brandmark img").get_attribute("src").startswith("/brand-image/")
    expect(p.get_by_role("heading", name="Ons dashboard instellen")).to_be_visible()
    p.get_by_role("button", name="Sluiten", exact=True).click()


def test_immich_album_selection_uses_popup_and_shows_only_chosen(dashboard):
    p = dashboard
    login(p)
    p.get_by_label("Serveradres (zonder /api)").fill("http://immich.local:2283")
    p.route(
        "**/api/admin/discover/immich",
        lambda route: route.fulfill(
            status=200,
            json=[
                {"id": "11111111-1111-4111-8111-111111111111", "name": "Vakantie"},
                {"id": "22222222-2222-4222-8222-222222222222", "name": "Verjaardag"},
                {"id": "33333333-3333-4333-8333-333333333333", "name": "Uitstapjes"},
            ],
        ),
    )

    p.get_by_role("button", name="Albums ophalen").click()
    expect(p.locator("#dialog")).to_be_visible()
    expect(p.locator("#album-dialog")).to_be_visible()
    expect(p.locator("#album-picker-list .check-label")).to_have_count(3)
    p.get_by_label("Vakantie").check()
    p.get_by_label("Uitstapjes").check()
    p.get_by_role("button", name="Selectie toepassen").click()

    expect(p.locator("#album-dialog")).not_to_be_visible()
    expect(p.locator("#dialog")).to_be_visible()
    expect(p.locator("#albums .check-label")).to_have_count(2)
    expect(p.locator("#albums")).to_contain_text("Vakantie")
    expect(p.locator("#albums")).to_contain_text("Uitstapjes")
    expect(p.locator("#albums")).not_to_contain_text("Verjaardag")
    assert p.locator("#albums input:checked").evaluate_all(
        "(inputs) => inputs.map(input => input.value)"
    ) == [
        "11111111-1111-4111-8111-111111111111",
        "33333333-3333-4333-8333-333333333333",
    ]


def test_grocery_crud_BO01_06(dashboard):
    p = dashboard
    section(p, "Boodschappen")
    details = p.get_by_role("button", name="Met details")
    add = p.get_by_role("button", name="Toevoegen", exact=True)
    assert (
        details.locator("xpath=..").get_by_role("button", name="Toevoegen", exact=True).count() == 1
    )
    assert details.bounding_box()["x"] < add.bounding_box()["x"]
    details.click()
    p.get_by_label("Wat hebben we nodig?").fill("Appels")
    p.get_by_label("Hoeveelheid").fill("2 kg")
    p.get_by_label("Notitie").fill("Groene")
    save(p)
    row = p.locator(".grocery-row")
    expect(row).to_contain_text("2 kg · Groene")
    p.get_by_role("button", name="Appels bewerken").click()
    p.get_by_label("Wat hebben we nodig?").fill("Peren")
    save(p)
    p.get_by_role("button", name="Vink af Peren").click()
    expect(p.get_by_text("IN HET MANDJE · 1")).to_be_visible()
    p.get_by_role("button", name="Heropen Peren").click()
    expect(p.get_by_text("NOG NODIG · 1")).to_be_visible()
    p.get_by_role("button", name="Peren bewerken").click()
    p.once("dialog", lambda d: d.accept())
    p.get_by_role("button", name="Verwijderen", exact=True).click()
    expect(row).to_have_count(0)
    grocery(p)
    p.get_by_role("button", name="Vink af Melk").click()
    p.once("dialog", lambda d: d.accept())
    p.get_by_role("button", name="Afgevinkte opruimen").click()
    expect(row).to_have_count(0)


def test_two_devices_polling_and_conflict_BO07_08(dashboard, browser, server):
    p = dashboard
    with browser.new_context() as other:
        q = other.new_page()
        q.goto(server)
        section(q, "Boodschappen")
        grocery(p)
        expect(q.get_by_role("button", name="Vink af Melk")).to_be_visible(timeout=2000)
        p.get_by_role("button", name="Melk bewerken").click()
        p.get_by_label("Notitie").fill("Mijn invoer")
        q.get_by_role("button", name="Melk bewerken").click()
        q.get_by_label("Notitie").fill("Ander apparaat")
        save(q)
        p.get_by_role("button", name="Opslaan", exact=True).click()
        expect(p.get_by_role("alert")).to_contain_text("Je invoer blijft staan")
        expect(p.get_by_label("Notitie")).to_have_value("Mijn invoer")
        assert p.request.get(p.url + "api/state").json()["groceries"][0]["note"] == "Ander apparaat"


def test_draft_navigation_and_escape_UI10(dashboard):
    p = dashboard
    section(p, "Boodschappen")
    p.get_by_role("textbox", name="Boodschap", exact=True).fill("Niet kwijt")
    p.once("dialog", lambda d: d.dismiss())
    p.get_by_role("button", name="Immich", exact=True).click()
    expect(p.get_by_role("textbox", name="Boodschap", exact=True)).to_have_value("Niet kwijt")
    p.get_by_role("button", name="Met details").click()
    p.get_by_label("Notitie").fill("Concept")
    p.keyboard.press("Escape")
    expect(p.get_by_label("Notitie")).to_have_value("Concept")
    confirmation = p.get_by_role("dialog", name="Niet-opgeslagen wijzigingen")
    expect(confirmation).to_be_visible()
    p.keyboard.press("Escape")
    expect(confirmation).not_to_be_visible()
    expect(p.locator("#dialog")).to_be_visible()
    p.keyboard.press("Escape")
    expect(confirmation).to_be_visible()
    confirmation.get_by_role("button", name="Wijzigingen verlaten").click()
    expect(p.locator("#dialog")).not_to_be_visible()


@pytest.mark.parametrize("response", ["offline", "invalid-json", "server-error"])
def test_failed_save_preserves_input_SYS02(dashboard, response):
    p = dashboard
    section(p, "Boodschappen")
    p.get_by_role("button", name="Met details").click()
    p.get_by_label("Wat hebben we nodig?").fill("Brood")

    def fail(route):
        if response == "offline":
            route.abort()
        elif response == "invalid-json":
            route.fulfill(status=502, body="<html>Error</html>")
        else:
            route.fulfill(status=500, json={"detail": "Opslaan mislukt"})

    p.route("**/api/entities/groceries", fail)
    p.get_by_role("button", name="Opslaan", exact=True).click()
    expect(p.get_by_role("alert")).to_be_visible()
    expect(p.get_by_label("Wat hebben we nodig?")).to_have_value("Brood")
    assert not p.request.get(p.url + "api/state").json()["groceries"]
    p.unroute("**/api/entities/groceries")
    save(p)
    expect(p.locator(".grocery-row")).to_have_count(1)


@pytest.mark.parametrize("mode,count", [("individual", 2), ("shared", 1)])
def test_task_assignment_repeat_undo_history_TK01_04(dashboard, mode, count):
    p = dashboard
    login(p)
    add_member(p)
    p.get_by_role("button", name="Beheerinstellingen", exact=True).click()
    add_member(p, "Sam")
    section(p, "Taken")
    p.get_by_role("button", name="Nieuwe taak", exact=True).click()
    p.get_by_label("Titel", exact=True).fill("Tafel dekken")
    p.get_by_label("Beschrijving").fill("Voor het ontbijt")
    p.get_by_label("Alex", exact=True).check()
    p.get_by_label("Sam", exact=True).check()
    p.get_by_label("Uitvoering").select_option(mode)
    p.get_by_label("Herhaling").select_option("daily")
    p.get_by_label("Punten").fill("5")
    save(p)
    expect(p.locator(".task-row")).to_have_count(count)
    p.get_by_role("button", name="Voltooi Tafel dekken").first.click()
    expect(p.locator(".confetti-piece")).to_have_count(28, timeout=1000)
    expect(p.get_by_role("button", name="Heropen Tafel dekken")).to_have_count(1)
    p.reload()
    section(p, "Taken")
    expect(p.get_by_role("button", name="Heropen Tafel dekken")).to_have_count(1)
    p.get_by_role("button", name="Volgende dag").click()
    expect(p.get_by_role("button", name="Voltooi Tafel dekken")).to_have_count(count)
    p.get_by_role("button", name="Vorige dag").click()
    p.get_by_role("button", name="Heropen Tafel dekken").click()
    expect(p.get_by_role("button", name="Voltooi Tafel dekken")).to_have_count(count)
    p.locator("[data-member]").filter(has_text="Alex").click()
    expect(p.locator(".task-row")).to_have_count(1)
    p.get_by_role("button", name="Historie bekijken").click()
    expect(p.locator(".history-item").filter(has_text="Voortgang")).to_have_count(2)


def test_task_mode_edit_removes_duplicate_from_overview(dashboard):
    p = dashboard
    login(p)
    add_member(p)
    section(p, "Taken")
    p.get_by_role("button", name="Nieuwe taak", exact=True).click()
    p.get_by_label("Titel", exact=True).fill("Kattenbak schoonmaken")
    p.get_by_label("Alex", exact=True).check()
    p.get_by_label("Uitvoering").select_option("individual")
    save(p)
    expect(p.locator(".task-row")).to_have_count(1)
    p.get_by_role("button", name="Voltooi Kattenbak schoonmaken").click()
    p.get_by_role("button", name="Heropen Kattenbak schoonmaken").click()
    p.get_by_role("button", name="Taak bewerken").click()
    p.get_by_label("Uitvoering").select_option("shared")
    save(p)
    expect(p.locator(".task-row")).to_have_count(1)
    p.reload()
    section(p, "Taken")
    expect(p.locator(".task-row")).to_have_count(1)
    p.get_by_role("button", name="Voltooi Kattenbak schoonmaken").click()
    expect(p.get_by_role("button", name="Heropen Kattenbak schoonmaken")).to_have_count(1)


def test_task_edit_updates_overview(dashboard):
    p = dashboard
    login(p)
    add_member(p)
    section(p, "Taken")
    p.get_by_role("button", name="Nieuwe taak", exact=True).click()
    p.get_by_label("Titel", exact=True).fill("Oude titel")
    p.get_by_label("Alex", exact=True).check()
    save(p)
    row = p.locator(".task-row")
    expect(row).to_contain_text("Oude titel")

    p.get_by_role("button", name="Taak bewerken").click()
    p.get_by_label("Titel", exact=True).fill("Nieuwe titel")
    p.get_by_label("Beschrijving").fill("Bijgewerkte beschrijving")
    save(p)

    expect(row).to_contain_text("Nieuwe titel")
    expect(row).to_contain_text("Bijgewerkte beschrijving")
    expect(row).not_to_contain_text("Oude titel")


def test_task_overview_shows_all_owners_and_active_weekdays(dashboard):
    p = dashboard
    login(p)
    add_member(p)
    p.get_by_role("button", name="Beheerinstellingen", exact=True).click()
    add_member(p, "Sam")
    section(p, "Taken")
    p.get_by_role("button", name="Nieuwe taak", exact=True).click()
    p.get_by_label("Titel", exact=True).fill("Planten water geven")
    p.get_by_label("Alex", exact=True).check()
    p.get_by_label("Sam", exact=True).check()
    p.get_by_label("Herhaling").select_option("weekly")
    current_weekday = p.request.get(p.url + "api/state").json()["day"]
    first_day = date.fromisoformat(current_weekday).weekday()
    active_days = {first_day, (first_day + 2) % 7}
    for index, checkbox in enumerate(p.locator('input[name="weekdays"]').all()):
        if index not in active_days:
            checkbox.uncheck()
    save(p)

    row = p.locator(".task-row").first
    expect(row.locator(".task-owners")).to_have_text("Voor: Alex, Sam")
    expect(row.locator(".task-schedule")).to_have_text(
        ", ".join(
            ["maandag", "dinsdag", "woensdag", "donderdag", "vrijdag", "zaterdag", "zondag"][i]
            for i in sorted(active_days)
        )
    )


def test_calendar_always_shows_local_tasks_without_caldav(dashboard):
    p = dashboard
    login(p)
    add_member(p)
    today = date.fromisoformat(p.request.get(p.url + "api/state").json()["day"])
    monday = today - timedelta(days=today.weekday())
    section(p, "Taken")
    p.get_by_role("button", name="Nieuwe taak", exact=True).click()
    p.get_by_label("Titel", exact=True).fill("Dagelijks opruimen")
    p.get_by_label("Startdatum").fill(monday.isoformat())
    p.get_by_label("Herhaling").select_option("daily")
    p.get_by_label("Alex", exact=True).check()
    save(p)

    def calendar_with_event(route):
        response = route.fetch()
        body = response.json()
        body["events"] = [
            {
                "title": "CalDAV-afspraak",
                "start": f"{body['day']}T08:00:00+01:00",
                "end": f"{body['day']}T09:00:00+01:00",
                "member": "alex",
                "calendar": "Gezin",
                "all_day": False,
            }
        ]
        route.fulfill(response=response, json=body)

    p.route("**/api/state*", calendar_with_event)
    p.reload()
    cards = p.locator(".agenda-task")
    expect(cards).to_have_count(7)
    expect(p.locator(".calendar-task-row")).to_be_visible()
    assert (
        p.locator(".calendar-task-row").evaluate(
            '(row) => row.compareDocumentPosition(document.querySelector(".calendar-schedule-row")) & Node.DOCUMENT_POSITION_FOLLOWING'
        )
        == 4
    )
    expect(p.locator(".day-timeline .agenda-task")).to_have_count(0)
    for column in p.locator(".day-column").all():
        expect(column.locator(".agenda-task")).to_have_count(1)
        expect(column.locator(".agenda-task")).to_contain_text("Dagelijks opruimen")
    selected_items = p.locator(".day-timeline.selected > .event")
    expect(selected_items).to_have_count(1)
    expect(selected_items.first).to_contain_text("CalDAV-afspraak")
    expect(cards.first).to_have_css("background-color", "rgb(255, 240, 194)")
    assert p.request.get(p.url + "api/state").json()["config"]["caldav_configured"] is False

    p.get_by_role("button", name="Voltooi Dagelijks opruimen").first.click()
    expect(p.locator(".agenda-task.done")).to_have_count(1)


def test_completed_calendar_task_hides_after_five_seconds(dashboard):
    p = dashboard
    login(p)
    add_member(p)
    section(p, "Taken")
    p.get_by_role("button", name="Nieuwe taak", exact=True).click()
    p.get_by_label("Titel", exact=True).fill("Vaatwasser uitruimen")
    p.get_by_label("Alex", exact=True).check()
    save(p)
    section(p, "Agenda")

    card = p.locator(".agenda-task")
    expect(card).to_have_count(1)
    card.get_by_role("button", name="Voltooi Vaatwasser uitruimen").click()
    expect(p.locator(".agenda-task.done")).to_have_count(1)

    p.wait_for_timeout(4000)
    expect(p.locator(".agenda-task.done")).to_have_count(1)
    expect(p.locator(".agenda-task")).to_have_count(0, timeout=2000)


def test_calendar_positions_events_on_duration_based_timeline(dashboard):
    p = dashboard

    def calendar_with_timed_events(route):
        response = route.fetch()
        body = response.json()
        body["events"] = [
            {
                "title": "Lange afspraak",
                "start": f"{body['day']}T08:00:00+01:00",
                "end": f"{body['day']}T10:00:00+01:00",
                "member": "",
                "calendar": "Gezin",
                "all_day": False,
            },
            {
                "title": "Overlappende afspraak",
                "start": f"{body['day']}T09:00:00+01:00",
                "end": f"{body['day']}T10:00:00+01:00",
                "member": "",
                "calendar": "Gezin",
                "all_day": False,
            },
            {
                "title": "Vroege afspraak",
                "start": f"{body['day']}T06:00:00+01:00",
                "end": f"{body['day']}T06:30:00+01:00",
                "member": "",
                "calendar": "Gezin",
                "all_day": False,
            },
            {
                "title": "Late afspraak",
                "start": f"{body['day']}T23:00:00+01:00",
                "end": f"{body['day']}T23:30:00+01:00",
                "member": "",
                "calendar": "Gezin",
                "all_day": False,
            },
        ]
        route.fulfill(response=response, json=body)

    p.route("**/api/state*", calendar_with_timed_events)
    p.reload()
    dimensions = p.locator(".calendar-time-scroll").evaluate(
        "(calendar) => ({width: calendar.clientWidth, scrollWidth: calendar.scrollWidth, height: calendar.clientHeight, scrollHeight: calendar.scrollHeight, scrollTop: calendar.scrollTop})"
    )
    assert dimensions["scrollWidth"] == dimensions["width"], dimensions
    assert dimensions["height"] == 360, dimensions
    assert dimensions["scrollHeight"] == 1440, dimensions
    now_minute = p.evaluate(
        '(timezone) => {const parts = new Intl.DateTimeFormat("en-CA", {timeZone: timezone, hour: "2-digit", minute: "2-digit", hourCycle: "h23"}).formatToParts(new Date()); const value = Object.fromEntries(parts.filter(part => part.type !== "literal").map(part => [part.type, part.value])); return Number(value.hour) * 60 + Number(value.minute)}',
        p.request.get(p.url + "api/state").json()["config"]["timezone"],
    )
    assert dimensions["scrollTop"] == max(0, min(1080, now_minute - 120)), dimensions
    current_time = p.locator(".current-time-indicator")
    expect(current_time).to_have_count(1)
    marker_minute = current_time.evaluate(
        '(marker) => parseFloat(marker.style.getPropertyValue("--current-time-top"))'
    )
    assert abs(marker_minute - now_minute) <= 1
    expect(current_time).to_have_attribute("role", "img")
    marker_bounds = current_time.bounding_box()
    schedule_bounds = p.locator(".calendar-day-schedules").bounding_box()
    assert marker_bounds["x"] == pytest.approx(schedule_bounds["x"])
    assert marker_bounds["width"] == pytest.approx(schedule_bounds["width"])
    expect(p.locator(".calendar-hour-label").first).to_have_text("00:00")
    expect(p.locator(".calendar-hour-label").last).to_have_text("24:00")
    long_event = p.locator(".timed-event").filter(has_text="Lange afspraak")
    expect(long_event).to_have_css("top", "480px")
    expect(long_event).to_have_css("height", "120px")
    overlap = p.locator(".timed-event").filter(has_text="Overlappende afspraak")
    expect(overlap).to_have_css("height", "60px")
    expect(p.locator(".timed-event").filter(has_text="Vroege afspraak")).to_have_css("top", "360px")
    expect(p.locator(".timed-event").filter(has_text="Late afspraak")).to_have_css("top", "1380px")
    expect(p.locator(".calendar-outside-row")).to_have_count(0)
    assert long_event.evaluate("(event) => getComputedStyle(event).width") == overlap.evaluate(
        "(event) => getComputedStyle(event).width"
    )


@pytest.mark.parametrize("size", [(390, 664), (1440, 1000)])
def test_task_editor_spacing_is_consistent_when_adding_and_editing(dashboard, size):
    p = dashboard
    p.set_viewport_size(dict(zip(("width", "height"), size)))
    login(p)
    add_member(p)
    section(p, "Taken")
    p.get_by_role("button", name="Nieuwe taak", exact=True).click()

    for editing in (False, True):
        for repeat in ("once", "weekly"):
            p.locator('#edit-form select[name="repeat"]').select_option(repeat)
            gaps = p.locator(".task-editor").evaluate("""form => {
                const rect = element => element.getBoundingClientRect();
                const children = [...form.children].filter(el => !el.hidden);
                const result = children.slice(1).map((el, i) =>
                    rect(el).top - rect(children[i]).bottom);
                for (const grid of form.querySelectorAll('.form-grid')) {
                    const rows = [...grid.children];
                    for (let i = 1; i < rows.length; i++) {
                        if (rect(rows[i]).top >= rect(rows[i - 1]).bottom)
                            result.push(rect(rows[i]).top - rect(rows[i - 1]).bottom);
                    }
                }
                return result;
            }""")
            assert gaps == pytest.approx([16] * len(gaps), abs=0.5)
            for label in p.locator(".form-grid label").all():
                expect(label).to_have_css("gap", "8px")
            for selector, control in (
                (".task-icon-label", ".task-icon-trigger"),
                (".entity-members-field > label", ".member-chips"),
                (".weekday-field > label", ".weekdays"),
            ):
                label = p.locator(selector)
                if label.is_visible():
                    label_box = label.bounding_box()
                    control_box = p.locator(control).bounding_box()
                    assert control_box["y"] - label_box["y"] - label_box["height"] == pytest.approx(
                        8
                    )
            title_box = p.get_by_label("Titel", exact=True).bounding_box()
            icon_box = p.locator(".task-icon-trigger").bounding_box()
            assert title_box["y"] == pytest.approx(icon_box["y"], abs=0.5)
        if not editing:
            p.get_by_label("Titel", exact=True).fill("Consistente marges")
            p.get_by_label("Alex", exact=True).check()
            save(p)
            p.get_by_role("button", name="Taak bewerken").click()
    p.screenshot(path=f"/tmp/task-editor-spacing-{size[0]}.png")


def test_task_icon_is_selected_from_relevant_choices(dashboard):
    p = dashboard
    login(p)
    add_member(p)
    section(p, "Taken")
    p.get_by_role("button", name="Nieuwe taak", exact=True).click()
    icon_choices = p.locator("[data-task-icon]")
    assert icon_choices.count() >= 180
    icon_values = icon_choices.evaluate_all("icons => icons.map(button => button.dataset.taskIcon)")
    assert len(icon_values) == len(set(icon_values))
    assert p.locator(".task-icon-category").count() >= 8
    expect(icon_choices.filter(has_text="🧹")).to_have_count(1)
    expect(p.locator(".task-icon-picker")).to_be_hidden()
    p.locator(".task-icon-trigger").click()
    expect(p.locator(".task-icon-picker")).to_be_visible()
    p.get_by_role("searchbox", name="Zoek pictogrammen").fill("ontstoppen")
    expect(p.locator('[data-task-icon][aria-label="Ontstoppen"]')).to_be_visible()
    expect(p.locator('[data-task-icon][aria-label="Tandenpoetsen"]')).to_be_hidden()
    p.get_by_role("searchbox", name="Zoek pictogrammen").fill("bagage")
    expect(p.locator('[data-task-icon][aria-label="Koffer"]')).to_be_visible()
    expect(p.locator(".task-icon-category:visible h4")).to_have_text("Klusjes en reizen")
    p.get_by_role("searchbox", name="Zoek pictogrammen").fill("")
    p.get_by_role("button", name="Vegen", exact=True).click()
    expect(p.locator(".task-icon-picker")).to_be_hidden()
    expect(p.locator(".task-icon-trigger")).to_contain_text("🧹")
    p.get_by_label("Titel", exact=True).fill("Stofzuigen")
    p.get_by_label("Alex", exact=True).check()
    save(p)

    expect(p.locator(".task-row .task-icon").first).to_have_text("🧹")
    p.get_by_role("button", name="Taak bewerken").click()
    expect(p.locator('input[name="icon"]')).to_have_value("🧹")
    selected_icon = p.locator('[data-task-icon][aria-pressed="true"]')
    expect(selected_icon).to_have_attribute("aria-label", "Vegen")
    expect(p.locator(".task-icon-picker")).to_be_hidden()
    p.locator(".task-icon-trigger").click()
    expect(p.locator(".task-icon-picker")).to_be_visible()
    p.keyboard.press("Escape")
    expect(p.locator(".task-icon-picker")).to_be_hidden()
    expect(p.locator(".task-icon-trigger")).to_contain_text("🧹")


def test_media_icons_are_shared_across_all_icon_pickers(dashboard):
    p = dashboard
    login(p)
    add_member(p)
    expected = {
        "📺": "Televisie",
        "📻": "Radio",
        "🎧": "Muziek luisteren",
    }

    def picker_values(index=0):
        return (
            p.locator(".task-icon-picker")
            .nth(index)
            .locator("[data-task-icon]")
            .evaluate_all(
                "buttons => buttons.map(button => [button.dataset.taskIcon, button.getAttribute('aria-label')])"
            )
        )

    section(p, "Taken")
    p.get_by_role("button", name="Nieuwe taak", exact=True).click()
    task_values = picker_values(0)
    assert all([emoji, label] in task_values for emoji, label in expected.items())
    p.locator("#close-dialog").click()

    section(p, "Routines")
    p.get_by_role("button", name="Nieuwe routine", exact=True).click()
    routine_values = picker_values(0)
    assert routine_values == task_values
    p.locator(".routine-step-row .task-icon-trigger").click()
    assert picker_values(1) == task_values
    p.locator("#close-dialog").click()

    p.get_by_role("button", name="Beheerinstellingen", exact=True).click()
    p.get_by_role("button", name="Beloning toevoegen").click()
    assert picker_values() == task_values


def test_routine_progress_new_day_RT01_04(dashboard):
    p = dashboard
    p.set_viewport_size({"width": 390, "height": 844})
    # Keep background polling from starting a fetch during the deliberate reload.
    p.clock.install()
    p.clock.pause_at(datetime.now(timezone.utc) + timedelta(seconds=1))
    p.reload()
    login(p)
    add_member(p)
    section(p, "Routines")
    p.get_by_role("button", name="Nieuwe routine", exact=True).click()
    assert p.locator(".routine-step-row").evaluate("(row) => row.scrollWidth <= row.clientWidth")
    assert p.locator("#dialog").evaluate("(dialog) => dialog.scrollWidth <= dialog.clientWidth")
    p.get_by_label("Titel", exact=True).fill("Ochtend")
    p.get_by_label("Alex", exact=True).check()
    p.locator(".routine-icon-field .task-icon-trigger").click()
    p.locator('#routine-icon-picker [aria-label="Blij"]').click()
    p.get_by_label("Titel stap 1").fill("Poetsen")
    p.locator(".routine-step-row").nth(0).locator(".task-icon-trigger").click()
    search = p.locator(".routine-step-row .task-icon-search").first
    search.fill("nietbestaand")
    expect(p.locator(".routine-step-row .task-icon-no-results")).to_be_visible()
    search.fill("tanden")
    expect(p.locator('.routine-step-row [aria-label="Tandenpoetsen"]')).to_be_visible()
    expect(p.locator('.routine-step-row [aria-label="Tas"]')).to_be_hidden()
    search.fill("🪥")
    expect(p.locator('.routine-step-row [aria-label="Tandenpoetsen"]')).to_be_visible()
    search.fill("")
    picker_metrics = p.locator(".routine-step-row .task-icon-picker").first.evaluate("""picker => {
        const content = document.querySelector('#dialog-content');
        const style = getComputedStyle(content);
        const bounds = content.getBoundingClientRect();
        const pickerBounds = picker.getBoundingClientRect();
        return {
            columns: getComputedStyle(picker.querySelector('.task-icon-category-grid')).gridTemplateColumns.split(' ').length,
            pickerWidth: pickerBounds.width,
            triggerWidth: picker.parentElement.querySelector('.task-icon-trigger').getBoundingClientRect().width,
            pickerLeft: pickerBounds.left,
            pickerRight: pickerBounds.right,
            contentLeft: bounds.left + parseFloat(style.paddingLeft),
            contentRight: bounds.right - parseFloat(style.paddingRight),
        };
    }""")
    assert picker_metrics["columns"] >= 5
    assert picker_metrics["pickerWidth"] > picker_metrics["triggerWidth"]
    assert picker_metrics["pickerLeft"] >= picker_metrics["contentLeft"]
    assert picker_metrics["pickerRight"] <= picker_metrics["contentRight"]
    p.locator(".routine-step-row").nth(0).locator('[aria-label="Tandenpoetsen"]').click()
    p.get_by_role("button", name="Stap toevoegen").click()
    p.get_by_label("Titel stap 2").fill("Tas inpakken")
    p.locator(".routine-step-row").nth(1).locator(".task-icon-trigger").click()
    p.locator(".routine-step-row").nth(1).locator('[aria-label="Tas"]').click()
    save(p)
    expect(p.locator(".routine-header h2")).to_contain_text("😊")
    expect(p.locator(".routine-step-label")).to_have_text(["🪥 Poetsen", "🎒 Tas inpakken"])
    p.get_by_role("button", name="Voltooi Poetsen").click()
    expect(p.get_by_text("1 van 2 stappen klaar")).to_be_visible()
    p.reload()
    section(p, "Routines")
    expect(p.get_by_role("button", name="Heropen Poetsen")).to_be_visible()
    p.get_by_role("button", name="Volgende dag").click()
    expect(p.get_by_text("0 van 2 stappen klaar")).to_be_visible()
    p.get_by_role("button", name="Vorige dag").click()
    expect(p.get_by_text("1 van 2 stappen klaar")).to_be_visible()


def test_routine_is_visible_when_not_scheduled_today(dashboard):
    p = dashboard
    login(p)
    add_member(p)
    section(p, "Routines")
    p.get_by_role("button", name="Nieuwe routine", exact=True).click()
    p.get_by_label("Titel", exact=True).fill("Avondroutine")
    p.get_by_label("Alex", exact=True).check()
    p.get_by_label("Titel stap 1").fill("Lezen")
    p.locator(".routine-step-row").nth(0).locator(".task-icon-trigger").click()
    p.locator(".routine-step-row").nth(0).locator('[aria-label="Boeken"]').click()
    today_index = p.evaluate("""() => {
        const weekday = new Intl.DateTimeFormat('en-US', {
            weekday: 'short',
            timeZone: 'Europe/Amsterdam',
        }).format(new Date());
        return ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'].indexOf(weekday);
    }""")
    p.locator('input[name="weekdays"]').nth(today_index).uncheck()
    save(p)
    expect(p.get_by_text("Geen routines op", exact=False)).to_be_visible()
    expect(p.locator(".routine-grid > .panel")).to_have_count(1)
    expect(p.locator(".routine-preview")).to_have_count(0)
    expect(p.locator(".routine-empty button[data-day]")).to_be_visible()
    p.get_by_role("button", name="Routines beheren", exact=True).click()
    expect(p.locator("#dialog [data-template]")).to_contain_text("Avondroutine")
    p.get_by_role("button", name="Sluiten", exact=True).click()
    expect(p.get_by_role("button", name="Voltooi Lezen")).to_have_count(0)


def test_routine_overview_shows_one_card_for_multiple_members(dashboard):
    p = dashboard
    login(p)
    add_member(p)
    p.get_by_role("button", name="Beheerinstellingen", exact=True).click()
    add_member(p, "Sam")
    section(p, "Routines")
    p.get_by_role("button", name="Nieuwe routine", exact=True).click()
    p.get_by_label("Titel", exact=True).fill("Ochtendroutine")
    p.get_by_label("Alex", exact=True).check()
    p.get_by_label("Sam", exact=True).check()
    p.get_by_label("Titel stap 1").fill("Aankleden")
    save(p)

    expect(p.locator(".routine-grid > .panel")).to_have_count(1)
    expect(p.locator(".routine-step-label")).to_have_text(["✓ Aankleden"])
    expect(p.get_by_role("button", name="Voltooi Aankleden voor Alex")).to_be_visible()
    expect(p.get_by_role("button", name="Voltooi Aankleden voor Sam")).to_be_visible()
    p.get_by_role("button", name="Voltooi Aankleden voor Alex").click()
    expect(p.locator(".routine-celebration h2")).to_contain_text("Alex")
    p.get_by_role("button", name="Viering sluiten").click()
    expect(p.get_by_role("button", name="Heropen Aankleden voor Alex")).to_be_visible()
    expect(p.get_by_role("button", name="Voltooi Aankleden voor Sam")).to_be_visible()
    p.get_by_role("button", name="Voltooi Aankleden voor Sam").click()
    expect(p.locator(".routine-celebration h2")).to_contain_text("Sam")
    p.get_by_role("button", name="Viering sluiten").click()


def test_routine_completion_celebrates_only_the_last_step_with_rotating_variants(dashboard):
    p = dashboard
    login(p)
    add_member(p)
    section(p, "Routines")
    p.get_by_role("button", name="Nieuwe routine", exact=True).click()
    p.get_by_label("Titel", exact=True).fill("Ochtendroutine")
    p.get_by_label("Alex", exact=True).check()
    p.get_by_label("Titel stap 1").fill("Aankleden")
    p.get_by_role("button", name="Stap toevoegen").click()
    p.get_by_label("Titel stap 2").fill("Tas inpakken")
    save(p)

    p.get_by_role("button", name="Voltooi Aankleden").click()
    # The next step must use the saved execution version, not race the first request.
    expect(p.get_by_role("button", name="Heropen Aankleden")).to_have_attribute(
        "aria-pressed", "true"
    )
    expect(p.locator(".routine-celebration")).to_have_count(0)
    expect(p.locator(".confetti-burst")).to_have_count(0)

    variants = []
    messages = []
    message_variants = {
        "Supergoed gedaan",
        "Wat heb jij dat goed gedaan",
        "Geweldig gedaan",
        "Fantastisch",
        "Wat een topper ben jij",
        "Jij hebt dit geweldig gedaan",
        "Knap gedaan",
        "Wauw, wat goed",
        "Echt super gedaan",
        "Wat mag je trots zijn",
    }
    for completion in range(10):
        if completion:
            p.get_by_role("button", name="Viering sluiten").click()
            p.get_by_role("button", name="Heropen Tas inpakken").click()
        p.get_by_role("button", name="Voltooi Tas inpakken").click()
        celebration = p.locator(".routine-celebration")
        expect(celebration).to_be_visible()
        expect(celebration.locator(".routine-celebration-icon")).to_have_count(42)
        expect(p.locator(".confetti-burst")).to_have_count(0)
        variants.append(celebration.get_attribute("data-variant"))
        message = celebration.locator("h2").inner_text()
        assert message.endswith(", Alex!")
        assert message[:-7] in message_variants
        messages.append(message)

    assert len(set(variants)) == 10
    assert all(first != second for first, second in zip(messages, messages[1:]))


def test_ha_custom_dashboard_is_embedded_without_entity_api(dashboard):
    p = dashboard
    requests = []
    p.on("request", lambda request: requests.append(request.url))
    p.route(
        "http://homeassistant.example.test:8123/**",
        lambda route: route.fulfill(content_type="text/html", body="<h1>Mijn HA-dashboard</h1>"),
    )
    login(p)
    p.get_by_label("Serveradres", exact=True).fill("http://homeassistant.example.test:8123")
    p.get_by_label("Dashboardpad", exact=True).fill("/dashboard-family/overview")
    p.get_by_role("button", name="Instellingen opslaan").click()
    expect(p.get_by_role("heading", name="Ons dashboard instellen")).to_be_visible()
    p.get_by_role("button", name="Sluiten", exact=True).click()
    p.get_by_role("button", name="Home Assistant", exact=True).click()
    frame = p.locator("#ha-dashboard")
    expect(frame).to_be_visible()
    expect(frame).to_have_attribute(
        "src", "http://homeassistant.example.test:8123/dashboard-family/overview"
    )
    assert not p.locator("[data-ha-entity]").count()
    assert not any("/api/ha/" in url for url in requests)
    expect(
        p.frame_locator("#ha-dashboard").get_by_role("heading", name="Mijn HA-dashboard")
    ).to_be_visible()


def photos(p):
    def state(route):
        response = route.fetch()
        body = response.json()
        body["photos"] = [{"id": "one", "album": "Testalbum"}, {"id": "two", "album": "Testalbum"}]
        route.fulfill(response=response, json=body)

    p.route("**/api/state*", state)
    p.route(
        "**/api/photos/*",
        lambda r: r.fulfill(
            content_type="image/svg+xml",
            body='<svg xmlns="http://www.w3.org/2000/svg" width="100" height="50"><rect width="100" height="50" fill="green"/></svg>',
        ),
    )
    p.reload()
    expect(p.locator("#calendar-date")).to_be_visible()


@pytest.mark.parametrize("size", [(390, 664), (750, 342), (1440, 1000)])
def test_integrations_fill_screen_below_topbar(dashboard, size):
    p = dashboard
    p.set_viewport_size(dict(zip(("width", "height"), size)))

    def state(route):
        response = route.fetch()
        body = response.json()
        body["config"]["ha_url"] = "http://home-assistant.example.test:8123"
        body["config"]["ha_dashboard"] = "/dashboard-family/overview"
        body["photos"] = [{"id": "one", "album": "Testalbum"}]
        route.fulfill(response=response, json=body)

    p.route("**/api/state*", state)
    p.reload()
    p.get_by_role("button", name="Home Assistant", exact=True).click()
    frame = p.locator("#ha-dashboard")
    if size[0] > 480:
        expect(p.locator("#calendar-date")).to_be_in_viewport()
    else:
        expect(p.locator("#calendar-date")).to_be_hidden()
    assert p.evaluate("document.documentElement.scrollWidth <= innerWidth")
    expect(frame).to_have_attribute(
        "src", "http://home-assistant.example.test:8123/dashboard-family/overview"
    )
    expect(p.locator(".welcome")).to_have_count(0)
    expect(p.locator("footer")).to_have_css("display", "none")

    header = p.locator(".topbar").bounding_box()
    frame_box = frame.bounding_box()
    assert frame_box["x"] == 0
    assert frame_box["y"] == pytest.approx(header["y"] + header["height"], abs=1)
    assert frame_box["width"] == pytest.approx(size[0], abs=1)
    assert frame_box["y"] + frame_box["height"] == pytest.approx(size[1], abs=1)

    if size[0] <= 760:
        nav = p.locator(".main-tabs")
        assert nav.evaluate("(element) => getComputedStyle(element).position") == "static"
        nav_box = nav.bounding_box()
        assert nav_box["y"] >= header["y"]
        assert nav_box["y"] + nav_box["height"] <= header["y"] + header["height"]
        expect(p.locator(".brand")).to_be_hidden()
        expect(p.locator("#admin")).to_be_visible()

    p.get_by_role("button", name="Immich", exact=True).click()
    if size[0] > 480:
        expect(p.locator("#calendar-date")).to_be_in_viewport()
    else:
        expect(p.locator("#calendar-date")).to_be_hidden()
    assert p.evaluate("document.documentElement.scrollWidth <= innerWidth")
    stage_box = p.locator(".photo-stage").bounding_box()
    assert stage_box["x"] == 0
    assert stage_box["y"] == pytest.approx(header["y"] + header["height"], abs=1)
    assert stage_box["width"] == pytest.approx(size[0], abs=1)
    assert stage_box["y"] + stage_box["height"] == pytest.approx(size[1], abs=1)


def test_slideshow_controls_failure_IM02_06_10_12(dashboard):
    p = dashboard
    photos(p)
    p.get_by_role("button", name="Immich", exact=True).click()
    expect(p.locator("#photo")).to_have_attribute("data-asset-id", "one")
    expect(p.locator("#photo")).to_have_css("object-fit", "contain")
    p.get_by_role("button", name="Volgende foto").click()
    expect(p.locator("#photo")).to_have_attribute("data-asset-id", "two")
    p.get_by_role("button", name="Vorige foto").click()
    p.get_by_role("button", name="Diavoorstelling pauzeren").click()
    p.clock.install()
    p.clock.fast_forward(31000)
    expect(p.locator("#photo")).to_have_attribute("data-asset-id", "one")
    p.locator("#photo").click()
    expect(p.locator("[data-tab=photos]")).to_have_class("active")
    p.route("**/api/photos/*", lambda r: r.fulfill(status=404))
    p.reload()
    p.get_by_role("button", name="Immich", exact=True).click()
    expect(
        p.get_by_text("De foto’s zijn momenteel niet beschikbaar. Probeer het later opnieuw.")
    ).to_be_visible()


def open_device_settings(page):
    page.get_by_role("button", name="Beheerinstellingen", exact=True).click()
    expect(page.locator("#dialog")).to_be_visible()
    if page.get_by_label("Beheerwachtwoord").is_visible():
        page.get_by_label("Beheerwachtwoord").fill("fictional-playwright-password")
        page.get_by_role("button", name="Ontgrendelen").click()
    page.get_by_role("tab", name="Dit apparaat").click()


@pytest.mark.parametrize("guard", ["none", "draft", "dialog", "routine"])
def test_idle_guards_IM09_11(dashboard, guard):
    p = dashboard
    photos(p)
    open_device_settings(p)
    p.get_by_label("Na inactiviteit").fill("1")
    p.get_by_role("button", name="Opslaan op dit scherm").click()
    expect(p.get_by_role("heading", name="Ons dashboard instellen")).to_be_visible()
    p.get_by_role("button", name="Sluiten", exact=True).click()
    if guard == "draft":
        section(p, "Boodschappen")
        p.get_by_role("textbox", name="Boodschap", exact=True).fill("Concept")
    elif guard == "dialog":
        open_device_settings(p)
    elif guard == "routine":
        section(p, "Routines")
    p.clock.install()
    p.clock.fast_forward(61000)
    expected_tab = "photos" if guard == "none" else "groceries" if guard == "draft" else "calendar"
    expect(p.locator(f"[data-tab={expected_tab}]")).to_have_class("active")


def test_preferences_local_SYS08(dashboard, browser, server):
    p = dashboard
    open_device_settings(p)
    p.get_by_label("Na inactiviteit").fill("3")
    p.get_by_label("Foto’s beeldvullend uitsnijden").check()
    p.get_by_role("button", name="Opslaan op dit scherm").click()
    expect(p.get_by_role("heading", name="Ons dashboard instellen")).to_be_visible()
    p.get_by_role("button", name="Sluiten", exact=True).click()
    p.reload()
    open_device_settings(p)
    expect(p.get_by_label("Na inactiviteit")).to_have_value("3")
    expect(p.get_by_label("Foto’s beeldvullend uitsnijden")).to_be_checked()
    with browser.new_context() as other:
        q = other.new_page()
        q.goto(server)
        open_device_settings(q)
        expect(q.get_by_label("Na inactiviteit")).to_have_value("0")
        expect(q.get_by_label("Foto’s beeldvullend uitsnijden")).not_to_be_checked()


def test_keyboard_and_xss_UI07_SYS04(dashboard):
    p = dashboard
    grocery(p, "<img src=x onerror=alert(1)>")
    expect(p.locator(".grocery-row img")).to_have_count(0)
    p.get_by_role("button", name="Met details").focus()
    p.keyboard.press("Enter")
    expect(p.locator("#dialog")).to_be_visible()
    p.get_by_label("Wat hebben we nodig?").fill("Toetsenbord")
    p.keyboard.press("Enter")
    expect(p.get_by_role("button", name="Vink af Toetsenbord")).to_be_visible()
    p.get_by_role("button", name="Vink af Toetsenbord").focus()
    expect(p.get_by_role("button", name="Vink af Toetsenbord")).to_have_css(
        "outline-style", "solid"
    )
    p.keyboard.press("Space")
    expect(p.get_by_role("button", name="Heropen Toetsenbord")).to_be_visible()


def test_calendar_timezone_filter_AG01_04(dashboard):
    p = dashboard

    def calendar(route):
        response = route.fetch()
        body = response.json()
        body["day"] = "2026-10-25"
        body["members"] = [
            {"id": "alex", "name": "Alex", "color": "#aa7755", "avatar": "🌻"},
            {"id": "sam", "name": "Sam", "color": "#5577aa", "avatar": ""},
        ]
        body["events"] = [
            {
                "title": "Voor wintertijd",
                "start": "2026-10-25T00:30:00Z",
                "end": "2026-10-25T00:45:00Z",
                "member": "alex",
                "calendar": "Gezin",
                "all_day": False,
            },
            {
                "title": "Na wintertijd",
                "start": "2026-10-25T01:30:00Z",
                "end": "2026-10-25T01:45:00Z",
                "member": "sam",
                "calendar": "Gezin",
                "all_day": False,
            },
            {
                "title": "Hele dag samen",
                "start": "2026-10-24",
                "end": "2026-10-26",
                "member": "",
                "calendar": "Gezin",
                "all_day": True,
            },
        ]
        route.fulfill(response=response, json=body)

    p.route("**/api/state*", calendar)
    p.reload()
    p.get_by_role("button", name="Selecteer 25 oktober").click()
    p.get_by_role("button", name="Dag", exact=True).click()
    expect(p.locator(".event time")).to_have_text(["Hele dag", "02:30–02:45", "02:30–02:45"])
    p.locator("[data-member=alex]").click()
    expect(p.locator(".event")).to_have_count(2)
    expect(p.locator(".event").filter(has_text="Na wintertijd")).to_have_count(0)


def test_lost_response_retry_no_duplicate_BO08(dashboard):
    p = dashboard
    section(p, "Boodschappen")

    def lost(route):
        response = route.fetch()
        assert response.ok
        route.abort()

    p.route("**/api/entities/groceries", lost, times=1)
    p.get_by_role("textbox", name="Boodschap", exact=True).fill("Een brood")
    p.get_by_role("button", name="Toevoegen", exact=True).click()
    expect(p.locator("#toast")).to_contain_text("niet bevestigd")
    p.get_by_role("button", name="Toevoegen", exact=True).click()
    expect(p.locator(".grocery-row")).to_have_count(1)
    assert len(p.request.get(p.url + "api/state").json()["groceries"]) == 1


def test_simultaneous_completion_SYS03(dashboard, browser, server):
    p = dashboard
    login(p)
    add_member(p)
    section(p, "Taken")
    p.get_by_role("button", name="Nieuwe taak", exact=True).click()
    p.get_by_label("Titel", exact=True).fill("Samen opruimen")
    p.get_by_label("Alex", exact=True).check()
    p.get_by_label("Uitvoering").select_option("shared")
    save(p)
    with browser.new_context() as other:
        q = other.new_page()
        q.goto(server)
        section(q, "Taken")
        pending = []

        def hold(route):
            pending.append((route, route.request.post_data_json))

        p.route("**/api/entities/runs", hold)
        q.route("**/api/entities/runs", hold)
        p.get_by_role("button", name="Voltooi Samen opruimen").click()
        q.get_by_role("button", name="Voltooi Samen opruimen").click()
        expect(q.get_by_role("button", name="Voltooi Samen opruimen")).to_be_disabled()
        assert len(pending) == 2

        def send(entry):
            return httpx.post(
                server + "/api/entities/runs", json=entry[1], headers={"X-Family-Request": "1"}
            )

        with ThreadPoolExecutor(max_workers=2) as pool:
            responses = list(pool.map(send, pending))
        for (route, _), response in zip(pending, responses):
            assert response.status_code == 200
            route.fulfill(
                status=response.status_code, body=response.text, content_type="application/json"
            )
        expect(p.get_by_role("button", name="Heropen Samen opruimen")).to_be_visible()
        expect(q.get_by_role("button", name="Heropen Samen opruimen")).to_be_visible()
        history = p.request.get(p.url + "api/history").json()
        assert len([h for h in history if h["kind"] == "runs"]) == 1


def test_backend_disconnect_recovers_SYS02(dashboard):
    p = dashboard
    p.route("**/api/state*", lambda r: r.abort())
    expect(p.locator("#connection")).to_be_visible()
    p.unroute("**/api/state*")
    expect(p.locator("#connection")).not_to_be_visible()


def test_points_reward_request_and_parent_approval_BEL01_05(dashboard):
    p = dashboard
    login(p)
    add_member(p)
    section(p, "Taken")
    p.get_by_role("button", name="Nieuwe taak", exact=True).click()
    p.get_by_label("Titel", exact=True).fill("Bed opmaken")
    p.get_by_label("Alex", exact=True).check()
    p.get_by_label("Punten bij voltooien").fill("5")
    save(p)
    p.get_by_role("button", name="Voltooi Bed opmaken").click()

    section(p, "Beloningen")
    p.locator("[data-member]").filter(has_text="Alex").click()
    expect(p.locator(".rewards-summary")).to_contain_text("5 beschikbaar")
    p.get_by_role("button", name="Beheerinstellingen", exact=True).click()
    p.get_by_role("button", name="Beloning toevoegen").click()
    p.get_by_label("Naam", exact=True).fill("Filmavond")
    p.get_by_label("Prijs in punten").fill("4")
    p.get_by_role("button", name="Opslaan", exact=True).click()
    expect(p.get_by_role("heading", name="Ons dashboard instellen")).to_be_visible()
    p.get_by_role("button", name="Sluiten", exact=True).click()

    section(p, "Beloningen")
    p.get_by_role("button", name="Aanvragen").click()
    expect(p.get_by_text("4 gereserveerd", exact=False)).to_be_visible()
    expect(p.get_by_text("In afwachting")).to_be_visible()

    p.get_by_role("button", name="Beheerinstellingen", exact=True).click()
    p.get_by_role("button", name="Goedkeuren").click()
    expect(p.get_by_text("Beloning goedgekeurd; punten afgeschreven.")).to_be_visible()
    p.get_by_role("button", name="Sluiten").click()
    section(p, "Beloningen")
    expect(p.locator(".rewards-summary")).to_contain_text("1 beschikbaar")
    expect(p.get_by_text("Goedgekeurd", exact=True)).to_be_visible()
    p.get_by_role("button", name="Vorige dag").click()
    expect(p.get_by_text("Geen transacties op deze datum.")).to_be_visible()
    p.get_by_role("button", name="Volgende dag").click()
    expect(p.get_by_text("Goedgekeurd", exact=True)).to_be_visible()


def test_forced_refresh_waits_for_an_inflight_dashboard_request(dashboard):
    p = dashboard
    entry_url = p.locator('script[type="module"]').get_attribute("src")
    shell_url = entry_url.rsplit("/", 1)[0] + "/js/shell.js"
    p.clock.install()
    p.clock.pause_at(datetime.now(timezone.utc) + timedelta(seconds=1))
    held = []
    p.route("**/api/state*", lambda route: held.append(route), times=1)

    with p.expect_request("**/api/state*"):
        p.evaluate("async url => { void (await import(url)).refresh(true); }", shell_url)
    try:
        assert not p.evaluate(
            """async url => {
                const {refresh} = await import(url);
                window.queuedRefreshDone = false;
                refresh(true).then(() => { window.queuedRefreshDone = true; });
                await Promise.resolve();
                return window.queuedRefreshDone;
            }""",
            shell_url,
        )
    finally:
        for route in held:
            route.continue_()
    p.clock.resume()
    p.wait_for_function("window.queuedRefreshDone")


@pytest.mark.parametrize("width", [390, 1200])
def test_admin_reward_list_spacing_and_price_alignment(dashboard, width):
    p = dashboard
    p.set_viewport_size({"width": width, "height": 844})
    login(p)
    add_member(p)
    p.get_by_role("button", name="Beheerinstellingen", exact=True).click()

    for title, price in (("Filmavond", "4"), ("Iets kiezen", "12")):
        p.get_by_role("button", name="Beloning toevoegen").click()
        p.get_by_label("Naam", exact=True).fill(title)
        p.get_by_label("Prijs in punten").fill(price)
        p.get_by_role("button", name="Opslaan", exact=True).click()
        expect(p.get_by_role("heading", name="Ons dashboard instellen")).to_be_visible()

    rows = p.locator(".reward-admin-table tbody tr")
    expect(rows).to_have_count(2)
    alignment = p.locator(".reward-admin-price").evaluate_all(
        "(cells) => cells.map((cell) => Math.round(cell.getBoundingClientRect().right))"
    )
    assert len(set(alignment)) == 1
    assert (
        p.locator("[data-reward-new]").evaluate("(button) => getComputedStyle(button).marginTop")
        == "12px"
    )
    assert (
        p.locator("#new-member").evaluate("(button) => getComputedStyle(button).marginTop")
        == "12px"
    )
    widths = p.locator(".reward-admin-table").evaluate(
        """table => ({
            available: table.clientWidth,
            content: table.scrollWidth,
            cells: [...table.querySelectorAll('th, td')].map(cell => ({
                text: cell.textContent,
                available: cell.clientWidth,
                content: cell.scrollWidth
            }))
        })"""
    )
    assert widths["content"] <= widths["available"], widths


def test_parent_can_adjust_member_points_without_a_reason(dashboard):
    p = dashboard
    login(p)
    add_member(p)
    p.get_by_role("button", name="Beheerinstellingen", exact=True).click()
    p.get_by_role("button", name="Saldo aanpassen voor Alex", exact=True).click()
    expect(p.get_by_role("heading", name="Puntensaldo aanpassen · Alex")).to_be_visible()
    p.get_by_label("Correctie in punten (+ of −)").fill("5")
    expect(
        p.get_by_text("Na correctie: 5 totaal · 0 gereserveerd · 5 beschikbaar.")
    ).to_be_visible()
    p.get_by_role("button", name="Correctie opslaan").click()
    expect(p.get_by_role("heading", name="Ons dashboard instellen")).to_be_visible()
    expect(p.get_by_text("5 totaal · 0 gereserveerd · 5 beschikbaar")).to_be_visible()

    p.get_by_role("button", name="Sluiten", exact=True).click()
    section(p, "Beloningen")
    p.locator("[data-member]").filter(has_text="Alex").click()
    expect(p.get_by_text("Handmatige correctie", exact=False)).to_be_visible()
    expect(p.get_by_text("+5", exact=True)).to_be_visible()


@pytest.mark.parametrize("size", [(390, 664), (750, 342), (768, 1024)])
def test_child_mode_personal_tasks_routines_and_rewards(dashboard, size):
    p = dashboard
    p.set_viewport_size(dict(zip(("width", "height"), size)))
    state_data = p.request.get(p.url + "api/state").json()
    today = date.fromisoformat(state_data["day"])
    p.clock.install(
        time=datetime.combine(today, time(10, 30), ZoneInfo(state_data["config"]["timezone"]))
    )
    p.reload()
    p.evaluate("""() => {
      window.completionSoundStarts = 0;
      window.supersonicSoundStarts = 0;
      window.supersonicDecodedBytes = 0;
      window.AudioContext = class {
        state = 'running';
        currentTime = 0;
        destination = {};
        decodeAudioData(audioData) {
          window.supersonicDecodedBytes = audioData.byteLength;
          return Promise.resolve({});
        }
        createOscillator() {
          return {
            frequency: { setValueAtTime() {}, exponentialRampToValueAtTime() {} },
            connect() { return this; },
            start() { window.completionSoundStarts++; },
            stop() {}
          };
        }
        createBufferSource() {
          return {
            buffer: null,
            connect() { return this; },
            start() { window.supersonicSoundStarts++; }
          };
        }
        createGain() {
          return {
            gain: {
              setValueAtTime() {},
              exponentialRampToValueAtTime() {}
            },
            connect() { return this; }
          };
        }
      };
    }""")
    login(p)
    add_member(p, "Ouder", role="Ouder")
    p.get_by_role("button", name="Beheerinstellingen", exact=True).click()
    add_member(p, "Alex")
    p.get_by_role("button", name="Beheerinstellingen", exact=True).click()
    add_member(p, "Sam")

    section(p, "Taken")
    p.get_by_role("button", name="Nieuwe taak", exact=True).click()
    p.get_by_label("Titel", exact=True).fill("Speelgoed opruimen")
    p.get_by_label("Alex", exact=True).check()
    p.get_by_label("Herhaling").select_option("daily")
    p.get_by_label("Punten bij voltooien").fill("5")
    save(p)

    section(p, "Routines")

    def add_routine(title, start_time, end_time, steps):
        p.get_by_role("button", name="Nieuwe routine", exact=True).click()
        p.get_by_label("Titel", exact=True).fill(title)
        p.get_by_label("Alex", exact=True).check()
        use_time = p.get_by_role("checkbox", name="Tijdvenster gebruiken", exact=True)
        if start_time:
            use_time.check()
            p.get_by_label("Vanaf", exact=True).fill(start_time)
            p.get_by_label("Tot", exact=True).fill(end_time)
        else:
            use_time.uncheck()
        for index, step in enumerate(steps, start=1):
            if index > 1:
                p.get_by_role("button", name="Stap toevoegen").click()
            p.get_by_label(f"Titel stap {index}").fill(step)
        save(p)

    add_routine("Korte routine", "10:00", "11:00", ["Boekje lezen", "Pyjama aan"])
    add_routine(
        "Dit is een bijzonder lange middagroutine met een titel die over meerdere regels "
        "wordt afgebroken",
        "12:00",
        "13:00",
        ["Buiten spelen"],
    )
    add_routine("Vrije routine", "", "", ["Vrij spelen"])

    section(p, "Beloningen")
    p.locator("[data-member]").filter(has_text="Alex").click()
    p.get_by_role("button", name="Beheerinstellingen", exact=True).click()
    p.get_by_role("button", name="Beloning toevoegen").click()
    p.locator(".task-icon-trigger").click()
    p.get_by_role("searchbox", name="Zoek pictogrammen").fill("verjaardag")
    p.get_by_role("button", name="Taart", exact=True).click()
    expect(p.locator(".task-icon-trigger")).to_contain_text("🍰")
    p.get_by_label("Naam", exact=True).fill("Film kiezen")
    p.get_by_label("Prijs in punten").fill("5")
    p.get_by_role("button", name="Opslaan", exact=True).click()
    expect(p.get_by_role("heading", name="Ons dashboard instellen")).to_be_visible()
    p.get_by_role("button", name="Sluiten", exact=True).click()

    section(p, "Agenda")
    expect(p.locator(".child-profile-switcher .child-profile-button")).to_have_count(2)
    expect(p.locator(".child-profile-switcher")).to_be_visible()
    gap = p.evaluate("""() => {
      const profiles = document.querySelector('#child-profile-switcher').getBoundingClientRect();
      const tabs = document.querySelector('.main-tabs').getBoundingClientRect();
      return tabs.left - profiles.right;
    }""")
    assert 0 <= gap <= 8
    p.get_by_role("button", name="Kindmodus voor Alex", exact=True).click()
    expect(p.get_by_role("heading", name="Hoi Alex!")).to_be_visible()
    expect(p.locator(".main-tabs")).to_be_visible()
    expect(p.locator("#child-dashboard-tab")).to_be_visible()
    expect(p.locator("#child-dashboard-tab")).to_have_attribute("aria-current", "page")
    expect(p.locator("#admin")).to_be_hidden()
    expect(p.locator(".topbar")).to_be_visible()
    expect(p.locator("#clock-toggle")).to_be_visible()
    expect(p.locator("#analog-clock")).to_have_attribute(
        "aria-label", "Analoge klok, 10:30. Klik voor een grote klok"
    )

    expect(p.get_by_role("heading", name="Hoi Alex!")).to_be_visible()
    expect(p.get_by_role("button", name="Naar ouderweergave")).to_have_count(0)
    assert p.evaluate("document.documentElement.scrollWidth <= innerWidth")
    for card in p.locator(".child-welcome, .child-task, .child-routine-card, .child-rewards").all():
        bounds = card.bounding_box()
        assert bounds["x"] >= 0 and bounds["x"] + bounds["width"] <= size[0], bounds
    assert_touch_targets(p)
    expect(p.get_by_role("heading", name="Mijn taken")).to_be_visible()
    expect(p.get_by_role("heading", name="Mijn routines")).to_be_visible()
    expect(p.locator(".child-routine-card")).to_have_count(1)
    expect(p.locator(".child-routine-card")).to_contain_text("Korte routine")
    expect(p.locator(".child-routine-time time")).to_have_text("10:00")
    expect(p.get_by_role("img", name="Analoge klok voor starttijd 10:00")).to_be_visible()
    expect(p.locator('[data-child-routine-nav="-1"]')).to_be_disabled()
    expect(p.locator('[data-child-routine-nav="1"]')).to_be_enabled()
    initial_clock_position = p.locator(".child-routine-clock").bounding_box()

    p.clock.fast_forward(30 * 60 * 1000)
    expect(p.locator(".child-routine-card")).to_contain_text("lange middagroutine")
    expect(p.locator(".child-routine-time time")).to_have_text("12:00")
    long_title_clock_position = p.locator(".child-routine-clock").bounding_box()
    assert long_title_clock_position["x"] == pytest.approx(initial_clock_position["x"], abs=1)
    assert long_title_clock_position["y"] == pytest.approx(initial_clock_position["y"], abs=1)
    p.clock.fast_forward(2 * 60 * 60 * 1000 + 30 * 60 * 1000)
    expect(p.locator(".child-routine-card")).to_contain_text("Vrije routine")
    expect(p.locator(".child-routine-time")).to_have_count(0)
    expect(p.locator('[data-child-routine-nav="1"]')).to_be_disabled()
    expect(p.locator("#analog-clock")).to_have_attribute(
        "aria-label", "Analoge klok, 13:30. Klik voor een grote klok"
    )
    p.locator('[data-child-routine-nav="-1"]').click()
    p.locator('[data-child-routine-nav="-1"]').click()
    expect(p.locator(".child-routine-card")).to_contain_text("Korte routine")

    expect(p.get_by_role("button", name="Voltooi Speelgoed opruimen")).to_be_visible()
    expect(p.get_by_role("button", name="Nog 5 nodig")).to_be_disabled()
    expect(p.get_by_text("Nog 5 sterren voor Film kiezen")).to_be_visible()
    expect(p.locator(".child-reward-icon")).to_have_text("🍰")

    p.get_by_role("button", name="Voltooi Speelgoed opruimen").click()
    expect(p.locator(".confetti-burst .confetti-piece")).to_have_count(28)
    assert p.evaluate("window.completionSoundStarts") >= 3
    assert p.evaluate("window.supersonicSoundStarts") == 0
    task = p.locator(".child-task").filter(has_text="Speelgoed opruimen")
    expect(task).to_contain_text("Klaar!")
    expect(task.get_by_role("button", name="Heropen Speelgoed opruimen")).to_have_attribute(
        "aria-pressed", "true"
    )
    completion_sound_starts = p.evaluate("window.completionSoundStarts")
    task.get_by_role("button", name="Heropen Speelgoed opruimen").click()
    expect(task.get_by_role("button", name="Voltooi Speelgoed opruimen")).to_be_visible()
    assert p.evaluate("window.completionSoundStarts") == completion_sound_starts
    task.get_by_role("button", name="Voltooi Speelgoed opruimen").click()
    expect(task.get_by_role("button", name="Heropen Speelgoed opruimen")).to_be_visible()
    assert p.evaluate("window.completionSoundStarts") >= completion_sound_starts + 3
    expect(p.get_by_role("button", name="Vraag aan")).to_be_enabled()

    expect(p.locator(".confetti-burst")).to_have_count(0)
    p.get_by_role("button", name="Voltooi Boekje lezen voor Alex").click()
    expect(p.get_by_text("1 van 2 klaar")).to_be_visible()
    assert p.evaluate("window.completionSoundStarts") >= completion_sound_starts + 6
    assert p.evaluate("window.supersonicSoundStarts") == 0
    expect(p.locator(".confetti-burst .confetti-piece")).to_have_count(28)
    expect(p.locator(".routine-celebration")).to_have_count(0)
    p.get_by_role("button", name="Voltooi Pyjama aan voor Alex").click()
    expect(p.locator(".routine-celebration")).to_be_visible()
    expect(p.locator(".routine-celebration h2")).to_contain_text("Alex")
    p.wait_for_function("window.supersonicSoundStarts === 1")
    assert p.evaluate("window.supersonicDecodedBytes") > 0
    p.get_by_role("button", name="Viering sluiten").click()

    p.get_by_role("button", name="Vraag aan").click()
    expect(p.get_by_role("button", name="Aangevraagd")).to_be_disabled()
    expect(p.locator(".child-request-status")).to_contain_text(
        "Je aanvraag wacht op een volwassene."
    )

    p.get_by_role("navigation", name="Hoofdnavigatie").get_by_role(
        "button", name="Kalender", exact=True
    ).click()
    expect(p.locator(".subnav")).to_be_visible()
    expect(p.locator(".family-filter")).to_be_visible()
    expect(p.locator("[data-member][aria-pressed='true']")).to_contain_text("Alex")
