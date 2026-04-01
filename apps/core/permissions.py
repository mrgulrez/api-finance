"""
Custom RBAC permission classes for Finance Backend.

Role hierarchy (ascending):  VIEWER < ANALYST < ADMIN

Usage in ViewSets:
    def get_permissions(self):
        if self.action == 'destroy':
            return [IsAuthenticated(), IsAdminRole()]
        if self.action in ['create', 'update', 'partial_update']:
            return [IsAuthenticated(), IsAnalystOrAdmin()]
        return [IsAuthenticated(), IsViewerOrAbove()]
"""

from rest_framework.permissions import BasePermission
from rest_framework.request import Request
from rest_framework.views import APIView


class IsAdminRole(BasePermission):
    """Allow access only to users with the ADMIN role."""

    message = "You must have the ADMIN role to perform this action."

    def has_permission(self, request: Request, view: APIView) -> bool:
        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.role == "ADMIN"
        )


class IsAnalystOrAdmin(BasePermission):
    """Allow access to users with ANALYST or ADMIN role."""

    message = "You must have the ANALYST or ADMIN role to perform this action."

    def has_permission(self, request: Request, view: APIView) -> bool:
        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.role in ("ANALYST", "ADMIN")
        )


class IsViewerOrAbove(BasePermission):
    """Allow access to any authenticated user (VIEWER, ANALYST, or ADMIN)."""

    message = "You must be authenticated to access this resource."

    def has_permission(self, request: Request, view: APIView) -> bool:
        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.role in ("VIEWER", "ANALYST", "ADMIN")
        )


class IsOwnerOrAdmin(BasePermission):
    """
    Allow access if the requesting user owns the object OR has the ADMIN role.
    Works for both User objects (checks .id) and FinancialRecord objects
    (checks .user_id).
    """

    message = "You can only modify your own data, or you must be an ADMIN."

    def has_permission(self, request: Request, view: APIView) -> bool:
        return bool(request.user and request.user.is_authenticated)

    def has_object_permission(self, request: Request, view: APIView, obj: object) -> bool:
        if request.user.role == "ADMIN":
            return True
        # User profile objects
        if hasattr(obj, "id") and not hasattr(obj, "user"):
            return obj.id == request.user.id  # type: ignore[union-attr]
        # FinancialRecord and similar objects with a FK to User
        if hasattr(obj, "user_id"):
            return obj.user_id == request.user.id  # type: ignore[union-attr]
        return False
