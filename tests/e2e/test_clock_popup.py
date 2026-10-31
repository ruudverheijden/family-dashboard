import re

import pytest
from playwright.sync_api import expect


def test_clock_opens_large_popup_and_can_be_closed_with_keyboard(dashboard):
    page = dashboard
    clock_button = page.get_by_role("button", name="Toon grote klok")
    dialog = page.get_by_role("dialog", name="Hoe laat is het?")

    clock_button.click()
    expect(dialog).to_be_visible()
    large_clock = page.locator("#clock-popup-face svg")
    expect(large_clock).to_be_visible()
    assert large_clock.bounding_box()["width"] >= 300
    expect(page.locator("#clock-popup-time")).to_have_text(re.compile(r"\d{2}:\d{2}"))

    page.keyboard.press("Escape")
    expect(dialog).to_be_hidden()

    clock_button.focus()
    page.keyboard.press("Enter")
    expect(dialog).to_be_visible()
    page.get_by_role("button", name="Sluiten").click()
    expect(dialog).to_be_hidden()


@pytest.mark.parametrize("width", [768, 1024, 1280])
def test_clock_and_navigation_do_not_overlap(dashboard, width):
    page = dashboard
    page.set_viewport_size({"width": width, "height": 900})
    for tab in ["Home Assistant", "Immich", "Boodschappen", "Kalender"]:
        navigation = page.get_by_role("navigation", name="Hoofdnavigatie")
        navigation.get_by_role("button", name=tab, exact=True).click()
        assert page.locator(".main-tabs").evaluate("""nav => {
            const clock = document.querySelector('#clock-toggle').getBoundingClientRect();
            return [...nav.querySelectorAll('button')].every(button => {
                const box = button.getBoundingClientRect();
                return box.right <= clock.left || box.left >= clock.right ||
                    box.bottom <= clock.top || box.top >= clock.bottom;
            });
        }""")
    page.get_by_role("button", name="Toon grote klok").click()
    expect(page.get_by_role("dialog", name="Hoe laat is het?")).to_be_visible()
