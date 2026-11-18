
from rest_framework import serializers

from apps.accounts.models import User
from apps.accounts.serializers import UserSummarySerializer
from apps.departments.models import Department
from apps.departments.serializers import DepartmentSummarySerializer
from apps.sla.serializers import TicketSLASerializer
from apps.teams.models import SupportTeam
from apps.teams.serializers import SupportTeamSummarySerializer
from .models import Ticket, TicketHistory


class TicketHistorySerializer(serializers.ModelSerializer):
    changed_by_detail = UserSummarySerializer(source="changed_by", read_only=True)

    class Meta:
        model = TicketHistory
        fields = (
            "id",
            "action_type",
            "field_name",
            "old_value",
            "new_value",
            "note",
            "changed_by",
            "changed_by_detail",
            "created_at",
        )
        read_only_fields = fields


class TicketListSerializer(serializers.ModelSerializer):
    created_by_detail = UserSummarySerializer(source="created_by", read_only=True)
    assigned_engineer_detail = UserSummarySerializer(source="assigned_engineer", read_only=True)
    department_detail = DepartmentSummarySerializer(source="department", read_only=True)
    support_team_detail = SupportTeamSummarySerializer(source="support_team", read_only=True)

    class Meta:
        model = Ticket
        fields = (
            "id",
            "ticket_number",
            "title",
            "category",
            "priority",
            "status",
            "created_by",
            "created_by_detail",
            "assigned_engineer",
            "assigned_engineer_detail",
            "department",
            "department_detail",
            "support_team",
            "support_team_detail",
            "response_deadline",
            "resolution_deadline",
            "created_at",
            "updated_at",
        )


class TicketDetailSerializer(TicketListSerializer):
    sla = TicketSLASerializer(read_only=True)

    class Meta(TicketListSerializer.Meta):
        fields = TicketListSerializer.Meta.fields + (
            "description",
            "first_responded_at",
            "resolved_at",
            "closed_at",
            "resolution_notes",
            "reopen_count",
            "sla",
        )


class TicketCreateSerializer(serializers.ModelSerializer):
    department = serializers.PrimaryKeyRelatedField(
        queryset=Department.objects.filter(is_active=True)
    )
    support_team = serializers.PrimaryKeyRelatedField(
        queryset=SupportTeam.objects.filter(is_active=True),
        required=False,
        allow_null=True,
    )

    class Meta:
        model = Ticket
        fields = (
            "title",
            "description",
            "category",
            "priority",
            "department",
            "support_team",
        )

    def validate(self, attrs):
        department = attrs["department"]
        support_team = attrs.get("support_team")

        if support_team and support_team.department_id != department.id:
            raise serializers.ValidationError({
                "support_team": (
                    "The selected support team must belong to the "
                    "selected ticket department."
                )
            })

        return attrs


class TicketUpdateSerializer(serializers.ModelSerializer):
    department = serializers.PrimaryKeyRelatedField(
        queryset=Department.objects.filter(is_active=True),
        required=False,
    )
    support_team = serializers.PrimaryKeyRelatedField(
        queryset=SupportTeam.objects.filter(is_active=True),
        required=False,
        allow_null=True,
    )

    class Meta:
        model = Ticket
        fields = (
            "title",
            "description",
            "category",
            "priority",
            "department",
            "support_team",
        )

    def validate(self, attrs):
        department = attrs.get("department", self.instance.department)
        support_team = attrs.get("support_team", self.instance.support_team)

        if support_team and support_team.department_id != department.id:
            raise serializers.ValidationError({
                "support_team": (
                    "The selected support team must belong to the "
                    "selected ticket department."
                )
            })

        return attrs


class TicketAssignSerializer(serializers.Serializer):
    assigned_engineer = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.filter(is_active=True),
        required=False,
        allow_null=True,
    )
    support_team = serializers.PrimaryKeyRelatedField(
        queryset=SupportTeam.objects.filter(is_active=True),
        required=False,
        allow_null=True,
    )
    note = serializers.CharField(required=False, allow_blank=True, default="")


class TicketStatusChangeSerializer(serializers.Serializer):
    status = serializers.ChoiceField(choices=Ticket.Status.choices)
    note = serializers.CharField(required=False, allow_blank=True, default="")


class TicketResolveSerializer(serializers.Serializer):
    resolution_notes = serializers.CharField(min_length=5)


class TicketReopenSerializer(serializers.Serializer):
    reason = serializers.CharField(min_length=5)
