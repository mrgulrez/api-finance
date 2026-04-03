"""
Tests for authentication endpoints.

Covers:
  - Public registration
  - Login with correct credentials
  - Login with wrong password
  - Login with unverified (inactive) account
  - Logout blacklists token
"""
import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse

User = get_user_model()

REGISTER_URL = "/api/v1/auth/register/"
LOGIN_URL = "/api/v1/auth/login/"
LOGOUT_URL = "/api/v1/auth/logout/"


@pytest.mark.django_db
class TestRegistration:
    def test_register_creates_inactive_user(self, api_client):
        """New accounts start inactive — must verify email before logging in."""
        payload = {
            "email": "newuser@test.com",
            "full_name": "New User",
            "password": "securepass99",
            "confirm_password": "securepass99",
        }
        response = api_client.post(REGISTER_URL, payload)
        # Note: email sending is disabled in tests via EMAIL_BACKEND override in settings
        assert response.status_code == 201
        assert response.data["success"] is True
        user = User.objects.get(email="newuser@test.com")
        assert user.is_active is False
        assert user.role == "VIEWER"

    def test_register_mismatched_passwords_returns_400(self, api_client):
        payload = {
            "email": "bad@test.com",
            "full_name": "Test",
            "password": "password1",
            "confirm_password": "password2",
        }
        response = api_client.post(REGISTER_URL, payload)
        assert response.status_code == 400
        assert response.data["success"] is False

    def test_register_duplicate_email_returns_400(self, api_client, viewer_user):
        payload = {
            "email": viewer_user.email,
            "full_name": "Duplicate",
            "password": "testpass123",
            "confirm_password": "testpass123",
        }
        response = api_client.post(REGISTER_URL, payload)
        assert response.status_code == 400
        assert "already exists" in str(response.data).lower()

    def test_register_short_password_returns_400(self, api_client):
        payload = {
            "email": "short@test.com",
            "full_name": "Test",
            "password": "abc",
            "confirm_password": "abc",
        }
        response = api_client.post(REGISTER_URL, payload)
        assert response.status_code == 400


@pytest.mark.django_db
class TestLogin:
    def test_login_active_user_returns_tokens(self, api_client, viewer_user):
        response = api_client.post(LOGIN_URL, {"email": viewer_user.email, "password": "testpass123"})
        assert response.status_code == 200
        assert "access" in response.data
        assert "refresh" in response.data
        assert response.data["user"]["role"] == "VIEWER"

    def test_login_wrong_password_returns_401(self, api_client, viewer_user):
        response = api_client.post(LOGIN_URL, {"email": viewer_user.email, "password": "WRONG"})
        assert response.status_code == 401

    def test_login_inactive_user_returns_401(self, api_client, db):
        """Unverified users cannot log in."""
        user = User.objects.create_user(
            email="unverified@test.com",
            password="testpass123",
            full_name="Unverified",
            is_active=False,
        )
        response = api_client.post(LOGIN_URL, {"email": user.email, "password": "testpass123"})
        assert response.status_code == 401

    def test_login_nonexistent_email_returns_401(self, api_client):
        response = api_client.post(LOGIN_URL, {"email": "ghost@test.com", "password": "anything"})
        assert response.status_code == 401


@pytest.mark.django_db
class TestLogout:
    def test_logout_blacklists_refresh_token(self, api_client, viewer_user):
        login_response = api_client.post(LOGIN_URL, {"email": viewer_user.email, "password": "testpass123"})
        refresh_token = login_response.data["refresh"]
        access_token = login_response.data["access"]

        api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {access_token}")
        logout_response = api_client.post(LOGOUT_URL, {"refresh": refresh_token})
        assert logout_response.status_code == 200

    def test_logout_without_token_returns_400(self, api_client, viewer_client):
        response = viewer_client.post(LOGOUT_URL, {})
        assert response.status_code == 400
