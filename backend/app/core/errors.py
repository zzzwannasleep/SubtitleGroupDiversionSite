import logging
import re
from http import HTTPStatus
from typing import Any
from uuid import uuid4

from fastapi import FastAPI, Request, status
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException


REQUEST_ID_HEADER = "X-Request-ID"

logger = logging.getLogger(__name__)
_REQUEST_ID_PATTERN = re.compile(r"^[A-Za-z0-9._:-]{1,128}$")


def _get_request_id(request: Request) -> str:
    existing_request_id = getattr(request.state, "request_id", None)
    if isinstance(existing_request_id, str) and existing_request_id:
        return existing_request_id

    header_value = request.headers.get(REQUEST_ID_HEADER)
    if header_value and _REQUEST_ID_PATTERN.fullmatch(header_value):
        request.state.request_id = header_value
        return header_value

    request_id = uuid4().hex
    request.state.request_id = request_id
    return request_id


def _status_code_to_error_code(status_code: int) -> str:
    try:
        phrase = HTTPStatus(status_code).phrase
    except ValueError:
        return "request_error"
    return phrase.lower().replace(" ", "_").replace("-", "_")


def _normalize_http_detail(detail: Any, fallback_message: str) -> tuple[str, str | None, Any | None]:
    if isinstance(detail, str):
        return detail, None, None

    if isinstance(detail, dict):
        message = detail.get("message") or detail.get("detail") or fallback_message
        code = detail.get("code")
        details = detail.get("details")
        if details is None:
            details = {key: value for key, value in detail.items() if key not in {"message", "detail", "code"}}
            if not details:
                details = None
        return str(message), str(code) if code else None, details

    if detail:
        return fallback_message, None, detail

    return fallback_message, None, None


def _error_response(
    request: Request,
    *,
    status_code: int,
    message: str,
    code: str | None = None,
    details: Any | None = None,
    headers: dict[str, str] | None = None,
) -> JSONResponse:
    request_id = _get_request_id(request)
    response_headers = dict(headers or {})
    response_headers[REQUEST_ID_HEADER] = request_id

    error_payload: dict[str, Any] = {
        "code": code or _status_code_to_error_code(status_code),
        "message": message,
        "status_code": status_code,
        "request_id": request_id,
    }
    if details is not None:
        error_payload["details"] = details

    return JSONResponse(
        status_code=status_code,
        content=jsonable_encoder({"detail": message, "error": error_payload}),
        headers=response_headers,
    )


def configure_error_handlers(app: FastAPI) -> None:
    @app.middleware("http")
    async def request_id_middleware(request: Request, call_next):  # type: ignore[no-untyped-def]
        request_id = _get_request_id(request)
        response = await call_next(request)
        response.headers[REQUEST_ID_HEADER] = request_id
        return response

    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
        fallback_message = _status_code_to_error_code(exc.status_code).replace("_", " ").capitalize()
        message, code, details = _normalize_http_detail(exc.detail, fallback_message)
        return _error_response(
            request,
            status_code=exc.status_code,
            message=message,
            code=code,
            details=details,
            headers=exc.headers,
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
        return _error_response(
            request,
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            message="Request validation failed",
            code="validation_error",
            details=exc.errors(),
        )

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        request_id = _get_request_id(request)
        logger.exception(
            "Unhandled request error %s %s request_id=%s",
            request.method,
            request.url.path,
            request_id,
        )

        return _error_response(
            request,
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message="Internal server error",
            code="internal_server_error",
        )
