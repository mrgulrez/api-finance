"""
FinancialRecord ViewSet.

Action-level RBAC:
    list / retrieve        → VIEWER, ANALYST, ADMIN
    create                 → ANALYST, ADMIN
    update / partial_update → ANALYST, ADMIN
    destroy                → ADMIN only (soft delete)
"""

from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from apps.core.mixins import ApiResponseMixin
from apps.core.permissions import IsAdminRole, IsAnalystOrAdmin, IsViewerOrAbove

from .filters import FinancialRecordFilter
from .models import FinancialRecord
from .serializers import FinancialRecordListSerializer, FinancialRecordSerializer


class FinancialRecordViewSet(ApiResponseMixin, ModelViewSet):
    """
    ViewSet for CRUD operations on FinancialRecord.

    - Automatically scopes queryset to the requesting user (non-admins).
    - Admins see all records.
    - Uses select_related('user') to prevent N+1 queries.
    - Soft delete: sets is_deleted=True, never hard-deletes.
    """

    filterset_class = FinancialRecordFilter
    search_fields = ["description", "category"]
    ordering_fields = ["date", "amount", "created_at", "transaction_type", "category"]
    ordering = ["-date"]

    def get_queryset(self):
        """
        Return active (non-deleted) records.
        Admins see all users' records; other roles see only their own.
        """
        qs = FinancialRecord.objects.active().select_related("user")
        if self.request.user.role != "ADMIN":
            qs = qs.filter(user=self.request.user)
        return qs

    def get_serializer_class(self):
        if self.action == "list":
            return FinancialRecordListSerializer
        return FinancialRecordSerializer

    def get_permissions(self):
        """Apply action-level RBAC."""
        if self.action in ("list", "retrieve"):
            return [IsAuthenticated(), IsViewerOrAbove()]
        if self.action in ("create", "update", "partial_update"):
            return [IsAuthenticated(), IsAnalystOrAdmin()]
        if self.action == "destroy":
            return [IsAuthenticated(), IsAdminRole()]
        return [IsAuthenticated()]

    # ── CRUD with response wrapping ───────────────────────────────────────────

    def list(self, request: Request, *args, **kwargs) -> Response:
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(queryset, many=True)
        return self.success_response(data=serializer.data)

    def retrieve(self, request: Request, *args, **kwargs) -> Response:
        instance = self.get_object()
        serializer = FinancialRecordSerializer(instance)
        return self.success_response(data=serializer.data)

    def create(self, request: Request, *args, **kwargs) -> Response:
        serializer = FinancialRecordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        return self.success_response(
            data=serializer.data,
            message="Financial record created successfully.",
            status_code=status.HTTP_201_CREATED,
        )

    def perform_create(self, serializer):
        """Inject the authenticated user as the record owner."""
        serializer.save(user=self.request.user)

    def update(self, request: Request, *args, **kwargs) -> Response:
        partial = kwargs.pop("partial", False)
        instance = self.get_object()
        serializer = FinancialRecordSerializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return self.success_response(
            data=serializer.data,
            message="Financial record updated successfully.",
        )

    def destroy(self, request: Request, *args, **kwargs) -> Response:
        """Soft delete — set is_deleted=True, never remove from DB."""
        instance = self.get_object()
        instance.is_deleted = True
        instance.save(update_fields=["is_deleted"])
        return self.success_response(message="Financial record deleted successfully.")
