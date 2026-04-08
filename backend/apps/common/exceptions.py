import logging

from django.db import IntegrityError
from rest_framework import status
from rest_framework.exceptions import APIException, AuthenticationFailed, NotAuthenticated, PermissionDenied, Throttled, ValidationError
from rest_framework.response import Response
from rest_framework.views import exception_handler

from apps.common.logging_utils import sanitize_url


logger = logging.getLogger("apps.api")


class BusinessException(APIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = "业务处理失败。"
    default_code = "business_error"


def _build_error_message(detail) -> str:
    if isinstance(detail, dict):
        return "参数校验失败。"
    if isinstance(detail, list):
        return str(detail[0]) if detail else "请求失败。"
    return str(detail)


def _resolve_error_code(exc) -> str:
    if isinstance(exc, ValidationError):
        return "validation_error"
    if isinstance(exc, Throttled):
        return "throttled"
    if isinstance(exc, AuthenticationFailed):
        return "authentication_failed"
    if isinstance(exc, NotAuthenticated):
        return "not_authenticated"
    if isinstance(exc, PermissionDenied):
        return "permission_denied"
    return getattr(exc, "default_code", "request_error")


def api_exception_handler(exc, context):
    request = context.get("request")
    method = getattr(request, "method", "<unknown>")
    path = sanitize_url(getattr(request, "get_full_path", lambda: "<unknown>")())

    if isinstance(exc, IntegrityError):
        logger.warning("data conflict on %s %s: %s", method, path, exc)
        return Response(
            {
                "success": False,
                "code": "data_conflict",
                "message": "数据已存在或与当前状态冲突。",
            },
            status=status.HTTP_400_BAD_REQUEST,
        )

    response = exception_handler(exc, context)
    if response is None:
        logger.exception("unhandled api error on %s %s", method, path)
        return Response(
            {"success": False, "code": "server_error", "message": "服务器内部错误。"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

    detail = response.data
    if isinstance(detail, dict) and "detail" in detail:
        message = str(detail["detail"])
    else:
        message = _build_error_message(detail)
    code = _resolve_error_code(exc)
    if isinstance(exc, Throttled):
        message = "请求过于频繁，请稍后再试。"
    payload = {"success": False, "code": code, "message": message}
    if isinstance(detail, dict) and "detail" not in detail:
        payload["errors"] = detail
    if isinstance(exc, Throttled) and exc.wait is not None:
        payload["retryAfter"] = int(exc.wait)
    log_level = logger.error if response.status_code >= 500 else logger.warning
    log_level("api request failed on %s %s with status %s: %s", method, path, response.status_code, message)
    response.data = payload
    return response
