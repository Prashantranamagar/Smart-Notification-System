from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import (
    Notification,
    NotificationPreference,
    NotificationDelivery,
    EventType,
    NotificationChannel,
    UserEventPreference,
)

User = get_user_model()


class EventTypeSerializer(serializers.ModelSerializer):
    """
    Serializer for event types
    """

    class Meta:
        model = EventType
        fields = ["id", "code", "name", "description", "is_active"]
        read_only_fields = ["id"]


class UserEventPreferenceSerializer(serializers.ModelSerializer):
    """
    Serializer for user event preferences
    """

    event_type = EventTypeSerializer(read_only=True)
    event_type_code = serializers.CharField(write_only=True)

    class Meta:
        model = UserEventPreference
        fields = ["event_type", "event_type_code", "is_enabled", "updated_at"]
        read_only_fields = ["event_type", "updated_at"]

    def validate_event_type_code(self, value):
        """
        Validate that the event type exists and is active
        """
        try:
            EventType.objects.get(code=value, is_active=True)
        except EventType.DoesNotExist:
            raise serializers.ValidationError(
                f"Event type '{value}' does not exist or is inactive"
            )
        return value


class NotificationPreferenceSerializer(serializers.ModelSerializer):
    """
    Enhanced serializer for notification preferences with dynamic event types
    """

    event_preferences = UserEventPreferenceSerializer(
        source="user.event_preferences", many=True, read_only=True
    )

    class Meta:
        model = NotificationPreference
        fields = [
            "in_app_enabled",
            "email_enabled",
            "sms_enabled",
            "event_preferences",
            "updated_at",
        ]
        read_only_fields = ["updated_at", "event_preferences"]

    def validate(self, data):
        """
        Custom validation to ensure at least one channel is enabled
        """
        channels_enabled = any(
            [
                data.get("in_app_enabled", False),
                data.get("email_enabled", False),
                data.get("sms_enabled", False),
            ]
        )

        if not channels_enabled:
            raise serializers.ValidationError(
                "At least one notification channel must be enabled."
            )

        return data


class UpdateEventPreferenceSerializer(serializers.Serializer):
    """
    Serializer for updating multiple event preferences at once
    """

    preferences = serializers.ListField(
        child=serializers.DictField(child=serializers.CharField()),
        help_text="List of {'event_type_code': str, 'is_enabled': bool}",
    )

    def validate_preferences(self, value):
        """
        Validate the preferences structure
        """
        valid_preferences = []
        for pref in value:
            if "event_type_code" not in pref or "is_enabled" not in pref:
                raise serializers.ValidationError(
                    "Each preference must have 'event_type_code' and 'is_enabled' fields"
                )

            is_enabled = pref["is_enabled"]
            if isinstance(is_enabled, str):
                is_enabled = is_enabled.lower() in ["true", "1", "yes"]

            try:
                event_type = EventType.objects.get(
                    code=pref["event_type_code"], is_active=True
                )
                valid_preferences.append(
                    {"event_type": event_type, "is_enabled": bool(is_enabled)}
                )
            except EventType.DoesNotExist:
                raise serializers.ValidationError(
                    f"Event type '{pref['event_type_code']}' does not exist or is inactive"
                )

        return valid_preferences


class NotificationDeliverySerializer(serializers.ModelSerializer):
    """
    Serializer for notification delivery tracking
    """

    class Meta:
        model = NotificationDelivery
        fields = [
            "channel",
            "status",
            "attempted_at",
            "delivered_at",
            "failed_at",
            "error_message",
            "retry_count",
        ]


class NotificationSerializer(serializers.ModelSerializer):
    """
    Serializer for notifications with delivery status
    """

    deliveries = NotificationDeliverySerializer(many=True, read_only=True)

    class Meta:
        model = Notification
        fields = [
            "id",
            "event_type",
            "title",
            "message",
            "metadata",
            "is_read",
            "read_at",
            "created_at",
            "deliveries",
        ]
        read_only_fields = ["id", "created_at", "deliveries"]


class NotificationListSerializer(serializers.ModelSerializer):
    """
    Lightweight serializer for notification lists
    """

    class Meta:
        model = Notification
        fields = ["id", "event_type", "title", "message", "is_read", "created_at"]


class MarkAsReadSerializer(serializers.Serializer):
    """
    Serializer for marking notifications as read
    """

    notification_ids = serializers.ListField(
        child=serializers.IntegerField(),
        allow_empty=False,
        help_text="List of notification IDs to mark as read",
    )

    def validate_notification_ids(self, value):
        """
        Validate that all notification IDs belong to the current user
        """
        user = self.context["request"].user
        valid_ids = Notification.objects.filter(id__in=value, user=user).values_list(
            "id", flat=True
        )

        invalid_ids = set(value) - set(valid_ids)
        if invalid_ids:
            raise serializers.ValidationError(
                f"Invalid notification IDs: {list(invalid_ids)}"
            )

        return value


class EventTriggerSerializer(serializers.Serializer):
    """
    Serializer for triggering notification events with dynamic event types
    """

    event_type_code = serializers.CharField(help_text="Event type code to trigger")
    payload = serializers.JSONField(default=dict)
    target_users = serializers.ListField(
        child=serializers.IntegerField(),
        required=False,
        help_text="List of user IDs to notify. If empty, will determine based on event type.",
    )

    def validate_event_type_code(self, value):
        """
        Validate that the event type exists and is active
        """
        try:
            EventType.objects.get(code=value, is_active=True)
        except EventType.DoesNotExist:
            raise serializers.ValidationError(
                f"Event type '{value}' does not exist or is inactive"
            )
        return value

    def validate_target_users(self, value):
        """
        Validate that target users exist
        """
        if value:
            existing_users = User.objects.filter(id__in=value).values_list(
                "id", flat=True
            )
            invalid_users = set(value) - set(existing_users)
            if invalid_users:
                raise serializers.ValidationError(
                    f"Invalid user IDs: {list(invalid_users)}"
                )
        return value
