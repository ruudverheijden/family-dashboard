"""Game acceptance uses a real server and a local, fictitious Immich upstream."""

import base64
import json
import threading
import uuid
from datetime import datetime, timedelta, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import pytest
from conftest import PASSWORD
from playwright.sync_api import expect

HEAD = {"X-Family-Request": "1"}
PNG = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAgAAAAICAIAAABLbSncAAAAEUlEQVR4nGNwSvbFihiGlgQAoWE8gZo0HtoAAAAASUVORK5CYII="
)


def test_games_and_immich_open_distinct_views(dashboard):
    dashboard.get_by_role("button", name="Immich", exact=True).click()
    album_picker = dashboard.get_by_role("button", name="Albums kiezen")
    expect(album_picker).to_be_visible()

    dashboard.get_by_role("button", name="Spelletjes", exact=True).click()
    expect(dashboard.get_by_role("heading", name="Spelletjes", exact=True)).to_be_visible()
    expect(album_picker).to_have_count(0)

    dashboard.get_by_role("button", name="Immich", exact=True).click()
    expect(album_picker).to_be_visible()


def prepare(page):
    url = page.url.rstrip("/")
    assert page.request.post(url + "/api/login", headers=HEAD, data={"password": PASSWORD}).ok
    member_id = str(uuid.uuid4())
    assert page.request.post(
        url + "/api/entities/members",
        headers=HEAD,
        data={
            "request_id": str(uuid.uuid4()),
            "id": member_id,
            "version": 0,
            "body": {"name": "Alex", "color": "#aa7755"},
        },
    ).ok
    assert page.request.post(
        url + "/api/admin/points/adjustments",
        headers=HEAD,
        data={
            "request_id": str(uuid.uuid4()),
            "member_id": member_id,
            "amount": 30,
            "reason": "Fictieve test",
        },
    ).ok
    page.reload()
    page.get_by_role("button", name="Spelletjes", exact=True).click()
    page.locator(".game-profiles button").filter(has_text="Alex").click()
    return url, member_id


def active(page, url):
    return page.request.get(url + "/api/state").json()["game_sessions"][0]


@pytest.mark.parametrize("size", [(390, 664), (750, 342), (768, 1024)])
def test_maze_purchase_resume_complete_and_layout(dashboard, size):
    p = dashboard
    p.set_viewport_size({"width": size[0], "height": size[1]})
    url, member = prepare(p)
    p.locator('[data-buy-game="maze"]').click()
    expect(p.locator("#game-dialog")).to_be_visible()
    session = active(p, url)
    assert p.request.get(url + "/api/state").json()["balances"][member]["available"] == 25
    # Polling must not rebuild the player or lose focus.
    p.get_by_role("button", name="Rechts", exact=True).focus()
    p.wait_for_timeout(1700)
    expect(p.get_by_role("button", name="Rechts", exact=True)).to_be_focused()
    p.reload()
    p.get_by_role("button", name="Spelletjes", exact=True).click()
    p.locator(".game-profiles button").filter(has_text="Alex").click()
    p.get_by_role("button", name="Verder spelen").click()
    assert active(p, url)["id"] == session["id"]
    assert active(p, url)["expires_at"] == session["expires_at"]
    grid = session["board"]["grid"]
    queue = [((1, 1), [])]
    seen = {(1, 1)}
    while queue:
        (x, y), path = queue.pop(0)
        if (x, y) == (7, 7):
            break
        for direction, dx, dy in [
            ("Rechts", 1, 0),
            ("Links", -1, 0),
            ("Omhoog", 0, -1),
            ("Omlaag", 0, 1),
        ]:
            target = x + dx, y + dy
            if target not in seen and not grid[target[1]][target[0]]:
                seen.add(target)
                queue.append((target, path + [direction]))
    for direction in path:
        with p.expect_response("**/actions"):
            p.get_by_role("button", name=direction, exact=True).click()
    expect(p.get_by_text("Goed gedaan! Je spel is klaar.")).to_be_visible()
    assert p.evaluate("document.documentElement.scrollWidth <= innerWidth")
    bounds = p.locator("#game-dialog").bounding_box()
    assert bounds["x"] >= 0 and bounds["x"] + bounds["width"] <= size[0] + 1
    p.get_by_role("button", name="Terug naar het dashboard").click()
    expect(p.locator("#game-dialog")).not_to_be_visible()


@pytest.mark.parametrize(
    "size,reduced_motion",
    [
        ((390, 664), "no-preference"),
        ((750, 342), "no-preference"),
        ((768, 1024), "no-preference"),
        ((390, 664), "reduce"),
    ],
)
def test_orchestra_visual_sequence_and_single_session(dashboard, size, reduced_motion):
    p = dashboard
    p.set_viewport_size({"width": size[0], "height": size[1]})
    p.emulate_media(reduced_motion=reduced_motion)
    url, _ = prepare(p)
    p.clock.install()
    p.clock.pause_at(datetime.now(timezone.utc) + timedelta(seconds=1))
    p.locator('[data-buy-game="orchestra"]').click()
    expect(p.locator("#game-dialog")).to_be_visible()
    expect(p.get_by_role("button", name="Geluid uitzetten", exact=True)).to_have_attribute(
        "aria-pressed", "true"
    )
    names = ["Kikker", "Poes", "Hond", "Kuiken"]
    delayed_polls = []
    for round_number in range(1, 7):
        session = active(p, url)
        assert session["board"]["round"] == round_number
        expect(p.locator(".routine-celebration")).to_have_count(0)
        p.clock.fast_forward(4600 + round_number * 800)
        for index, value in enumerate(session["board"]["sequence"]):
            if round_number == 6 and index == 5 and size[0] == 390 and reduced_motion != "reduce":
                p.route("**/api/game-sessions/*", lambda route: delayed_polls.append(route))
                p.clock.fast_forward(1000)
                p.wait_for_timeout(50)
            button = p.get_by_role("button", name=names[value], exact=True)
            expect(button).to_be_enabled()
            with p.expect_response("**/actions"):
                button.click()
    if size[0] == 390 and reduced_motion != "reduce":
        assert delayed_polls
    for route in delayed_polls:
        route.fulfill(response=route.fetch())
    p.unroute("**/api/game-sessions/*")
    celebration = p.locator('#game-dialog .routine-celebration[data-variant="orchestra"]')
    if reduced_motion == "reduce":
        expect(celebration).to_have_count(0)
    else:
        expect(celebration).to_be_visible()
        expect(celebration.locator("h2")).to_contain_text("Alex")
        icons = celebration.locator(".routine-celebration-icon").all_text_contents()
        assert len(icons) == 42
        assert set(icons) == {"🐸", "🐱", "🐶", "🐤"}
        p.clock.resume()
        expect(celebration).to_have_css("opacity", "1")
        expect(celebration.locator("h2")).to_be_in_viewport(ratio=1)
        expect(p.get_by_role("button", name="Viering sluiten")).to_be_in_viewport(ratio=1)
        if size[0] == 390:
            # Normal polling must neither replay nor remove the celebration.
            p.wait_for_timeout(1500)
            expect(celebration).to_have_count(1)
            expect(celebration).to_have_count(0, timeout=5000)
        else:
            p.get_by_role("button", name="Viering sluiten").click()
            expect(celebration).to_have_count(0)
    expect(p.get_by_text("Goed gedaan! Je spel is klaar.")).to_be_visible()
    assert p.request.get(url + "/api/state").json()["game_sessions"] == []
    p.get_by_role("button", name="Terug naar het dashboard").click()
    expect(p.locator("#game-dialog")).not_to_be_visible()


@pytest.fixture
def immich_server():
    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            if self.path.startswith("/api/albums/"):
                body = json.dumps(
                    {
                        "albumName": "Fictief album",
                        "assets": [{"id": f"photo-{i}", "type": "IMAGE"} for i in range(6)],
                    }
                ).encode()
                mime = "application/json"
            else:
                body, mime = PNG, "image/png"
            self.send_response(200)
            self.send_header("Content-Type", mime)
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, *args):
            pass

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    yield f"http://127.0.0.1:{server.server_port}"
    server.shutdown()
    server.server_close()
    thread.join()


def configure_photos(p, url, upstream):
    cfg = p.request.get(url + "/api/admin/settings").json()
    cfg.update(
        immich_url=upstream,
        immich_key="fictional-key",
        albums=["00000000-0000-4000-8000-000000000001"],
    )
    assert p.request.post(url + "/api/admin/settings", headers=HEAD, data=cfg).ok
    assert p.request.post(url + "/api/admin/sync", headers=HEAD).ok
    p.reload()
    p.get_by_role("button", name="Spelletjes", exact=True).click()
    p.locator(".game-profiles button").filter(has_text="Alex").click()


def test_memory_own_photos_and_preflight_failure(dashboard, immich_server):
    p = dashboard
    url, member = prepare(p)
    expect(p.locator('[data-buy-game="memory"]')).to_be_disabled()
    configure_photos(p, url, immich_server)
    p.route("**/api/photos/*", lambda route: route.fulfill(status=503, body="Unavailable"))
    p.locator('[data-buy-game="memory"]').click()
    expect(p.locator("#toast")).to_contain_text("geen punten afgeschreven")
    assert p.request.get(url + "/api/state").json()["balances"][member]["available"] == 30
    p.unroute("**/api/photos/*")
    p.locator('[data-buy-game="memory"]').click()
    expect(p.locator("#game-dialog")).to_be_visible()
    session_id = active(p, url)["id"]
    found = {}
    matched = set()
    # Discover pairs through visible cards, without inspecting server-private state.
    for index in range(12):
        if index in matched:
            continue
        with p.expect_response("**/actions"):
            p.locator(f'[data-card="{index}"]').click()
        session = p.request.get(url + f"/api/game-sessions/{session_id}").json()
        photo = session["board"]["cards"][index]
        if photo in found:
            other = found[photo]
            # A previously revealed pair may still be open; choose matching cards in order.
            current_open = session["board"]["open"]
            if other not in current_open and index not in session["board"]["matched"]:
                if len(current_open) == 2:
                    # Next click hides the previous mismatch, so reveal this card again afterwards.
                    with p.expect_response("**/actions"):
                        p.locator(f'[data-card="{other}"]').click()
                    with p.expect_response("**/actions"):
                        p.locator(f'[data-card="{index}"]').click()
                else:
                    with p.expect_response("**/actions"):
                        p.locator(f'[data-card="{other}"]').click()
            matched.update([other, index])
        else:
            found[photo] = index
    expect(p.get_by_text("Goed gedaan! Je spel is klaar.")).to_be_visible()
    assert p.request.get(url + "/api/state").json()["balances"][member]["available"] == 25


def test_game_price_admin_and_child_entry(dashboard):
    p = dashboard
    url, _ = prepare(p)
    p.get_by_role("button", name="Beheerinstellingen", exact=True).click()
    form = p.locator('[data-game-price="maze"]')
    form.locator("input").fill("7")
    form.get_by_role("button", name="Spelprijs opslaan").click()
    expect(form.get_by_role("status")).to_have_text("Opgeslagen")
    p.get_by_role("button", name="Sluiten", exact=True).click()
    expect(p.locator('[data-buy-game="maze"]')).to_have_text("Speel voor 7 punten")
    p.get_by_role("button", name="Kindmodus voor Alex").click()
    p.get_by_role("button", name="🎮 Naar de spelletjes").click()
    p.locator('[data-buy-game="maze"]').click()
    expect(p.locator("#game-dialog")).to_be_visible()
    p.on("dialog", lambda dialog: dialog.accept())
    p.get_by_role("button", name="Stoppen", exact=True).click()
    expect(p.get_by_text("Je spelsessie is afgelopen.")).to_be_visible()
    p.get_by_role("button", name="Terug naar het dashboard").click()
    p.get_by_role("button", name="Terug naar mijn dag").click()
    expect(p.get_by_role("heading", name="Hoi Alex!")).to_be_visible()
    assert p.request.get(url + "/api/state").json()["game_sessions"] == []


def test_price_save_preserves_other_settings_draft(dashboard):
    p = dashboard
    prepare(p)
    p.get_by_role("button", name="Beheerinstellingen", exact=True).click()
    p.get_by_label("Titel", exact=True).fill("Concepttitel")
    form = p.locator('[data-game-price="memory"]')
    form.locator("input").fill("3")
    form.get_by_role("button", name="Spelprijs opslaan").click()
    expect(form.get_by_role("status")).to_have_text("Opgeslagen")
    p.get_by_role("button", name="Sluiten", exact=True).click()
    expect(p.locator("#discard-confirmation")).to_be_visible()
    p.get_by_role("button", name="Verder bewerken", exact=True).click()
    expect(p.get_by_label("Titel", exact=True)).to_have_value("Concepttitel")
    p.get_by_role("button", name="Instellingen opslaan", exact=True).click()
    expect(p.get_by_role("heading", name="Ons dashboard instellen")).to_be_visible()
    expect(p.locator('[data-game-price="memory"] input')).to_have_value("3")


def test_uncertain_purchase_and_move_responses_do_not_duplicate(dashboard):
    p = dashboard
    url, member = prepare(p)

    def uncertain_response(route):
        response = route.fetch()
        assert response.ok
        route.fulfill(status=503, json={"detail": "Tijdelijke verbindingsfout"})

    p.route("**/api/games/maze/sessions", uncertain_response)
    p.locator('[data-buy-game="maze"]').click()
    expect(p.locator("#toast")).to_contain_text("Tijdelijke verbindingsfout")
    original = active(p, url)
    p.unroute("**/api/games/maze/sessions")
    # Either the retry button or polling's resume button may be shown first.
    p.reload()
    p.get_by_role("button", name="Spelletjes", exact=True).click()
    p.locator(".game-profiles button").filter(has_text="Alex").click()
    p.get_by_role("button", name="Verder spelen").click()
    assert active(p, url)["id"] == original["id"]
    p.route("**/api/game-sessions/*/actions", uncertain_response)
    p.get_by_role("button", name="Rechts", exact=True).click()
    expect(p.locator("#game-error")).to_contain_text("dezelfde zet opnieuw")
    changed = active(p, url)
    p.unroute("**/api/game-sessions/*/actions")
    with p.expect_response("**/actions"):
        p.get_by_role("button", name="Rechts", exact=True).click()
    assert active(p, url)["version"] == changed["version"]
    assert p.request.get(url + "/api/state").json()["balances"][member]["available"] == 25


@pytest.mark.parametrize("size", [(390, 664), (750, 342), (768, 1024), (1280, 900)])
def test_orchestra_countdown_pause_and_header_sound_control(dashboard, size):
    p = dashboard
    p.set_viewport_size({"width": size[0], "height": size[1]})
    url, _ = prepare(p)
    p.clock.install()
    p.clock.pause_at(datetime.now(timezone.utc) + timedelta(seconds=1))
    p.locator('[data-buy-game="orchestra"]').click()
    overlay = p.locator(".orchestra-countdown")
    number = p.locator("#orchestra-countdown-number")
    expect(overlay).to_be_visible()
    expect(number).to_have_text("3")
    expect(p.locator("#game-title .game-title-icon")).to_have_text("🎶")
    dialog_box = p.locator("#game-dialog").bounding_box()
    overlay_box = overlay.bounding_box()
    for dimension in ["x", "y", "width", "height"]:
        assert overlay_box[dimension] == pytest.approx(dialog_box[dimension], abs=2)
    number_box = number.bounding_box()
    assert number_box["y"] >= dialog_box["y"]
    assert number_box["y"] + number_box["height"] <= dialog_box["y"] + dialog_box["height"]
    assert (
        abs(
            (number_box["x"] + number_box["width"] / 2)
            - (dialog_box["x"] + dialog_box["width"] / 2)
        )
        <= 1
    )
    expect(overlay).to_have_css("border-radius", "0px")
    assert (
        overlay.evaluate(
            "element => getComputedStyle(element).backdropFilter || getComputedStyle(element).webkitBackdropFilter"
        )
        == "blur(12px)"
    )
    expect(p.locator(".animal-cue")).to_have_count(0)
    expect(p.locator('[data-animal="0"]')).to_be_disabled()
    sound = p.get_by_role("button", name="Geluid uitzetten", exact=True)
    expect(sound).to_have_attribute("aria-pressed", "true")
    expect(sound.locator("svg")).to_have_count(1)
    sound_box = sound.bounding_box()
    stop_box = p.get_by_role("button", name="Stoppen", exact=True).bounding_box()
    assert abs(sound_box["y"] - stop_box["y"]) <= 1
    assert sound_box["x"] + sound_box["width"] <= stop_box["x"]
    sound.click()
    expect(p.get_by_role("button", name="Geluid aanzetten", exact=True)).to_have_attribute(
        "aria-pressed", "false"
    )
    expect(number).to_have_text("3")
    p.clock.run_for(1000)
    expect(number).to_have_text("2")
    p.clock.run_for(1000)
    expect(number).to_have_text("1")
    p.clock.run_for(1000)
    expect(overlay).to_be_hidden()
    expect(p.locator(".animal-cue")).to_have_count(0)
    p.clock.run_for(1499)
    expect(p.locator(".animal-cue")).to_have_count(0)
    p.clock.run_for(1)
    expect(p.locator(".animal-cue")).to_have_count(1)
    p.clock.run_for(900)
    expect(p.locator('[data-animal="0"]')).to_be_enabled()
    repeat = p.get_by_role("button", name="Reeks opnieuw afspelen", exact=True)
    expect(repeat.locator("svg")).to_have_count(1)
    assert repeat.locator("svg").bounding_box()["width"] >= 36
    repeat_box = repeat.bounding_box()
    board_box = p.locator(".animal-board").bounding_box()
    instructions_box = p.locator(".orchestra-instructions").bounding_box()
    assert (
        abs(
            (repeat_box["x"] + repeat_box["width"] / 2)
            - (dialog_box["x"] + dialog_box["width"] / 2)
        )
        <= 1
    )
    assert repeat_box["y"] >= board_box["y"] + board_box["height"] + 16
    assert board_box["y"] >= instructions_box["y"] + instructions_box["height"] + 16
    assert repeat_box["y"] + repeat_box["height"] <= dialog_box["y"] + dialog_box["height"] - 16
    if size[0] >= 768:
        assert dialog_box["width"] > 700
    repeat.click()
    expect(overlay).to_be_hidden()
    p.clock.run_for(400)
    expect(p.locator(".animal-cue")).to_have_count(1)
    p.clock.run_for(900)
    first = active(p, url)["board"]["sequence"][0]
    with p.expect_response("**/actions"):
        p.locator(f'[data-animal="{first}"]').click()
    expect(p.locator(".orchestra-countdown")).to_be_visible()
    expect(p.locator("#orchestra-countdown-number")).to_have_text("3")
    p.clock.run_for(1000)
    expect(p.locator("#orchestra-countdown-number")).to_have_text("2")
    p.clock.run_for(1000)
    expect(p.locator("#orchestra-countdown-number")).to_have_text("1")
    p.clock.run_for(1000)
    expect(p.locator(".orchestra-countdown")).to_be_hidden()
    p.clock.run_for(1499)
    expect(p.locator(".animal-cue")).to_have_count(0)
    p.clock.run_for(1)
    expect(p.locator(".animal-cue")).to_have_count(1)
    p.on("dialog", lambda dialog: dialog.accept())
    p.get_by_role("button", name="Stoppen", exact=True).click()
    expect(p.get_by_text("Je spelsessie is afgelopen.")).to_be_visible()
    p.clock.run_for(5000)
    expect(p.locator(".orchestra-countdown")).to_have_count(0)


@pytest.mark.parametrize("sound_enabled", [True, False])
def test_orchestra_mistake_overlay_error_sound_and_retry(dashboard, sound_enabled):
    p = dashboard
    url, member = prepare(p)
    p.evaluate("""() => {
      window.playedClips = [];
      HTMLMediaElement.prototype.play = function() {
        window.playedClips.push(this.src.split('/').pop());
        return Promise.resolve();
      };
    }""")
    p.clock.install()
    p.clock.pause_at(datetime.now(timezone.utc) + timedelta(seconds=1))
    p.locator('[data-buy-game="orchestra"]').click()
    expect(p.locator("#game-dialog")).to_be_visible()
    if not sound_enabled:
        p.get_by_role("button", name="Geluid uitzetten", exact=True).click()
    p.clock.fast_forward(6000)
    first = active(p, url)["board"]["sequence"][0]
    wrong = (first + 1) % 4
    with p.expect_response("**/actions"):
        p.locator(f'[data-animal="{wrong}"]').click()
    feedback = p.locator(".orchestra-feedback")
    expect(feedback).to_be_visible()
    expect(feedback).to_contain_text("Oeps, die volgorde klopt niet.")
    expect(feedback).to_contain_text("dezelfde reeks")
    expect(p.locator(".orchestra-countdown")).to_be_hidden()
    expect(p.locator('[data-animal="0"]')).to_be_disabled()
    played = p.evaluate("window.playedClips")
    names = ["frog.wav", "cat.wav", "dog.wav", "chick.wav"]
    assert played == ([names[first], names[wrong], "error.wav"] if sound_enabled else [])
    assert active(p, url)["board"]["round"] == 1
    assert active(p, url)["board"]["mistakes"] == 1
    assert p.request.get(url + "/api/state").json()["balances"][member]["available"] == 25
    p.clock.run_for(1999)
    expect(feedback).to_be_visible()
    p.clock.run_for(1)
    expect(feedback).to_be_hidden()
    expect(p.locator("#orchestra-countdown-number")).to_have_text("3")
    p.clock.fast_forward(6000)
    with p.expect_response("**/actions"):
        p.locator(f'[data-animal="{first}"]').click()
    expect(p.locator(".orchestra-feedback")).to_be_hidden()
    assert active(p, url)["board"]["feedback"] == ""
    assert active(p, url)["board"]["round"] == 2
    p.on("dialog", lambda dialog: dialog.accept())
    p.get_by_role("button", name="Stoppen", exact=True).click()
    expect(p.get_by_text("Je spelsessie is afgelopen.")).to_be_visible()
    p.clock.fast_forward(10000)
    expect(p.locator(".orchestra-feedback")).to_have_count(0)


def test_orchestra_local_audio_files_decode_in_browser(dashboard):
    p = dashboard
    result = p.evaluate("""async () => {
      const context = new AudioContext();
      try {
        return await Promise.all(['frog', 'cat', 'dog', 'chick', 'error'].map(async name => {
          const response = await fetch(`/static/audio/orchestra/${name}.wav`);
          if (!response.ok) throw new Error(`Missing ${name}`);
          const buffer = await context.decodeAudioData(await response.arrayBuffer());
          const peak = Math.max(...buffer.getChannelData(0).map(Math.abs));
          return {name, duration: buffer.duration, peak};
        }));
      } finally { await context.close(); }
    }""")
    assert len(result) == 5
    for clip in result:
        assert 0.25 < clip["duration"] < 0.8, clip
        assert 0.05 < clip["peak"] < 0.7, clip


def test_orchestra_recording_can_play_by_default(dashboard):
    p = dashboard
    url, _ = prepare(p)
    p.evaluate("""() => {
      window.audioResults = [];
      const play = HTMLMediaElement.prototype.play;
      HTMLMediaElement.prototype.play = function() {
        const src = this.src;
        const promise = play.call(this);
        promise.then(() => window.audioResults.push({src, ok: true}),
                     error => window.audioResults.push({src, ok: false, error: error.name}));
        return promise;
      };
    }""")
    p.clock.install()
    p.clock.pause_at(datetime.now(timezone.utc) + timedelta(seconds=1))
    p.locator('[data-buy-game="orchestra"]').click()
    expect(p.get_by_role("button", name="Geluid uitzetten", exact=True)).to_have_attribute(
        "aria-pressed", "true"
    )
    first = active(p, url)["board"]["sequence"][0]
    p.clock.fast_forward(4500)
    p.wait_for_function("() => window.audioResults.length > 0")
    results = p.evaluate("window.audioResults")
    assert results[0]["ok"], results
    assert results[0]["src"].endswith(["frog.wav", "cat.wav", "dog.wav", "chick.wav"][first])
    expect(p.locator("#orchestra-audio-notice")).to_be_empty()
    p.get_by_role("button", name="Geluid uitzetten", exact=True).click()
