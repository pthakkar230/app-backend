from django.conf import settings
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.contrib.postgres.fields import JSONField
from django.db import models
from django.urls import reverse

from base.namespace import Namespace


class Action(models.Model):
    PENDING = 0
    IN_PROGRESS = 1
    CANCELING = 2
    CANCELLED = 3
    SUCCESS = 4
    FAILED = 5

    STATE_CHOICES = (
        (PENDING, "Pending"),
        (IN_PROGRESS, "In Progress"),
        (CANCELING, "Canceling"),
        (CANCELLED, "Cancelled"),
        (SUCCESS, "Success"),
        (FAILED, "Failed"),
    )

    path = models.CharField(max_length=255)
    payload = JSONField(default={})
    action = models.CharField(max_length=100, db_index=True)
    method = models.CharField(max_length=7)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='actions', null=True)
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

    class Meta:
        ordering = ('-start_date',)

    def get_absolute_url(self, namespace: Namespace):
        return reverse('action-detail', args=[str(self.id)])

    def get_state_display(self):
        return dict(self.STATE_CHOICES)[self.state]

    def content_object_url(self, namespace: Namespace):
        return self.content_object.get_absolute_url(namespace) if self.content_object else ''
