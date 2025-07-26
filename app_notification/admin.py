from django.contrib import admin
from .models import (Notification, NotificationPreference, NotificationEventType)

admin.site.register(Notification)
admin.site.register(NotificationPreference)
admin.site.register(NotificationEventType)