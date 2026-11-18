import logging
from django.conf import settings
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import send_mail
from django.db import transaction
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from rest_framework.exceptions import ValidationError

from .models import User

logger = logging.getLogger("apps.accounts")


@transaction.atomic
def create_user(*, created_by: User | None = None, **validated_data) -> User:
    password = validated_data.pop("password")
    email = validated_data.pop("email").strip().lower()

    if User.objects.filter(email__iexact=email).exists():
        raise ValidationError({"email": "A user with this email already exists."})

    role = validated_data.get("role", User.Role.EMPLOYEE)
    is_staff = role == User.Role.ADMIN
    user = User.objects.create_user(
        email=email,
        password=password,
        is_staff=is_staff,
        **validated_data,
    )
    logger.info("User %s created with role %s by %s", user.email, user.role, getattr(created_by, "email", "system"))
    return user


@transaction.atomic
def update_user(*, user: User, updated_by: User, **validated_data) -> User:
    if user.pk == updated_by.pk:
        if "role" in validated_data and validated_data["role"] != user.role:
            raise ValidationError({"role": "Administrators cannot change their own role."})
        if "is_active" in validated_data and not validated_data["is_active"]:
            raise ValidationError({"is_active": "Administrators cannot deactivate their own account."})

    for field, value in validated_data.items():
        setattr(user, field, value)

    if "role" in validated_data:
        user.is_staff = user.role == User.Role.ADMIN

    user.save()
    logger.info("User %s updated by %s", user.email, updated_by.email)
    return user


@transaction.atomic
def toggle_user_active(*, target_user: User, actor: User) -> User:
    if target_user.pk == actor.pk:
        raise ValidationError("You cannot deactivate your own account.")

    target_user.is_active = not target_user.is_active
    target_user.save(update_fields=["is_active", "updated_at"])
    logger.info(
        "User %s active status set to %s by %s",
        target_user.email,
        target_user.is_active,
        actor.email,
    )
    return target_user


@transaction.atomic
def update_own_profile(*, user: User, **validated_data) -> User:
    allowed_fields = {"first_name", "last_name", "job_title", "phone"}
    for field, value in validated_data.items():
        if field in allowed_fields:
            setattr(user, field, value)
    user.save()
    return user


@transaction.atomic
def change_user_password(*, user: User, old_password: str, new_password: str) -> None:
    if not user.check_password(old_password):
        raise ValidationError({"old_password": "Current password is incorrect."})

    user.set_password(new_password)
    user.save(update_fields=["password", "updated_at"])
    logger.info("Password changed for user %s", user.email)


def request_password_reset(*, email: str) -> None:
    """Send password reset link if an active user exists; silently succeed otherwise."""
    user = User.objects.filter(email__iexact=email.strip(), is_active=True).first()
    if not user:
        return

    uid = urlsafe_base64_encode(force_bytes(user.pk))
    token = default_token_generator.make_token(user)
    reset_url = f"{settings.FRONTEND_URL.rstrip('/')}/reset-password?uid={uid}&token={token}"

    send_mail(
        subject="HelpDesk Password Reset Request",
        message=(
            f"Hello {user.first_name},\n\n"
            f"A password reset was requested for your HelpDesk account.\n"
            f"Use the link below to set a new password:\n{reset_url}\n\n"
            f"If you did not request this, please ignore this email."
        ),
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user.email],
        fail_silently=True,
    )
    logger.info("Password reset email dispatched to %s", user.email)


@transaction.atomic
def confirm_password_reset(*, uid: str, token: str, new_password: str) -> None:
    try:
        user_id = force_str(urlsafe_base64_decode(uid))
        user = User.objects.get(pk=user_id, is_active=True)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        raise ValidationError({"token": "Invalid or expired password reset link."})

    if not default_token_generator.check_token(user, token):
        raise ValidationError({"token": "Invalid or expired password reset token."})

    user.set_password(new_password)
    user.save(update_fields=["password", "updated_at"])
    logger.info("Password reset completed for user %s", user.email)
