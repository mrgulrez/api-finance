"""
Serializers for user registration, authentication, and profile management.

Includes:
    UserRegistrationSerializer  — public registration (POST /auth/register/)
    UserSerializer              — read representation of a User
    UserUpdateSerializer        — PATCH own profile (full_name only)
    RoleUpdateSerializer        — PATCH role (ADMIN only)
    StatusUpdateSerializer      — PATCH is_active (ADMIN only)
    CustomTokenObtainPairSerializer — extends JWT response with user info
"""

from typing import Any

from django.contrib.auth import get_user_model
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

User = get_user_model()


class UserRegistrationSerializer(serializers.ModelSerializer):
    """
    Validates and creates a new user account.

    Enforces password confirmation and uniqueness of email.
    New accounts are always created with the VIEWER role.
    """

    password = serializers.CharField(
        write_only=True,
        min_length=8,
        style={"input_type": "password"},
    )
    confirm_password = serializers.CharField(
        write_only=True,
        style={"input_type": "password"},
    )

    class Meta:
        model = User
        fields = ["email", "full_name", "password", "confirm_password"]

    def validate_email(self, value: str) -> str:
        """Normalize to lowercase and check uniqueness."""
        value = value.lower().strip()
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("A user with this email already exists.")
        return value

    def validate_full_name(self, value: str) -> str:
        if not value.strip():
            raise serializers.ValidationError("Full name cannot be blank.")
        return value.strip()

    def validate(self, attrs: dict[str, Any]) -> dict[str, Any]:
        if attrs["password"] != attrs.pop("confirm_password"):
            raise serializers.ValidationError({"confirm_password": "Passwords do not match."})
        return attrs

    def create(self, validated_data: dict[str, Any]) -> User:
        return User.objects.create_user(
            email=validated_data["email"],
            password=validated_data["password"],
            full_name=validated_data["full_name"],
            role=User.Role.VIEWER,
        )


class UserSerializer(serializers.ModelSerializer):
    """Read-only serializer for displaying User data."""

    class Meta:
        model = User
        fields = ["id", "email", "full_name", "role", "is_active", "created_at", "updated_at"]
        read_only_fields = fields


class UserUpdateSerializer(serializers.ModelSerializer):
    """
    PATCH own profile — users can only update their full_name.
    Admins may use this too but role/status changes have dedicated serializers.
    """

    class Meta:
        model = User
        fields = ["full_name"]

    def validate_full_name(self, value: str) -> str:
        if not value.strip():
            raise serializers.ValidationError("Full name cannot be blank.")
        return value.strip()


class RoleUpdateSerializer(serializers.ModelSerializer):
    """PATCH user role — ADMIN only."""

    class Meta:
        model = User
        fields = ["role"]

    def validate_role(self, value: str) -> str:
        valid = [choice[0] for choice in User.Role.choices]
        if value not in valid:
            raise serializers.ValidationError(
                f"Invalid role. Valid choices are: {', '.join(valid)}"
            )
        return value


class StatusUpdateSerializer(serializers.ModelSerializer):
    """PATCH user active/inactive status — ADMIN only."""

    class Meta:
        model = User
        fields = ["is_active"]


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """
    Extends the default JWT token serializer to include user info in the response.

    Returns:
        access     — short-lived access token
        refresh    — long-lived refresh token
        user       — { id, email, full_name, role }
    """

    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token["user"] = {
            "id": user.id,
            "email": user.email,
            "full_name": user.full_name,
            "role": user.role,
        }
        return token

    def validate(self, attrs: dict[str, Any]) -> dict[str, Any]:
        data = super().validate(attrs)
        data["user"] = {
            "id": self.user.id,
            "email": self.user.email,
            "full_name": self.user.full_name,
            "role": self.user.role,
        }
        return data
