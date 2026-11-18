from rest_framework import serializers

from apps.accounts.serializers import UserSummarySerializer
from .models import Escalation, SLAPolicy, TicketSLA


class SLAPolicySerializer(serializers.ModelSerializer):
    department_name = serializers.CharField(source="department.name", read_only=True, default=None)

    class Meta:
        model = SLAPolicy
        fields = (
            "id",
            "name",
            "priority",
            "department",
            "department_name",
            "first_response_minutes",
            "resolution_minutes",
            "escalation_threshold_pct",
            "business_hours_only",
            "business_start_time",
            "business_end_time",
            "working_days",
            "is_active",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("id", "created_at", "updated_at")


class TicketSLASerializer(serializers.ModelSerializer):
    policy_name = serializers.CharField(source="policy.name", read_only=True)

    class Meta:
        model = TicketSLA
        fields = (
            "id",
            "policy",
            "policy_name",
            "response_due_at",
            "resolution_due_at",
            "first_response_at",
            "resolved_at",
            "response_breached",
            "resolution_breached",
            "paused_at",
            "total_paused_seconds",
        )
        read_only_fields = fields


class EscalationSerializer(serializers.ModelSerializer):
    ticket_number = serializers.CharField(source="ticket.ticket_number", read_only=True)
    ticket_title = serializers.CharField(source="ticket.title", read_only=True)
    escalated_from_detail = UserSummarySerializer(source="escalated_from", read_only=True)
    escalated_to_detail = UserSummarySerializer(source="escalated_to", read_only=True)
    acknowledged_by_detail = UserSummarySerializer(source="acknowledged_by", read_only=True)

    class Meta:
        model = Escalation
        fields = (
            "id",
            "ticket",
            "ticket_number",
            "ticket_title",
            "escalation_type",
            "escalated_from",
            "escalated_from_detail",
            "escalated_to",
            "escalated_to_detail",
            "reason",
            "is_acknowledged",
            "acknowledged_by",
            "acknowledged_by_detail",
            "acknowledged_at",
            "created_at",
        )
        read_only_fields = fields


class ManualEscalationSerializer(serializers.Serializer):
    reason = serializers.CharField(min_length=5, max_length=1000)
    escalated_to = serializers.IntegerField(required=False, allow_null=True)
