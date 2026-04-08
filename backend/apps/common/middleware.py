from __future__ import annotations

import logging
import time

from apps.common.logging_utils import get_request_actor, get_request_ip, sanitize_url


logger = logging.getLogger("apps.request")


class RequestLoggingMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        started_at = time.perf_counter()
        response = None
        try:
            response = self.get_response(request)
            return response
        finally:
            duration_ms = int((time.perf_counter() - started_at) * 1000)
            path = sanitize_url(request.get_full_path())
            status_code = getattr(response, "status_code", 500)
            logger.info(
                "request completed method=%s path=%s status=%s duration_ms=%s actor=%s ip=%s",
                request.method,
                path,
                status_code,
                duration_ms,
                get_request_actor(request),
                get_request_ip(request),
            )
