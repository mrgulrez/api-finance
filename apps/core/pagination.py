"""
Standard page-number pagination for all Finance Backend list endpoints.

Response envelope:
    {
        "success": true,
        "data": [...],
        "pagination": {
            "total_count": 100,
            "total_pages": 5,
            "current_page": 1,
            "page_size": 20,
            "next": "http://...",
            "previous": null
        }
    }
"""

from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response


class StandardPageNumberPagination(PageNumberPagination):
    """
    Page-based pagination returning 20 items per page by default.
    Clients can override with ?page_size=N (max 100).
    """

    page_size = 20
    page_size_query_param = "page_size"
    max_page_size = 100

    def get_paginated_response(self, data: list) -> Response:
        """Return paginated data wrapped in the standard success envelope."""
        return Response(
            {
                "success": True,
                "data": data,
                "pagination": {
                    "total_count": self.page.paginator.count,
                    "total_pages": self.page.paginator.num_pages,
                    "current_page": self.page.number,
                    "page_size": self.get_page_size(self.request),
                    "next": self.get_next_link(),
                    "previous": self.get_previous_link(),
                },
            }
        )

    def get_paginated_response_schema(self, schema: dict) -> dict:
        """OpenAPI schema for the paginated response."""
        return {
            "type": "object",
            "required": ["success", "data", "pagination"],
            "properties": {
                "success": {"type": "boolean", "example": True},
                "data": schema,
                "pagination": {
                    "type": "object",
                    "properties": {
                        "total_count": {"type": "integer"},
                        "total_pages": {"type": "integer"},
                        "current_page": {"type": "integer"},
                        "page_size": {"type": "integer"},
                        "next": {"type": "string", "nullable": True},
                        "previous": {"type": "string", "nullable": True},
                    },
                },
            },
        }
