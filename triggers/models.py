import requests
from collections import defaultdict
from django.db import models
from django.conf import settings
from django.contrib.postgres.fields import JSONField

from actions.models import Action
from utils import copy_model


class TriggerQuerySet(models.QuerySet):
    def namespace(self, namespace):
        return self.filter(user=namespace.object)


class Trigger(models.Model):
    ALLOWED_ACTIONS = ['server-stop', 'server-start', 'server-terminate', 'send-slack-message']

    name = models.CharField(max_length=50, blank=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='triggers')
    cause = models.ForeignKey('actions.Action', related_name='cause_triggers', blank=True, null=True)
    effect = models.ForeignKey('actions.Action', related_name='effect_triggers', blank=True, null=True)
    schedule = models.CharField(max_length=20, blank=True, help_text='Cron schedule')
    webhook = JSONField(default=defaultdict(str))

    objects = TriggerQuerySet.as_manager()

    def __str__(self):
        if self.cause:
            return '{} -> {}'.format(self.cause, self.effect)
        return '{}: {}'.format(self.effect, self.schedule)

    def dispatch(self, url='http://localhost'):
        new_effect = copy_model(self.effect)
        self._set_action_state(new_effect, Action.CREATED)
        new_cause = copy_model(self.cause)
        self._set_action_state(new_cause, Action.CREATED)
        if self.effect:
            self.effect.dispatch(url)
        if self.webhook and self.webhook.get('url'):
            resp = requests.post(self.webhook['url'], json=self.webhook.get('config', {}))
            resp.raise_for_status()
        self.effect = new_effect
        self.cause = new_cause
        self.save()

    @staticmethod
    def _set_action_state(action, state):
        if action:
            action.state = state
            action.save()
