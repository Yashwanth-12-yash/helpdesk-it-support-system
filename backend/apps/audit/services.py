from common.utilities import get_client_ip
from .models import AuditLog


def record_audit_event(
    *,
    action: str,
    resource_type: str,
    resource_id: str | int = "",
    actor=None,
    request=None,
    metadata: dict | None = None,
) -> AuditLog:
    ip_address = get_client_ip(request) if request else None
    user_agent = (request.META.get("HTTP_USER_AGENT", "")[:500]) if request else ""
    actor_email = getattr(actor, "email", "system") if actor else "system"

    return AuditLog.objects.create(
        actor=actor if getattr(actor, "is_authenticated", False) else None,
        actor_email=actor_email,
        action=action,
        resource_type=resource_type,
        resource_id=str(resource_id),
        ip_address=ip_address,
        user_agent=user_agent,
        metadata=metadata or {},
    )
