from conftest import add_member, login, section
from playwright.sync_api import expect


def test_task_dialog_closes_on_backdrop_and_preserves_unsaved_changes(dashboard):
    page = dashboard
    login(page)
    add_member(page)
    section(page, "Taken")
    dialog = page.locator("#dialog")

    page.get_by_role("button", name="Nieuwe taak", exact=True).click()
    expect(dialog).to_be_visible()
    page.mouse.click(1, 1)
    expect(dialog).to_be_hidden()

    page.get_by_role("button", name="Nieuwe taak", exact=True).click()
    expect(dialog).to_be_visible()
    page.get_by_label("Titel", exact=True).fill("Ongeslagen taak")
    page.mouse.click(1, 1)
    confirmation = page.get_by_role("dialog", name="Niet-opgeslagen wijzigingen")
    expect(confirmation).to_be_visible()

    page.mouse.click(1, 1)
    expect(confirmation).to_be_hidden()
    expect(dialog).to_be_visible()
    expect(page.get_by_label("Titel", exact=True)).to_have_value("Ongeslagen taak")

    page.mouse.click(1, 1)
    page.get_by_role("button", name="Wijzigingen verlaten").click()
    expect(dialog).to_be_hidden()
