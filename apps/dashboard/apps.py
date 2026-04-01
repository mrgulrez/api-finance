"""Dashboard app — analytics & summary APIs."""

from django.apps import AppConfig


class DashboardConfig(AppConfig):
    """Read-only analytics endpoints backed by ORM aggregation."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.dashboard"
    label = "dashboard"
