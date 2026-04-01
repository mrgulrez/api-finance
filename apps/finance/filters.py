"""
FilterSet for FinancialRecord list endpoint.

Supported query params:
    ?type=INCOME|EXPENSE        — filter by transaction type
    ?category=salary            — case-insensitive category match
    ?date_from=2024-01-01       — records on or after this date
    ?date_to=2024-12-31         — records on or before this date
    ?search=keyword             — full-text search on category + description
    ?ordering=-date             — any model field (default: -date)
"""

import django_filters

from .models import FinancialRecord


class FinancialRecordFilter(django_filters.FilterSet):
    """FilterSet for the FinancialRecord list endpoint."""

    type = django_filters.CharFilter(
        field_name="transaction_type",
        lookup_expr="iexact",
        label="Transaction type (INCOME or EXPENSE)",
    )
    category = django_filters.CharFilter(
        field_name="category",
        lookup_expr="icontains",
        label="Category (partial match)",
    )
    date_from = django_filters.DateFilter(
        field_name="date",
        lookup_expr="gte",
        label="Start date (inclusive)",
    )
    date_to = django_filters.DateFilter(
        field_name="date",
        lookup_expr="lte",
        label="End date (inclusive)",
    )

    class Meta:
        model = FinancialRecord
        fields = ["type", "category", "date_from", "date_to"]
