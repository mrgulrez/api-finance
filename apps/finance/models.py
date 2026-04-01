"""
FinancialRecord model.

Represents a single financial transaction (income or expense).
Supports soft delete via is_deleted flag — no records are ever hard-deleted.
"""

from django.conf import settings
from django.db import models
from django.utils import timezone

from .managers import FinancialRecordManager


class FinancialRecord(models.Model):
    """
    A single financial transaction record.

    Fields:
        user             — FK to the owning User
        amount           — positive decimal, 2 decimal places
        transaction_type — INCOME or EXPENSE
        category         — free-text label (e.g. "salary", "rent")
        date             — the date the transaction occurred (cannot be future)
        description      — optional notes
        is_deleted       — soft-delete flag
        created_at       — auto-set on creation
        updated_at       — auto-updated on every save
    """

    class TransactionType(models.TextChoices):
        INCOME = "INCOME", "Income"
        EXPENSE = "EXPENSE", "Expense"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="financial_records",
        db_index=True,
    )
    amount = models.DecimalField(max_digits=14, decimal_places=2)
    transaction_type = models.CharField(
        max_length=10,
        choices=TransactionType.choices,
        db_index=True,
    )
    category = models.CharField(max_length=100, db_index=True)
    date = models.DateField(db_index=True)
    description = models.TextField(blank=True, default="")
    is_deleted = models.BooleanField(default=False, db_index=True)

    # Timestamps
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    # Fat manager
    objects = FinancialRecordManager()

    class Meta:
        verbose_name = "Financial Record"
        verbose_name_plural = "Financial Records"
        ordering = ["-date", "-created_at"]
        indexes = [
            models.Index(fields=["user", "is_deleted"]),
            models.Index(fields=["transaction_type", "date"]),
        ]

    def __str__(self) -> str:
        return (
            f"{self.transaction_type} | {self.amount} | "
            f"{self.category} | {self.date}"
        )
