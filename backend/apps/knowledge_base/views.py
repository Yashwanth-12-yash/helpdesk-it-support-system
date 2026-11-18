from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.accounts.models import User
from apps.tickets.models import Ticket
from .models import KnowledgeArticle
from .permissions import KnowledgeArticlePermission
from .serializers import KnowledgeArticleSerializer, KnowledgeArticleWriteSerializer
from .services import (
    archive_article,
    create_article,
    increment_article_views,
    publish_article,
    recommend_articles_for_ticket,
    update_article,
)


class KnowledgeArticleViewSet(viewsets.ModelViewSet):
    http_method_names = ["get", "post", "patch", "head", "options"]
    permission_classes = [IsAuthenticated, KnowledgeArticlePermission]
    filterset_fields = ["category", "status"]
    search_fields = ["title", "summary", "content", "troubleshooting_steps"]
    ordering_fields = ["updated_at", "published_at", "view_count", "title"]

    def get_queryset(self):
        qs = KnowledgeArticle.objects.select_related("author", "published_by")
        if self.request.user.role == User.Role.EMPLOYEE:
            return qs.filter(status=KnowledgeArticle.Status.PUBLISHED)
        return qs

    def get_serializer_class(self):
        if self.action in {"create", "partial_update", "update"}:
            return KnowledgeArticleWriteSerializer
        return KnowledgeArticleSerializer

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        increment_article_views(instance)
        instance.refresh_from_db()
        return Response(KnowledgeArticleSerializer(instance).data)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        article = create_article(author=request.user, **serializer.validated_data)
        return Response(KnowledgeArticleSerializer(article).data, status=status.HTTP_201_CREATED)

    def partial_update(self, request, *args, **kwargs):
        article = self.get_object()
        serializer = self.get_serializer(article, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        updated = update_article(article=article, actor=request.user, **serializer.validated_data)
        return Response(KnowledgeArticleSerializer(updated).data)

    @extend_schema(request=None, responses=KnowledgeArticleSerializer)
    @action(detail=True, methods=["post"], url_path="publish")
    def publish(self, request, pk=None):
        article = self.get_object()
        updated = publish_article(article=article, actor=request.user)
        return Response(KnowledgeArticleSerializer(updated).data)

    @extend_schema(request=None, responses=KnowledgeArticleSerializer)
    @action(detail=True, methods=["post"], url_path="archive")
    def archive(self, request, pk=None):
        article = self.get_object()
        updated = archive_article(article=article)
        return Response(KnowledgeArticleSerializer(updated).data)

    @extend_schema(responses=KnowledgeArticleSerializer(many=True))
    @action(detail=False, methods=["get"], url_path="recommend")
    def recommend(self, request):
        ticket_id = request.query_params.get("ticket_id")
        if not ticket_id:
            return Response(KnowledgeArticleSerializer([], many=True).data)
        ticket = get_object_or_404(Ticket, pk=ticket_id)
        articles = recommend_articles_for_ticket(ticket=ticket)
        return Response(KnowledgeArticleSerializer(articles, many=True).data)
