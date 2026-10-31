"""Real HTTP server per test; never reads .env or the family's database."""

import os
import socket
import subprocess
import sys
import time
from pathlib import Path

import httpx
import pytest
from playwright.sync_api import expect

PASSWORD = "fictional-playwright-password"


@pytest.fixture
def server(tmp_path):
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        port = sock.getsockname()[1]
    url = f"http://127.0.0.1:{port}"
    env = {
        **os.environ,
        "DATA_DIR": str(tmp_path / "data"),
        "CACHE_DIR": str(tmp_path / "cache"),
        "ADMIN_PASSWORD": PASSWORD,
        "COOKIE_SECURE": "false",
    }
    with (tmp_path / "server.log").open("w+") as log:
        process = subprocess.Popen(
            [
                sys.executable,
                "-c",
                "import os,sys; from pathlib import Path; import uvicorn; "
                "from app.application import create_app; from app.config import AppConfig; "
                "cfg=AppConfig(Path(os.environ['DATA_DIR']), Path(os.environ['CACHE_DIR']), "
                "os.environ['ADMIN_PASSWORD']); "
                "uvicorn.run(create_app(cfg), host='127.0.0.1', port=int(sys.argv[1]))",
                str(port),
            ],
            cwd=Path(__file__).resolve().parents[2],
            env=env,
            stdout=log,
            stderr=log,
        )
        try:
            for _ in range(100):
                try:
                    if httpx.get(url + "/api/health").status_code == 200:
                        break
                except httpx.TransportError:
                    pass
                if process.poll() is not None:
                    log.seek(0)
                    pytest.fail(log.read())
                time.sleep(0.05)
            else:
                pytest.fail("Test server did not start")
            yield url
        finally:
            process.terminate()
            process.wait(timeout=10)


@pytest.fixture
def dashboard(page, server):
    errors = []
    page.on("pageerror", lambda error: errors.append(str(error)))
    page.goto(server)
    expect(page.locator("#calendar-date")).to_be_visible()
    yield page
    page.unroute_all(behavior="wait")
    assert not errors, errors


def login(page):
    page.get_by_role("button", name="Beheerinstellingen", exact=True).click()
    page.get_by_label("Beheerwachtwoord").fill(PASSWORD)
    page.get_by_role("button", name="Ontgrendelen").click()
    expect(page.get_by_role("heading", name="Ons dashboard instellen")).to_be_visible()


def add_member(page, name="Alex"):
    page.get_by_role("button", name="Gezinslid toevoegen").click()
    page.get_by_label("Naam", exact=True).fill(name)
    page.get_by_label("Avatar").fill("🌻")
    save(page)


def save(page):
    page.get_by_role("button", name="Opslaan", exact=True).click()
    expect(page.locator("#dialog")).not_to_be_visible()


def section(page, name):
    if name == "Boodschappen":
        page.get_by_role("navigation", name="Hoofdnavigatie").get_by_role(
            "button", name=name, exact=True
        ).click()
    else:
        page.get_by_role("navigation", name="Hoofdnavigatie").get_by_role(
            "button", name="Kalender", exact=True
        ).click()
        page.get_by_role("navigation", name="Gezinsplanner").get_by_role(
            "button", name=name
        ).click()


def grocery(page, name="Melk"):
    section(page, "Boodschappen")
    page.get_by_role("textbox", name="Boodschap", exact=True).fill(name)
    page.get_by_role("button", name="Toevoegen", exact=True).click()
    expect(page.get_by_role("button", name=f"Vink af {name}", exact=True)).to_be_visible()
