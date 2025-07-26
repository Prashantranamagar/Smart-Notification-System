from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from .dispatcher import handle_event_trigger

User = get_user_model()

@receiver(post_save, sender=User)
def user_created_handler(sender, instance, created, **kwargs):
    if created:
        handle_event_trigger(
            event_type="new_user_created",
            payload={"user_id": instance.id}
        )

