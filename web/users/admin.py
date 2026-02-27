from __future__ import annotations

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import User, UserAPNSToken


class CustomUserAdmin(UserAdmin):
    model = User
    list_display = ["email", "first_name", "last_name", "is_staff"]
    readonly_fields = ["date_joined"]
    fieldsets = (
        (None, {"fields": ("email", "password", "site")}),
        ("Personal info", {"fields": ("first_name", "last_name", "phone_number")}),
        ("Important dates", {"fields": ("date_joined",)}),
        (
            "Permissions",
            {
                "fields": (
                    "is_active",
                    "is_staff",
                    "is_superuser",
                    "groups",
                    "user_permissions",
                )
            },
        ),
    )
    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": ("email", "password1", "password2"),
            },
        ),
    )
    ordering = ("-pk",)


admin.site.register(User, CustomUserAdmin)

admin.site.register(UserAPNSToken)
