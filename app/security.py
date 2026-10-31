"""HTTP request size, origin and response header policy."""

from fastapi import Response
from fastapi.responses import JSONResponse

MAX_REQUEST_BODY_BYTES = 1_048_576
MAX_REQUEST_BODY_CHUNKS = 1024


class RequestBodyLimitMiddleware:
    def __init__(self, app, max_body_size):
        self.app = app
        self.max_body_size = max_body_size

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        content_length = next(
            (
                value
                for name, value in scope.get("headers", [])
                if name.lower() == b"content-length"
            ),
            None,
        )
        if content_length is not None:
            try:
                declared_size = int(content_length)
            except ValueError:
                declared_size = 0
            if declared_size > self.max_body_size:
                await self.reject(scope, receive, send)
                return

        body = bytearray()
        total_size = 0
        chunk_count = 0
        while True:
            message = await receive()
            if message["type"] == "http.disconnect":
                return
            if message["type"] != "http.request":
                continue
            chunk = message.get("body", b"")
            total_size += len(chunk)
            chunk_count += 1
            if total_size > self.max_body_size or chunk_count > MAX_REQUEST_BODY_CHUNKS:
                await self.reject(scope, receive, send)
                return
            body.extend(chunk)
            if not message.get("more_body", False):
                break

        message = {"type": "http.request", "body": bytes(body), "more_body": False}
        message_available = True

        async def replay_receive():
            nonlocal message_available
            if message_available:
                message_available = False
                return message
            return await receive()

        await self.app(scope, replay_receive, send)

    async def reject(self, scope, receive, send):
        response = JSONResponse(
            {"detail": "Verzoek is te groot."},
            status_code=413,
            headers={
                "Cache-Control": "no-store",
                "X-Content-Type-Options": "nosniff",
                "Referrer-Policy": "no-referrer",
                "Content-Security-Policy": "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data: blob:; frame-src http: https:; connect-src 'self'; object-src 'none'; base-uri 'self'; frame-ancestors 'self'; form-action 'self'",
            },
        )
        await response(scope, receive, send)


async def security(request, call_next):
    if request.method not in ("GET", "HEAD", "OPTIONS"):
        if request.headers.get("x-family-request") != "1":
            return Response("Verzoek geweigerd", status_code=403)
        origin = request.headers.get("origin")
        if origin and origin.rstrip("/") != str(request.base_url).rstrip("/"):
            return Response("Andere oorsprong geweigerd", status_code=403)
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["Referrer-Policy"] = "no-referrer"
    response.headers["Content-Security-Policy"] = (
        "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data: blob:; frame-src http: https:; connect-src 'self'; object-src 'none'; base-uri 'self'; frame-ancestors 'self'; form-action 'self'"
    )
    if request.url.path.startswith("/api"):
        response.headers["Cache-Control"] = "no-store"
    return response
