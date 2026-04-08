import hashlib

from rest_framework.throttling import SimpleRateThrottle


class PasskeyOrIPRateThrottle(SimpleRateThrottle):
    def get_cache_key(self, request, view):
        ident = self._build_ident(request)
        if not ident:
            return None
        return self.cache_format % {"scope": self.scope, "ident": ident}

    def _build_ident(self, request) -> str | None:
        passkey = request.query_params.get("passkey", "").strip()
        if passkey:
            digest = hashlib.sha256(passkey.encode("utf-8")).hexdigest()
            return f"passkey:{digest}"

        user = getattr(request, "user", None)
        if getattr(user, "is_authenticated", False):
            return f"user:{user.pk}"

        ident = self.get_ident(request)
        return f"ip:{ident}" if ident else None


class RssFeedThrottle(PasskeyOrIPRateThrottle):
    scope = "rss"


class TorrentDownloadThrottle(PasskeyOrIPRateThrottle):
    scope = "download"
