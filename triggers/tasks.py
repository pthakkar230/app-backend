from celery import shared_task

from .models import Trigger


@shared_task()
def dispatch_trigger(trigger_id, url='http://localhost'):
    trigger = Trigger.objects.get(pk=trigger_id)
    trigger.dispatch(url=url)
