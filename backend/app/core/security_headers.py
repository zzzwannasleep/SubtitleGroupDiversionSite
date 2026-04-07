from collections.abc import Awaitable, Callable

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    def __init__(
        self,
        app,  # type: ignore[no-untyped-def]
        *,
        content_security_policy: str | None = None,
        hsts_enabled: bool = False,
        hsts_max_age_seconds: int = 31536000,
    ) -> None:
        super().__init__(app)
        self.content_security_policy = content_security_policy
        self.hsts_enabled = hsts_enabled
        self.hsts_max_age_seconds = hsts_max_age_seconds

    async def dispatch(self, request: Request, call_next: Callable[[Request], Awaitable[Response]]) -> Response:
        response = await call_next(request)
        if not isinstance(response, Response):
            return response

        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        response.headers.setdefault("X-Frame-Options", "DENY")
        response.headers.setdefault("Referrer-Policy", "same-origin")
        response.headers.setdefault("Permissions-Policy", "camera=(), microphone=(), geolocation=()")
        response.headers.setdefault("Cross-Origin-Opener-Policy", "same-origin")

        if self.content_security_policy:
            response.headers.setdefault("Content-Security-Policy", self.content_security_policy)

        if self.hsts_enabled:
            response.headers.setdefault("Strict-Transport-Security", f"max-age={self.hsts_max_age_seconds}; includeSubDomains")

        return response
