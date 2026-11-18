import os
from celery import Celery
from celery.schedules import crontab

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.development")

app = Celery("helpdesk")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()

app.conf.beat_schedule = {
    "check-sla-deadlines-every-minute": {
        "task": "apps.sla.tasks.check_sla_deadlines",
        "schedule": crontab(minute="*"),
    },
}
