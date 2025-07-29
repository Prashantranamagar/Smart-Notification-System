from django.db import models
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError

User = get_user_model()


class NotificationChannel(models.TextChoices):
    """Enum for notification delivery channels"""

    IN_APP = "in_app", "In App"
    EMAIL = "email", "Email"
    SMS = "sms", "SMS"


class EventType(models.Model):
    """Dynamic model for event types that trigger notifications"""

    code = models.CharField(
        max_length=50, unique=True, help_text="Unique code for the event type"
    )
    name = models.CharField(max_length=100, help_text="Human readable name")
    description = models.TextField(
        blank=True, help_text="Description of when this event is triggered"
    )
    is_active = models.BooleanField(default=True)

    # Default preference when user signs up
    default_enabled = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "event_types"
        verbose_name = "Event Type"
        verbose_name_plural = "Event Types"
        ordering = ["name"]

    def __str__(self):
        return self.name

    @classmethod
    def get_default_event_types(cls):
        """Create default event types if they don't exist"""
        defaults = [
            {
                "code": "new_comment",
                "name": "New Comment Posted",
                "description": "Triggered when someone comments on a post you follow",
                "default_enabled": True,
            },
            {
                "code": "unrecognized_login",
                "name": "New Login from Unrecognized Device",
                "description": "Triggered when login detected from new device/location",
                "default_enabled": True,
            },
            {
                "code": "weekly_summary",
                "name": "Weekly Summary Report",
                "description": "Weekly digest of your activity and notifications",
                "default_enabled": True,
            },
        ]

        for event_data in defaults:
            cls.objects.get_or_create(code=event_data["code"], defaults=event_data)


class DeliveryStatus(models.TextChoices):
    """Enum for notification delivery status"""

    PENDING = "pending", "Pending"
    SENT = "sent", "Sent"
    FAILED = "failed", "Failed"
    RETRYING = "retrying", "Retrying"


class UserEventPreference(models.Model):
    """
    Dynamic model to store user preferences for each event type
    """

    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="event_preferences"
    )
    event_type = models.ForeignKey(
        EventType, on_delete=models.CASCADE, related_name="user_preferences"
    )
    is_enabled = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "user_event_preferences"
        verbose_name = "User Event Preference"
        verbose_name_plural = "User Event Preferences"
        unique_together = [["user", "event_type"]]

    def __str__(self):
        return f"{self.user.username} - {self.event_type.name} - {self.is_enabled}"


class NotificationPreference(models.Model):
    """
    Model to store user notification channel preferences
    """

    user = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name="notification_preferences"
    )
    in_app_enabled = models.BooleanField(default=True)
    email_enabled = models.BooleanField(default=True)
    sms_enabled = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "notification_preferences"
        verbose_name = "Notification Preference"
        verbose_name_plural = "Notification Preferences"

    def get_enabled_channels(self):
        """
        Get all enabled channels for this user
        """
        channels = []
        if self.in_app_enabled:
            channels.append(NotificationChannel.IN_APP)
        if self.email_enabled:
            channels.append(NotificationChannel.EMAIL)
        if self.sms_enabled:
            channels.append(NotificationChannel.SMS)

        return channels

    def is_event_enabled(self, event_type_code):
        """
        Check if user wants to receive notifications for this event type
        """
        try:
            event_type = EventType.objects.get(code=event_type_code, is_active=True)
            preference, created = UserEventPreference.objects.get_or_create(
                user=self.user,
                event_type=event_type,
                defaults={"is_enabled": event_type.default_enabled},
            )
            return preference.is_enabled
        except EventType.DoesNotExist:
            return False


class Notification(models.Model):
    """
    Model to store individual notifications
    """

    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="notifications"
    )
    event_type = models.ForeignKey(
        EventType, on_delete=models.CASCADE, related_name="notifications"
    )
    title = models.CharField(max_length=255)
    message = models.TextField()
    metadata = models.JSONField(default=dict, blank=True)

    is_read = models.BooleanField(default=False)
    read_at = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "notifications"
        verbose_name = "Notification"
        verbose_name_plural = "Notifications"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["user", "-created_at"]),
            models.Index(fields=["user", "is_read"]),
        ]

    def __str__(self):
        return f"{self.user.username} - {self.title}"


class NotificationDelivery(models.Model):
    """
    Model to track notification delivery across different channels
    """

    notification = models.ForeignKey(
        Notification, on_delete=models.CASCADE, related_name="deliveries"
    )
    channel = models.CharField(max_length=20, choices=NotificationChannel.choices)
    status = models.CharField(
        max_length=20, choices=DeliveryStatus.choices, default=DeliveryStatus.PENDING
    )

    # Delivery tracking
    attempted_at = models.DateTimeField(null=True, blank=True)
    delivered_at = models.DateTimeField(null=True, blank=True)
    failed_at = models.DateTimeField(null=True, blank=True)
    error_message = models.TextField(blank=True)
    retry_count = models.PositiveIntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "notification_deliveries"
        verbose_name = "Notification Delivery"
        verbose_name_plural = "Notification Deliveries"
        unique_together = [["notification", "channel"]]
        indexes = [
            models.Index(fields=["status", "created_at"]),
            models.Index(fields=["channel", "status"]),
        ]

    def __str__(self):
        return f"{self.notification} - {self.channel} - {self.status}"


class NotificationTemplate(models.Model):
    """
    Model to store notification templates for different event types and channels
    """

    event_type = models.ForeignKey(
        EventType, on_delete=models.CASCADE, related_name="templates"
    )
    channel = models.CharField(max_length=20, choices=NotificationChannel.choices)

    title_template = models.CharField(max_length=255)
    message_template = models.TextField()

    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "notification_templates"
        verbose_name = "Notification Template"
        verbose_name_plural = "Notification Templates"
        unique_together = [["event_type", "channel"]]

    def render(self, context):
        """
        Render template with given context
        """
        title = self.title_template.format(**context)
        message = self.message_template.format(**context)
        return title, message
