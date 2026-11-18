from celery import shared_task

from .services import run_sla_deadline_sweep


@shared_task(name="apps.sla.tasks.check_sla_deadlines")
def check_sla_deadlines():
    """Scheduled Celery Beat task scanning active tickets for SLA warnings and breaches."""
    return run_sla_deadline_sweep()
