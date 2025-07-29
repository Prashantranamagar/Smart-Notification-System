from typing import List, Dict, Any, Optional
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.db import transaction
from celery import shared_task
import logging

from .models import (
    Notification, NotificationPreference, NotificationDelivery,
    NotificationTemplate, EventType, NotificationChannel, DeliveryStatus,
    UserEventPreference
)
from .backend import get_notification_backend

User = get_user_model()
logger = logging.getLogger(__name__)

class NotificationService:
    """
    Central service for handling notification logic with dynamic event types
    """
    
    @classmethod
    def create_notification(
        cls, 
        user: User, 
        event_type_code: str, 
        context: Dict[str, Any]
    ) -> Notification:
        """
        Create a notification for a user using dynamic event type
        """
        print(f'Event: {event_type_code}')
        try:
            event_type = EventType.objects.get(code=event_type_code, is_active=True)
        except EventType.DoesNotExist:
            raise ValueError(f"Event type '{event_type_code}' does not exist or is inactive")
        
        # Get or create template
        logger.info("******************* Getting notification template started *******************")
        print(f'******hello {event_type}*****')
        template = cls._get_template(event_type, NotificationChannel.IN_APP)
        print("******************* template *******************")
        title, message = template.render(context)
        print(f'******************* title: {title} message:{message} *******************')
       
        notification = Notification.objects.create(
            user=user,
            event_type=event_type,
            title=title,
            message=message,
            metadata=context
        )
        
        logger.info(f"Created notification {notification.id} for user {user.id}")
        return notification
    
    @classmethod
    def dispatch_notification(
        cls,
        event_type_code: str,
        context: Dict[str, Any],
        target_users: Optional[List[int]] = None
    ) -> List[Notification]:
        """
        Dispatch notifications to multiple users based on their preferences
        """
        logger.info("******************* Dispatching notification started *******************")

        try:
            event_type = EventType.objects.get(code=event_type_code, is_active=True)
        except EventType.DoesNotExist:
            logger.error(f"Event type '{event_type_code}' does not exist or is inactive")
            return []
        
        
        if target_users is None:
            logger.info("******************* No target users provided, determining target users *******************")
            target_users = cls._determine_target_users(event_type_code, context)

        logger.info("******************* Target user Fetched sucessfully *******************")
        
        notifications = []
        
        for user_id in target_users:
            try:
                user = User.objects.get(id=user_id)
                logger.info("*******************Getting user preferences started *******************")

                preferences = cls._get_user_preferences(user)
                
                if preferences.is_event_enabled(event_type_code):

                    logger.info("******************* Creating notification started *******************")
                    notification = cls.create_notification(user, event_type_code, context)
                    notifications.append(notification)
                    
                    # Schedule delivery tasks
                    logger.info("******************* Getting enabled channels started *******************")
                    enabled_channels = preferences.get_enabled_channels()
                    logger.info(f"Enabled channels for user {user.id}: {enabled_channels}")
                    for channel in enabled_channels:
                        logger.info("******************* Delivering notification task started *******************")
                        deliver_notification_task.delay(notification.id, channel) #using celery
                        # deliver_notification_task(notification.id, channel) #without celery

                
            except User.DoesNotExist:
                logger.warning(f"User {user_id} not found")
                continue
            except Exception as e:
                logger.error(f"Error dispatching notification to user {user_id}: {e}")
                continue
        
        return notifications
    
    @classmethod
    def update_user_event_preferences(
        cls, 
        user: User, 
        preferences: List[Dict[str, Any]]
    ) -> List[UserEventPreference]:
        """
        Update user's event preferences
        """
        updated_preferences = []
        
        for pref_data in preferences:
            event_type = pref_data['event_type']
            is_enabled = pref_data['is_enabled']
            
            preference, created = UserEventPreference.objects.update_or_create(
                user=user,
                event_type=event_type,
                defaults={'is_enabled': is_enabled}
            )
            updated_preferences.append(preference)
            
            logger.info(f"Updated event preference for user {user.id}: {event_type.code} = {is_enabled}")
        
        return updated_preferences
    
    @classmethod
    def create_event_type(
        cls,
        code: str,
        name: str,
        description: str = "",
        default_enabled: bool = True
    ) -> EventType:
        """
        Create a new dynamic event type
        """
        event_type, created = EventType.objects.get_or_create(
            code=code,
            defaults={
                'name': name,
                'description': description,
                'default_enabled': default_enabled,
                'is_active': True
            }
        )
        
        if created:
            logger.info(f"Created new event type: {code}")
            
            # Create default preferences for all existing users
            cls._create_default_preferences_for_event_type(event_type)
        
        return event_type
    
    @classmethod
    def _create_default_preferences_for_event_type(cls, event_type: EventType):
        """
        Create default preferences for all existing users when a new event type is added
        """
        users = User.objects.all()
        preferences_to_create = []
        
        for user in users:
            if not UserEventPreference.objects.filter(user=user, event_type=event_type).exists():
                preferences_to_create.append(
                    UserEventPreference(
                        user=user,
                        event_type=event_type,
                        is_enabled=event_type.default_enabled
                    )
                )
        
        if preferences_to_create:
            UserEventPreference.objects.bulk_create(preferences_to_create)
            logger.info(f"Created default preferences for {len(preferences_to_create)} users")
    
    @classmethod
    def _get_template(cls, event_type: EventType, channel: str) -> NotificationTemplate:
        """
        Get or create notification template for dynamic event type
        """
        print("***************** Get or create notification template  *******************")
        print(f"hellp me {event_type}")
        template, created = NotificationTemplate.objects.get_or_create(
            event_type=event_type,
            channel=channel,
            defaults=cls._get_default_template(event_type.code, channel)
        )
        print(template)
        return template
    
    @classmethod
    def _get_default_template(cls, event_type_code: str, channel: str) -> Dict[str, str]:
        """
        Get default template content for dynamic event types
        """
        templates = {
            'new_comment': {
                'title_template': 'New Comment on {post_title}',
                'message_template': '{commenter} commented: "{comment_text}"'
            },
            'unrecognized_login': {
                'title_template': 'New Login Detected',
                'message_template': 'New login from {device} at {location} on {timestamp}'
            },
            'weekly_summary': {
                'title_template': 'Your Weekly Summary',
                'message_template': 'You have {notification_count} new notifications this week.'
            },
            'welcome': {
            'title_template': 'Welcome to Our App, {username}!',
            'message_template': 'Hi {username}, we’re excited to have you onboard. Explore features and enjoy your journey!'
            }
                
        }
        
        return templates.get(event_type_code, {
            'title_template': 'Notification: {event_name}',
            'message_template': 'You have a new notification of type: {event_name}'
        })
    
    @classmethod
    def _determine_target_users(cls, event_type_code: str, context: Dict[str, Any]) -> List[int]:
        """
        Determine target users based on dynamic event type and context
        """
        logger.info("******************* Determining target users started *******************")

        if event_type_code == 'new_comment':
            # For new comments, notify all users who follow the post/thread
            return context.get('follower_ids', [])
        
        elif event_type_code == 'unrecognized_login':
            # For unrecognized login, only notify the specific user
            return [context.get('user_id')]
        
        elif event_type_code == 'weekly_summary':
            # For weekly summary, notify all active users
            return list(User.objects.filter(is_active=True).values_list('id', flat=True))
        
        # For unknown event types, check if target_users provided in context
        return context.get('target_users', [])
    
    @classmethod
    def mark_as_read(cls, user: User, notification_ids: List[int]) -> int:
        """
        Mark notifications as read for a user
        """
        updated_count = Notification.objects.filter(
            id__in=notification_ids,
            user=user,
            is_read=False
        ).update(
            is_read=True,
            read_at=timezone.now()
        )
        
        logger.info(f"Marked {updated_count} notifications as read for user {user.id}")
        return updated_count
    
    @classmethod
    def _get_user_preferences(cls, user: User) -> NotificationPreference:
        """
        Get or create user notification preferences with dynamic event types
        """
        preferences, created = NotificationPreference.objects.get_or_create(
            user=user,
            defaults={
                'in_app_enabled': True,
                'email_enabled': True,
                'sms_enabled': False,
            }
        )
        
        # If user is new, create default event preferences
        if created:
            cls._create_default_event_preferences(user)
        
        return preferences
    
    @classmethod
    def _create_default_event_preferences(cls, user: User):
        """
        Create default event preferences for a new user
        """
        # Ensure default event types exist
        EventType.get_default_event_types()
        
        # Create preferences for all active event types
        active_event_types = EventType.objects.filter(is_active=True)
        preferences_to_create = []
        
        for event_type in active_event_types:
            preferences_to_create.append(
                UserEventPreference(
                    user=user,
                    event_type=event_type,
                    is_enabled=event_type.default_enabled
                )
            )
        
        UserEventPreference.objects.bulk_create(preferences_to_create)
        logger.info(f"Created default event preferences for user {user.id}")
    
    @classmethod
    def _get_template(cls, event_type: str, channel: str) -> NotificationTemplate:
        """
        Get or create notification template
        """
        print(event_type)
        print(channel)
        get_template = NotificationTemplate.objects.get(
            event_type=event_type,
            channel=channel
        )
        print(get_template.event_type, get_template.channel)
        defaults = cls._get_default_template(event_type.code, channel)

        if defaults:
            template, created = NotificationTemplate.objects.get_or_create(
                event_type=event_type,
                channel=channel,
                defaults=defaults
            )
        else:
            try:
                template = NotificationTemplate.objects.get(
                    event_type=event_type,
                    channel=channel
                )
            except NotificationTemplate.DoesNotExist:
                logger.warning(f"No template found for event type {event_type} and channel {channel}, please create one.")
                template = None
        return template
    
    @classmethod
    def _get_default_template(cls, event_type: str, channel: str) -> Dict[str, str]:
        """
        Get default template content
        """
        templates = {
            'new_comment': {
                'title_template': 'New Comment on {post_title}',
                'message_template': '{commenter} commented: "{comment_text}"'
            },
            'unrecognized_login': {
                'title_template': 'New Login Detected',
                'message_template': 'New login from {device} at {location} on {timestamp}'
            },
            'weekly_summary': {
                'title_template': 'Your Weekly Summary',
                'message_template': 'You have {notification_count} new notifications this week.'
            }
            
        }
        return templates.get(event_type, {
            'title_template': 'Notification',
            'message_template': 'You have a new notification.'
        })
    
    @classmethod
    def _determine_target_users(cls, event_type: str, context: Dict[str, Any]) -> List[int]:
        """
        Determine target users based on event type and context
        """
        if event_type == EventType.NEW_COMMENT:
            # For new comments, notify all users who follow the post/thread
            # This is a simplified implementation
            return context.get('follower_ids', [])
        
        elif event_type == EventType.UNRECOGNIZED_LOGIN:
            # For unrecognized login, only notify the specific user
            return [context.get('user_id')]
        
        elif event_type == EventType.WEEKLY_SUMMARY:
            # For weekly summary, notify all active users
            return list(User.objects.filter(is_active=True).values_list('id', flat=True))
        
        return []

@shared_task(bind=True, max_retries=3)
def deliver_notification_task(self, notification_id: int, channel: str):
    """
    Celery task to deliver notification via specific channel
    """
    logger.info("******************* Delivering notification task started *******************")

    try:
        notification = Notification.objects.get(id=notification_id)
        
        # Create or get delivery record
        delivery, created = NotificationDelivery.objects.get_or_create(
            notification=notification,
            channel=channel,
            defaults={'status': DeliveryStatus.PENDING}
        )
        
        # Update status to retrying if this is a retry
        if not created and delivery.retry_count > 0:
            delivery.status = DeliveryStatus.RETRYING
            delivery.save()
        
        logger.info(f"Attempting to deliver notification {notification_id} via {channel}")
        backend = get_notification_backend(channel)
        
        # Attempt delivery
        delivery.attempted_at = timezone.now()
        delivery.save()
        
        success = backend.send_notification(notification)
        
        if success:
            delivery.status = DeliveryStatus.SENT
            delivery.delivered_at = timezone.now()
            logger.info(f"Successfully delivered notification {notification_id} via {channel}")
        else:
            raise Exception("Backend returned failure")
            
    except Exception as exc:
        delivery.status = DeliveryStatus.FAILED
        delivery.failed_at = timezone.now()
        delivery.error_message = str(exc)
        delivery.retry_count += 1
        delivery.save()
        
        logger.error(f"Failed to deliver notification {notification_id} via {channel}: {exc}")
        
        # Retry with exponential backoff
        if delivery.retry_count < 3:
            raise self.retry(exc=exc, countdown=60 * (2 ** delivery.retry_count))
        else:
            logger.error(f"Max retries exceeded for notification {notification_id} via {channel}")
    
    finally:
        delivery.save()