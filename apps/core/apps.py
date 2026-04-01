"""Core app configuration."""

from django.apps import AppConfig


class CoreConfig(AppConfig):
    """Shared utilities: pagination, permissions, exception handler, middleware."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.core"
    label = "core"
