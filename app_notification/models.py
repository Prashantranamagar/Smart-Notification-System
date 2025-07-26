from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()

CHANNEL_CHOICES = [
    ('in_app', 'In App'),
    ('email', 'Email'),
    ('sms', 'SMS'),
]

STATUS_CHOICES = [
    ('pending', 'Pending'),
    ('sent', 'Sent'),
    ('failed', 'Failed'),
]


class NotificationEventType(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField()

    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name_plural = "Notification Event Types"


class Notification(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    message = models.TextField()
    channel = models.CharField(max_length=20, choices=CHANNEL_CHOICES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    is_read = models.BooleanField(default=False)
    event_type = models.ForeignKey(NotificationEventType, null=True, on_delete=models.SET_NULL)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Notification to {self.user} via {self.channel}"


# == apps/notifications/models/preference.py ==
class NotificationPreference(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="notifications")
    event_type = models.ForeignKey(NotificationEventType, on_delete=models.CASCADE, related_name="notifications")
    channel = models.CharField(max_length=20, choices=CHANNEL_CHOICES)
    enabled = models.BooleanField(default=True)

    class Meta:
        unique_together = ('user', 'event_type', 'channel')

    def __str__(self):
        return f"{self.user} - {self.event_type} - {self.channel}"
