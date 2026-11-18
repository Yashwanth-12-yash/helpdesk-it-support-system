from unittest.mock import patch
import pytest
from django.urls import reverse
from rest_framework import status

from apps.ai_assistant.gemini_client import GeminiUnavailableError
from apps.knowledge_base.models import KnowledgeArticle
from apps.tickets.models import Ticket
from apps.tickets.services import create_ticket
from tests.factories import DepartmentFactory


@pytest.mark.django_db
class TestAnalyticsKnowledgeAndAI:
    def test_dashboard_analytics_reflects_real_records(self, auth_client_factory, admin_user, employee_user):
        dept = DepartmentFactory()
        create_ticket(
            created_by=employee_user,
            title="Outlook sync issue",
            description="Emails delayed",
            category=Ticket.Category.EMAIL,
            priority=Ticket.Priority.MEDIUM,
            department=dept,
        )
        client = auth_client_factory(admin_user)
        res = client.get(reverse("analytics-dashboard"))
        assert res.status_code == status.HTTP_200_OK
        assert res.data["kpis"]["total_tickets"] == 1
        assert res.data["kpis"]["open_tickets"] == 1

    def test_knowledge_base_publish_visibility(self, auth_client_factory, engineer_user, manager_user, employee_user):
        eng_client = auth_client_factory(engineer_user)
        mgr_client = auth_client_factory(manager_user)
        emp_client = auth_client_factory(employee_user)

        draft = eng_client.post(
            reverse("knowledge-list"),
            {
                "title": "Resetting VPN Token",
                "category": Ticket.Category.NETWORK,
                "summary": "How to resync MFA token",
                "content": "Open Authenticator and resync clock.",
                "status": KnowledgeArticle.Status.PUBLISHED,  # Engineer forced to DRAFT
            },
            format="json",
        )
        assert draft.status_code == status.HTTP_201_CREATED
        assert draft.data["status"] == KnowledgeArticle.Status.DRAFT

        # Employee cannot see draft
        emp_list = emp_client.get(reverse("knowledge-list")).data
        assert emp_list["count"] == 0

        # Manager publishes
        pub = mgr_client.post(reverse("knowledge-publish", args=[draft.data["id"]]))
        assert pub.status_code == status.HTTP_200_OK
        assert pub.data["status"] == KnowledgeArticle.Status.PUBLISHED

        emp_list_after = emp_client.get(reverse("knowledge-list")).data
        assert emp_list_after["count"] == 1

    def test_ai_unavailable_returns_graceful_503_without_crashing(self, auth_client_factory, employee_user):
        client = auth_client_factory(employee_user)
        with patch(
            "apps.ai_assistant.services.generate_structured_json",
            side_effect=GeminiUnavailableError("Gemini API offline"),
        ):
            res = client.post(
                reverse("ai-classify-ticket"),
                {"title": "Cannot connect to Wi-Fi", "description": "802.1X auth failed"},
                format="json",
            )
        assert res.status_code == status.HTTP_503_SERVICE_UNAVAILABLE
        assert res.data["error"]["code"] == "ai_service_unavailable"
