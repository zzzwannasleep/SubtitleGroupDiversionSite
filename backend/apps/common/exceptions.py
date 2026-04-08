import logging

from rest_framework import status
from rest_framework.exceptions import APIException
from rest_framework.response import Response
from rest_framework.views import exception_handler


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


def api_exception_handler(exc, context):
    request = context.get("request")
    method = getattr(request, "method", "<unknown>")
    path = getattr(request, "path", "<unknown>")
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
    code = getattr(exc, "default_code", "request_error")
    payload = {"success": False, "code": code, "message": message}
    if isinstance(detail, dict) and "detail" not in detail:
        payload["errors"] = detail
    log_level = logger.error if response.status_code >= 500 else logger.warning
    log_level("api request failed on %s %s with status %s: %s", method, path, response.status_code, message)
    response.data = payload
    return response
