from django.contrib import admin

from .models import AIRecommendation


@admin.register(AIRecommendation)
class AIRecommendationAdmin(admin.ModelAdmin):
    list_display = ("id", "ticket", "recommendation_type", "suggested_category", "suggested_priority", "status", "created_at")
    list_filter = ("recommendation_type", "status")
    search_fields = ("ticket__ticket_number", "summary_text")
