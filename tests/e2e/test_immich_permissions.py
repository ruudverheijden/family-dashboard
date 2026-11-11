import pytest
from playwright.sync_api import expect


def test_missing_asset_view_shows_instruction(dashboard):
    page = dashboard

    def state(route):
        response = route.fetch()
        body = response.json()
        body["photos"] = [{"id": "denied", "album": "Testalbum"}]
        route.fulfill(response=response, json=body)

    page.route("**/api/state*", state)
    page.route(
        "**/api/photos/*",
        lambda route: route.fulfill(
            status=403, json={"detail": "Geef de API-sleutel in Immich het recht asset.view."}
        ),
    )
    page.reload()
    page.get_by_role("button", name="Immich", exact=True).click()
    expect(page.get_by_role("alert")).to_contain_text("asset.view")


@pytest.mark.parametrize("shuffle", [False, True])
def test_only_next_five_photos_are_preloaded_and_reused(dashboard, shuffle):
    page = dashboard
    requests = []

    def state(route):
        response = route.fetch()
        body = response.json()
        body["photos"] = [{"id": str(i), "album": "Testalbum"} for i in range(20)]
        route.fulfill(response=response, json=body)

    def image(route):
        requests.append(route.request.url.rsplit("/", 1)[-1])
        route.fulfill(
            content_type="image/svg+xml",
            body=('<svg xmlns="http://www.w3.org/2000/svg" width="10" height="10"/>'),
        )

    page.route("**/api/state*", state)
    page.route("**/api/photos/*", image)
    page.evaluate(
        '(shuffle) => localStorage.setItem("samen-screen", JSON.stringify({shuffle}))', shuffle
    )
    page.reload()
    entry_url = page.locator('script[type="module"]').get_attribute("src")
    module_url = entry_url.rsplit("/", 1)[0] + "/js/photos.js"
    assert requests == []
    page.get_by_role("button", name="Immich", exact=True).click()
    wait_for_preloads(page, module_url)
    expected = page.evaluate(
        "async (url) => (await import(url)).photoOrder.slice(0,6).map(p => p.id)",
        module_url,
    )
    assert set(requests) == set(expected)
    assert len(requests) == 6
    page.get_by_role("button", name="Diavoorstelling pauzeren").click()
    next_id = page.evaluate("async (url) => (await import(url)).photoOrder[1].id", module_url)
    page.get_by_role("button", name="Volgende foto").click()
    expect(page.locator("#photo")).to_have_attribute("data-asset-id", next_id)
    wait_for_preloads(page, module_url)
    assert len(requests) == 7
    assert len(set(requests)) == 7
    page.get_by_role("button", name="Kalender", exact=True).click()
    assert page.evaluate("async (url) => (await import(url)).photoCache.size", module_url) == 0


def wait_for_preloads(page, module_url):
    for _ in range(100):
        if page.evaluate(
            """async (url) => {
                const {photoCache} = await import(url);
                return photoCache.size === 6 && [...photoCache.values()].every(entry => entry.url);
            }""",
            module_url,
        ):
            return
        page.wait_for_timeout(20)
    pytest.fail("De zes afbeeldingen zijn niet geladen")
