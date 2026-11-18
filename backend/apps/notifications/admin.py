from django.contrib import admin

from .models import Notification


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ("recipient", "event_type", "title", "is_read", "email_sent", "created_at")
    list_filter = ("event_type", "is_read", "email_sent")
    search_fields = ("recipient__email", "title", "message")
