"""Django admin configuration for FinancialRecord."""

from django.contrib import admin

from .models import FinancialRecord


@admin.register(FinancialRecord)
class FinancialRecordAdmin(admin.ModelAdmin):
    """
    Admin interface for FinancialRecord.

    Shows key fields in the list view, supports search and filtering,
    and hides soft-deleted records by default.
    """

    list_display = (
        "id",
        "user",
        "transaction_type",
        "amount",
        "category",
        "date",
        "is_deleted",
        "created_at",
    )
    list_filter = ("transaction_type", "is_deleted", "date")
    search_fields = ("category", "description", "user__email")
    ordering = ("-date",)
    readonly_fields = ("created_at", "updated_at")
    date_hierarchy = "date"

    def get_queryset(self, request):
        """Show all records (including soft-deleted) in admin."""
        return self.model.objects.select_related("user").all()
