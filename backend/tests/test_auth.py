import pytest
from django.urls import reverse
from rest_framework import status

from apps.accounts.models import User
from tests.factories import UserFactory


@pytest.mark.django_db
class TestAuthentication:
    def test_login_success_returns_jwt_and_user(self, api_client, employee_user):
        response = api_client.post(
            reverse("auth-login"),
            {"email": employee_user.email, "password": "StrongPass#2026!"},
            format="json",
        )
        assert response.status_code == status.HTTP_200_OK
        assert "access" in response.data
        assert "refresh" in response.data
        assert response.data["user"]["email"] == employee_user.email
        assert response.data["user"]["role"] == User.Role.EMPLOYEE

    def test_login_rejects_inactive_user(self, api_client):
        inactive = UserFactory(email="disabled@helpdesk.local", is_active=False)
        response = api_client.post(
            reverse("auth-login"),
            {"email": inactive.email, "password": "StrongPass#2026!"},
            format="json",
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_refresh_token_rotates_tokens(self, api_client, employee_user):
        login_res = api_client.post(
            reverse("auth-login"),
            {"email": employee_user.email, "password": "StrongPass#2026!"},
            format="json",
        )
        refresh_token = login_res.data["refresh"]

        refresh_res = api_client.post(
            reverse("auth-refresh"),
            {"refresh": refresh_token},
            format="json",
        )
        assert refresh_res.status_code == status.HTTP_200_OK
        assert "access" in refresh_res.data
        assert "refresh" in refresh_res.data
        assert refresh_res.data["refresh"] != refresh_token

    def test_logout_blacklists_refresh_token(self, api_client, employee_user):
        login_res = api_client.post(
            reverse("auth-login"),
            {"email": employee_user.email, "password": "StrongPass#2026!"},
            format="json",
        )
        access = login_res.data["access"]
        refresh = login_res.data["refresh"]

        api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {access}")
        logout_res = api_client.post(reverse("auth-logout"), {"refresh": refresh}, format="json")
        assert logout_res.status_code == status.HTTP_205_RESET_CONTENT

        reuse_res = api_client.post(reverse("auth-refresh"), {"refresh": refresh}, format="json")
        assert reuse_res.status_code == status.HTTP_401_UNAUTHORIZED

    def test_me_endpoint_prevents_role_escalation(self, auth_client_factory, employee_user):
        client = auth_client_factory(employee_user)
        response = client.patch(
            reverse("auth-me"),
            {"first_name": "Updated", "role": User.Role.ADMIN},
            format="json",
        )
        assert response.status_code == status.HTTP_200_OK
        employee_user.refresh_from_db()
        assert employee_user.first_name == "Updated"
        assert employee_user.role == User.Role.EMPLOYEE
