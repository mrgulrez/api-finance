"""
Request logging middleware.

Logs every HTTP request with: method, path, status code, and duration (ms).
Format: [METHOD] /path/to/endpoint → 200 (12.34ms)
"""

import logging
import time
from collections.abc import Callable

from django.http import HttpRequest, HttpResponse

logger = logging.getLogger("apps.core.middleware")


class RequestLoggingMiddleware:
    """
    WSGI middleware that logs each request's method, URL, status code,
    and total response time in milliseconds.
    """

    def __init__(self, get_response: Callable[[HttpRequest], HttpResponse]) -> None:
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:
        start = time.monotonic()
        response: HttpResponse = self.get_response(request)
        duration_ms = (time.monotonic() - start) * 1000

        logger.info(
            "[%s] %s → %s (%.2fms)",
            request.method,
            request.get_full_path(),
            response.status_code,
            duration_ms,
        )
        return response
