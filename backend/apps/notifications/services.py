import logging
from django.db import transaction
from django.utils import timezone

from apps.accounts.models import User
from .models import Notification
from .tasks import send_notification_email_task

logger = logging.getLogger("apps.notifications")


def _dispatch_email_async(notification_id: int) -> None:
    """Queue email task cleanly after DB transaction commits (failsafe if broker unavailable)."""
    def _enqueue():
        try:
            send_notification_email_task.delay(notification_id)
        except Exception as exc:
            logger.warning("Could not enqueue email task for notification %s: %s", notification_id, exc)

    transaction.on_commit(_enqueue)


@transaction.atomic
def create_notification(
    *,
    recipient: User,
    event_type: str,
    title: str,
    message: str,
    ticket=None,
    send_email: bool = True,
) -> Notification:
    notification = Notification.objects.create(
        recipient=recipient,
        ticket=ticket,
        event_type=event_type,
        title=title[:255],
        message=message,
    )
    if send_email:
        _dispatch_email_async(notification.id)
    return notification


def notify_users(
    *,
    recipients: list[User],
    event_type: str,
    title: str,
    message: str,
    ticket=None,
    exclude_user_id: int | None = None,
    send_email: bool = True,
) -> None:
    seen_ids = set()
    for user in recipients:
        if not user or not user.is_active:
            continue
        if exclude_user_id and user.id == exclude_user_id:
            continue
        if user.id in seen_ids:
            continue
        seen_ids.add(user.id)
        create_notification(
            recipient=user,
            event_type=event_type,
            title=title,
            message=message,
            ticket=ticket,
            send_email=send_email,
        )


@transaction.atomic
def mark_notification_read(*, notification: Notification) -> Notification:
    if not notification.is_read:
        notification.is_read = True
        notification.read_at = timezone.now()
        notification.save(update_fields=["is_read", "read_at"])
    return notification


@transaction.atomic
def mark_all_notifications_read(*, user: User) -> int:
    return Notification.objects.filter(recipient=user, is_read=False).update(
        is_read=True,
        read_at=timezone.now(),
    )
