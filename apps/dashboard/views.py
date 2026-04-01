"""
Dashboard analytics views.

All queries delegate to the fat FinancialRecordManager — no Python loops
over querysets, pure ORM aggregation (Sum, Count, annotate).

Endpoints:
    GET /api/v1/dashboard/summary/       → totals
    GET /api/v1/dashboard/by-category/   → per-category breakdown
    GET /api/v1/dashboard/trends/        → monthly or weekly time series
    GET /api/v1/dashboard/recent/        → last N records
"""

from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core.mixins import ApiResponseMixin
from apps.core.permissions import IsViewerOrAbove
from apps.finance.models import FinancialRecord
from apps.finance.serializers import FinancialRecordListSerializer

from .serializers import (
    ByCategorySerializer,
    RecentRecordSerializer,
    SummarySerializer,
    TrendItemSerializer,
)


def _base_queryset(request: Request):
    """
    Return the base active queryset, scoped to user unless ADMIN.
    Uses select_related to avoid N+1 when serializing user fields.
    """
    qs = FinancialRecord.objects.active().select_related("user")
    if request.user.role != "ADMIN":
        qs = qs.filter(user=request.user)
    return qs


class SummaryView(ApiResponseMixin, APIView):
    """
    GET /api/v1/dashboard/summary/

    Returns aggregate totals: income, expenses, net balance, and counts.
    Requires: VIEWER or above.
    """

    permission_classes = [IsAuthenticated, IsViewerOrAbove]

    def get(self, request: Request) -> Response:
        data = _base_queryset(request).summary()
        serializer = SummarySerializer(data)
        return self.success_response(data=serializer.data)


class ByCategoryView(ApiResponseMixin, APIView):
    """
    GET /api/v1/dashboard/by-category/

    Returns per-category totals and percentages, split into income and expense sections.
    Requires: VIEWER or above.
    """

    permission_classes = [IsAuthenticated, IsViewerOrAbove]

    def get(self, request: Request) -> Response:
        data = _base_queryset(request).by_category()
        serializer = ByCategorySerializer(data)
        return self.success_response(data=serializer.data)


class TrendsView(ApiResponseMixin, APIView):
    """
    GET /api/v1/dashboard/trends/?period=monthly|weekly

    Returns time-series income/expenses/net.
    - monthly (default) → last 12 months
    - weekly            → last 8 weeks

    Requires: VIEWER or above.
    """

    permission_classes = [IsAuthenticated, IsViewerOrAbove]

    def get(self, request: Request) -> Response:
        period = request.query_params.get("period", "monthly").lower()

        qs = _base_queryset(request)

        if period == "weekly":
            trends = qs.weekly_trends(weeks=8)
        else:
            trends = qs.monthly_trends(months=12)

        serializer = TrendItemSerializer(trends, many=True)
        return self.success_response(
            data={
                "period": period,
                "trends": serializer.data,
            }
        )


class RecentView(ApiResponseMixin, APIView):
    """
    GET /api/v1/dashboard/recent/?limit=10

    Returns the last N financial records (default 10, max 50).
    Requires: VIEWER or above.
    """

    permission_classes = [IsAuthenticated, IsViewerOrAbove]

    def get(self, request: Request) -> Response:
        try:
            limit = int(request.query_params.get("limit", 10))
            limit = max(1, min(limit, 50))  # clamp between 1 and 50
        except (TypeError, ValueError):
            limit = 10

        records = _base_queryset(request).order_by("-date", "-created_at")[:limit]
        serializer = FinancialRecordListSerializer(records, many=True)
        return self.success_response(
            data={
                "limit": limit,
                "records": serializer.data,
            }
        )
