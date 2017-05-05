from django.conf import settings
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.contrib.postgres.fields import JSONField
from django.db import models
from django.urls import reverse
from requests import Session, Request

from base.namespace import Namespace


class ActionQuerySet(models.QuerySet):
    def get_or_create_action(self, filter_kwargs, defaults):
        try:
            action, created = self.get_or_create(
                **filter_kwargs,
                defaults=defaults
            )
        except Action.MultipleObjectsReturned:
            action = Action.objects.filter(**filter_kwargs).first()
        return action



class Action(models.Model):
    PENDING = 0
    IN_PROGRESS = 1
    CANCELING = 2
    CANCELLED = 3
    SUCCESS = 4
    FAILED = 5
    CREATED = 6

    STATE_CHOICES = (
        (PENDING, "Pending"),
        (IN_PROGRESS, "In Progress"),
        (CANCELING, "Canceling"),
        (CANCELLED, "Cancelled"),
        (SUCCESS, "Success"),
        (FAILED, "Failed"),
        (CREATED, "Created"),
    )

    path = models.CharField(max_length=255, blank=True)
    payload = JSONField(default={})
    action = models.CharField(max_length=100, db_index=True)
    method = models.CharField(max_length=7)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='actions', null=True, blank=True)
    user_agent = models.CharField(max_length=255)
    start_date = models.DateTimeField(auto_now_add=True)
    end_date = models.DateTimeField(blank=True, null=True)
    state = models.PositiveSmallIntegerField(choices=STATE_CHOICES)
    ip = models.GenericIPAddressField(null=True)
    content_type = models.ForeignKey(ContentType, models.SET_NULL, null=True)
    object_id = models.UUIDField(null=True)
    content_object = GenericForeignKey()
    can_be_cancelled = models.BooleanField(default=False)
    can_be_retried = models.BooleanField(default=False)
    is_user_action = models.BooleanField(default=True)

    objects = ActionQuerySet.as_manager()

    class Meta:
        ordering = ('-start_date',)

    def __str__(self):
        return self.action

    def get_absolute_url(self, namespace: Namespace):
        return reverse('action-detail', args=[str(self.id)])

    def get_state_display(self):
        return dict(self.STATE_CHOICES)[self.state]

    def content_object_url(self, namespace: Namespace):
        return self.content_object.get_absolute_url(namespace) if self.content_object else ''

    def dispatch(self, url='http://localhost'):
        url = '{}{}'.format(url, self.path)
        s = Session()
        headers = {'AUTHORIZATION': 'Token {}'.format(self.user.auth_token.key)}
        request = Request(self.method.upper(), url, json=self.payload, headers=headers).prepare()
        resp = s.send(request)
        resp.raise_for_status()
        return resp
