from rest_framework import status
from rest_framework.exceptions import APIException
from rest_framework.response import Response
from rest_framework.views import exception_handler


class BusinessException(APIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = "业务处理失败。"
    default_code = "business_error"


def api_exception_handler(exc, context):
    response = exception_handler(exc, context)
    if response is None:
        return Response(
            {"success": False, "code": "server_error", "message": "服务器内部错误。"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

    detail = response.data
    if isinstance(detail, dict) and "detail" in detail:
        message = str(detail["detail"])
    else:
        message = "请求失败。"
    code = getattr(exc, "default_code", "request_error")
    payload = {"success": False, "code": code, "message": message}
    if isinstance(detail, dict) and "detail" not in detail:
        payload["errors"] = detail
    response.data = payload
    return response
