from datetime import datetime
from django.db.models import Avg, Count, DurationField, ExpressionWrapper, F, Q
from django.utils import timezone

from apps.accounts.models import User
from apps.sla.models import TicketSLA
from apps.tickets.models import Ticket
from apps.tickets.permissions import scope_tickets_queryset_for_user


def _apply_filters(qs, *, start_date: str | None, end_date: str | None, department_id: int | None):
    if start_date:
        try:
            dt = timezone.make_aware(datetime.fromisoformat(start_date)) if "T" not in start_date else datetime.fromisoformat(start_date)
            qs = qs.filter(created_at__gte=dt)
        except ValueError:
            pass
    if end_date:
        try:
            dt = timezone.make_aware(datetime.fromisoformat(end_date)) if "T" not in end_date else datetime.fromisoformat(end_date)
            qs = qs.filter(created_at__lte=dt)
        except ValueError:
            pass
    if department_id:
        qs = qs.filter(department_id=department_id)
    return qs


def get_dashboard_analytics(*, user: User, start_date=None, end_date=None, department_id=None) -> dict:
    now = timezone.now()
    qs = scope_tickets_queryset_for_user(Ticket.objects.all(), user)
    qs = _apply_filters(qs, start_date=start_date, end_date=end_date, department_id=department_id)

    active_statuses = [
        Ticket.Status.OPEN,
        Ticket.Status.ASSIGNED,
        Ticket.Status.IN_PROGRESS,
        Ticket.Status.ON_HOLD,
        Ticket.Status.REOPENED,
    ]

    summary = qs.aggregate(
        total_tickets=Count("id"),
        open_tickets=Count("id", filter=Q(status=Ticket.Status.OPEN)),
        assigned_tickets=Count("id", filter=Q(status=Ticket.Status.ASSIGNED)),
        in_progress_tickets=Count("id", filter=Q(status=Ticket.Status.IN_PROGRESS)),
        on_hold_tickets=Count("id", filter=Q(status=Ticket.Status.ON_HOLD)),
        resolved_tickets=Count("id", filter=Q(status__in=[Ticket.Status.RESOLVED, Ticket.Status.CLOSED])),
        reopened_tickets=Count("id", filter=Q(status=Ticket.Status.REOPENED)),
        critical_tickets=Count("id", filter=Q(priority=Ticket.Priority.CRITICAL, status__in=active_statuses)),
        overdue_tickets=Count("id", filter=Q(status__in=active_statuses, resolution_deadline__lt=now)),
        avg_first_response=Avg(
            ExpressionWrapper(F("first_responded_at") - F("created_at"), output_field=DurationField()),
            filter=Q(first_responded_at__isnull=False),
        ),
        avg_resolution=Avg(
            ExpressionWrapper(F("resolved_at") - F("created_at"), output_field=DurationField()),
            filter=Q(resolved_at__isnull=False),
        ),
    )

    sla_qs = TicketSLA.objects.filter(ticket__in=qs)
    sla_stats = sla_qs.aggregate(
        total_resolved_sla=Count("id", filter=Q(resolved_at__isnull=False)),
        met_sla=Count("id", filter=Q(resolved_at__isnull=False, resolution_breached=False)),
    )
    resolved_sla = sla_stats["total_resolved_sla"] or 0
    sla_compliance = (
        round((sla_stats["met_sla"] / resolved_sla) * 100, 2)
        if resolved_sla
        else None
    )

    avg_resp_minutes = (
        round(summary["avg_first_response"].total_seconds() / 60, 1)
        if summary["avg_first_response"]
        else 0.0
    )
    avg_res_hours = (
        round(summary["avg_resolution"].total_seconds() / 3600, 2)
        if summary["avg_resolution"]
        else 0.0
    )

    by_priority = list(qs.values("priority").annotate(count=Count("id")).order_by("priority"))
    by_status = list(qs.values("status").annotate(count=Count("id")).order_by("status"))
    by_category = list(qs.values("category").annotate(count=Count("id")).order_by("-count"))
    by_department = list(
        qs.values("department_id", name=F("department__name"), code=F("department__code"))
        .annotate(count=Count("id"))
        .order_by("-count")
    )

    return {
        "kpis": {
            "total_tickets": summary["total_tickets"],
            "open_tickets": summary["open_tickets"],
            "assigned_tickets": summary["assigned_tickets"],
            "in_progress_tickets": summary["in_progress_tickets"],
            "on_hold_tickets": summary["on_hold_tickets"],
            "resolved_tickets": summary["resolved_tickets"],
            "reopened_tickets": summary["reopened_tickets"],
            "critical_tickets": summary["critical_tickets"],
            "overdue_tickets": summary["overdue_tickets"],
            "sla_compliance_percentage": sla_compliance,
            "avg_response_minutes": avg_resp_minutes,
            "avg_resolution_hours": avg_res_hours,
        },
        "by_priority": by_priority,
        "by_status": by_status,
        "by_category": by_category,
        "by_department": by_department,
    }


def get_engineer_performance(*, user: User, start_date=None, end_date=None, department_id=None) -> list[dict]:
    qs = scope_tickets_queryset_for_user(Ticket.objects.all(), user).filter(assigned_engineer__isnull=False)
    qs = _apply_filters(qs, start_date=start_date, end_date=end_date, department_id=department_id)

    rows = (
        qs.values(
            "assigned_engineer_id",
            email=F("assigned_engineer__email"),
            first_name=F("assigned_engineer__first_name"),
            last_name=F("assigned_engineer__last_name"),
        )
        .annotate(
            total_assigned=Count("id"),
            resolved_count=Count("id", filter=Q(status__in=[Ticket.Status.RESOLVED, Ticket.Status.CLOSED])),
            open_count=Count(
                "id",
                filter=Q(
                    status__in=[
                        Ticket.Status.OPEN,
                        Ticket.Status.ASSIGNED,
                        Ticket.Status.IN_PROGRESS,
                        Ticket.Status.ON_HOLD,
                        Ticket.Status.REOPENED,
                    ]
                ),
            ),
            sla_breached_count=Count("id", filter=Q(sla__resolution_breached=True)),
            avg_resolution=Avg(
                ExpressionWrapper(F("resolved_at") - F("created_at"), output_field=DurationField()),
                filter=Q(resolved_at__isnull=False),
            ),
        )
        .order_by("-resolved_count", "-total_assigned")
    )

    result = []
    for row in rows:
        avg_hours = round(row["avg_resolution"].total_seconds() / 3600, 2) if row["avg_resolution"] else 0.0
        resolved = row["resolved_count"] or 0
        breached = row["sla_breached_count"] or 0
        compliance = round(((max(resolved - breached, 0)) / resolved) * 100, 2) if resolved else 100.0
        result.append(
            {
                "engineer_id": row["assigned_engineer_id"],
                "name": f"{row['first_name']} {row['last_name']}".strip(),
                "email": row["email"],
                "total_assigned": row["total_assigned"],
                "resolved_count": resolved,
                "open_count": row["open_count"],
                "sla_breached_count": breached,
                "sla_compliance_percentage": compliance,
                "avg_resolution_hours": avg_hours,
            }
        )
    return result
