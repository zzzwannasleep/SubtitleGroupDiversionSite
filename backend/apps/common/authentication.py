from django.contrib.auth import get_user_model
from rest_framework.authentication import BaseAuthentication, SessionAuthentication
from rest_framework.exceptions import AuthenticationFailed


User = get_user_model()


class UserApiTokenAuthentication(BaseAuthentication):
    def authenticate(self, request):
        token = self._extract_token(request)
        if not token:
            return None

        user = User.objects.filter(api_token=token, status="active").first()
        if not user:
            raise AuthenticationFailed("API token 无效或账户已禁用。")
        return (user, token)

    def _extract_token(self, request) -> str | None:
        header = (request.META.get("HTTP_AUTHORIZATION") or "").strip()
        if header:
            parts = header.split(None, 1)
            if len(parts) == 2 and parts[0].lower() in {"token", "bearer"}:
                return parts[1].strip() or None
        return None


class UserApiKeyAuthentication(BaseAuthentication):
    api_key_header = "HTTP_X_API_KEY"

    def authenticate(self, request):
        api_key = self._extract_token(request)
        if not api_key:
            return None

        user = User.objects.filter(api_token=api_key, status="active").first()
        if not user:
            raise AuthenticationFailed("API Key 无效或账户已禁用。")
        return (user, api_key)

    def _extract_token(self, request) -> str | None:
        api_key = (request.META.get(self.api_key_header) or "").strip()
        return api_key or None


class CsrfExemptSessionAuthentication(SessionAuthentication):
    def enforce_csrf(self, request):
        return
