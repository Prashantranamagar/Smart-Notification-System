from django.core.management.base import BaseCommand
from django.utils.timezone import now
from app_notification.models import EventType, NotificationTemplate
from app_notification.models import NotificationChannel


class Command(BaseCommand):
    help = "Generate default notification templates for predefined event types and channels."

    def handle(self, *args, **options):
        # Ensure EventTypes exist
        EventType.get_default_event_types()

        # Templates for each event type and channel
        templates = {
            'new_comment': {
                NotificationChannel.IN_APP: {
                    'title': 'New comment on your post',
                    'message': '{username} commented on "{post_title}".'
                },
                NotificationChannel.EMAIL: {
                    'title': 'You’ve got a new comment!',
                    'message': 'Hi {user_name},\n\nA new comment was posted on "{post_title}".\n\nCheck it out!'
                },
                NotificationChannel.SMS: {
                    'title': '',
                    'message': 'New comment on "{post_title}". View it now.'
                }
            },
            'unrecognized_login': {
                NotificationChannel.IN_APP: {
                    'title': 'New login detected',
                    'message': 'A login from an unknown device occurred at {timestamp}.'
                },
                NotificationChannel.EMAIL: {
                    'title': 'Security alert: New login detected',
                    'message': 'Hi {user_name},\n\nWe noticed a login from an unrecognized device at {timestamp}.\n\nIf this wasn’t you, please secure your account.'
                },
                NotificationChannel.SMS: {
                    'title': '',
                    'message': 'New login at {timestamp}. Was this you?'
                }
            },
            'weekly_summary': {
                NotificationChannel.IN_APP: {
                    'title': 'Your Weekly Summary',
                    'message': 'Your weekly summary is ready. View your highlights now.'
                },
                NotificationChannel.EMAIL: {
                    'title': 'Your Weekly Activity Summary',
                    'message': 'Hi {user_name},\n\nHere’s your activity summary for the week:Notification count is \n{notification_count}\n\nThanks for staying active!'
                },
                NotificationChannel.SMS: {
                    'title': '',
                    'message': 'Your weekly summary is ready. Check email for details.'
                }
            }
        }

        created_count = 0

        for code, channels in templates.items():
            try:
                event = EventType.objects.get(code=code)
            except EventType.DoesNotExist:
                self.stdout.write(self.style.ERROR(f"Event type '{code}' not found."))
                continue

            for channel, content in channels.items():
                obj, created = NotificationTemplate.objects.get_or_create(
                    event_type=event,
                    channel=channel,
                    defaults={
                        'title_template': content['title'],
                        'message_template': content['message'],
                        'is_active': True,
                        'created_at': now(),
                        'updated_at': now(),
                    }
                )
                if created:
                    created_count += 1
                    self.stdout.write(self.style.SUCCESS(f"Created template for '{code}' [{channel}]"))
                else:
                    self.stdout.write(self.style.WARNING(f"Template already exists for '{code}' [{channel}]"))

        self.stdout.write(self.style.SUCCESS(f"Done. {created_count} new templates created."))
