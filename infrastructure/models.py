import logging
from django.conf import settings
from django.db import models
from docker import Client
from docker.errors import APIError

from .managers import DockerHostQuerySet


logger = logging.getLogger(__name__)


class DockerHost(models.Model):
    AVAILABLE = 'Available'
    NOT_AVAILABLE = 'Not Available'
    ERROR = 'Error'

    name = models.CharField(max_length=100)
    ip = models.GenericIPAddressField()
    port = models.IntegerField(default=2375)
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='nodes')
    created_at = models.DateTimeField(auto_now_add=True)

    objects = DockerHostQuerySet.as_manager()

    def __str__(self):
        return self.name

    @property
    def url(self):
        return 'tcp://{self.ip}:{self.port}'.format(self=self)

    @property
    def client(self):
        return Client(base_url=self.url)

    @property
    def status(self):
        try:
            self.client.info()
        except APIError:
            logger.exception("Node status error")
            return self.NOT_AVAILABLE
        return self.AVAILABLE
