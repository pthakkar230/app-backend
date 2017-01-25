import os

from django.conf import settings
from django.contrib.postgres.fields import HStoreField
from django.db import models
from django.utils.functional import cached_property
from django_redis import get_redis_connection

from base.models import HashIDMixin
from servers.managers import ServerQuerySet
from servers.spawners import DockerSpawner
from utils import encode_id


class ServerDataSources(models.Model):
    server = models.ForeignKey('Server')
    data_source = models.ForeignKey('DataSource')

    class Meta:
        db_table = 'server_data_sources'
        unique_together = (('server', 'data_source'),)


class Server(models.Model):
    private_ip = models.CharField(max_length=19)
    public_ip = models.CharField(max_length=19)
    port = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    environment_type = models.ForeignKey('EnvironmentType')
    name = models.CharField(max_length=50)
    container_id = models.CharField(max_length=100, blank=True, null=True)
    environment_resources = models.ForeignKey('EnvironmentResource')
    type = models.CharField(max_length=1, blank=True, null=True)
    env_vars = HStoreField(blank=True, null=True)
    startup_script = models.CharField(max_length=50, blank=True, null=True)
    data_sources = models.ManyToManyField('DataSource', through=ServerDataSources, related_name='servers')
    project = models.ForeignKey('projects.Project', related_name='servers', null=True)

    class Meta:
        db_table = 'servers'

    def __str__(self):
        return self.name


class EnvironmentType(HashIDMixin, models.Model):
    name = models.CharField(unique=True, max_length=20)
    image_name = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True, null=True)
    cmd = models.CharField(max_length=512, blank=True, null=True)
    description = models.CharField(max_length=200, blank=True, null=True)
    work_dir = models.CharField(max_length=250, blank=True, null=True)
    env_vars = HStoreField(blank=True, null=True)
    container_path = models.CharField(max_length=250, blank=True, null=True)
    container_port = models.IntegerField(blank=True, null=True)
    active = models.BooleanField(default=True)
    urldoc = models.CharField(max_length=200, blank=True, null=True)
    type = models.CharField(max_length=1, blank=True, null=True)
    usage = HStoreField(blank=True, null=True)

    class Meta:
        db_table = 'environment_type'

    def __str__(self):
        return self.name


class EnvironmentResource(HashIDMixin, models.Model):
    name = models.CharField(unique=True, max_length=50)
    cpu = models.IntegerField()
    memory = models.IntegerField()
    description = models.CharField(max_length=200, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True, blank=True, null=True)
    active = models.BooleanField()
    storage_size = models.IntegerField(blank=True, null=True)

    class Meta:
        db_table = 'environment_resources'

    def __str__(self):
        return self.name


class ServerModelBase(HashIDMixin, models.Model):
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

    class Meta:
        abstract = True

    def __str__(self):
        return self.server.name

    @cached_property
    def hashid(self):
        return encode_id(self.server_id)

    @property
    def container_name(self):
        return self.CONTAINER_NAME_FORMAT.format(self.hashid, self.server.environment_type.name)

    def get_start_kwargs(self):
        return {}

    @property
    def volume_path(self):
        return os.path.join(settings.RESOURCE_DIR, self.server.project.get_owner_name(), self.server.project.hashid)

    @property
    def state_cache_key(self):
        return '{}{}'.format(self.SERVER_STATE_CACHE_PREFIX, self.hashid)

    @property
    def status(self):
        cache = get_redis_connection("default")
        status = cache.hget(self.state_cache_key, "status")
        if status is None:
            spawner = DockerSpawner(self)
            status = spawner.status()
            cache.hset(self.state_cache_key, "status", status)
        return status.decode()

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


class Workspace(ServerModelBase):
    server = models.OneToOneField(Server, primary_key=True)

    class Meta:
        db_table = 'workspace'


class Job(ServerModelBase):
    server = models.OneToOneField(Server, primary_key=True)
    script = models.CharField(max_length=255)
    method = models.CharField(max_length=50, blank=True, null=True)
    auto_restart = models.BooleanField(default=False)
    schedule = models.CharField(max_length=20, blank=True, null=True)

    class Meta:
        db_table = 'jobs'

    def get_start_kwargs(self):
        return {
            'command': self.server.environment_type.cmd.format(job=self,
                                                               script_name_len=len(self.script.split('.')[0])),
            'restart': {"Name": "on-failure", "MaximumRetryCount": 2} if self.auto_restart else None
        }


class Model(ServerModelBase):
    server = models.OneToOneField(Server, primary_key=True)
    script = models.CharField(max_length=255)
    method = models.CharField(max_length=50, blank=True, null=True)

    class Meta:
        db_table = 'models'

    def get_start_kwargs(self):
        return {
            'command': self.server.environment_type.cmd.format(model=self,
                                                               script_name_len=len(self.script.split('.')[0]))
        }


class DataSource(ServerModelBase):
    server = models.OneToOneField(Server, primary_key=True)

    class Meta:
        db_table = 'data_source'


class ServerRunStatistics(models.Model):
    server = models.ForeignKey(Server, blank=True, null=True)
    start = models.DateTimeField(blank=True, null=True)
    stop = models.DateTimeField(blank=True, null=True)
    exit_code = models.IntegerField(blank=True, null=True)
    size = models.BigIntegerField(blank=True, null=True)
    stacktrace = models.TextField(blank=True, null=True)

    class Meta:
        db_table = 'server_run_statistics'


class ServerStatistics(models.Model):
    start = models.DateTimeField(blank=True, null=True)
    stop = models.DateTimeField(blank=True, null=True)
    size = models.BigIntegerField(blank=True, null=True)
    server = models.ForeignKey(Server, blank=True, null=True)

    class Meta:
        db_table = 'server_statistics'


class SshTunnel(models.Model):
    name = models.CharField(max_length=50)
    host = models.CharField(max_length=50)
    local_port = models.IntegerField()
    endpoint = models.CharField(max_length=50)
    remote_port = models.IntegerField()
    username = models.CharField(max_length=32)
    server = models.ForeignKey(Server, models.CASCADE, null=True)

    class Meta:
        db_table = 'ssh_tunnel'
        unique_together = (('name', 'server'),)
