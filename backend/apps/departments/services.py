import logging
from django.db import transaction
from rest_framework.exceptions import ValidationError

from apps.accounts.models import User
from .models import Department

logger = logging.getLogger("apps.departments")


def _validate_manager(manager: User | None) -> None:
    if manager is None:
        return
    if not manager.is_active:
        raise ValidationError({"manager": "Selected manager account is inactive."})
    if manager.role not in {User.Role.MANAGER, User.Role.ADMIN}:
        raise ValidationError({"manager": "Department manager must have the MANAGER or ADMIN role."})


@transaction.atomic
def create_department(*, created_by: User, **validated_data) -> Department:
    manager = validated_data.get("manager")
    _validate_manager(manager)

    validated_data["code"] = validated_data["code"].strip().upper()
    validated_data["name"] = validated_data["name"].strip()

    department = Department.objects.create(**validated_data)
    logger.info("Department %s created by %s", department.code, created_by.email)
    return department


@transaction.atomic
def update_department(*, department: Department, updated_by: User, **validated_data) -> Department:
    if "manager" in validated_data:
        _validate_manager(validated_data["manager"])

    if "code" in validated_data:
        validated_data["code"] = validated_data["code"].strip().upper()
    if "name" in validated_data:
        validated_data["name"] = validated_data["name"].strip()

    for field, value in validated_data.items():
        setattr(department, field, value)

    department.save()
    logger.info("Department %s updated by %s", department.code, updated_by.email)
    return department
