from rest_framework import serializers

from apps.accounts.serializers import UserSummarySerializer
from .models import TicketAttachment, TicketComment


class TicketAttachmentSerializer(serializers.ModelSerializer):
    uploaded_by_detail = UserSummarySerializer(source="uploaded_by", read_only=True)
    download_url = serializers.SerializerMethodField()

    class Meta:
        model = TicketAttachment
        fields = (
            "id",
            "ticket",
            "comment",
            "original_filename",
            "content_type",
            "file_size",
            "uploaded_by",
            "uploaded_by_detail",
            "download_url",
            "created_at",
        )
        read_only_fields = fields

    def get_download_url(self, obj):
        return f"/api/v1/attachments/{obj.id}/download/"


class TicketCommentSerializer(serializers.ModelSerializer):
    author_detail = UserSummarySerializer(source="author", read_only=True)

    class Meta:
        model = TicketComment
        fields = (
            "id",
            "ticket",
            "author",
            "author_detail",
            "body",
            "is_internal",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("id", "ticket", "author", "created_at", "updated_at")


class TicketCommentCreateSerializer(serializers.Serializer):
    body = serializers.CharField(min_length=1)
    is_internal = serializers.BooleanField(default=False)


class TicketAttachmentUploadSerializer(serializers.Serializer):
    file = serializers.FileField()
    comment = serializers.PrimaryKeyRelatedField(
        queryset=TicketComment.objects.all(),
        required=False,
        allow_null=True,
    )
