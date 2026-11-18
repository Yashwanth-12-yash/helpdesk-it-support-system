from django.db.models import QuerySet

from apps.accounts.models import User
from .models import Ticket, TicketHistory
from .permissions import scope_tickets_queryset_for_user


def get_tickets_queryset(*, requesting_user: User) -> QuerySet[Ticket]:
    base_qs = (
        Ticket.objects.select_related(
            "created_by",
            "assigned_engineer",
            "department",
            "support_team",
        )
        .order_by("-created_at")
    )
    return scope_tickets_queryset_for_user(base_qs, requesting_user)


def get_ticket_history_queryset(*, ticket: Ticket) -> QuerySet[TicketHistory]:
    return (
        TicketHistory.objects.filter(ticket=ticket)
        .select_related("changed_by")
        .order_by("created_at")
    )
