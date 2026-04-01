"""
Response wrapper mixin for standardized API responses.

Success envelope:
    { "success": true, "data": {...}, "message": "Optional" }

Error envelope (produced by custom_exception_handler):
    { "success": false, "error": { "code": "...", "message": "...", "details": {} } }
"""

from typing import Any

from rest_framework import status
from rest_framework.response import Response


class ApiResponseMixin:
    """
    Mixin to be used with APIView / ViewSet subclasses.
    Provides helper methods for returning standardized success responses.
    """

    def success_response(
        self,
        data: Any = None,
        message: str = "",
        status_code: int = status.HTTP_200_OK,
    ) -> Response:
        """Return a standardized success response."""
        payload: dict[str, Any] = {"success": True}
        if data is not None:
            payload["data"] = data
        if message:
            payload["message"] = message
        return Response(payload, status=status_code)

    def error_response(
        self,
        message: str,
        code: str = "ERROR",
        details: dict | None = None,
        status_code: int = status.HTTP_400_BAD_REQUEST,
    ) -> Response:
        """Return a standardized error response (use sparingly; prefer raising DRF exceptions)."""
        return Response(
            {
                "success": False,
                "error": {
                    "code": code,
                    "message": message,
                    "details": details or {},
                },
            },
            status=status_code,
        )
