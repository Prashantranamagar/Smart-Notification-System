from django.contrib import admin
from django.utils.html import format_html
from .models import (
    EventType,
    NotificationPreference,
    UserEventPreference,
    Notification,
    NotificationDelivery,
    NotificationTemplate,
)


@admin.register(EventType)
class EventTypeAdmin(admin.ModelAdmin):
    list_display = ["code", "name", "is_active", "default_enabled", "created_at"]
    list_filter = ["is_active", "default_enabled", "created_at"]
    search_fields = ["code", "name", "description"]
    readonly_fields = ["created_at", "updated_at"]

    fieldsets = (
        (None, {"fields": ("code", "name", "description")}),
        ("Settings", {"fields": ("is_active", "default_enabled")}),
        (
            "Timestamps",
            {"fields": ("created_at", "updated_at"), "classes": ("collapse",)},
        ),
    )


# class UserEventPreferenceInline(admin.TabularInline):
#     model = UserEventPreference
#     extra = 0
#     readonly_fields = ['created_at', 'updated_at']

# @admin.register(NotificationPreference)
# class NotificationPreferenceAdmin(admin.ModelAdmin):
#     list_display = ['user', 'in_app_enabled', 'email_enabled', 'sms_enabled', 'updated_at']
#     list_filter = ['in_app_enabled', 'email_enabled', 'sms_enabled']
#     search_fields = ['user__username', 'user__email']
#     readonly_fields = ['created_at', 'updated_at']
#     inlines = [UserEventPreferenceInline]

from django.utils.html import format_html, format_html_join


@admin.register(NotificationPreference)
class NotificationPreferenceAdmin(admin.ModelAdmin):
    list_display = [
        "user",
        "in_app_enabled",
        "email_enabled",
        "sms_enabled",
        "updated_at",
    ]
    list_filter = ["in_app_enabled", "email_enabled", "sms_enabled"]
    search_fields = ["user__username", "user__email"]
    readonly_fields = ["created_at", "updated_at", "display_event_preferences"]

    def display_event_preferences(self, obj):
        prefs = obj.user.event_preferences.all()
        if not prefs.exists():
            return "No event preferences set."

        return format_html(
            "<ul>{}</ul>",
            format_html_join(
                "\n",
                "<li><strong>{}</strong>: {}</li>",
                (
                    (p.event_type.name, "Enabled" if p.is_enabled else "Disabled")
                    for p in prefs
                ),
            ),
        )

    display_event_preferences.short_description = "User Event Preferences"


admin.site.register(UserEventPreference)


class NotificationDeliveryInline(admin.TabularInline):
    model = NotificationDelivery
    extra = 0
    readonly_fields = [
        "attempted_at",
        "delivered_at",
        "failed_at",
        "created_at",
        "updated_at",
    ]


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = [
        "user",
        "event_type",
        "title",
        "is_read",
        "created_at",
        "delivery_status",
    ]
    list_filter = ["is_read", "event_type", "created_at"]
    search_fields = ["user__username", "title", "message"]
    readonly_fields = ["created_at", "updated_at", "read_at"]
    inlines = [NotificationDeliveryInline]

    def delivery_status(self, obj):
        """Show delivery status summary"""
        deliveries = obj.deliveries.all()
        if not deliveries:
            return format_html('<span style="color: orange;">No deliveries</span>')

        status_counts = {}
        for delivery in deliveries:
            status_counts[delivery.status] = status_counts.get(delivery.status, 0) + 1

        status_html = []
        for status, count in status_counts.items():
            color = {
                "sent": "green",
                "failed": "red",
                "pending": "orange",
                "retrying": "blue",
            }.get(status, "black")
            status_html.append(
                f'<span style="color: {color};">{status}: {count}</span>'
            )

        return format_html(" | ".join(status_html))

    delivery_status.short_description = "Delivery Status"


@admin.register(NotificationDelivery)
class NotificationDeliveryAdmin(admin.ModelAdmin):
    list_display = [
        "notification",
        "channel",
        "status",
        "retry_count",
        "attempted_at",
        "delivered_at",
    ]
    list_filter = ["channel", "status", "attempted_at", "delivered_at"]
    search_fields = ["notification__title", "notification__user__username"]
    readonly_fields = [
        "attempted_at",
        "delivered_at",
        "failed_at",
        "created_at",
        "updated_at",
    ]


@admin.register(NotificationTemplate)
class NotificationTemplateAdmin(admin.ModelAdmin):
    list_display = ["event_type", "channel", "is_active", "created_at"]
    list_filter = ["channel", "is_active", "created_at"]
    search_fields = ["event_type__name", "title_template"]
    readonly_fields = ["created_at", "updated_at"]
