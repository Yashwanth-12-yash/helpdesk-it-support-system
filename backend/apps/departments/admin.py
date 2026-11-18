from django.contrib import admin

from .models import Department


@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "manager", "is_active", "created_at")
    list_filter = ("is_active",)
    search_fields = ("code", "name", "manager__email")
    autocomplete_fields = ("manager",)
