from datetime import timedelta
import pytest
from django.utils import timezone

from apps.sla.models import Escalation, TicketSLA
from apps.sla.services import run_sla_deadline_sweep
from apps.tickets.models import Ticket
from apps.tickets.services import create_ticket
from tests.factories import DepartmentFactory


@pytest.mark.django_db
class TestSLAAndEscalations:
    def test_sla_breach_creates_single_deduplicated_escalation(self, employee_user, manager_user):
        dept = DepartmentFactory(manager=manager_user)
        ticket = create_ticket(
            created_by=employee_user,
            title="Core switch unreachable",
            description="Building A offline",
            category=Ticket.Category.NETWORK,
            priority=Ticket.Priority.CRITICAL,
            department=dept,
        )

        # Backdate SLA deadlines to simulate breach
        sla = TicketSLA.objects.get(ticket=ticket)
        past = timezone.now() - timedelta(hours=3)
        sla.response_due_at = past
        sla.resolution_due_at = past
        sla.save(update_fields=["response_due_at", "resolution_due_at"])

        first_run = run_sla_deadline_sweep()
        second_run = run_sla_deadline_sweep()

        assert first_run["breaches_created"] == 2
        assert second_run["breaches_created"] == 0
        assert Escalation.objects.filter(ticket=ticket).count() == 2
