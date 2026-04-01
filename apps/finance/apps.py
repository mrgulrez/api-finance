"""Finance app — financial records CRUD with filtering, soft delete, and analytics."""

from django.apps import AppConfig


class FinanceConfig(AppConfig):
    """FinancialRecord model with fat manager for ORM-based aggregation queries."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.finance"
    label = "finance"
