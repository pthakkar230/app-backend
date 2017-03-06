import os

from django.conf import settings
from django.contrib.postgres.fields import HStoreField, JSONField
from django.db import models
from django.urls import reverse
from django_redis import get_redis_connection

from base.namespace import Namespace
from .managers import ServerQuerySet
from .spawners import DockerSpawner


class Server(models.Model):
    # statuses
    STOPPED = "Stopped"
    STOPPING = "Stopping"
    RUNNING = "Running"
    PENDING = "Pending"
    LAUNCHING = "Launching"
    ERROR = "Error"
    TERMINATED = "Terminated"
    TERMINATING = "Terminating"

    SERVER_STATE_CACHE_PREFIX = 'server_state_'

    STOP = 'stop'
    START = 'start'
    TERMINATE = 'terminate'

    CONTAINER_NAME_FORMAT = "server_{}_{}"

    objects = ServerQuerySet.as_manager()

    private_ip = models.CharField(max_length=19)
    public_ip = models.CharField(max_length=19)
    port = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    environment_type = models.ForeignKey('EnvironmentType')
    name = models.CharField(max_length=50)
    container_id = models.CharField(max_length=100, blank=True)
    environment_resources = models.ForeignKey('EnvironmentResource')
    env_vars = HStoreField(default={})
    startup_script = models.CharField(max_length=50, blank=True)
    project = models.ForeignKey('projects.Project', related_name='servers')
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='servers')
    config = JSONField(default={})
    auto_restart = models.BooleanField(default=False)
    connected = models.ManyToManyField('self', related_name='servers')

    def __str__(self):
        return self.name

    def get_absolute_url(self, namespace):
        return reverse(
            'server-detail',
            kwargs={'namespace': namespace.name, 'project_pk': str(self.project.pk), 'pk': str(self.pk)}
        )

    @property
    def container_name(self):
        return self.CONTAINER_NAME_FORMAT.format(self.pk, self.environment_type.name)

    @property
    def volume_path(self):
        return os.path.join(settings.RESOURCE_DIR, self.project.get_owner_name(), str(self.project.pk))

    @property
    def state_cache_key(self):
        return '{}{}'.format(self.SERVER_STATE_CACHE_PREFIX, self.pk)

    @property
    def status(self):
        cache = get_redis_connection("default")
        status = cache.hget(self.state_cache_key, "status")
        if status is None:
            spawner = DockerSpawner(self)
            status = spawner.status()
            cache.hset(self.state_cache_key, "status", status)
        return status.decode() if isinstance(status, bytes) else status

    @status.setter
    def status(self, value):
        if self.status != value:
            cache = get_redis_connection("default")
            cache.hset(self.state_cache_key, "status", value)

    def needs_update(self):
        cache = get_redis_connection("default")
        return bool(cache.hexists(self.state_cache_key, "update"))

    @property
    def update_message(self):
        cache = get_redis_connection("default")
        return cache.hget(self.state_cache_key, "update").decode()

    @update_message.setter
    def update_message(self, value):
        cache = get_redis_connection("default")
        cache.hset(self.state_cache_key, "update", value)

    @update_message.deleter
    def update_message(self):
        cache = get_redis_connection("default")
        cache.hdel(self.state_cache_key, "update")

    def script_name_len(self):
        return len(self.config.get('script', '').split('.')[0])

    def is_running(self):
        return self.status == self.RUNNING


class EnvironmentType(models.Model):
    name = models.CharField(unique=True, max_length=20)
    image_name = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)
    cmd = models.CharField(max_length=512, blank=True)
    description = models.CharField(max_length=200, blank=True)
    work_dir = models.CharField(max_length=250, blank=True)
    env_vars = HStoreField(null=True)
    container_path = models.CharField(max_length=250, blank=True)
    container_port = models.IntegerField(blank=True, null=True)
    active = models.BooleanField(default=True)
    urldoc = models.CharField(max_length=200, blank=True)
    usage = HStoreField(null=True)

    def __str__(self):
        return self.name

    def get_absolute_url(self, namespace: Namespace):
        return reverse('environmenttype-detail', kwargs={'namespace': namespace.name, 'pk': str(self.pk)})


class EnvironmentResource(models.Model):
    name = models.CharField(unique=True, max_length=50)
    cpu = models.IntegerField()
    memory = models.IntegerField()
    description = models.CharField(max_length=200, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    active = models.BooleanField()
    storage_size = models.IntegerField(blank=True, null=True)

    def __str__(self):
        return self.name

    def get_absolute_url(self, namespace: Namespace):
        return reverse('environmentresource-detail', kwargs={'namespace': namespace.name, 'pk': str(self.pk)})


class ServerRunStatistics(models.Model):
    server = models.ForeignKey(Server, null=True)
    start = models.DateTimeField(blank=True, null=True)
    stop = models.DateTimeField(blank=True, null=True)
    exit_code = models.IntegerField(blank=True, null=True)
    size = models.BigIntegerField(blank=True, null=True)
    stacktrace = models.TextField(blank=True)


class ServerStatistics(models.Model):
    start = models.DateTimeField(blank=True, null=True)
    stop = models.DateTimeField(blank=True, null=True)
    size = models.BigIntegerField(blank=True, null=True)
    server = models.ForeignKey(Server, null=True)


class SshTunnel(models.Model):
    name = models.CharField(max_length=50)
    host = models.CharField(max_length=50)
    local_port = models.IntegerField()
    endpoint = models.CharField(max_length=50)
    remote_port = models.IntegerField()
    username = models.CharField(max_length=32)
    server = models.ForeignKey(Server, models.CASCADE)

    class Meta:
        unique_together = (('name', 'server'),)
