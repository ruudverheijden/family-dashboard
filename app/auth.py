"""Per-application administrator sessions and login throttling."""

import hashlib
import hmac
import secrets
import threading
import time

from fastapi import HTTPException, Request, Response

from .schemas import Login

LOGIN_BURST = 5
LOGIN_REFILL_SECONDS = 10


class Authentication:
    def __init__(self, database, password, cookie_secure=False):
        self.database = database
        self.password = password
        self.cookie_secure = cookie_secure
        self.sessions = {}
        self.attempts = {}
        self.login_lock = threading.Lock()
        self.salt = secrets.token_bytes(16)
        self.password_hash = hashlib.scrypt(password.encode(), salt=self.salt, n=16384, r=8, p=1)

    def check(self, request: Request):
        key = request.cookies.get("family_admin", "")
        if self.sessions.get(key, 0) < time.time():
            self.sessions.pop(key, None)
            raise HTTPException(401, "Meld je aan als beheerder.")

    def login(self, body: Login, request: Request, response: Response):
        if not self.password or self.password == "vervang-dit-door-een-uniek-wachtwoord":
            raise HTTPException(
                503, "Stel op de server een eigen ADMIN_PASSWORD in en herstart de app."
            )
        ip = request.client.host if request.client else "unknown"
        with self.login_lock:
            now = time.time()
            for address, timestamps in list(self.attempts.items()):
                active = [timestamp for timestamp in timestamps if timestamp > now - 300]
                if active:
                    self.attempts[address] = active
                else:
                    del self.attempts[address]
            ip_attempts = self.attempts.get(ip, [])
            if len(ip_attempts) >= 5:
                retry_after = max(1, int(ip_attempts[0] + 300 - now))
                raise HTTPException(
                    429,
                    "Te veel pogingen. Probeer het over vijf minuten opnieuw.",
                    headers={"Retry-After": str(retry_after)},
                )

            retry_after = None
            with self.database.connect() as db:
                db.execute("BEGIN IMMEDIATE")
                limiter = db.execute(
                    "SELECT tokens,updated_at FROM login_limiter WHERE id=1"
                ).fetchone()
                tokens = min(
                    LOGIN_BURST,
                    limiter["tokens"] + max(0, now - limiter["updated_at"]) / LOGIN_REFILL_SECONDS,
                )
                if tokens < 1:
                    retry_after = max(1, int((1 - tokens) * LOGIN_REFILL_SECONDS + 0.999))
                else:
                    tokens -= 1
                db.execute(
                    "UPDATE login_limiter SET tokens=?,updated_at=? WHERE id=1",
                    (tokens, now),
                )
            if retry_after is not None:
                raise HTTPException(
                    429,
                    "Te veel aanmeldpogingen. Wacht even voordat je het opnieuw probeert.",
                    headers={"Retry-After": str(retry_after)},
                )

            candidate = hashlib.scrypt(body.password.encode(), salt=self.salt, n=16384, r=8, p=1)
            if not hmac.compare_digest(candidate, self.password_hash):
                self.attempts.setdefault(ip, []).append(now)
                raise HTTPException(401, "Het wachtwoord klopt niet.")
            self.attempts.pop(ip, None)
        now = time.time()
        for expired in [k for k, expiry in self.sessions.items() if expiry < now]:
            del self.sessions[expired]
        key = secrets.token_urlsafe(32)
        self.sessions[key] = now + 1800
        response.set_cookie(
            "family_admin",
            key,
            httponly=True,
            samesite="strict",
            secure=self.cookie_secure,
            max_age=1800,
        )
        return {"ok": True}

    def logout(self, request: Request, response: Response):
        self.sessions.pop(request.cookies.get("family_admin", ""), None)
        response.delete_cookie("family_admin")
        return {"ok": True}


def admin(request: Request):
    request.app.state.runtime.auth.check(request)
