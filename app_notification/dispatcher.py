# notifications/dispatcher.py
from .models import Notification, NotificationEventType, NotificationPreference
from .delivery import get_delivery_handler
from django.contrib.auth import get_user_model

User = get_user_model()

def handle_event_trigger(event_type_name, payload):
    try:
        event_type = NotificationEventType.objects.get(name=event_type_name)
    except NotificationEventType.DoesNotExist:
        return

    users = resolve_users_for_event(event_type, payload)

    for user in users:
        preferences = NotificationPreference.objects.filter(user=user, event_type=event_type, enabled=True)

        for pref in preferences:
            message = generate_message(event_type.name, payload)
            status = get_delivery_handler(pref.channel).send(user, message)

            Notification.objects.create(
                user=user,
                message=message,
                event_type=event_type,
                channel=pref.channel,
                status=status
            )

def resolve_users_for_event(event_type, payload):
    # Just return all users for now
    return User.objects.all()

def generate_message(event_type_name, payload):
    return f"[{event_type_name.upper()}] {payload}"
