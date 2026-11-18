import logging
from celery import shared_task
from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils import timezone

logger = logging.getLogger("apps.notifications")


@shared_task(bind=True, max_retries=3, default_retry_delay=30)
def send_notification_email_task(self, notification_id: int):
    """Send email for a persisted Notification record with automatic retry."""
    from .models import Notification

    try:
        notification = Notification.objects.select_related("recipient", "ticket").get(pk=notification_id)
    except Notification.DoesNotExist:
        logger.warning("Notification %s no longer exists; skipping email.", notification_id)
        return

    recipient = notification.recipient
    if not recipient.email or not recipient.is_active:
        return

    ticket_number = notification.ticket.ticket_number if notification.ticket else ""
    ticket_url = (
        f"{settings.FRONTEND_URL.rstrip('/')}/tickets/{notification.ticket_id}"
        if notification.ticket_id
        else settings.FRONTEND_URL
    )

    context = {
        "recipient_name": recipient.first_name or recipient.email,
        "title": notification.title,
        "message": notification.message,
        "ticket_number": ticket_number,
        "ticket_url": ticket_url,
    }

    try:
        html_body = render_to_string("emails/ticket_notification.html", context)
        email = EmailMultiAlternatives(
            subject=f"[HelpDesk] {notification.title}",
            body=notification.message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[recipient.email],
        )
        email.attach_alternative(html_body, "text/html")
        email.send(fail_silently=False)

        notification.email_sent = True
        notification.email_sent_at = timezone.now()
        notification.save(update_fields=["email_sent", "email_sent_at"])
    except Exception as exc:
        logger.warning("Email send failed for notification %s: %s", notification_id, exc)
        raise self.retry(exc=exc)
