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
