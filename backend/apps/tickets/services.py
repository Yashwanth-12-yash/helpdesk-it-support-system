
import logging

from django.db import transaction
from django.utils import timezone
from rest_framework.exceptions import NotFound, PermissionDenied, ValidationError

from apps.accounts.models import User
from apps.audit.services import record_audit_event
from apps.notifications.models import Notification
from apps.notifications.services import notify_users
from apps.sla.services import (
    initialize_ticket_sla,
    mark_sla_resolved,
    pause_sla,
    recalculate_ticket_sla_for_priority,
    record_first_response,
    resume_sla,
)
from .models import Ticket, TicketHistory, TicketSequence

logger = logging.getLogger("apps.tickets")

ALLOWED_STATUS_TRANSITIONS = {
    Ticket.Status.OPEN: {
        Ticket.Status.ASSIGNED,
        Ticket.Status.IN_PROGRESS,
        Ticket.Status.CLOSED,
    },
    Ticket.Status.ASSIGNED: {
        Ticket.Status.OPEN,
        Ticket.Status.IN_PROGRESS,
        Ticket.Status.ON_HOLD,
        Ticket.Status.RESOLVED,
        Ticket.Status.CLOSED,
    },
    Ticket.Status.IN_PROGRESS: {
        Ticket.Status.ASSIGNED,
        Ticket.Status.ON_HOLD,
        Ticket.Status.RESOLVED,
    },
    Ticket.Status.ON_HOLD: {
        Ticket.Status.IN_PROGRESS,
        Ticket.Status.RESOLVED,
    },
    Ticket.Status.RESOLVED: {
        Ticket.Status.CLOSED,
        Ticket.Status.REOPENED,
    },
    Ticket.Status.CLOSED: {
        Ticket.Status.REOPENED,
    },
    Ticket.Status.REOPENED: {
        Ticket.Status.ASSIGNED,
        Ticket.Status.IN_PROGRESS,
        Ticket.Status.RESOLVED,
    },
}


def generate_ticket_number() -> str:
    """Generate a race-free HD-YYYY-NNNNN ticket number."""
    year = timezone.now().year

    seq, _ = TicketSequence.objects.select_for_update().get_or_create(
        year=year,
        defaults={"last_number": 0},
    )

    seq.last_number += 1
    seq.save(update_fields=["last_number"])

    return f"HD-{year}-{seq.last_number:05d}"


def _log_history(
    *,
    ticket: Ticket,
    changed_by: User | None,
    action_type: str,
    field_name: str = "",
    old_value: str = "",
    new_value: str = "",
    note: str = "",
) -> None:
    TicketHistory.objects.create(
        ticket=ticket,
        changed_by=changed_by,
        action_type=action_type,
        field_name=field_name,
        old_value=str(old_value),
        new_value=str(new_value),
        note=note,
    )


def _validate_assignment_actor(*, ticket: Ticket, actor: User) -> None:
    """Validate which users may perform ticket assignment."""
    if not actor.is_active:
        raise PermissionDenied("Inactive users cannot assign tickets.")

    if actor.role == User.Role.ADMIN:
        return

    if actor.role == User.Role.MANAGER:
        department = ticket.department

        if not (
            department.manager_id == actor.id
            or department.id == actor.department_id
        ):
            raise PermissionDenied(
                "Managers can only assign tickets in their own department."
            )
        return

    if actor.role == User.Role.ENGINEER:
        return

    raise PermissionDenied(
        "You do not have permission to assign tickets."
    )


def _validate_assigned_engineer(
    *,
    ticket: Ticket,
    assigned_engineer: User,
    actor: User,
) -> None:
    """Validate the engineer receiving the ticket."""
    if not assigned_engineer.is_active:
        raise ValidationError({
            "assigned_engineer": "Cannot assign a ticket to an inactive user."
        })

    if assigned_engineer.role not in {
        User.Role.ENGINEER,
        User.Role.MANAGER,
        User.Role.ADMIN,
    }:
        raise ValidationError({
            "assigned_engineer": (
                "Tickets can only be assigned to Engineers, Managers, or Admins."
            )
        })

    # The assignee must belong to the ticket's department.
    if assigned_engineer.department_id != ticket.department_id:
        raise ValidationError({
            "assigned_engineer": (
                "The assigned user must belong to the ticket's department."
            )
        })

    # Engineers may only accept tickets for themselves.
    if actor.role == User.Role.ENGINEER:
        if assigned_engineer.id != actor.id:
            raise PermissionDenied(
                "Engineers can only accept tickets for themselves."
            )

        # An engineer must belong to the ticket's department or its team.
        is_team_member = (
            ticket.support_team_id is not None
            and ticket.support_team.memberships.filter(
                user_id=actor.id
            ).exists()
        )

        if (
            actor.department_id != ticket.department_id
            and not is_team_member
        ):
            raise PermissionDenied(
                "You can only accept tickets belonging to your department "
                "or your support team."
            )


def _validate_assignment_team(
    *,
    ticket: Ticket,
    support_team,
) -> None:
    """Ensure the support team belongs to the ticket's department."""
    if support_team is None:
        return

    if not support_team.is_active:
        raise ValidationError({
            "support_team": "Cannot assign a ticket to an inactive support team."
        })

    if support_team.department_id != ticket.department_id:
        raise ValidationError({
            "support_team": (
                "The support team must belong to the ticket's department."
            )
        })


@transaction.atomic
def create_ticket(
    *,
    created_by: User,
    request=None,
    **validated_data,
) -> Ticket:
    ticket_number = generate_ticket_number()

    ticket = Ticket.objects.create(
        ticket_number=ticket_number,
        created_by=created_by,
        status=Ticket.Status.OPEN,
        **validated_data,
    )

    initialize_ticket_sla(ticket=ticket)

    _log_history(
        ticket=ticket,
        changed_by=created_by,
        action_type="CREATED",
        new_value=ticket.status,
        note=(
            f"Ticket {ticket.ticket_number} created "
            f"with priority {ticket.priority}."
        ),
    )

    recipients = list(
        User.objects.filter(
            role=User.Role.ADMIN,
            is_active=True,
        )
    )

    if ticket.department and ticket.department.manager:
        recipients.append(ticket.department.manager)

    notify_users(
        recipients=recipients,
        event_type=Notification.EventType.TICKET_CREATED,
        title=f"New Ticket {ticket.ticket_number}: {ticket.title}",
        message=(
            f"{created_by.full_name} reported a {ticket.priority} "
            f"ticket in {ticket.department.name}."
        ),
        ticket=ticket,
        exclude_user_id=created_by.id,
    )

    record_audit_event(
        action="TICKET_CREATED",
        resource_type="Ticket",
        resource_id=ticket.id,
        actor=created_by,
        request=request,
        metadata={
            "ticket_number": ticket.ticket_number,
            "priority": ticket.priority,
        },
    )

    logger.info(
        "Ticket %s created by %s",
        ticket.ticket_number,
        created_by.email,
    )

    return ticket


@transaction.atomic
def update_ticket(
    *,
    ticket: Ticket,
    updated_by: User,
    request=None,
    **validated_data,
) -> Ticket:
    if updated_by.role == User.Role.EMPLOYEE:
        if ticket.status not in {
            Ticket.Status.OPEN,
            Ticket.Status.REOPENED,
        }:
            raise ValidationError(
                "Employees can only edit tickets that are OPEN or REOPENED."
            )

        disallowed = set(validated_data.keys()) - {
            "title",
            "description",
            "category",
        }

        if disallowed:
            raise PermissionDenied(
                "Employees cannot modify priority, department, or assignment fields."
            )

    priority_changed = (
        "priority" in validated_data
        and validated_data["priority"] != ticket.priority
    )

    for field, new_val in validated_data.items():
        old_val = getattr(ticket, field)

        if old_val != new_val:
            setattr(ticket, field, new_val)

            _log_history(
                ticket=ticket,
                changed_by=updated_by,
                action_type="FIELD_UPDATED",
                field_name=field,
                old_value=str(old_val or ""),
                new_value=str(new_val or ""),
            )

    ticket.save()

    if (
        priority_changed
        and ticket.status not in {
            Ticket.Status.RESOLVED,
            Ticket.Status.CLOSED,
        }
    ):
        recalculate_ticket_sla_for_priority(ticket=ticket)

        record_audit_event(
            action="TICKET_PRIORITY_CHANGED",
            resource_type="Ticket",
            resource_id=ticket.id,
            actor=updated_by,
            request=request,
            metadata={
                "ticket_number": ticket.ticket_number,
                "priority": ticket.priority,
            },
        )

    return ticket


@transaction.atomic
def assign_ticket(
    *,
    ticket: Ticket,
    actor: User,
    assigned_engineer: User | None = None,
    support_team=None,
    note: str = "",
    request=None,
) -> Ticket:
    if ticket.status in {
        Ticket.Status.RESOLVED,
        Ticket.Status.CLOSED,
    }:
        raise ValidationError(
            "Cannot assign a ticket that is already resolved or closed."
        )

    _validate_assignment_actor(
        ticket=ticket,
        actor=actor,
    )

    if actor.role == User.Role.ENGINEER:
        if assigned_engineer and assigned_engineer.id != actor.id:
            raise PermissionDenied(
                "Engineers can only accept tickets for themselves."
            )

        assigned_engineer = actor

    if assigned_engineer is not None:
        _validate_assigned_engineer(
            ticket=ticket,
            assigned_engineer=assigned_engineer,
            actor=actor,
        )

    if support_team is not None:
        _validate_assignment_team(
            ticket=ticket,
            support_team=support_team,
        )

    old_engineer = ticket.assigned_engineer

    is_reassignment = (
        old_engineer is not None
        and assigned_engineer is not None
        and old_engineer.id != assigned_engineer.id
    )

    if assigned_engineer is not None:
        ticket.assigned_engineer = assigned_engineer

    if support_team is not None:
        ticket.support_team = support_team

    if (
        ticket.status in {
            Ticket.Status.OPEN,
            Ticket.Status.REOPENED,
        }
        and ticket.assigned_engineer is not None
    ):
        old_status = ticket.status
        ticket.status = Ticket.Status.ASSIGNED

        _log_history(
            ticket=ticket,
            changed_by=actor,
            action_type="STATUS_CHANGED",
            field_name="status",
            old_value=old_status,
            new_value=ticket.status,
        )

    ticket.save()

    _log_history(
        ticket=ticket,
        changed_by=actor,
        action_type="REASSIGNED" if is_reassignment else "ASSIGNED",
        field_name="assigned_engineer",
        old_value=old_engineer.email if old_engineer else "",
        new_value=(
            ticket.assigned_engineer.email
            if ticket.assigned_engineer
            else ""
        ),
        note=note,
    )

    if ticket.assigned_engineer:
        event_type = (
            Notification.EventType.TICKET_REASSIGNED
            if is_reassignment
            else Notification.EventType.TICKET_ASSIGNED
        )

        notify_users(
            recipients=[
                ticket.assigned_engineer,
                ticket.created_by,
            ],
            event_type=event_type,
            title=(
                f"Ticket {ticket.ticket_number} "
                f"{'Reassigned' if is_reassignment else 'Assigned'}"
            ),
            message=(
                f"{ticket.ticket_number} is now assigned to "
                f"{ticket.assigned_engineer.full_name}."
            ),
            ticket=ticket,
            exclude_user_id=actor.id,
        )

    record_audit_event(
        action="TICKET_ASSIGNED",
        resource_type="Ticket",
        resource_id=ticket.id,
        actor=actor,
        request=request,
        metadata={
            "ticket_number": ticket.ticket_number,
            "assigned_engineer_id": ticket.assigned_engineer_id,
            "support_team_id": ticket.support_team_id,
        },
    )

    return ticket


@transaction.atomic
def change_ticket_status(
    *,
    ticket: Ticket,
    new_status: str,
    actor: User,
    note: str = "",
    request=None,
) -> Ticket:
    old_status = ticket.status

    if old_status == new_status:
        return ticket

    allowed_targets = ALLOWED_STATUS_TRANSITIONS.get(
        old_status,
        set(),
    )

    if new_status not in allowed_targets:
        raise ValidationError({
            "status": (
                f"Invalid status transition from '{old_status}' "
                f"to '{new_status}'."
            )
        })

    if (
        new_status == Ticket.Status.RESOLVED
        and not note
        and not ticket.resolution_notes
    ):
        raise ValidationError({
            "note": "Resolution notes are required when resolving a ticket."
        })

    if (
        old_status == Ticket.Status.ON_HOLD
        and new_status != Ticket.Status.ON_HOLD
    ):
        resume_sla(ticket=ticket)

    ticket.status = new_status

    if new_status == Ticket.Status.ON_HOLD:
        pause_sla(ticket=ticket)

    elif new_status == Ticket.Status.IN_PROGRESS:
        if actor.role in {
            User.Role.ENGINEER,
            User.Role.MANAGER,
            User.Role.ADMIN,
        }:
            record_first_response(ticket=ticket)

    elif new_status == Ticket.Status.RESOLVED:
        ticket.resolved_at = timezone.now()

        if note:
            ticket.resolution_notes = note

        record_first_response(ticket=ticket)

        mark_sla_resolved(
            ticket=ticket,
            resolved_at=ticket.resolved_at,
        )

    elif new_status == Ticket.Status.CLOSED:
        ticket.closed_at = timezone.now()

        if not ticket.resolved_at:
            ticket.resolved_at = ticket.closed_at

            mark_sla_resolved(
                ticket=ticket,
                resolved_at=ticket.resolved_at,
            )

    elif new_status == Ticket.Status.REOPENED:
        ticket.reopen_count += 1
        ticket.resolved_at = None
        ticket.closed_at = None

    ticket.save()

    _log_history(
        ticket=ticket,
        changed_by=actor,
        action_type="STATUS_CHANGED",
        field_name="status",
        old_value=old_status,
        new_value=new_status,
        note=note,
    )

    event_type = Notification.EventType.STATUS_CHANGED

    if new_status == Ticket.Status.RESOLVED:
        event_type = Notification.EventType.TICKET_RESOLVED

    elif new_status == Ticket.Status.REOPENED:
        event_type = Notification.EventType.TICKET_REOPENED

    recipients = [ticket.created_by]

    if ticket.assigned_engineer:
        recipients.append(ticket.assigned_engineer)

    if ticket.department and ticket.department.manager:
        recipients.append(ticket.department.manager)

    notify_users(
        recipients=recipients,
        event_type=event_type,
        title=f"Ticket {ticket.ticket_number} status: {new_status}",
        message=(
            f"Ticket {ticket.ticket_number} moved from "
            f"{old_status} to {new_status}."
        ),
        ticket=ticket,
        exclude_user_id=actor.id,
    )

    record_audit_event(
        action="TICKET_STATUS_CHANGED",
        resource_type="Ticket",
        resource_id=ticket.id,
        actor=actor,
        request=request,
        metadata={
            "ticket_number": ticket.ticket_number,
            "old_status": old_status,
            "new_status": new_status,
        },
    )

    return ticket


@transaction.atomic
def resolve_ticket(
    *,
    ticket: Ticket,
    actor: User,
    resolution_notes: str,
    request=None,
) -> Ticket:
    return change_ticket_status(
        ticket=ticket,
        new_status=Ticket.Status.RESOLVED,
        actor=actor,
        note=resolution_notes,
        request=request,
    )


@transaction.atomic
def reopen_ticket(
    *,
    ticket: Ticket,
    actor: User,
    reason: str,
    request=None,
) -> Ticket:
    if ticket.status not in {
        Ticket.Status.RESOLVED,
        Ticket.Status.CLOSED,
    }:
        raise ValidationError(
            "Only RESOLVED or CLOSED tickets can be reopened."
        )

    return change_ticket_status(
        ticket=ticket,
        new_status=Ticket.Status.REOPENED,
        actor=actor,
        note=reason,
        request=request,
    )
