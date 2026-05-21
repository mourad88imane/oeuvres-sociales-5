"""Users admin configuration."""

from simple_history.admin import SimpleHistoryAdmin

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .models import User


@admin.register(User)
class UserAdmin(BaseUserAdmin, SimpleHistoryAdmin):
    list_display = [
        "email",
        "first_name",
        "last_name",
        "role",
        "is_active",
        "last_login",
        "date_joined",
    ]
    list_filter = ["role", "is_active", "is_staff", "date_joined"]
    search_fields = ["email", "first_name", "last_name"]
    ordering = ["email"]
    readonly_fields = ["id", "last_login", "date_joined", "created_at", "updated_at"]

    fieldsets = (
        ("Authentification", {"fields": ("email", "password")}),
        ("Informations personnelles", {"fields": ("first_name", "last_name", "phone", "avatar")}),
        (
            "Rôle & Permissions",
            {"fields": ("role", "is_active", "is_staff", "is_superuser", "must_change_password")},
        ),
        ("Groupes Django", {"fields": ("groups", "user_permissions"), "classes": ("collapse",)}),
        (
            "Métadonnées",
            {
                "fields": (
                    "id",
                    "last_login",
                    "last_login_ip",
                    "date_joined",
                    "created_at",
                    "updated_at",
                ),
                "classes": ("collapse",),
            },
        ),
        ("Préférences", {"fields": ("preferences",), "classes": ("collapse",)}),
    )

    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": ("email", "first_name", "last_name", "role", "password1", "password2"),
            },
        ),
    )
