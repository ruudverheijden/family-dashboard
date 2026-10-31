"""Read-only Immich adapter and permission-bound photo cache."""

import hashlib
import os
import threading
from pathlib import Path

import httpx

from ..db import settings
from .common import log_failure, set_status


def immich_get(cfg, path):
    return httpx.get(
        cfg["immich_url"].rstrip("/") + "/api" + path,
        headers={"x-api-key": cfg["immich_key"]},
        timeout=20,
        follow_redirects=False,
    )


def albums(cfg):
    response = immich_get(cfg, "/albums")
    response.raise_for_status()
    return [{"id": a["id"], "name": a["albumName"]} for a in response.json()]


def album_assets(cfg, album_id, album):
    # Older servers embed assets; newer servers expose them through search.
    if "assets" in album:
        yield from album["assets"]
        return
    page = 1
    while True:
        response = httpx.post(
            cfg["immich_url"].rstrip("/") + "/api/search/metadata",
            headers={"x-api-key": cfg["immich_key"]},
            json={"albumIds": [album_id], "type": "IMAGE", "size": 1000, "page": page},
            timeout=20,
            follow_redirects=False,
        )
        response.raise_for_status()
        result = response.json()["assets"]
        yield from result["items"]
        next_page = result.get("nextPage")
        if next_page is None:
            return
        next_page = int(next_page)
        if next_page <= page:
            raise ValueError("Ongeldige paginering")
        page = next_page


class PhotoLibrary:
    def __init__(self, database, cache_dir, cache_limit):
        self.database = database
        self.cache = Path(cache_dir)
        self.cache_limit = cache_limit
        self.assets = {}
        self.lock = threading.RLock()
        self.sync_guard = threading.Lock()
        self.generation = 0

    def snapshot(self):
        with self.lock:
            return list(self.assets.values())

    def invalidate(self):
        with self.lock:
            self.generation += 1
            self.assets = {}
            self.purge_cache()

    def sync(self):
        # Prevent two refreshes from publishing out of order, without blocking readers.
        with self.sync_guard:
            with self.lock, self.database.connect() as db:
                cfg = settings(db)
                generation = self.generation
            fresh = {}
            error = None
            configured = bool(cfg["immich_url"] and cfg["albums"])
            try:
                if configured:
                    for album in cfg["albums"]:
                        response = immich_get(cfg, "/albums/" + album)
                        response.raise_for_status()
                        info = response.json()
                        for asset in album_assets(cfg, album, info):
                            if asset.get("type") == "IMAGE" and not asset.get("isTrashed", False):
                                fresh[asset["id"]] = {
                                    "id": asset["id"],
                                    "album": info.get("albumName", "Album"),
                                }
            except Exception as failure:
                error = failure
                fresh = {}
                log_failure("Immich synchronization", failure)
            with self.lock, self.database.connect() as db:
                db.execute("BEGIN IMMEDIATE")
                if generation != self.generation or settings(db)["version"] != cfg["version"]:
                    return
                if set(fresh) != set(self.assets) or error is not None:
                    self.generation += 1
                self.assets = fresh
                self.purge_cache()
                if error:
                    denied = isinstance(
                        error, httpx.HTTPStatusError
                    ) and error.response.status_code in (401, 403)
                    message = (
                        "Immich weigert toegang. Geef de API-sleutel de rechten album.read, asset.read en asset.view."
                        if denied
                        else "Immich niet bereikbaar of album niet toegankelijk. Controleer de verbinding en API-sleutel."
                    )
                    set_status(db, "immich", False, message)
                elif configured:
                    set_status(db, "immich", True, "Albums bijgewerkt")

    def purge_cache(self):
        # Also used by settings invalidation; callers may already hold this RLock.
        with self.lock:
            self.cache.mkdir(parents=True, exist_ok=True)
            allowed = {hashlib.sha256(x.encode()).hexdigest() for x in self.assets}
            for path in self.cache.iterdir():
                if path.is_file() and path.name not in allowed:
                    path.unlink(missing_ok=True)
            files = sorted(
                (p for p in self.cache.iterdir() if p.is_file()), key=lambda p: p.stat().st_mtime
            )
            total = sum(p.stat().st_size for p in files)
            for path in files:
                if total <= self.cache_limit:
                    break
                total -= path.stat().st_size
                path.unlink(missing_ok=True)

    def photo(self, asset_id):
        with self.lock:
            if asset_id not in self.assets:
                raise KeyError(asset_id)
            self.cache.mkdir(parents=True, exist_ok=True)
            path = self.cache / hashlib.sha256(asset_id.encode()).hexdigest()
            if path.exists():
                os.utime(path, None)
                return path.read_bytes()
            generation = self.generation
            with self.database.connect() as db:
                cfg = settings(db)
        response = immich_get(cfg, "/assets/" + asset_id + "/thumbnail?size=preview")
        response.raise_for_status()
        if not response.headers.get("content-type", "").startswith("image/") or len(
            response.content
        ) > min(self.cache_limit, 20 * 1024 * 1024):
            raise ValueError("Ongeldige afbeelding")
        with self.lock:
            # Never return or cache a response authorized by an obsolete selection.
            if generation != self.generation or asset_id not in self.assets:
                raise KeyError(asset_id)
            path.write_bytes(response.content)
            self.purge_cache()
            return response.content
