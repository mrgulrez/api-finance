"""
Serializers for dashboard analytics responses.

These are output-only serializers used for Swagger schema generation
and response documentation. They do not interact with models directly.
"""

from decimal import Decimal

from rest_framework import serializers


class SummarySerializer(serializers.Serializer):
    """Schema for GET /dashboard/summary/"""

    total_income = serializers.DecimalField(max_digits=14, decimal_places=2)
    total_expenses = serializers.DecimalField(max_digits=14, decimal_places=2)
    net_balance = serializers.DecimalField(max_digits=14, decimal_places=2)
    record_count = serializers.IntegerField()
    income_count = serializers.IntegerField()
    expense_count = serializers.IntegerField()


class CategoryBreakdownItemSerializer(serializers.Serializer):
    """A single category row in the by-category response."""

    category = serializers.CharField()
    total = serializers.DecimalField(max_digits=14, decimal_places=2)
    count = serializers.IntegerField()
    percentage_of_total = serializers.FloatField()


class ByCategorySerializer(serializers.Serializer):
    """Schema for GET /dashboard/by-category/"""

    income = CategoryBreakdownItemSerializer(many=True)
    expenses = CategoryBreakdownItemSerializer(many=True)


class TrendItemSerializer(serializers.Serializer):
    """A single period row in the trends response."""

    period_label = serializers.CharField()
    income = serializers.DecimalField(max_digits=14, decimal_places=2)
    expenses = serializers.DecimalField(max_digits=14, decimal_places=2)
    net = serializers.DecimalField(max_digits=14, decimal_places=2)


class RecentRecordSerializer(serializers.Serializer):
    """Lightweight record for GET /dashboard/recent/"""

    id = serializers.IntegerField()
    amount = serializers.DecimalField(max_digits=14, decimal_places=2)
    transaction_type = serializers.CharField()
    category = serializers.CharField()
    date = serializers.DateField()
    description = serializers.CharField()
