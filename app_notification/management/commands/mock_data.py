from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from app_notification.models import NotificationEventType
from app_notification.models import NotificationPreference
from app_notification.dispatcher import handle_event_trigger

User = get_user_model()


class Command(BaseCommand):
    help = "Seed mock users, event types, preferences, and trigger a test notification"

    def handle(self, *args, **kwargs):
        self.stdout.write("🔁 Creating mock users...")
        users = self.create_users()

        self.stdout.write("🔁 Creating event types...")
        events = self.create_event_types()

        self.stdout.write("🔁 Creating user preferences...")
        self.create_preferences(users, events)

        self.stdout.write("🚀 Triggering test event (new_comment)...")
        payload = {"commenter": "user1", "thread_id": 123}
        handle_event_trigger("new_comment", payload)

        self.stdout.write(self.style.SUCCESS("✅ Mock data seeded and test notification triggered."))

    def create_users(self):
        users = []
        for i in range(1, 4):
            user, created = User.objects.get_or_create(
                username=f"user{i}",
                defaults={
                    "email": f"user{i}@test.com"
                }
            )
            if created:
                user.set_password("test1234")
                user.save()
            users.append(user)
        return users

    def create_event_types(self):
        event_types = [
            ("new_comment", "Triggered when a new comment is posted"),
            ("unrecognized_device_login", "Login from a new device"),
            ("weekly_summary", "Weekly report sum                    "phone_number": f"98000000{i}"mary")
        ]
        events = []
        for name, desc in event_types:
            event, _ = NotificationEventType.objects.get_or_create(name=name, defaults={"description": desc})
            events.append(event)
        return events

    def create_preferences(self, users, events):
        for user in users:
            for event in events:
                for channel in ["in_app", "email", "sms"]:
                    NotificationPreference.objects.get_or_create(
                        user=user,
                        event_type=event,
                        channel=channel,
                        defaults={"enabled": True}
                    )
