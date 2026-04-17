import hashlib

from rest_framework.throttling import SimpleRateThrottle


class LoginRateThrottle(SimpleRateThrottle):
    scope = "login"

    def get_cache_key(self, request, view):
        username = ""
        try:
            username = str(request.data.get("username", "")).strip().lower()
        except Exception:
            username = ""

        ident = self.get_ident(request) or "unknown"
        source = f"{ident}:{username or 'anonymous'}"
        digest = hashlib.sha256(source.encode("utf-8")).hexdigest()
        return self.cache_format % {"scope": self.scope, "ident": digest}


class UserOrIPRateThrottle(SimpleRateThrottle):
    def get_cache_key(self, request, view):
        ident = self._build_ident(request)
        if not ident:
            return None
        return self.cache_format % {"scope": self.scope, "ident": ident}

    def _build_ident(self, request) -> str | None:
        user = getattr(request, "user", None)
        if getattr(user, "is_authenticated", False):
            return f"user:{user.pk}"

        ident = self.get_ident(request)
        return f"ip:{ident}" if ident else None


class RssFeedThrottle(UserOrIPRateThrottle):
    scope = "rss"


class TorrentDownloadThrottle(UserOrIPRateThrottle):
    scope = "download"
