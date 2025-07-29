from django.contrib import admin
from .models import User, UserDevice


class UserAdmin(admin.ModelAdmin):
    list_display = (
        "username",
        "phone_number",
        "email",
        "is_active",
        "is_staff",
        "is_superuser",
        "created_at",
    )
    search_fields = ("username", "email")
    list_filter = ("is_active", "is_staff")
    ordering = ("-created_at",)


admin.site.register(User, UserAdmin)


class UserDeviceAdmin(admin.ModelAdmin):
    list_display = ("user", "device_id", "device_name", "updated_at", "created_at")
    search_fields = ("user__username", "device_id", "device_name")
    list_filter = ("user",)
    ordering = ("-created_at",)


admin.site.register(UserDevice, UserDeviceAdmin)
