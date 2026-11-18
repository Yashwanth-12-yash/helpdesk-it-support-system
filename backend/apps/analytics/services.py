import csv
from django.http import HttpResponse

from apps.accounts.models import User
from apps.tickets.models import Ticket
from apps.tickets.permissions import scope_tickets_queryset_for_user
from .selectors import _apply_filters


def export_tickets_csv_response(*, user: User, start_date=None, end_date=None, department_id=None) -> HttpResponse:
    qs = (
        scope_tickets_queryset_for_user(Ticket.objects.all(), user)
        .select_related("department", "created_by", "assigned_engineer", "sla")
        .order_by("-created_at")
    )
    qs = _apply_filters(qs, start_date=start_date, end_date=end_date, department_id=department_id)

    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = 'attachment; filename="helpdesk_tickets_report.csv"'

    writer = csv.writer(response)
    writer.writerow(
        [
            "Ticket Number",
            "Title",
            "Category",
            "Priority",
            "Status",
            "Department",
            "Created By",
            "Assigned Engineer",
            "Created At",
            "Resolved At",
            "Resolution SLA Breached",
        ]
    )

    for ticket in qs.iterator(chunk_size=500):
        sla = getattr(ticket, "sla", None)
        writer.writerow(
            [
                ticket.ticket_number,
                ticket.title,
                ticket.category,
                ticket.priority,
                ticket.status,
                ticket.department.name if ticket.department else "",
                ticket.created_by.email,
                ticket.assigned_engineer.email if ticket.assigned_engineer else "Unassigned",
                ticket.created_at.isoformat(),
                ticket.resolved_at.isoformat() if ticket.resolved_at else "",
                "Yes" if (sla and sla.resolution_breached) else "No",
            ]
        )

    return response
