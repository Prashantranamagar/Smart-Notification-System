from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta
from app_notification.services import NotificationService

User = get_user_model()

class Command(BaseCommand):
    help = 'Send weekly summary notifications to all active users'
    
    def handle(self, *args, **options):
        # Get active users
        active_users = User.objects.filter(is_active=True)
        
        for user in active_users:
            # Calculate notification count for the week
            week_ago = timezone.now() - timedelta(days=7)
            notification_count = user.notifications.filter(
                created_at__gte=week_ago
            ).count()
            
            # Dispatch weekly summary
            NotificationService.dispatch_notification(
                event_type_code='weekly_summary',
                context={
                    'user_id': user.id,
                    'notification_count': notification_count,
                    'week_start': week_ago.strftime('%Y-%m-%d'),
                    'week_end': timezone.now().strftime('%Y-%m-%d')
                },
                target_users=[user.id]
            )
        
        self.stdout.write(
            self.style.SUCCESS(f'Sent weekly summaries to {active_users.count()} users')
        )