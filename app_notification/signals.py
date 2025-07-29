from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from .services import NotificationService
from django.contrib.auth.signals import user_logged_in
from authentication.models import UserDevice
from django.dispatch import Signal

jwt_logged_in = Signal()  # Custom signal for JWT login
from django.utils import timezone
from post.models import Comment
import logging

logger = logging.getLogger(__name__)


User = get_user_model()


@receiver(post_save, sender=User)
def create_user_notification_preferences(sender, instance, created, **kwargs):
    """
    Automatically create notification preferences when a new user is created
    """
    if created:
        NotificationService._get_user_preferences(instance)


@receiver(jwt_logged_in)
def track_device_on_login(sender, request, user, **kwargs):

    device_id = request.headers.get("Device-ID")
    print("************** hello device id ****************")
    print("Device ID:", device_id)
    if not device_id:
        return

    try:
        existing_device = UserDevice.objects.get(user=user)
        if existing_device.device_id != device_id:
            print("Updating device ID for user:", user.username)
            existing_device.device_id = device_id
            existing_device.save()
            NotificationService.dispatch_notification(
                event_type_code="unrecognized_login",
                context={
                    "user_id": user.id,
                    "timestamp": timezone.now().strftime("%Y-%m-%d %H:%M:%S"),
                },
                target_users=[user.id],
            )
        else:
            print("Device ID already exists for user:", user.username)
            existing_device.save()
    except UserDevice.DoesNotExist:
        print("Creating new device entry for user:", user.username)
        UserDevice.objects.create(user=user, device_id=device_id)
        NotificationService.dispatch_notification(
            event_type_code="new_device_login",
            context={"user_id": user.id, "device_id": device_id},
            target_users=[user.id],
        )
    except Exception as e:
        print(f"Error tracking device on login: {e}")
        return


@receiver(post_save, sender=Comment)
def notify_on_new_comment(sender, instance, created, **kwargs):
    if not created:
        return
    post = instance.post
    username = instance.author.username
    user_ids = get_related_user_ids(post)
    logger.info(f"Related user IDs for post {post.id}: {user_ids}")
    if user_ids:
        NotificationService.dispatch_notification(
            event_type_code="new_comment",
            context={"post_title": post.title, "username": username},
            target_users=user_ids,
        )


def get_related_user_ids(post):
    """
    Returns a list of user IDs connected to a post:
    - Post author
    - All users who commented on the post
    """
    author_id = post.author_id

    commenter_ids = (
        post.comments.exclude(author_id=author_id) 
        .values_list("author_id", flat=True)
        .distinct()
    )

    related_user_ids = set(commenter_ids)
    related_user_ids.add(author_id)

    return list(related_user_ids)  
