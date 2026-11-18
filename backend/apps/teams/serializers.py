from rest_framework import serializers

from apps.accounts.models import User
from apps.accounts.serializers import UserSummarySerializer
from apps.departments.models import Department
from apps.departments.serializers import DepartmentSummarySerializer
from .models import SupportTeam, TeamMembership


class TeamMembershipSerializer(serializers.ModelSerializer):
    user = UserSummarySerializer(read_only=True)

    class Meta:
        model = TeamMembership
        fields = ("id", "user", "is_primary", "joined_at")
        read_only_fields = fields


class TeamMembershipWriteSerializer(serializers.Serializer):
    user = serializers.PrimaryKeyRelatedField(queryset=User.objects.all())
    is_primary = serializers.BooleanField(default=False)


class SupportTeamSummarySerializer(serializers.ModelSerializer):
    class Meta:
        model = SupportTeam
        fields = ("id", "name", "department", "is_active")
        read_only_fields = fields


class SupportTeamSerializer(serializers.ModelSerializer):
    department_detail = DepartmentSummarySerializer(source="department", read_only=True)
    lead_detail = UserSummarySerializer(source="lead", read_only=True)
    members = TeamMembershipSerializer(source="memberships", many=True, read_only=True)

    class Meta:
        model = SupportTeam
        fields = (
            "id",
            "name",
            "department",
            "department_detail",
            "lead",
            "lead_detail",
            "description",
            "is_active",
            "members",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("id", "created_at", "updated_at")


class SupportTeamWriteSerializer(serializers.ModelSerializer):
    department = serializers.PrimaryKeyRelatedField(queryset=Department.objects.filter(is_active=True))
    lead = serializers.PrimaryKeyRelatedField(queryset=User.objects.all(), required=False, allow_null=True)

    class Meta:
        model = SupportTeam
        fields = ("name", "department", "lead", "description", "is_active")
