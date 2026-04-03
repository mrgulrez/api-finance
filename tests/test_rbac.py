"""
Tests for RBAC enforcement on FinancialRecord endpoints.

Core rules:
  VIEWER     → can only GET (list/retrieve)
  ANALYST    → can GET, POST, PUT/PATCH
  ADMIN      → full access including DELETE
  Unauthenticated → 401 on all protected endpoints
"""
import pytest
from django.contrib.auth import get_user_model

User = get_user_model()

RECORDS_URL = "/api/v1/finance/records/"


def record_url(pk):
    return f"/api/v1/finance/records/{pk}/"


@pytest.mark.django_db
class TestUnauthenticatedAccess:
    def test_list_requires_auth(self, api_client):
        response = api_client.get(RECORDS_URL)
        assert response.status_code == 401

    def test_create_requires_auth(self, api_client):
        response = api_client.post(RECORDS_URL, {})
        assert response.status_code == 401


@pytest.mark.django_db
class TestViewerRBAC:
    """VIEWER: read-only access."""

    def test_viewer_can_list_records(self, viewer_client):
        response = viewer_client.get(RECORDS_URL)
        assert response.status_code == 200
        assert response.data["success"] is True

    def test_viewer_cannot_create_record(self, viewer_client):
        payload = {
            "amount": "100.00",
            "transaction_type": "INCOME",
            "category": "salary",
            "date": "2024-01-01",
        }
        response = viewer_client.post(RECORDS_URL, payload)
        assert response.status_code == 403

    def test_viewer_cannot_delete_record(self, viewer_client, sample_record):
        response = viewer_client.delete(record_url(sample_record.pk))
        assert response.status_code == 403


@pytest.mark.django_db
class TestAnalystRBAC:
    """ANALYST: can read + write, but NOT delete."""

    def test_analyst_can_create_record(self, analyst_client):
        payload = {
            "amount": "250.00",
            "transaction_type": "EXPENSE",
            "category": "utilities",
            "date": "2024-02-15",
            "description": "Monthly electricity bill",
        }
        response = analyst_client.post(RECORDS_URL, payload)
        assert response.status_code == 201
        assert response.data["success"] is True
        # Confirm the record was actually saved
        assert response.data["data"]["category"] == "utilities"

    def test_analyst_can_update_own_record(self, analyst_client, sample_record):
        response = analyst_client.patch(
            record_url(sample_record.pk), {"description": "Updated description"}
        )
        assert response.status_code == 200

    def test_analyst_cannot_delete_record(self, analyst_client, sample_record):
        response = analyst_client.delete(record_url(sample_record.pk))
        assert response.status_code == 403

    def test_analyst_cannot_see_other_users_records(self, analyst_client, admin_user):
        """Non-admin users should only see their own records."""
        from apps.finance.models import FinancialRecord
        # Create a record for admin_user
        FinancialRecord.objects.create(
            user=admin_user,
            amount="1000.00",
            transaction_type="INCOME",
            category="investment",
            date="2024-01-01",
        )
        response = analyst_client.get(RECORDS_URL)
        # analyst should not see admin's records in their list
        for record in response.data.get("data", []):
            assert record.get("user_email") != admin_user.email


@pytest.mark.django_db
class TestAdminRBAC:
    """ADMIN: full access."""

    def test_admin_can_create_record(self, admin_client):
        payload = {
            "amount": "5000.00",
            "transaction_type": "INCOME",
            "category": "revenue",
            "date": "2024-03-01",
        }
        response = admin_client.post(RECORDS_URL, payload)
        assert response.status_code == 201

    def test_admin_can_soft_delete_record(self, admin_client, sample_record):
        response = admin_client.delete(record_url(sample_record.pk))
        assert response.status_code == 200
        # Record still exists in DB (soft delete)
        from apps.finance.models import FinancialRecord
        record = FinancialRecord.objects.get(pk=sample_record.pk)
        assert record.is_deleted is True

    def test_admin_can_see_all_users_records(self, admin_client, sample_record, viewer_user):
        """Admin should see all records regardless of owner."""
        from apps.finance.models import FinancialRecord
        # Create record for viewer user too
        FinancialRecord.objects.create(
            user=viewer_user,
            amount="100.00",
            transaction_type="EXPENSE",
            category="food",
            date="2024-01-01",
        )
        response = admin_client.get(RECORDS_URL)
        assert response.status_code == 200
        assert response.data["pagination"]["total_count"] >= 2


@pytest.mark.django_db
class TestRecordValidation:
    """Validation tests for FinancialRecord creation."""

    def test_negative_amount_rejected(self, analyst_client):
        payload = {
            "amount": "-100.00",
            "transaction_type": "INCOME",
            "category": "salary",
            "date": "2024-01-01",
        }
        response = analyst_client.post(RECORDS_URL, payload)
        assert response.status_code == 400

    def test_zero_amount_rejected(self, analyst_client):
        payload = {
            "amount": "0.00",
            "transaction_type": "INCOME",
            "category": "salary",
            "date": "2024-01-01",
        }
        response = analyst_client.post(RECORDS_URL, payload)
        assert response.status_code == 400

    def test_missing_required_fields_rejected(self, analyst_client):
        response = analyst_client.post(RECORDS_URL, {"amount": "100.00"})
        assert response.status_code == 400

    def test_invalid_transaction_type_rejected(self, analyst_client):
        payload = {
            "amount": "100.00",
            "transaction_type": "TRANSFER",  # Invalid
            "category": "misc",
            "date": "2024-01-01",
        }
        response = analyst_client.post(RECORDS_URL, payload)
        assert response.status_code == 400


@pytest.mark.django_db
class TestRecordFiltering:
    """Tests for the filtering and search functionality."""

    def test_filter_by_type(self, analyst_client, sample_record):
        response = analyst_client.get(f"{RECORDS_URL}?type=INCOME")
        assert response.status_code == 200
        for record in response.data.get("data", []):
            assert record["transaction_type"] == "INCOME"

    def test_filter_by_category(self, analyst_client, sample_record):
        response = analyst_client.get(f"{RECORDS_URL}?category=salary")
        assert response.status_code == 200
        for record in response.data.get("data", []):
            assert record["category"] == "salary"

    def test_search_by_description(self, analyst_client, sample_record):
        response = analyst_client.get(f"{RECORDS_URL}?search=Monthly%20salary")
        assert response.status_code == 200
