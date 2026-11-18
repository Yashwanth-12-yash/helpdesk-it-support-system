from rest_framework import serializers

from apps.accounts.models import User
from apps.accounts.serializers import UserSummarySerializer
from .models import Department


class DepartmentSummarySerializer(serializers.ModelSerializer):
    class Meta:
        model = Department
        fields = ("id", "name", "code", "is_active")
        read_only_fields = fields


class DepartmentSerializer(serializers.ModelSerializer):
    manager_detail = UserSummarySerializer(source="manager", read_only=True)
    team_count = serializers.IntegerField(read_only=True, default=0)

    class Meta:
        model = Department
        fields = (
            "id",
            "name",
            "code",
            "description",
            "manager",
            "manager_detail",
            "team_count",
            "is_active",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("id", "created_at", "updated_at")


class DepartmentWriteSerializer(serializers.ModelSerializer):
    manager = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(), required=False, allow_null=True
    )

    class Meta:
        model = Department
        fields = ("name", "code", "description", "manager", "is_active")
