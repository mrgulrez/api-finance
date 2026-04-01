"""
Fat manager / QuerySet for FinancialRecord.

Business logic lives here (Fat Models, Thin Views):
    - active()            → exclude soft-deleted records
    - for_user()          → filter by user FK
    - summary()           → ORM aggregation for income/expense/net totals
    - by_category()       → per-category breakdown with percentages
    - monthly_trends()    → last N months of income/expense/net
    - weekly_trends()     → last N weeks of income/expense/net

All aggregation uses Django ORM (Sum, Count, annotate) — no Python loops.
"""

from __future__ import annotations

from decimal import Decimal
from typing import TYPE_CHECKING

from django.db import models
from django.db.models import Count, Q, Sum
from django.db.models.functions import TruncMonth, TruncWeek

if TYPE_CHECKING:
    pass  # avoid circular import for type hints


class FinancialRecordQuerySet(models.QuerySet):
    """Domain-specific queryset methods for FinancialRecord."""

    def active(self) -> FinancialRecordQuerySet:
        """Exclude soft-deleted records."""
        return self.filter(is_deleted=False)

    def for_user(self, user) -> FinancialRecordQuerySet:
        """Filter records belonging to a specific user."""
        return self.filter(user=user)

    def income(self) -> FinancialRecordQuerySet:
        """Filter to INCOME records only."""
        return self.filter(transaction_type="INCOME")

    def expenses(self) -> FinancialRecordQuerySet:
        """Filter to EXPENSE records only."""
        return self.filter(transaction_type="EXPENSE")

    # ── Aggregation methods (Fat Model) ───────────────────────────────────────

    def summary(self) -> dict:
        """
        Compute total income, expenses, net balance, and record counts.
        Uses ORM aggregation in a single query — no Python iteration.
        """
        result = self.active().aggregate(
            total_income=Sum("amount", filter=Q(transaction_type="INCOME")),
            total_expenses=Sum("amount", filter=Q(transaction_type="EXPENSE")),
            record_count=Count("id"),
            income_count=Count("id", filter=Q(transaction_type="INCOME")),
            expense_count=Count("id", filter=Q(transaction_type="EXPENSE")),
        )
        total_income: Decimal = result["total_income"] or Decimal("0.00")
        total_expenses: Decimal = result["total_expenses"] or Decimal("0.00")
        return {
            "total_income": total_income,
            "total_expenses": total_expenses,
            "net_balance": total_income - total_expenses,
            "record_count": result["record_count"],
            "income_count": result["income_count"],
            "expense_count": result["expense_count"],
        }

    def by_category(self) -> dict:
        """
        Per-category totals and percentage of grand total, split by type.
        Two queries total (income grouping + expense grouping).
        """
        active_qs = self.active()
        total_income: Decimal = (
            active_qs.income().aggregate(t=Sum("amount"))["t"] or Decimal("0.00")
        )
        total_expense: Decimal = (
            active_qs.expenses().aggregate(t=Sum("amount"))["t"] or Decimal("0.00")
        )

        income_rows = (
            active_qs.income()
            .values("category")
            .annotate(total=Sum("amount"), count=Count("id"))
            .order_by("-total")
        )
        expense_rows = (
            active_qs.expenses()
            .values("category")
            .annotate(total=Sum("amount"), count=Count("id"))
            .order_by("-total")
        )

        def _with_pct(rows, grand_total: Decimal) -> list[dict]:
            out = []
            for row in rows:
                pct = (
                    round(float(row["total"]) / float(grand_total) * 100, 2)
                    if grand_total > 0
                    else 0.0
                )
                out.append(
                    {
                        "category": row["category"],
                        "total": row["total"],
                        "count": row["count"],
                        "percentage_of_total": pct,
                    }
                )
            return out

        return {
            "income": _with_pct(income_rows, total_income),
            "expenses": _with_pct(expense_rows, total_expense),
        }

    def monthly_trends(self, months: int = 12) -> list[dict]:
        """
        Monthly income/expenses/net for the last ``months`` calendar months.
        Uses TruncMonth for grouping — single ORM query.
        """
        from datetime import date

        from dateutil.relativedelta import relativedelta

        cutoff = date.today().replace(day=1) - relativedelta(months=months - 1)

        rows = (
            self.active()
            .filter(date__gte=cutoff)
            .annotate(period=TruncMonth("date"))
            .values("period")
            .annotate(
                income=Sum("amount", filter=Q(transaction_type="INCOME")),
                expenses=Sum("amount", filter=Q(transaction_type="EXPENSE")),
            )
            .order_by("period")
        )
        return [
            {
                "period_label": row["period"].strftime("%Y-%m"),
                "income": row["income"] or Decimal("0.00"),
                "expenses": row["expenses"] or Decimal("0.00"),
                "net": (row["income"] or Decimal("0.00"))
                - (row["expenses"] or Decimal("0.00")),
            }
            for row in rows
        ]

    def weekly_trends(self, weeks: int = 8) -> list[dict]:
        """
        Weekly income/expenses/net for the last ``weeks`` calendar weeks.
        Uses TruncWeek for grouping — single ORM query.
        """
        from datetime import date, timedelta

        cutoff = date.today() - timedelta(weeks=weeks)

        rows = (
            self.active()
            .filter(date__gte=cutoff)
            .annotate(period=TruncWeek("date"))
            .values("period")
            .annotate(
                income=Sum("amount", filter=Q(transaction_type="INCOME")),
                expenses=Sum("amount", filter=Q(transaction_type="EXPENSE")),
            )
            .order_by("period")
        )
        return [
            {
                "period_label": row["period"].strftime("%Y-W%W"),
                "income": row["income"] or Decimal("0.00"),
                "expenses": row["expenses"] or Decimal("0.00"),
                "net": (row["income"] or Decimal("0.00"))
                - (row["expenses"] or Decimal("0.00")),
            }
            for row in rows
        ]


class FinancialRecordManager(models.Manager):
    """Custom manager that returns FinancialRecordQuerySet."""

    def get_queryset(self) -> FinancialRecordQuerySet:
        return FinancialRecordQuerySet(self.model, using=self._db)

    def active(self) -> FinancialRecordQuerySet:
        """Shortcut: queryset of non-deleted records."""
        return self.get_queryset().active()
