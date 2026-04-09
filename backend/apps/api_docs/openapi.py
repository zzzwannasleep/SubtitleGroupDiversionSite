from drf_spectacular.extensions import OpenApiAuthenticationExtension


class CsrfExemptSessionAuthenticationScheme(OpenApiAuthenticationExtension):
    target_class = "apps.common.authentication.CsrfExemptSessionAuthentication"
    name = "sessionCookieAuth"

    def get_security_definition(self, auto_schema):
        return {
            "type": "apiKey",
            "in": "cookie",
            "name": "sessionid",
            "description": "使用 Django Session Cookie 认证。",
        }


class UserApiTokenAuthenticationScheme(OpenApiAuthenticationExtension):
    target_class = "apps.common.authentication.UserApiTokenAuthentication"
    name = "userApiTokenAuth"

    def get_security_definition(self, auto_schema):
        return {
            "type": "apiKey",
            "in": "header",
            "name": "Authorization",
            "description": "使用 `Authorization: Token <api_token>` 或 `Authorization: Bearer <api_token>` 认证。",
        }


class UserApiKeyAuthenticationScheme(OpenApiAuthenticationExtension):
    target_class = "apps.common.authentication.UserApiKeyAuthentication"
    name = "userApiKeyAuth"

    def get_security_definition(self, auto_schema):
        return {
            "type": "apiKey",
            "in": "header",
            "name": "X-API-Key",
            "description": "使用 `X-API-Key: <api_token>` 认证。",
        }
