"""Users app — custom User model, auth, and role management."""

from django.apps import AppConfig


class UsersConfig(AppConfig):
    """Custom User model replacing Django's default with email-based auth."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.users"
    label = "users"
