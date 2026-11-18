import pytest
from django.urls import reverse
from rest_framework import status

from apps.accounts.models import User
from tests.factories import UserFactory


@pytest.mark.django_db
class TestUserManagementRBAC:
    def test_unauthenticated_user_cannot_list_users(self, api_client):
        response = api_client.get(reverse("user-list"))
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    @pytest.mark.parametrize("fixture_name", ["employee_user", "engineer_user"])
    def test_employee_and_engineer_forbidden_from_user_list(self, request, auth_client_factory, fixture_name):
        user = request.getfixturevalue(fixture_name)
        client = auth_client_factory(user)
        response = client.get(reverse("user-list"))
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_manager_can_read_active_users_but_cannot_create(self, auth_client_factory, manager_user):
        client = auth_client_factory(manager_user)
        list_res = client.get(reverse("user-list"))
        assert list_res.status_code == status.HTTP_200_OK

        create_res = client.post(
            reverse("user-list"),
            {
                "email": "new.emp@helpdesk.local",
                "first_name": "New",
                "last_name": "Employee",
                "role": User.Role.EMPLOYEE,
                "password": "StrongPass#2026!",
            },
            format="json",
        )
        assert create_res.status_code == status.HTTP_403_FORBIDDEN

    def test_admin_can_create_and_toggle_user_active(self, auth_client_factory, admin_user):
        client = auth_client_factory(admin_user)
        create_res = client.post(
            reverse("user-list"),
            {
                "email": "tech.lead@helpdesk.local",
                "first_name": "Alex",
                "last_name": "Rivera",
                "role": User.Role.ENGINEER,
                "job_title": "Systems Engineer",
                "password": "StrongPass#2026!",
            },
            format="json",
        )
        assert create_res.status_code == status.HTTP_201_CREATED
        created_id = create_res.data["id"]

        toggle_res = client.post(reverse("user-toggle-active", args=[created_id]))
        assert toggle_res.status_code == status.HTTP_200_OK
        assert toggle_res.data["is_active"] is False

    def test_admin_cannot_deactivate_self(self, auth_client_factory, admin_user):
        client = auth_client_factory(admin_user)
        response = client.post(reverse("user-toggle-active", args=[admin_user.id]))
        assert response.status_code == status.HTTP_400_BAD_REQUEST
