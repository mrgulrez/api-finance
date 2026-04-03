"""
Tests for the User management endpoints (ADMIN-only).

Verifies:
  - Only ADMINs can list all users
  - Role update is ADMIN-only
  - Status update is ADMIN-only
  - Soft delete preserves data in DB
  - Users can update their own profile fields
"""
import pytest
from django.contrib.auth import get_user_model

User = get_user_model()

USERS_URL = "/api/v1/users/"


def user_url(pk):
    return f"/api/v1/users/{pk}/"


def user_role_url(pk):
    return f"/api/v1/users/{pk}/role/"


def user_status_url(pk):
    return f"/api/v1/users/{pk}/status/"


@pytest.mark.django_db
class TestUserListAccess:
    def test_admin_can_list_all_users(self, admin_client, viewer_user, analyst_user):
        response = admin_client.get(USERS_URL)
        assert response.status_code == 200
        assert response.data["success"] is True
        # At least the 3 users created (admin + viewer + analyst)
        assert response.data["pagination"]["total_count"] >= 3

    def test_viewer_cannot_list_users(self, viewer_client):
        response = viewer_client.get(USERS_URL)
        assert response.status_code == 403

    def test_analyst_cannot_list_users(self, analyst_client):
        response = analyst_client.get(USERS_URL)
        assert response.status_code == 403

    def test_unauthenticated_cannot_list_users(self, api_client):
        response = api_client.get(USERS_URL)
        assert response.status_code == 401


@pytest.mark.django_db
class TestRoleManagement:
    def test_admin_can_change_user_role(self, admin_client, viewer_user):
        response = admin_client.patch(
            user_role_url(viewer_user.pk), {"role": "ANALYST"}
        )
        assert response.status_code == 200
        viewer_user.refresh_from_db()
        assert viewer_user.role == "ANALYST"

    def test_non_admin_cannot_change_role(self, analyst_client, viewer_user):
        response = analyst_client.patch(
            user_role_url(viewer_user.pk), {"role": "ADMIN"}
        )
        assert response.status_code == 403

    def test_invalid_role_returns_400(self, admin_client, viewer_user):
        response = admin_client.patch(
            user_role_url(viewer_user.pk), {"role": "SUPERUSER"}
        )
        assert response.status_code == 400


@pytest.mark.django_db
class TestStatusManagement:
    def test_admin_can_deactivate_user(self, admin_client, viewer_user):
        response = admin_client.patch(
            user_status_url(viewer_user.pk), {"is_active": False}
        )
        assert response.status_code == 200
        viewer_user.refresh_from_db()
        assert viewer_user.is_active is False

    def test_admin_can_reactivate_user(self, admin_client, viewer_user):
        viewer_user.is_active = False
        viewer_user.save()
        response = admin_client.patch(
            user_status_url(viewer_user.pk), {"is_active": True}
        )
        assert response.status_code == 200
        viewer_user.refresh_from_db()
        assert viewer_user.is_active is True


@pytest.mark.django_db
class TestSoftDelete:
    def test_admin_soft_delete_preserves_data(self, admin_client, viewer_user):
        pk = viewer_user.pk
        response = admin_client.delete(user_url(pk))
        assert response.status_code == 200
        # Data still in DB
        user = User.objects.filter(pk=pk).first()
        assert user is not None
        assert user.is_deleted is True
        assert user.is_active is False

    def test_soft_deleted_user_does_not_appear_in_list(self, admin_client, viewer_user):
        viewer_user.is_deleted = True
        viewer_user.save()
        response = admin_client.get(USERS_URL)
        emails = [u["email"] for u in response.data.get("data", [])]
        assert viewer_user.email not in emails


@pytest.mark.django_db
class TestProfileUpdate:
    def test_user_can_update_own_full_name(self, viewer_client, viewer_user):
        response = viewer_client.patch(user_url(viewer_user.pk), {"full_name": "Updated Name"})
        assert response.status_code == 200
        viewer_user.refresh_from_db()
        assert viewer_user.full_name == "Updated Name"

    def test_user_cannot_update_another_users_profile(self, viewer_client, analyst_user):
        response = viewer_client.patch(user_url(analyst_user.pk), {"full_name": "Hacked"})
        assert response.status_code == 403
