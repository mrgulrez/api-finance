"""
Custom exception handler for Finance Backend.

All errors return a consistent JSON envelope:
    {
        "success": false,
        "error": {
            "code": "VALIDATION_ERROR",
            "message": "Human readable message",
            "details": { ... field-level errors ... }
        }
    }
"""

import logging
from typing import Any

from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import status
from rest_framework.exceptions import (
    APIException,
    AuthenticationFailed,
    NotAuthenticated,
    NotFound,
    PermissionDenied,
    ValidationError,
)
from rest_framework.response import Response
from rest_framework.views import exception_handler

logger = logging.getLogger("apps.core")

_STATUS_CODE_MAP: dict[int, str] = {
    400: "BAD_REQUEST",
    401: "UNAUTHORIZED",
    403: "FORBIDDEN",
    404: "NOT_FOUND",
    405: "METHOD_NOT_ALLOWED",
    409: "CONFLICT",
    429: "THROTTLED",
    500: "INTERNAL_SERVER_ERROR",
}


def custom_exception_handler(exc: Exception, context: dict[str, Any]) -> Response | None:
    """
    Custom DRF exception handler returning standardized JSON error responses.

    Converts DjangoValidationError to DRF ValidationError before delegating
    to the default handler, then rewraps the response data.
    """
    if isinstance(exc, DjangoValidationError):
        exc = ValidationError(
            detail=exc.message_dict if hasattr(exc, "message_dict") else exc.messages
        )

    response = exception_handler(exc, context)

    if response is not None:
        status_code: int = response.status_code
        error_code = _STATUS_CODE_MAP.get(status_code, "ERROR")
        message = "An error occurred."
        details: dict = {}

        if isinstance(exc, ValidationError):
            error_code = "VALIDATION_ERROR"
            message = "Validation failed. Please check the provided data."
            details = _flatten_errors(response.data)

        elif isinstance(exc, AuthenticationFailed):
            error_code = "AUTHENTICATION_FAILED"
            message = _extract_message(exc.detail)

        elif isinstance(exc, NotAuthenticated):
            error_code = "NOT_AUTHENTICATED"
            message = "Authentication credentials were not provided."

        elif isinstance(exc, PermissionDenied):
            error_code = "PERMISSION_DENIED"
            message = "You do not have permission to perform this action."

        elif isinstance(exc, NotFound):
            error_code = "NOT_FOUND"
            message = "The requested resource was not found."

        elif isinstance(exc, APIException):
            error_code = _STATUS_CODE_MAP.get(status_code, "API_ERROR")
            if isinstance(exc.detail, dict):
                details = _flatten_errors(exc.detail)
                message = "Request failed."
            elif isinstance(exc.detail, list):
                message = " ".join(str(d) for d in exc.detail)
            else:
                message = str(exc.detail)

        logger.debug("API error [%s] %s: %s", error_code, status_code, message)

        response.data = {
            "success": False,
            "error": {
                "code": error_code,
                "message": message,
                "details": details,
            },
        }

    return response


def _flatten_errors(data: Any) -> dict:
    """Recursively flatten DRF error detail into a plain dict."""
    if isinstance(data, dict):
        return {
            key: [str(e) for e in val] if isinstance(val, list) else _flatten_errors(val)
            for key, val in data.items()
        }
    if isinstance(data, list):
        return {"non_field_errors": [str(e) for e in data]}
    return {"detail": str(data)}


def _extract_message(detail: Any) -> str:
    """Extract a human-readable string from DRF error detail."""
    if isinstance(detail, dict):
        return next(iter(detail.values()), "Authentication failed.")
    if isinstance(detail, list):
        return str(detail[0])
    return str(detail)
