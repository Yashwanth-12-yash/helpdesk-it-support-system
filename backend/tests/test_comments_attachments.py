
import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from rest_framework import status

from apps.tickets.models import Ticket
from tests.factories import DepartmentFactory


@pytest.mark.django_db
class TestCommentsAndAttachments:
    def test_employee_cannot_create_or_see_internal_notes(
        self, auth_client_factory, engineer_user, employee_user, admin_user
    ):
        dept = DepartmentFactory()

        # The engineer must belong to the ticket's department
        # before the Admin assigns the ticket.
        engineer_user.department = dept
        engineer_user.save(update_fields=["department"])

        emp_client = auth_client_factory(employee_user)
        admin_client = auth_client_factory(admin_user)
        eng_client = auth_client_factory(engineer_user)

        ticket = emp_client.post(
            reverse("ticket-list"),
            {
                "title": "ERP login failure",
                "description": "SSO loop",
                "department": dept.id,
            },
            format="json",
        ).data

        assignment_response = admin_client.post(
            reverse("ticket-assign", args=[ticket["id"]]),
            {"assigned_engineer": engineer_user.id},
            format="json",
        )

        assert assignment_response.status_code == status.HTTP_200_OK

        # Employee is blocked from posting an internal note.
        bad = emp_client.post(
            reverse("ticket-comments", args=[ticket["id"]]),
            {"body": "Internal attempt", "is_internal": True},
            format="json",
        )
        assert bad.status_code == status.HTTP_403_FORBIDDEN

        # Assigned engineer posts an internal and a public note.
        internal_response = eng_client.post(
            reverse("ticket-comments", args=[ticket["id"]]),
            {
                "body": "Checking Okta SAML logs",
                "is_internal": True,
            },
            format="json",
        )
        assert internal_response.status_code == status.HTTP_201_CREATED

        public_response = eng_client.post(
            reverse("ticket-comments", args=[ticket["id"]]),
            {
                "body": "We are investigating your SSO issue.",
                "is_internal": False,
            },
            format="json",
        )
        assert public_response.status_code == status.HTTP_201_CREATED

        # Employee should see only the public comment.
        emp_comments = emp_client.get(
            reverse("ticket-comments", args=[ticket["id"]])
        ).data

        assert len(emp_comments) == 1
        assert emp_comments[0]["is_internal"] is False

    def test_attachment_rejects_disallowed_extension_and_allows_pdf(
        self, auth_client_factory, employee_user
    ):
        dept = DepartmentFactory()
        emp_client = auth_client_factory(employee_user)

        ticket = emp_client.post(
            reverse("ticket-list"),
            {
                "title": "Invoice crash",
                "description": "Crash screenshot",
                "department": dept.id,
            },
            format="json",
        ).data

        bad_file = SimpleUploadedFile(
            "malware.exe",
            b"MZ...",
            content_type="application/octet-stream",
        )

        bad_res = emp_client.post(
            reverse("ticket-attachments", args=[ticket["id"]]),
            {"file": bad_file},
            format="multipart",
        )
        assert bad_res.status_code == status.HTTP_400_BAD_REQUEST

        good_file = SimpleUploadedFile(
            "error_log.txt",
            b"Traceback line 1",
            content_type="text/plain",
        )

        good_res = emp_client.post(
            reverse("ticket-attachments", args=[ticket["id"]]),
            {"file": good_file},
            format="multipart",
        )

        assert good_res.status_code == status.HTTP_201_CREATED
        assert good_res.data["original_filename"] == "error_log.txt"
