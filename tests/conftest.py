"""
Shared test fixtures and configuration for the Finance Backend test suite.
"""
import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

User = get_user_model()


@pytest.fixture
def api_client():
    """Return an unauthenticated DRF test client."""
    return APIClient()


@pytest.fixture
def viewer_user(db):
    """Create a VIEWER role user, active and verified."""
    return User.objects.create_user(
        email="viewer@test.com",
        password="testpass123",
        full_name="Viewer User",
        role="VIEWER",
        is_active=True,
    )


@pytest.fixture
def analyst_user(db):
    """Create an ANALYST role user."""
    return User.objects.create_user(
        email="analyst@test.com",
        password="testpass123",
        full_name="Analyst User",
        role="ANALYST",
        is_active=True,
    )


@pytest.fixture
def admin_user(db):
    """Create an ADMIN role user."""
    return User.objects.create_user(
        email="admin@test.com",
        password="testpass123",
        full_name="Admin User",
        role="ADMIN",
        is_active=True,
    )


@pytest.fixture
def viewer_client(api_client, viewer_user):
    """Authenticated API client with VIEWER role."""
    api_client.force_authenticate(user=viewer_user)
    return api_client


@pytest.fixture
def analyst_client(api_client, analyst_user):
    """Authenticated API client with ANALYST role."""
    api_client.force_authenticate(user=analyst_user)
    return api_client


@pytest.fixture
def admin_client(api_client, admin_user):
    """Authenticated API client with ADMIN role."""
    api_client.force_authenticate(user=admin_user)
    return api_client


@pytest.fixture
def sample_record(db, analyst_user):
    """Create a single FinancialRecord owned by the analyst user."""
    from apps.finance.models import FinancialRecord
    return FinancialRecord.objects.create(
        user=analyst_user,
        amount="500.00",
        transaction_type="INCOME",
        category="salary",
        date="2024-03-01",
        description="Monthly salary",
    )
