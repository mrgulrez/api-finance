"""
Serializers for FinancialRecord.

Includes validation:
    - amount must be positive
    - date cannot be in the future
    - category cannot be blank
"""

from datetime import date
from decimal import Decimal

from rest_framework import serializers

from .models import FinancialRecord


class FinancialRecordSerializer(serializers.ModelSerializer):
    """
    Full serializer for creating and reading FinancialRecord instances.

    The ``user`` field is read-only — it is automatically set from the
    authenticated request in the ViewSet's perform_create().
    """

    user_email = serializers.EmailField(source="user.email", read_only=True)

    class Meta:
        model = FinancialRecord
        fields = [
            "id",
            "user",
            "user_email",
            "amount",
            "transaction_type",
            "category",
            "date",
            "description",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "user", "user_email", "created_at", "updated_at"]

    def validate_amount(self, value: Decimal) -> Decimal:
        """Amount must be a positive number."""
        if value <= Decimal("0"):
            raise serializers.ValidationError("Amount must be a positive number.")
        return value

    def validate_date(self, value: date) -> date:
        """Date cannot be in the future."""
        if value > date.today():
            raise serializers.ValidationError("Date cannot be in the future.")
        return value

    def validate_category(self, value: str) -> str:
        """Category cannot be blank or whitespace-only."""
        if not value.strip():
            raise serializers.ValidationError("Category cannot be blank.")
        return value.strip()


class FinancialRecordListSerializer(serializers.ModelSerializer):
    """
    Lightweight serializer for list views — omits heavy fields.
    """

    user_email = serializers.EmailField(source="user.email", read_only=True)

    class Meta:
        model = FinancialRecord
        fields = [
            "id",
            "user_email",
            "amount",
            "transaction_type",
            "category",
            "date",
            "created_at",
        ]
        read_only_fields = fields
