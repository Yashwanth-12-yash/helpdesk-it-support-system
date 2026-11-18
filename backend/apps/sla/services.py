import logging
from datetime import datetime, timedelta
from django.db import IntegrityError, transaction
from django.utils import timezone
from rest_framework.exceptions import ValidationError

from apps.accounts.models import User
from apps.audit.services import record_audit_event
from apps.notifications.models import Notification
from apps.notifications.services import notify_users
from apps.tickets.models import Ticket
from .models import Escalation, SLAPolicy, TicketSLA

logger = logging.getLogger("apps.sla")

DEFAULT_SLA_CONFIG = {
    Ticket.Priority.CRITICAL: {"name": "Critical Priority SLA", "first_response": 15, "resolution": 120},
    Ticket.Priority.HIGH: {"name": "High Priority SLA", "first_response": 30, "resolution": 240},
    Ticket.Priority.MEDIUM: {"name": "Medium Priority SLA", "first_response": 120, "resolution": 1440},
    Ticket.Priority.LOW: {"name": "Low Priority SLA", "first_response": 240, "resolution": 2880},
}


def add_sla_minutes(
    start_dt: datetime,
    minutes: int,
    policy: SLAPolicy,
    holidays: set | None = None,
) -> datetime:
    """
    Calculate SLA deadline timestamp. Supports 24/7 or business-hours schedules
    and accepts an optional set of holiday dates for future business-calendar support.
    """
    if not policy.business_hours_only:
        return start_dt + timedelta(minutes=minutes)

    holidays = holidays or set()
    working_days = set(policy.working_days or [0, 1, 2, 3, 4])
    remaining = minutes
    cursor = start_dt

    while remaining > 0:
        if cursor.weekday() not in working_days or cursor.date() in holidays:
            next_day = (cursor + timedelta(days=1)).date()
            cursor = timezone.make_aware(
                datetime.combine(next_day, policy.business_start_time),
                cursor.tzinfo,
            )
            continue

        day_start = timezone.make_aware(datetime.combine(cursor.date(), policy.business_start_time), cursor.tzinfo)
        day_end = timezone.make_aware(datetime.combine(cursor.date(), policy.business_end_time), cursor.tzinfo)

        if cursor < day_start:
            cursor = day_start
        if cursor >= day_end:
            next_day = (cursor + timedelta(days=1)).date()
            cursor = timezone.make_aware(
                datetime.combine(next_day, policy.business_start_time),
                cursor.tzinfo,
            )
            continue

        available_minutes = int((day_end - cursor).total_seconds() // 60)
        if remaining <= available_minutes:
            return cursor + timedelta(minutes=remaining)

        remaining -= max(available_minutes, 1)
        next_day = (cursor + timedelta(days=1)).date()
        cursor = timezone.make_aware(
            datetime.combine(next_day, policy.business_start_time),
            cursor.tzinfo,
        )

    return cursor


def resolve_sla_policy(*, priority: str, department_id: int | None) -> SLAPolicy:
    """Fetch department override SLA policy, global policy, or auto-provision default."""
    if department_id:
        dept_policy = SLAPolicy.objects.filter(
            priority=priority, department_id=department_id, is_active=True
        ).first()
        if dept_policy:
            return dept_policy

    global_policy = SLAPolicy.objects.filter(
        priority=priority, department__isnull=True, is_active=True
    ).first()
    if global_policy:
        return global_policy

    defaults = DEFAULT_SLA_CONFIG[priority]
    policy, _ = SLAPolicy.objects.get_or_create(
        priority=priority,
        department=None,
        defaults={
            "name": defaults["name"],
            "first_response_minutes": defaults["first_response"],
            "resolution_minutes": defaults["resolution"],
            "is_active": True,
        },
    )
    return policy


@transaction.atomic
def initialize_ticket_sla(*, ticket: Ticket) -> TicketSLA:
    policy = resolve_sla_policy(priority=ticket.priority, department_id=ticket.department_id)
    now = ticket.created_at or timezone.now()
    response_due = add_sla_minutes(now, policy.first_response_minutes, policy)
    resolution_due = add_sla_minutes(now, policy.resolution_minutes, policy)

    sla = TicketSLA.objects.create(
        ticket=ticket,
        policy=policy,
        response_due_at=response_due,
        resolution_due_at=resolution_due,
    )
    ticket.response_deadline = response_due
    ticket.resolution_deadline = resolution_due
    ticket.save(update_fields=["response_deadline", "resolution_deadline", "updated_at"])
    return sla


@transaction.atomic
def recalculate_ticket_sla_for_priority(*, ticket: Ticket) -> TicketSLA:
    policy = resolve_sla_policy(priority=ticket.priority, department_id=ticket.department_id)
    sla = getattr(ticket, "sla", None)
    if not sla:
        return initialize_ticket_sla(ticket=ticket)

    base_time = ticket.created_at
    paused_offset = timedelta(seconds=sla.total_paused_seconds)
    response_due = add_sla_minutes(base_time, policy.first_response_minutes, policy)
    resolution_due = add_sla_minutes(base_time, policy.resolution_minutes, policy) + paused_offset

    sla.policy = policy
    sla.response_due_at = response_due
    sla.resolution_due_at = resolution_due
    sla.save(update_fields=["policy", "response_due_at", "resolution_due_at", "updated_at"])

    ticket.response_deadline = response_due
    ticket.resolution_deadline = resolution_due
    ticket.save(update_fields=["response_deadline", "resolution_deadline", "updated_at"])
    return sla


@transaction.atomic
def record_first_response(*, ticket: Ticket, responded_at: datetime | None = None) -> None:
    if ticket.first_responded_at is not None:
        return
    now = responded_at or timezone.now()
    ticket.first_responded_at = now
    ticket.save(update_fields=["first_responded_at", "updated_at"])

    sla = getattr(ticket, "sla", None)
    if sla and sla.first_response_at is None:
        sla.first_response_at = now
        if now > sla.response_due_at:
            sla.response_breached = True
        sla.save(update_fields=["first_response_at", "response_breached", "updated_at"])


@transaction.atomic
def pause_sla(*, ticket: Ticket) -> None:
    sla = getattr(ticket, "sla", None)
    if sla and sla.paused_at is None and sla.resolved_at is None:
        sla.paused_at = timezone.now()
        sla.save(update_fields=["paused_at", "updated_at"])


@transaction.atomic
def resume_sla(*, ticket: Ticket) -> None:
    sla = getattr(ticket, "sla", None)
    if sla and sla.paused_at is not None:
        now = timezone.now()
        paused_seconds = max(int((now - sla.paused_at).total_seconds()), 0)
        sla.total_paused_seconds += paused_seconds
        sla.resolution_due_at = sla.resolution_due_at + timedelta(seconds=paused_seconds)
        sla.paused_at = None
        sla.save(update_fields=["total_paused_seconds", "resolution_due_at", "paused_at", "updated_at"])

        ticket.resolution_deadline = sla.resolution_due_at
        ticket.save(update_fields=["resolution_deadline", "updated_at"])


@transaction.atomic
def mark_sla_resolved(*, ticket: Ticket, resolved_at: datetime | None = None) -> None:
    now = resolved_at or timezone.now()
    sla = getattr(ticket, "sla", None)
    if sla:
        if sla.paused_at is not None:
            resume_sla(ticket=ticket)
            sla.refresh_from_db()
        sla.resolved_at = now
        if now > sla.resolution_due_at:
            sla.resolution_breached = True
        sla.save(update_fields=["resolved_at", "resolution_breached", "updated_at"])


def _get_escalation_recipients(ticket: Ticket) -> list[User]:
    recipients = list(User.objects.filter(role=User.Role.ADMIN, is_active=True))
    if ticket.department and ticket.department.manager and ticket.department.manager.is_active:
        recipients.append(ticket.department.manager)
    if ticket.assigned_engineer and ticket.assigned_engineer.is_active:
        recipients.append(ticket.assigned_engineer)
    return recipients


@transaction.atomic
def create_manual_escalation(
    *,
    ticket: Ticket,
    escalated_by: User,
    reason: str,
    escalated_to: User | None = None,
    request=None,
) -> Escalation:
    target = escalated_to or (ticket.department.manager if ticket.department else None)
    sla = getattr(ticket, "sla", None)

    escalation = Escalation.objects.create(
        ticket=ticket,
        ticket_sla=sla,
        escalation_type=Escalation.EscalationType.MANUAL,
        escalated_from=escalated_by,
        escalated_to=target,
        reason=reason,
    )
    recipients = _get_escalation_recipients(ticket)
    if target:
        recipients.append(target)

    notify_users(
        recipients=recipients,
        event_type=Notification.EventType.ESCALATED,
        title=f"Ticket {ticket.ticket_number} Escalated",
        message=f"{escalated_by.full_name} escalated {ticket.ticket_number}: {reason}",
        ticket=ticket,
        exclude_user_id=escalated_by.id,
    )
    record_audit_event(
        action="TICKET_ESCALATED",
        resource_type="Ticket",
        resource_id=ticket.id,
        actor=escalated_by,
        request=request,
        metadata={"ticket_number": ticket.ticket_number, "reason": reason},
    )
    return escalation


@transaction.atomic
def acknowledge_escalation(*, escalation: Escalation, actor: User) -> Escalation:
    if escalation.is_acknowledged:
        raise ValidationError("This escalation has already been acknowledged.")
    escalation.is_acknowledged = True
    escalation.acknowledged_by = actor
    escalation.acknowledged_at = timezone.now()
    escalation.save(update_fields=["is_acknowledged", "acknowledged_by", "acknowledged_at"])
    return escalation


def run_sla_deadline_sweep() -> dict:
    """
    Periodic Celery Beat job checking active tickets for approaching SLA warnings
    and response/resolution breaches without creating duplicate Escalation events.
    """
    now = timezone.now()
    active_statuses = [
        Ticket.Status.OPEN,
        Ticket.Status.ASSIGNED,
        Ticket.Status.IN_PROGRESS,
        Ticket.Status.REOPENED,
    ]
    active_slas = (
        TicketSLA.objects.select_related(
            "ticket",
            "ticket__department",
            "ticket__department__manager",
            "ticket__assigned_engineer",
            "policy",
        )
        .filter(ticket__status__in=active_statuses, paused_at__isnull=True)
    )

    warnings_sent = 0
    breaches_created = 0

    for sla in active_slas:
        ticket = sla.ticket
        recipients = _get_escalation_recipients(ticket)

        # 1. Warning threshold check
        if sla.warning_sent_at is None and sla.resolved_at is None:
            total_window = (sla.resolution_due_at - ticket.created_at).total_seconds()
            elapsed = (now - ticket.created_at).total_seconds()
            if total_window > 0 and (elapsed / total_window) * 100 >= sla.policy.escalation_threshold_pct:
                if now < sla.resolution_due_at:
                    sla.warning_sent_at = now
                    sla.save(update_fields=["warning_sent_at", "updated_at"])
                    notify_users(
                        recipients=recipients,
                        event_type=Notification.EventType.SLA_WARNING,
                        title=f"SLA Warning: {ticket.ticket_number}",
                        message=(
                            f"Ticket {ticket.ticket_number} ({ticket.priority}) is approaching its "
                            f"resolution deadline at {sla.resolution_due_at.isoformat()}."
                        ),
                        ticket=ticket,
                    )
                    warnings_sent += 1

        # 2. First response breach check
        if sla.first_response_at is None and now > sla.response_due_at and not sla.response_breached:
            dedup = f"{sla.id}:RESPONSE_BREACH"
            with transaction.atomic():
                sla.response_breached = True
                sla.save(update_fields=["response_breached", "updated_at"])
                try:
                    Escalation.objects.create(
                        ticket=ticket,
                        ticket_sla=sla,
                        escalation_type=Escalation.EscalationType.RESPONSE_BREACH,
                        dedup_key=dedup,
                        escalated_to=ticket.department.manager if ticket.department else None,
                        reason="First response SLA deadline exceeded.",
                    )
                    breaches_created += 1
                    notify_users(
                        recipients=recipients,
                        event_type=Notification.EventType.SLA_BREACHED,
                        title=f"Response SLA Breached: {ticket.ticket_number}",
                        message=f"Ticket {ticket.ticket_number} missed its first response SLA target.",
                        ticket=ticket,
                    )
                except IntegrityError:
                    pass

        # 3. Resolution breach check
        if sla.resolved_at is None and now > sla.resolution_due_at and not sla.resolution_breached:
            dedup = f"{sla.id}:RESOLUTION_BREACH"
            with transaction.atomic():
                sla.resolution_breached = True
                sla.breach_notified_at = now
                sla.save(update_fields=["resolution_breached", "breach_notified_at", "updated_at"])
                try:
                    Escalation.objects.create(
                        ticket=ticket,
                        ticket_sla=sla,
                        escalation_type=Escalation.EscalationType.RESOLUTION_BREACH,
                        dedup_key=dedup,
                        escalated_to=ticket.department.manager if ticket.department else None,
                        reason="Resolution SLA deadline exceeded.",
                    )
                    breaches_created += 1
                    notify_users(
                        recipients=recipients,
                        event_type=Notification.EventType.SLA_BREACHED,
                        title=f"Resolution SLA Breached: {ticket.ticket_number}",
                        message=f"Ticket {ticket.ticket_number} has exceeded its resolution SLA deadline.",
                        ticket=ticket,
                    )
                except IntegrityError:
                    pass

    logger.info("SLA sweep completed: warnings=%s breaches=%s", warnings_sent, breaches_created)
    return {"warnings_sent": warnings_sent, "breaches_created": breaches_created}
