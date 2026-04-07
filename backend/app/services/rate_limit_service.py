from collections import defaultdict, deque
from math import ceil
from threading import Lock
from time import monotonic
from typing import Deque

from fastapi import Request


class RateLimitExceeded(Exception):
    def __init__(self, retry_after_seconds: int) -> None:
        super().__init__("rate limit exceeded")
        self.retry_after_seconds = max(1, retry_after_seconds)


class InMemoryRateLimiter:
    def __init__(self) -> None:
        self._hits: dict[str, Deque[float]] = defaultdict(deque)
        self._lock = Lock()

    def hit(self, key: str, limit: int, window_seconds: int) -> None:
        if limit <= 0 or window_seconds <= 0:
            return

        now = monotonic()
        earliest_allowed = now - window_seconds

        with self._lock:
            hits = self._hits[key]
            while hits and hits[0] <= earliest_allowed:
                hits.popleft()

            if len(hits) >= limit:
                retry_after_seconds = ceil(window_seconds - (now - hits[0]))
                raise RateLimitExceeded(retry_after_seconds)

            hits.append(now)


def get_request_ip(request: Request) -> str:
    forwarded_for = request.headers.get("x-forwarded-for")
    if forwarded_for:
        client_ip = forwarded_for.split(",", 1)[0].strip()
        if client_ip:
            return client_ip

    real_ip = request.headers.get("x-real-ip")
    if real_ip:
        return real_ip.strip()

    if request.client is not None and request.client.host:
        return request.client.host

    return "unknown"


auth_rate_limiter = InMemoryRateLimiter()
