from django.core.management.base import BaseCommand
from app_notification.models import EventType

class Command(BaseCommand):
    help = 'Create default event types for the notification system'
    
    def handle(self, *args, **options):
        EventType.get_default_event_types()
        self.stdout.write(
            self.style.SUCCESS('Successfully created default event types')
        )