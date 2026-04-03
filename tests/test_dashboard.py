"""
Tests for the dashboard analytics endpoints.

Verifies:
  - Summary calculations are arithmetically correct
  - by-category totals and percentages add up
  - Trends endpoint returns expected structure
  - Recent records endpoint respects limit
"""
import pytest
from decimal import Decimal
from django.contrib.auth import get_user_model

User = get_user_model()

SUMMARY_URL = "/api/v1/dashboard/summary/"
CATEGORY_URL = "/api/v1/dashboard/by-category/"
TRENDS_URL = "/api/v1/dashboard/trends/"
RECENT_URL = "/api/v1/dashboard/recent/"


@pytest.fixture
def populated_analyst(db, analyst_user):
    """Analyst with known financial records to test calculations."""
    from apps.finance.models import FinancialRecord
    FinancialRecord.objects.create(
        user=analyst_user, amount="1000.00", transaction_type="INCOME",
        category="salary", date="2024-01-10"
    )
    FinancialRecord.objects.create(
        user=analyst_user, amount="500.00", transaction_type="INCOME",
        category="freelance", date="2024-01-15"
    )
    FinancialRecord.objects.create(
        user=analyst_user, amount="300.00", transaction_type="EXPENSE",
        category="rent", date="2024-01-20"
    )
    FinancialRecord.objects.create(
        user=analyst_user, amount="200.00", transaction_type="EXPENSE",
        category="food", date="2024-01-25"
    )
    return analyst_user


@pytest.mark.django_db
class TestDashboardSummary:
    def test_summary_unauthenticated_returns_401(self, api_client):
        response = api_client.get(SUMMARY_URL)
        assert response.status_code == 401

    def test_summary_calculations_are_correct(self, api_client, populated_analyst):
        api_client.force_authenticate(user=populated_analyst)
        response = api_client.get(SUMMARY_URL)
        assert response.status_code == 200

        data = response.data["data"]
        # Total income: 1000 + 500 = 1500
        assert Decimal(data["total_income"]) == Decimal("1500.00")
        # Total expenses: 300 + 200 = 500
        assert Decimal(data["total_expenses"]) == Decimal("500.00")
        # Net balance: 1500 - 500 = 1000
        assert Decimal(data["net_balance"]) == Decimal("1000.00")
        # Counts
        assert data["income_count"] == 2
        assert data["expense_count"] == 2
        assert data["record_count"] == 4

    def test_summary_empty_returns_zeros(self, viewer_client):
        response = viewer_client.get(SUMMARY_URL)
        assert response.status_code == 200
        data = response.data["data"]
        assert Decimal(data["total_income"]) == Decimal("0.00")
        assert Decimal(data["net_balance"]) == Decimal("0.00")


@pytest.mark.django_db
class TestDashboardCategories:
    def test_by_category_returns_income_and_expenses(self, api_client, populated_analyst):
        api_client.force_authenticate(user=populated_analyst)
        response = api_client.get(CATEGORY_URL)
        assert response.status_code == 200

        data = response.data["data"]
        assert "income" in data
        assert "expenses" in data

        # Income categories: salary (1000), freelance (500)
        income_categories = {c["category"]: Decimal(c["total"]) for c in data["income"]}
        assert income_categories["salary"] == Decimal("1000.00")
        assert income_categories["freelance"] == Decimal("500.00")

        # Expense categories: rent (300), food (200)
        expense_categories = {c["category"]: Decimal(c["total"]) for c in data["expenses"]}
        assert expense_categories["rent"] == Decimal("300.00")
        assert expense_categories["food"] == Decimal("200.00")

    def test_by_category_percentages_sum_to_100(self, api_client, populated_analyst):
        api_client.force_authenticate(user=populated_analyst)
        response = api_client.get(CATEGORY_URL)
        data = response.data["data"]

        income_pcts = sum(c["percentage_of_total"] for c in data["income"])
        expense_pcts = sum(c["percentage_of_total"] for c in data["expenses"])

        # Allow for floating point tolerance
        assert abs(income_pcts - 100.0) < 0.1
        assert abs(expense_pcts - 100.0) < 0.1


@pytest.mark.django_db
class TestDashboardTrends:
    def test_trends_monthly_returns_correct_structure(self, analyst_client):
        response = analyst_client.get(f"{TRENDS_URL}?period=monthly")
        assert response.status_code == 200
        data = response.data["data"]
        assert data["period"] == "monthly"
        assert "trends" in data

    def test_trends_weekly_returns_correct_structure(self, analyst_client):
        response = analyst_client.get(f"{TRENDS_URL}?period=weekly")
        assert response.status_code == 200
        data = response.data["data"]
        assert data["period"] == "weekly"

    def test_trends_each_item_has_required_fields(self, api_client, populated_analyst):
        api_client.force_authenticate(user=populated_analyst)
        response = api_client.get(f"{TRENDS_URL}?period=monthly")
        trends = response.data["data"]["trends"]
        if trends:
            item = trends[0]
            assert "period_label" in item
            assert "income" in item
            assert "expenses" in item
            assert "net" in item


@pytest.mark.django_db
class TestDashboardRecent:
    def test_recent_default_limit(self, analyst_client, sample_record):
        response = analyst_client.get(RECENT_URL)
        assert response.status_code == 200
        assert "records" in response.data["data"]
        assert response.data["data"]["limit"] == 10

    def test_recent_custom_limit(self, analyst_client, sample_record):
        response = analyst_client.get(f"{RECENT_URL}?limit=3")
        assert response.status_code == 200
        assert response.data["data"]["limit"] == 3
        assert len(response.data["data"]["records"]) <= 3

    def test_recent_limit_max_capped_at_50(self, analyst_client):
        response = analyst_client.get(f"{RECENT_URL}?limit=999")
        assert response.status_code == 200
        assert response.data["data"]["limit"] == 50
