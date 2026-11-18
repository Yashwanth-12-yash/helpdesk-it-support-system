
import pytest
from django.urls import reverse
from rest_framework import status

from apps.accounts.models import User
from apps.tickets.models import Ticket
from tests.factories import DepartmentFactory, SupportTeamFactory, UserFactory


@pytest.mark.django_db
class TestTicketLifecycle:
    def test_create_ticket_generates_hd_number_and_sla(
        self, auth_client_factory, employee_user
    ):
        dept = DepartmentFactory()
        client = auth_client_factory(employee_user)

        res = client.post(
            reverse("ticket-list"),
            {
                "title": "VPN disconnects every 10 minutes",
                "description": "Cisco AnyConnect drops repeatedly on Windows 11.",
                "category": Ticket.Category.NETWORK,
                "priority": Ticket.Priority.HIGH,
                "department": dept.id,
            },
            format="json",
        )

        assert res.status_code == status.HTTP_201_CREATED
        assert res.data["ticket_number"].startswith("HD-")
        assert res.data["status"] == Ticket.Status.OPEN
        assert res.data["sla"] is not None
        assert res.data["response_deadline"] is not None

    def test_employee_only_sees_own_tickets(
        self, auth_client_factory, employee_user
    ):
        other_emp = UserFactory(role=User.Role.EMPLOYEE)
        dept = DepartmentFactory()

        client1 = auth_client_factory(employee_user)
        client2 = auth_client_factory(other_emp)

        t1 = client1.post(
            reverse("ticket-list"),
            {
                "title": "Emp1 issue",
                "description": "Details",
                "department": dept.id,
            },
            format="json",
        ).data

        res2 = client2.get(
            reverse("ticket-detail", args=[t1["id"]])
        )

        assert res2.status_code == status.HTTP_404_NOT_FOUND

    def test_invalid_status_transition_rejected(
        self, auth_client_factory, admin_user, employee_user
    ):
        dept = DepartmentFactory()
        emp_client = auth_client_factory(employee_user)

        ticket = emp_client.post(
            reverse("ticket-list"),
            {
                "title": "Printer offline",
                "description": "Floor 3 printer",
                "department": dept.id,
            },
            format="json",
        ).data

        admin_client = auth_client_factory(admin_user)

        bad_res = admin_client.post(
            reverse("ticket-change-status", args=[ticket["id"]]),
            {
                "status": Ticket.Status.RESOLVED,
                "note": "Trying to jump directly",
            },
            format="json",
        )

        assert bad_res.status_code == status.HTTP_400_BAD_REQUEST

    def test_assign_resolve_and_reopen_flow(
        self,
        auth_client_factory,
        manager_user,
        engineer_user,
        employee_user,
    ):
        dept = DepartmentFactory(manager=manager_user)
        team = SupportTeamFactory(department=dept)

        # The engineer must belong to the ticket's department.
        engineer_user.department = dept
        engineer_user.save(update_fields=["department"])

        emp_client = auth_client_factory(employee_user)
        mgr_client = auth_client_factory(manager_user)
        eng_client = auth_client_factory(engineer_user)

        t = emp_client.post(
            reverse("ticket-list"),
            {
                "title": "Laptop battery swelling",
                "description": "Urgent hardware replacement needed",
                "category": Ticket.Category.HARDWARE,
                "priority": Ticket.Priority.CRITICAL,
                "department": dept.id,
                "support_team": team.id,
            },
            format="json",
        ).data

        assign_res = mgr_client.post(
            reverse("ticket-assign", args=[t["id"]]),
            {"assigned_engineer": engineer_user.id},
            format="json",
        )

        assert assign_res.status_code == status.HTTP_200_OK
        assert assign_res.data["status"] == Ticket.Status.ASSIGNED

        prog_res = eng_client.post(
            reverse("ticket-change-status", args=[t["id"]]),
            {"status": Ticket.Status.IN_PROGRESS},
            format="json",
        )

        assert prog_res.status_code == status.HTTP_200_OK
        assert prog_res.data["first_responded_at"] is not None

        resolve_res = eng_client.post(
            reverse("ticket-resolve", args=[t["id"]]),
            {
                "resolution_notes": (
                    "Replaced battery module and tested charging."
                )
            },
            format="json",
        )

        assert resolve_res.status_code == status.HTTP_200_OK
        assert resolve_res.data["status"] == Ticket.Status.RESOLVED

        reopen_res = emp_client.post(
            reverse("ticket-reopen", args=[t["id"]]),
            {"reason": "Battery still drains unexpectedly."},
            format="json",
        )

        assert reopen_res.status_code == status.HTTP_200_OK
        assert reopen_res.data["status"] == Ticket.Status.REOPENED
        assert reopen_res.data["reopen_count"] == 1
