# request_id_middleware.py
from __future__ import annotations

import uuid
from typing import Callable, Awaitable

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

from request_id import request_id_var


class RequestIdMiddleware(BaseHTTPMiddleware):
    """
    Middleware, die pro HTTP-Request eine request_id vergibt.

    Verhalten:
    - Wenn der Client einen Header X-Request-ID schickt, wird dieser verwendet.
    - Andernfalls wird eine neue UUID4 erzeugt.
    - Die request_id wird:
      * im ContextVar request_id_var gespeichert
      * im Response-Header X-Request-ID zurückgegeben
    """

    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable],
    ):
        incoming = request.headers.get("X-Request-ID")
        request_id = incoming or str(uuid.uuid4())

        # ContextVar setzen und Token merken, damit wir später wieder resetten können
        token = request_id_var.set(request_id)
        try:
            response = await call_next(request)
        finally:
            # ContextVar zurücksetzen, damit Background-Tasks / andere Requests
            # keinen "falschen" Wert erben.
            request_id_var.reset(token)

        # request_id immer im Response-Header zurückgeben
        response.headers["X-Request-ID"] = request_id
        return response
