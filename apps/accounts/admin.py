from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin

from .models import User


@admin.register(User)
class UserAdmin(DjangoUserAdmin):
    fieldsets = DjangoUserAdmin.fieldsets + (("SENTRA", {"fields": ("role", "unit", "phone")}),)
    add_fieldsets = DjangoUserAdmin.add_fieldsets + (
        ("SENTRA", {"fields": ("role", "unit", "phone")}),
    )
    list_display = ("username", "first_name", "role", "unit", "is_active")
    list_filter = ("role", "unit", "is_active")