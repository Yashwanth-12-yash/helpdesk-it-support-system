
import pytest
from django.urls import reverse
from rest_framework import status

from apps.accounts.models import User
from tests.factories import DepartmentFactory, SupportTeamFactory, UserFactory


@pytest.mark.django_db
class TestDepartmentsAndTeams:
    def test_admin_can_create_department_with_manager(
        self, auth_client_factory, admin_user, manager_user
    ):
        client = auth_client_factory(admin_user)
        response = client.post(
            reverse("department-list"),
            {
                "name": "Infrastructure & Cloud",
                "code": "infra",
                "description": "Servers, Cloud, and Networking",
                "manager": manager_user.id,
            },
            format="json",
        )

        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["code"] == "INFRA"
        assert response.data["manager"] == manager_user.id

    def test_department_rejects_employee_as_manager(
        self, auth_client_factory, admin_user, employee_user
    ):
        client = auth_client_factory(admin_user)
        response = client.post(
            reverse("department-list"),
            {
                "name": "Security Operations",
                "code": "SEC",
                "manager": employee_user.id,
            },
            format="json",
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_non_admin_cannot_create_department(
        self, auth_client_factory, manager_user
    ):
        client = auth_client_factory(manager_user)
        response = client.post(
            reverse("department-list"),
            {"name": "Finance IT", "code": "FIN"},
            format="json",
        )

        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_manager_can_manage_members_only_for_own_department_team(
        self, auth_client_factory, manager_user, engineer_user
    ):
        own_dept = DepartmentFactory(manager=manager_user)

        # The engineer must belong to the Manager's department.
        engineer_user.department = own_dept
        engineer_user.save(update_fields=["department"])

        other_manager = UserFactory(role=User.Role.MANAGER)
        other_dept = DepartmentFactory(manager=other_manager)

        own_team = SupportTeamFactory(department=own_dept)
        other_team = SupportTeamFactory(department=other_dept)

        client = auth_client_factory(manager_user)

        # Allowed: add an engineer from the Manager's own department.
        add_res = client.post(
            reverse("team-members", args=[own_team.id]),
            {"user": engineer_user.id, "is_primary": True},
            format="json",
        )

        assert add_res.status_code == status.HTTP_201_CREATED
        assert add_res.data["is_primary"] is True

        # Forbidden: manage another Manager's department team.
        denied_res = client.post(
            reverse("team-members", args=[other_team.id]),
            {"user": engineer_user.id, "is_primary": False},
            format="json",
        )

        # The other department's team is hidden from this Manager.
        assert denied_res.status_code == status.HTTP_404_NOT_FOUND

    def test_team_rejects_employee_membership(
        self, auth_client_factory, admin_user, employee_user
    ):
        team = SupportTeamFactory()
        client = auth_client_factory(admin_user)

        response = client.post(
            reverse("team-members", args=[team.id]),
            {"user": employee_user.id, "is_primary": False},
            format="json",
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
