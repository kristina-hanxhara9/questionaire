from __future__ import annotations

import hmac
import uuid
from collections.abc import Awaitable, Callable

from starlette.requests import Request
from starlette.responses import JSONResponse, Response
from starlette.types import ASGIApp, Receive, Scope, Send

from .config import Settings
from .logging_setup import clear_request_id, get_logger, set_request_id

EXEMPT_PATHS = ("/healthz", "/readyz")


class APIKeyMiddleware:
    """Bearer token / X-API-Key auth for the MCP HTTP transport."""

    def __init__(self, app: ASGIApp, settings: Settings) -> None:
        self.app = app
        self.settings = settings
        self._log = get_logger("mcp.auth")

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        request = Request(scope, receive=receive)
        request_id = request.headers.get("x-request-id") or uuid.uuid4().hex
        set_request_id(request_id)

        path = scope.get("path", "")
        if any(path.startswith(p) for p in EXEMPT_PATHS):
            try:
                await self.app(scope, receive, send)
            finally:
                clear_request_id()
            return

        if not _authenticate(request, self.settings.api_keys):
            self._log.warning("auth_rejected", path=path)
            response = JSONResponse(
                {
                    "jsonrpc": "2.0",
                    "error": {"code": -32001, "message": "Unauthorized"},
                    "id": None,
                },
                status_code=401,
                headers={"WWW-Authenticate": 'Bearer realm="mcp"'},
            )
            await _send_response(response, send)
            clear_request_id()
            return

        try:
            await self.app(scope, receive, send)
        finally:
            clear_request_id()


def _authenticate(request: Request, valid_keys: tuple[str, ...]) -> bool:
    if not valid_keys:
        return False

    header = request.headers.get("authorization", "")
    presented: str | None = None
    if header.lower().startswith("bearer "):
        presented = header.split(" ", 1)[1].strip()
    if presented is None:
        presented = request.headers.get("x-api-key", "").strip() or None
    if not presented:
        return False
    return any(hmac.compare_digest(presented, key) for key in valid_keys)


async def _send_response(response: Response, send: Send) -> None:
    await send(
        {
            "type": "http.response.start",
            "status": response.status_code,
            "headers": [(k.encode(), v.encode()) for k, v in response.headers.items()],
        }
    )
    await send({"type": "http.response.body", "body": response.body})
