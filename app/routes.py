"""HTTP boundary: authentication, request envelopes and response translation."""

import asyncio
import base64
import binascii
import json

import httpx
from fastapi import APIRouter, Depends, HTTPException, Request, Response

from .auth import admin
from .db import settings
from .integrations import caldav, immich
from .integrations.common import EndpointChanged, endpoint_secret, log_failure, valid_url
from .schemas import (
    GameActionInput,
    GamePriceInput,
    GamePurchaseInput,
    Login,
    Mutation,
    PointAdjustmentInput,
    RewardDecisionInput,
    RewardRequestInput,
)
from .services import dashboard, entities, games, rewards
from .services import settings as configuration
from .services.points import adjust_points
from .validation import _uuid

router = APIRouter()


def runtime(request: Request):
    return request.app.state.runtime


@router.post("/api/login")
def login(body: Login, request: Request, response: Response, rt=Depends(runtime)):
    return rt.auth.login(body, request, response)


@router.post("/api/logout")
def logout(request: Request, response: Response, rt=Depends(runtime)):
    return rt.auth.logout(request, response)


@router.get("/api/state")
def state(day: str | None = None, period: str = "day", rt=Depends(runtime)):
    return dashboard.state(rt.database, rt.photos, day, period)


@router.post("/api/entities/{kind}")
def mutate(kind: str, body: Mutation, request: Request, rt=Depends(runtime)):
    # Preserve the existing validation-before-authentication response for invalid IDs.
    if kind in ("members", "rewards"):
        if not _uuid(body.id):
            raise HTTPException(422, "Ongeldig itemnummer.")
        admin(request)
    return entities.mutate(kind, body, rt.database)


@router.post("/api/reward-requests")
def request_reward(body: RewardRequestInput, rt=Depends(runtime)):
    return rewards.request_reward(body, rt.database)


@router.post(
    "/api/admin/reward-requests/{reward_request_id}/decision", dependencies=[Depends(admin)]
)
def decide_reward_request(reward_request_id: str, body: RewardDecisionInput, rt=Depends(runtime)):
    return rewards.decide_reward_request(reward_request_id, body, rt.database)


@router.post("/api/admin/points/adjustments", dependencies=[Depends(admin)])
def adjust_member_points(body: PointAdjustmentInput, rt=Depends(runtime)):
    return adjust_points(body, rt.database)


@router.get("/api/history")
def history(rt=Depends(runtime)):
    return dashboard.history(rt.database)


@router.get("/api/admin/settings", dependencies=[Depends(admin)])
def get_settings(rt=Depends(runtime)):
    return configuration.get_settings(rt.database)


@router.post("/api/admin/settings", dependencies=[Depends(admin)])
def save_settings(body: dict, rt=Depends(runtime)):
    return configuration.save_settings(body, rt.database, rt.photos)


@router.get("/brand-image/{version}")
def get_brand_image(version: int, rt=Depends(runtime)):
    with rt.database.connect() as db:
        cfg = settings(db)
    if version != cfg["version"] or not cfg["brand_image"]:
        raise HTTPException(404, "Gezinsfoto niet beschikbaar.")
    image = base64.b64decode(cfg["brand_image"].partition(",")[2], validate=True)
    return Response(
        image,
        media_type="image/jpeg",
        headers={"Cache-Control": "public, max-age=31536000, immutable"},
    )


@router.get("/member-avatar/{member_id}/{version}")
def get_member_avatar(member_id: str, version: int, rt=Depends(runtime)):
    if not _uuid(member_id):
        raise HTTPException(404, "Profielfoto niet beschikbaar.")
    with rt.database.connect() as db:
        row = db.execute(
            "SELECT version,body FROM entities WHERE kind=? AND id=?", ("members", member_id)
        ).fetchone()
    if not row or version != row["version"]:
        raise HTTPException(404, "Profielfoto niet beschikbaar.")
    avatar = json.loads(row["body"]).get("avatar", "")
    if not avatar.startswith("data:image/jpeg;base64,"):
        raise HTTPException(404, "Profielfoto niet beschikbaar.")
    try:
        image = base64.b64decode(avatar.partition(",")[2], validate=True)
    except (ValueError, binascii.Error):
        raise HTTPException(404, "Profielfoto niet beschikbaar.")
    return Response(
        image,
        media_type="image/jpeg",
        headers={"Cache-Control": "public, max-age=31536000, immutable"},
    )


@router.post("/api/admin/discover/{service}", dependencies=[Depends(admin)])
def discover(service: str, body: dict, rt=Depends(runtime)):
    with rt.database.connect() as db:
        cfg = settings(db)
    try:
        if service == "caldav":
            previous = next((a for a in cfg["caldav"] if a["id"] == body.get("id")), {})
            account = previous | body
            account["password"] = endpoint_secret(
                previous.get("url", ""),
                account["url"],
                previous.get("password", ""),
                body.get("password"),
            )
            valid_url(account["url"])
            return caldav.discover(account)
        if service == "immich":
            url = valid_url(body.get("url") or cfg["immich_url"])
            cfg["immich_key"] = endpoint_secret(
                cfg["immich_url"], url, cfg["immich_key"], body.get("key")
            )
            cfg["immich_url"] = url
            return immich.albums(cfg)
    except EndpointChanged as error:
        raise HTTPException(422, str(error))
    except Exception as error:
        log_failure("Integration discovery", error)
        raise HTTPException(
            502, "Verbinding mislukt. Controleer serveradres, inloggegevens en rechten."
        )
    raise HTTPException(404)


@router.post("/api/admin/sync", dependencies=[Depends(admin)])
async def sync(rt=Depends(runtime)):
    await asyncio.gather(asyncio.to_thread(rt.calendars.sync), asyncio.to_thread(rt.photos.sync))
    return {"ok": True}


@router.get("/api/photos/{asset_id}")
def get_photo(asset_id: str, rt=Depends(runtime)):
    try:
        return Response(
            rt.photos.photo(asset_id),
            media_type="image/jpeg",
            headers={"Cache-Control": "no-store"},
        )
    except KeyError:
        raise HTTPException(404, "Foto niet beschikbaar.")
    except httpx.HTTPStatusError as error:
        log_failure("Photo download", error)
        if error.response.status_code in (401, 403):
            raise HTTPException(
                403,
                "Immich weigert toegang tot de foto. Geef de API-sleutel in Immich het recht asset.view en vernieuw daarna deze pagina.",
            )
        raise HTTPException(502, "Foto kon niet worden geladen.")
    except Exception as error:
        log_failure("Photo download", error)
        raise HTTPException(502, "Foto kon niet worden geladen.")


@router.get("/api/health")
def health(rt=Depends(runtime)):
    with rt.database.connect() as db:
        db.execute("SELECT 1").fetchone()
    return {"status": "ok", "version": "0.3.0"}


@router.post("/api/admin/games/{game_id}", dependencies=[Depends(admin)])
def configure_game(game_id: str, body: GamePriceInput, rt=Depends(runtime)):
    return games.configure(game_id, body, rt.database)


@router.post("/api/games/{game_id}/sessions")
def purchase_game(game_id: str, body: GamePurchaseInput, rt=Depends(runtime)):
    return games.purchase(game_id, body, rt.database, rt.photos)


@router.get("/api/game-sessions/{session_id}")
def get_game_session(session_id: str, rt=Depends(runtime)):
    return games.get_session(session_id, rt.database)


@router.post("/api/game-sessions/{session_id}/actions")
def play_game(session_id: str, body: GameActionInput, rt=Depends(runtime)):
    return games.play(session_id, body, rt.database)
