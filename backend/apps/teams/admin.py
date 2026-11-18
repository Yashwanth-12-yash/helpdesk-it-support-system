from django.contrib import admin

from .models import SupportTeam, TeamMembership


class TeamMembershipInline(admin.TabularInline):
    model = TeamMembership
    extra = 0
    autocomplete_fields = ("user",)


@admin.register(SupportTeam)
class SupportTeamAdmin(admin.ModelAdmin):
    list_display = ("name", "department", "lead", "is_active", "created_at")
    list_filter = ("department", "is_active")
    search_fields = ("name", "department__name", "lead__email")
    inlines = [TeamMembershipInline]
