"""
User management views.

Auth flow:
    POST /api/v1/auth/register/         → RegisterView
    POST /api/v1/auth/login/            → LoginView (CustomTokenObtainPairView)
    POST /api/v1/auth/logout/           → LogoutView
    POST /api/v1/auth/token/refresh/    → TokenRefreshView (from simplejwt)

User management (ADMIN):
    GET    /api/v1/users/               → UserViewSet.list
    GET    /api/v1/users/{id}/          → UserViewSet.retrieve
    PATCH  /api/v1/users/{id}/          → UserViewSet.partial_update
    PATCH  /api/v1/users/{id}/role/     → UserViewSet.update_role
    PATCH  /api/v1/users/{id}/status/   → UserViewSet.update_status
    DELETE /api/v1/users/{id}/          → UserViewSet.destroy (soft delete)
"""

from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_decode
from django.utils.encoding import force_str
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView

from apps.core.mixins import ApiResponseMixin
from apps.core.permissions import IsAdminRole, IsOwnerOrAdmin

from .serializers import (
    CustomTokenObtainPairSerializer,
    RoleUpdateSerializer,
    StatusUpdateSerializer,
    UserRegistrationSerializer,
    UserSerializer,
    UserUpdateSerializer,
)
from .utils import send_password_reset_email

User = get_user_model()


# ─── Auth Views ───────────────────────────────────────────────────────────────


class RegisterView(ApiResponseMixin, APIView):
    """
    POST /api/v1/auth/register/

    Public endpoint. Creates a new user account with default VIEWER role.
    """

    permission_classes = [AllowAny]

    def post(self, request: Request, *args, **kwargs) -> Response:
        serializer = UserRegistrationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return self.success_response(
            data=UserSerializer(user).data,
            message="Account created successfully.",
            status_code=status.HTTP_201_CREATED,
        )


class LoginView(TokenObtainPairView):
    """
    POST /api/v1/auth/login/

    Returns JWT access + refresh tokens plus user info (id, email, full_name, role).
    """

    serializer_class = CustomTokenObtainPairSerializer


class LogoutView(ApiResponseMixin, APIView):
    """
    POST /api/v1/auth/logout/

    Blacklists the provided refresh token, invalidating the session.
    Body: { "refresh": "<refresh_token>" }
    """

    permission_classes = [IsAuthenticated]

    def post(self, request: Request, *args, **kwargs) -> Response:
        refresh_token = request.data.get("refresh")
        if not refresh_token:
            return self.error_response(
                message="A refresh token is required.",
                code="MISSING_REFRESH_TOKEN",
                status_code=status.HTTP_400_BAD_REQUEST,
            )
        try:
            token = RefreshToken(refresh_token)
            token.blacklist()
        except TokenError as exc:
            return self.error_response(
                message=str(exc),
                code="INVALID_TOKEN",
                status_code=status.HTTP_400_BAD_REQUEST,
            )
        return self.success_response(message="Logged out successfully.")

class VerifyEmailView(ApiResponseMixin, APIView):
    """
    POST /api/v1/auth/verify-email/
    """
    permission_classes = [AllowAny]
    
    def post(self, request: Request, *args, **kwargs) -> Response:
        uidb64 = request.data.get("uidb64")
        token = request.data.get("token")
        
        if not uidb64 or not token:
            return self.error_response("Missing parameters.", status_code=status.HTTP_400_BAD_REQUEST)
        
        try:
            uid = force_str(urlsafe_base64_decode(uidb64))
            user = User.objects.get(pk=uid)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            user = None
            
        if user is not None and default_token_generator.check_token(user, token):
            if not user.is_active:
                user.is_active = True
                user.save(update_fields=['is_active'])
            return self.success_response(message="Email verified successfully.")
        else:
            return self.error_response("Invalid or expired token.", status_code=status.HTTP_400_BAD_REQUEST)

class ForgotPasswordView(ApiResponseMixin, APIView):
    """
    POST /api/v1/auth/forgot-password/
    """
    permission_classes = [AllowAny]
    
    def post(self, request: Request, *args, **kwargs) -> Response:
        email = request.data.get("email", "").lower().strip()
        if not email:
            return self.error_response("Email is required.", status_code=status.HTTP_400_BAD_REQUEST)
            
        try:
            user = User.objects.get(email=email)
            if user.is_active: 
               send_password_reset_email(user)
        except User.DoesNotExist:
            pass # Prevent user enumeration by not returning an error
            
        return self.success_response(message="If an account with that email exists, a reset link has been sent.")

class ResetPasswordView(ApiResponseMixin, APIView):
    """
    POST /api/v1/auth/reset-password/
    """
    permission_classes = [AllowAny]

    def post(self, request: Request, *args, **kwargs) -> Response:
        uidb64 = request.data.get("uidb64")
        token = request.data.get("token")
        new_password = request.data.get("new_password")
        
        if not all([uidb64, token, new_password]):
            return self.error_response("Missing parameters.", status_code=status.HTTP_400_BAD_REQUEST)
            
        if len(new_password) < 8:
            return self.error_response("Password must be at least 8 characters long.", status_code=status.HTTP_400_BAD_REQUEST)
            
        try:
            uid = force_str(urlsafe_base64_decode(uidb64))
            user = User.objects.get(pk=uid)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            user = None

        if user is not None and default_token_generator.check_token(user, token):
            user.set_password(new_password)
            user.save()
            return self.success_response(message="Password reset successfully.")
        else:
            return self.error_response("Invalid or expired token.", status_code=status.HTTP_400_BAD_REQUEST)


# ─── User Management ViewSet ──────────────────────────────────────────────────


class UserViewSet(ApiResponseMixin, ModelViewSet):
    """
    ViewSet for user management operations (mostly ADMIN-only).

    Action-level RBAC is applied via get_permissions().
    Soft delete: sets is_deleted=True and is_active=False; data is preserved.
    """

    queryset = User.objects.filter(is_deleted=False).order_by("-created_at")
    http_method_names = ["get", "patch", "delete", "head", "options"]

    def get_serializer_class(self):
        """Return the appropriate serializer for each action."""
        if self.action == "partial_update":
            return UserUpdateSerializer
        if self.action == "update_role":
            return RoleUpdateSerializer
        if self.action == "update_status":
            return StatusUpdateSerializer
        return UserSerializer

    def get_permissions(self):
        """Apply action-level RBAC."""
        if self.action == "list":
            return [IsAuthenticated(), IsAdminRole()]
        if self.action in ("retrieve", "partial_update"):
            return [IsAuthenticated(), IsOwnerOrAdmin()]
        if self.action in ("destroy", "update_role", "update_status"):
            return [IsAuthenticated(), IsAdminRole()]
        return [IsAuthenticated()]

    # ── Standard actions with response wrapping ───────────────────────────────

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
        return self.success_response(data=UserSerializer(instance).data)

    def partial_update(self, request: Request, *args, **kwargs) -> Response:
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return self.success_response(
            data=UserSerializer(instance).data,
            message="Profile updated successfully.",
        )

    def destroy(self, request: Request, *args, **kwargs) -> Response:
        """Soft delete: mark as deleted and deactivate."""
        instance = self.get_object()
        instance.is_deleted = True
        instance.is_active = False
        instance.save(update_fields=["is_deleted", "is_active"])
        return self.success_response(message="User deleted successfully.")

    # ── Custom actions ────────────────────────────────────────────────────────

    @action(detail=True, methods=["patch"], url_path="role")
    def update_role(self, request: Request, pk=None) -> Response:
        """PATCH /users/{id}/role/ — change a user's role (ADMIN only)."""
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return self.success_response(
            data=UserSerializer(instance).data,
            message="User role updated successfully.",
        )

    @action(detail=True, methods=["patch"], url_path="status")
    def update_status(self, request: Request, pk=None) -> Response:
        """PATCH /users/{id}/status/ — activate or deactivate a user (ADMIN only)."""
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return self.success_response(
            data=UserSerializer(instance).data,
            message="User status updated successfully.",
        )
