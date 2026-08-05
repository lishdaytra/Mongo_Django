from django.contrib import admin

from .models import CompanyAccess


@admin.register(CompanyAccess)
class CompanyAccessAdmin(admin.ModelAdmin):
    list_display = (
        "user",
        "company_name",
        "company_id",
        "is_active",
    )
    list_filter = ("is_active",)
    search_fields = (
        "user__username",
        "company_name",
        "company_id",
    )
    autocomplete_fields = ("user",)