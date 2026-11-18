from django.contrib import admin

from .models import KnowledgeArticle


@admin.register(KnowledgeArticle)
class KnowledgeArticleAdmin(admin.ModelAdmin):
    list_display = ("title", "category", "status", "author", "published_at", "view_count")
    list_filter = ("status", "category")
    search_fields = ("title", "summary", "content")
    prepopulated_fields = {"slug": ("title",)}
