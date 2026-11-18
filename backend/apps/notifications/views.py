from drf_spectacular.utils import extend_schema
from rest_framework import serializers, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import Notification
from .services import mark_all_notifications_read, mark_notification_read


class NotificationSerializer(serializers.ModelSerializer):
    ticket_number = serializers.CharField(source="ticket.ticket_number", read_only=True, default=None)

    class Meta:
        model = Notification
        fields = (
            "id",
            "ticket",
            "ticket_number",
            "event_type",
            "title",
            "message",
            "is_read",
            "read_at",
            "email_sent",
            "created_at",
        )
        read_only_fields = fields


class NotificationViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = NotificationSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ["is_read", "event_type"]
    ordering_fields = ["created_at"]

    def get_queryset(self):
        return (
            Notification.objects.filter(recipient=self.request.user)
            .select_related("ticket")
            .order_by("-created_at")
        )

    @extend_schema(request=None, responses=NotificationSerializer)
    @action(detail=True, methods=["post"], url_path="read")
    def mark_read(self, request, pk=None):
        notification = self.get_object()
        updated = mark_notification_read(notification=notification)
        return Response(NotificationSerializer(updated).data)

    @extend_schema(request=None, responses={200: dict})
    @action(detail=False, methods=["post"], url_path="read-all")
    def mark_all_read(self, request):
        count = mark_all_notifications_read(user=request.user)
        return Response({"marked_read": count}, status=status.HTTP_200_OK)

    @extend_schema(responses={200: dict})
    @action(detail=False, methods=["get"], url_path="unread-count")
    def unread_count(self, request):
        count = Notification.objects.filter(recipient=request.user, is_read=False).count()
        return Response({"unread_count": count})
