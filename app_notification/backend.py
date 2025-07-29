from abc import ABC, abstractmethod
from typing import Dict, Any
from django.core.mail import send_mail
from django.conf import settings
import logging
from .models import NotificationChannel

logger = logging.getLogger(__name__)

class NotificationBackend(ABC):
    """
    Abstract base class for notification backends
    """
    
    @abstractmethod
    def send_notification(self, notification) -> bool:
        """
        Send notification and return success status
        """
        pass

class InAppBackend(NotificationBackend):
    """
    In-app notification backend (already stored in database)
    """
    
    def send_notification(self, notification) -> bool:
        """
        For in-app notifications, they're already stored in the database
        """
        logger.info(f"In-app notification {notification.id} send success for user {notification.user.username}")
        return True

class EmailBackend(NotificationBackend):
    """
    Email notification backend (mocked)
    """
    
    def send_notification(self, notification) -> bool:
        """
        Send email notification (mocked)
        """
        try:
            # In a real implementation, you'd use Django's email system
            # For now, we'll just log it
            logger.info(f"[MOCK EMAIL] To: {notification.user.email}")
            logger.info(f"[MOCK EMAIL] Subject: {notification.title}")
            logger.info(f"[MOCK EMAIL] Body: {notification.message}")
            
            # Simulate email sending
            # send_mail(
            #     subject=notification.title,
            #     message=notification.message,
            #     from_email=settings.DEFAULT_FROM_EMAIL,
            #     recipient_list=[notification.user.email],
            #     fail_silently=False,
            # )
            logger.info(f"Email sent success {notification.user.email} for notification {notification.id}")    
            return True
            
        except Exception as e:
            logger.error(f"Failed to send email notification: {e}")
            return False

class SMSBackend(NotificationBackend):
    """
    SMS notification backend (mocked)
    """
    
    def send_notification(self, notification) -> bool:
        """
        Send SMS notification (mocked)
        """
        try:
            phone = getattr(notification.user, 'phone_number', None)
            
            if not phone:
                logger.warning(f"No phone number for user {notification.user.id}")
                return False
            
            # Mock SMS sending - in production, you'd use Twilio, AWS SNS, etc.
            logger.info(f"[MOCK SMS] To: {phone}")
            logger.info(f"[MOCK SMS] Message: {notification.title}")
            logger.info(f"[MOCK SMS] Body: {notification.message[:160]}...")  # SMS character limit
            
            # Simulate SMS sending with external service
            # import twilio
            # client = twilio.rest.Client(account_sid, auth_token)
            # client.messages.create(
            #     body=f"{notification.title}\n{notification.message}",
            #     from_='+1234567890',
            #     to=phone
            # )
            logger.info(f"SMS sent success {phone} for notification {notification.id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send SMS notification: {e}")
            return False

def get_notification_backend(channel: str) -> NotificationBackend:
    """
    Factory function to get the appropriate notification backend
    """
    backends = {
        NotificationChannel.IN_APP: InAppBackend(),
        NotificationChannel.EMAIL: EmailBackend(),
        NotificationChannel.SMS: SMSBackend(),
    }
    
    backend = backends.get(channel)
    if not backend:
        raise ValueError(f"Unknown notification channel: {channel}")
    
    return backend