
import logging

from django.db import transaction
from rest_framework.exceptions import NotFound, ValidationError

from apps.accounts.models import User
from .models import SupportTeam, TeamMembership

logger = logging.getLogger("apps.teams")


def _validate_team_lead(lead: User | None) -> None:
    if lead is None:
        return

    if not lead.is_active:
        raise ValidationError(
            {"lead": "Selected team lead account is inactive."}
        )

    if lead.role not in {
        User.Role.ENGINEER,
        User.Role.MANAGER,
        User.Role.ADMIN,
    }:
        raise ValidationError(
            {"lead": "Team lead must be a Support Engineer, Manager, or Admin."}
        )


def _validate_team_member(member: User) -> None:
    if not member.is_active:
        raise ValidationError(
            {"user": "Cannot add an inactive user to a support team."}
        )

    if member.role not in {User.Role.ENGINEER, User.Role.MANAGER}:
        raise ValidationError(
            {"user": "Only Support Engineers or Managers can be assigned to support teams."}
        )


def _validate_manager_team_scope(
    *,
    team: SupportTeam,
    user: User,
    actor: User,
) -> None:
    """
    A Manager can manage memberships only in a department they manage.
    They can only add members belonging to that same department.
    Admins are not restricted by this department check.
    """
    if actor.role == User.Role.ADMIN:
        return

    if actor.role != User.Role.MANAGER:
        raise ValidationError(
            {"detail": "You do not have permission to manage team membership."}
        )

    if team.department.manager_id != actor.id:
        raise ValidationError(
            {"detail": "You can only manage teams in your own department."}
        )

    if user.department_id != team.department_id:
        raise ValidationError(
            {"user": "You can only add members from your own department."}
        )


@transaction.atomic
def create_support_team(*, created_by: User, **validated_data) -> SupportTeam:
    _validate_team_lead(validated_data.get("lead"))
    validated_data["name"] = validated_data["name"].strip()

    team = SupportTeam.objects.create(**validated_data)

    logger.info(
        "SupportTeam '%s' created by %s",
        team.name,
        created_by.email,
    )

    return team


@transaction.atomic
def update_support_team(
    *,
    team: SupportTeam,
    updated_by: User,
    **validated_data,
) -> SupportTeam:
    if "lead" in validated_data:
        _validate_team_lead(validated_data["lead"])

    if "name" in validated_data:
        validated_data["name"] = validated_data["name"].strip()

    for field, value in validated_data.items():
        setattr(team, field, value)

    team.save()

    logger.info(
        "SupportTeam '%s' updated by %s",
        team.name,
        updated_by.email,
    )

    return team


@transaction.atomic
def add_team_member(
    *,
    team: SupportTeam,
    user: User,
    is_primary: bool,
    actor: User,
) -> TeamMembership:
    _validate_team_member(user)

    _validate_manager_team_scope(
        team=team,
        user=user,
        actor=actor,
    )

    if is_primary:
        TeamMembership.objects.filter(
            user=user,
            is_primary=True,
        ).exclude(team=team).update(is_primary=False)

    membership, created = TeamMembership.objects.update_or_create(
        team=team,
        user=user,
        defaults={"is_primary": is_primary},
    )

    action = "added to" if created else "updated in"

    logger.info(
        "User %s %s team '%s' by %s",
        user.email,
        action,
        team.name,
        actor.email,
    )

    return membership


@transaction.atomic
def remove_team_member(
    *,
    team: SupportTeam,
    user_id: int,
    actor: User,
) -> None:
    if actor.role not in {User.Role.ADMIN, User.Role.MANAGER}:
        raise ValidationError(
            {"detail": "You do not have permission to remove team members."}
        )

    if (
        actor.role == User.Role.MANAGER
        and team.department.manager_id != actor.id
    ):
        raise ValidationError(
            {"detail": "You can only manage teams in your own department."}
        )

    membership = TeamMembership.objects.filter(
        team=team,
        user_id=user_id,
    ).first()

    if not membership:
        raise NotFound("User is not a member of this support team.")

    email = membership.user.email
    membership.delete()

    logger.info(
        "User %s removed from team '%s' by %s",
        email,
        team.name,
        actor.email,
    )
