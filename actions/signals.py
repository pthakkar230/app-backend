from django.db.models.signals import post_save
from django.dispatch import receiver

from triggers.models import Trigger
from .models import Action


@receiver(post_save, sender=Action)
def trigger_action(sender, instance, created, **kwargs):
    if created:
        return
    for trigger in Trigger.objects.filter(cause=instance):
        trigger.dispatch()
