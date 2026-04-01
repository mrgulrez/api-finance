"""
Custom manager for the User model.

Replaces Django's default username-based manager with email-based creation.
"""

from django.contrib.auth.base_user import BaseUserManager


class UserManager(BaseUserManager):
    """
    Custom manager where email is the unique identifier instead of username.

    Usage:
        User.objects.create_user(email="a@b.com", password="secret")
        User.objects.create_superuser(email="admin@b.com", password="secret")
    """

    use_in_migrations = True

    def _create_user(self, email: str, password: str | None, **extra_fields):
        """Core creation helper — normalizes email, hashes password."""
        if not email:
            raise ValueError("An email address is required.")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email: str, password: str | None = None, **extra_fields):
        """Create and return a regular (non-staff) user."""
        extra_fields.setdefault("is_staff", False)
        extra_fields.setdefault("is_superuser", False)
        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, email: str, password: str, **extra_fields):
        """Create and return a superuser with ADMIN role and all privileges."""
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("role", "ADMIN")

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")

        return self._create_user(email, password, **extra_fields)
