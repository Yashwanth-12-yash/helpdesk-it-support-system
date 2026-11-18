from rest_framework import serializers

from apps.accounts.serializers import UserSummarySerializer
from .models import KnowledgeArticle


class KnowledgeArticleSerializer(serializers.ModelSerializer):
    author_detail = UserSummarySerializer(source="author", read_only=True)
    published_by_detail = UserSummarySerializer(source="published_by", read_only=True)

    class Meta:
        model = KnowledgeArticle
        fields = (
            "id",
            "title",
            "slug",
            "category",
            "summary",
            "content",
            "troubleshooting_steps",
            "keywords",
            "status",
            "author",
            "author_detail",
            "published_by",
            "published_by_detail",
            "published_at",
            "view_count",
            "created_at",
            "updated_at",
        )
        read_only_fields = (
            "id",
            "slug",
            "author",
            "published_by",
            "published_at",
            "view_count",
            "created_at",
            "updated_at",
        )


class KnowledgeArticleWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = KnowledgeArticle
        fields = ("title", "category", "summary", "content", "troubleshooting_steps", "keywords", "status")
