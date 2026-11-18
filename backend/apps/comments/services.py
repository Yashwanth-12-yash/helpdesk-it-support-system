import os
from django.db import transaction
from rest_framework.exceptions import PermissionDenied

from apps.accounts.models import User
from apps.notifications.models import Notification
from apps.notifications.services import notify_users
from apps.sla.services import record_first_response
from apps.tickets.models import Ticket, TicketHistory
from common.utilities import validate_uploaded_file
from .models import TicketAttachment, TicketComment


@transaction.atomic
def add_ticket_comment(*, ticket: Ticket, author: User, body: str, is_internal: bool = False) -> TicketComment:
    if is_internal and author.role == User.Role.EMPLOYEE:
        raise PermissionDenied("Employees cannot create internal notes.")

    comment = TicketComment.objects.create(
        ticket=ticket,
        author=author,
        body=body,
        is_internal=is_internal,
    )

    if not is_internal and author.role in {User.Role.ENGINEER, User.Role.MANAGER, User.Role.ADMIN}:
        record_first_response(ticket=ticket)

    TicketHistory.objects.create(
        ticket=ticket,
        changed_by=author,
        action_type="INTERNAL_NOTE_ADDED" if is_internal else "COMMENT_ADDED",
        note=body[:200],
    )

    recipients = []
    if is_internal:
        if ticket.assigned_engineer:
            recipients.append(ticket.assigned_engineer)
        if ticket.department and ticket.department.manager:
            recipients.append(ticket.department.manager)
    else:
        recipients.append(ticket.created_by)
        if ticket.assigned_engineer:
            recipients.append(ticket.assigned_engineer)

    notify_users(
        recipients=recipients,
        event_type=Notification.EventType.COMMENT_ADDED,
        title=f"New {'Internal Note' if is_internal else 'Comment'} on {ticket.ticket_number}",
        message=f"{author.full_name} posted on {ticket.ticket_number}: {body[:140]}",
        ticket=ticket,
        exclude_user_id=author.id,
    )
    return comment


@transaction.atomic
def add_ticket_attachment(
    *,
    ticket: Ticket,
    uploaded_by: User,
    uploaded_file,
    comment: TicketComment | None = None,
) -> TicketAttachment:
    validate_uploaded_file(uploaded_file)

    safe_original_name = os.path.basename(uploaded_file.name)[:255]
    attachment = TicketAttachment.objects.create(
        ticket=ticket,
        comment=comment,
        uploaded_by=uploaded_by,
        file=uploaded_file,
        original_filename=safe_original_name,
        content_type=getattr(uploaded_file, "content_type", "") or "application/octet-stream",
        file_size=uploaded_file.size,
    )
    TicketHistory.objects.create(
        ticket=ticket,
        changed_by=uploaded_by,
        action_type="ATTACHMENT_UPLOADED",
        new_value=safe_original_name,
    )
    return attachment
