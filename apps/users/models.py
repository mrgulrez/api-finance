"""
Custom User model using email as the primary authentication identifier.

Roles:
    VIEWER  — read-only access to records and dashboard
    ANALYST — can create/update financial records
    ADMIN   — full access including user management
"""

from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.db import models
from django.utils import timezone

from .managers import UserManager


class User(AbstractBaseUser, PermissionsMixin):
    """
    Custom user model replacing Django's default.

    USERNAME_FIELD is email, so all auth flows use email + password.
    Role is stored as a CharField with a fixed set of choices (TextChoices).
    """

    class Role(models.TextChoices):
        VIEWER = "VIEWER", "Viewer"
        ANALYST = "ANALYST", "Analyst"
        ADMIN = "ADMIN", "Admin"

    email = models.EmailField(
        unique=True,
        db_index=True,
        help_text="Primary identifier — used to log in.",
    )
    full_name = models.CharField(max_length=255)
    role = models.CharField(
        max_length=10,
        choices=Role.choices,
        default=Role.VIEWER,
        db_index=True,
    )

    # Status flags
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)      # Django admin access
    is_deleted = models.BooleanField(default=False, db_index=True)

    # Timestamps
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    objects = UserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["full_name"]

    class Meta:
        verbose_name = "User"
        verbose_name_plural = "Users"
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"{self.email} [{self.role}]"

    # ── Convenience properties ────────────────────────────────────────────────

    @property
    def is_admin(self) -> bool:
        """True when the user holds the ADMIN role."""
        return self.role == self.Role.ADMIN

    @property
    def is_analyst_or_above(self) -> bool:
        """True when the user holds ANALYST or ADMIN role."""
        return self.role in (self.Role.ANALYST, self.Role.ADMIN)
