from __future__ import annotations

import hashlib

from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit


SENSITIVE_QUERY_KEYS = {"passkey", "token", "rss_token", "torrent_pass"}


def fingerprint_secret(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()[:12]


def sanitize_url(url: str) -> str:
    if not url:
        return url

    parts = urlsplit(url)
    if not parts.query:
        return url

    sanitized_query = []
    for key, value in parse_qsl(parts.query, keep_blank_values=True):
        sanitized_query.append((key, "***" if key.lower() in SENSITIVE_QUERY_KEYS and value else value))

    return urlunsplit((parts.scheme, parts.netloc, parts.path, urlencode(sanitized_query), parts.fragment))


def get_request_ip(request) -> str:
    forwarded = request.META.get("HTTP_X_FORWARDED_FOR")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR", "-")


def get_request_actor(request) -> str:
    user = getattr(request, "user", None)
    if getattr(user, "is_authenticated", False):
        return getattr(user, "username", "authenticated")

    if hasattr(request, "GET"):
        passkey = (request.GET.get("passkey") or "").strip()
        if passkey:
            from apps.users.models import User

            username = User.objects.filter(passkey=passkey).values_list("username", flat=True).first()
            if username:
                return f"passkey:{username}"
            return f"passkey:{fingerprint_secret(passkey)}"

    return "anonymous"
