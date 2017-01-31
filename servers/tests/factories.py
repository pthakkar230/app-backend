import random
import factory
from django.utils import timezone
from datetime import timedelta

from projects.tests.factories import ProjectFactory
from servers import models
from users.tests.factories import UserFactory


class EnvironmentTypeFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.EnvironmentType

    name = factory.Sequence(lambda n: 'project_{}'.format(n))
    image_name = '3blades/ipython-notebook'
    cmd = ''


class EnvironmentResourcesFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.EnvironmentResource

    name = factory.Sequence(lambda n: 'resource_{}'.format(n))
    cpu = random.randint(1, 9)
    memory = random.randint(4, 256)
    active = True


class ServerFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.Server

    private_ip = '127.0.0.1'
    public_ip = '127.0.0.1'
    name = factory.Faker('name')
    environment_type = factory.SubFactory(EnvironmentTypeFactory)
    environment_resources = factory.SubFactory(EnvironmentResourcesFactory)
    project = factory.SubFactory(ProjectFactory)
    created_by = factory.SubFactory(UserFactory)


class WorkspaceFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.Workspace

    server = factory.SubFactory(ServerFactory)


class ModelFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.Model

    server = factory.SubFactory(ServerFactory)
    script = 'test.py'
    method = 'test'


class JobFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.Job

    server = factory.SubFactory(ServerFactory)
    script = 'test.py'
    method = 'test'
    schedule = '* * * * *'


class ServerRunStatisticsFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.ServerRunStatistics

    server = factory.SubFactory(ServerFactory)
    start = timezone.now() - timedelta(hours=1)
    stop = timezone.now()
    exit_code = 0


class ServerStatisticsFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.ServerStatistics

    server = factory.SubFactory(ServerFactory)
    start = timezone.now() - timedelta(hours=1)
    stop = timezone.now()
    size = 0

class SSHTunnelFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.SshTunnel

    name = factory.Faker('name')
    host = factory.Faker('domain_name')
    local_port = factory.Faker('pyint')
    endpoint = factory.Faker('domain_name')
    remote_port = factory.Faker('pyint')
    username = factory.Faker('user_name')
    server = factory.SubFactory(ServerFactory)


class DataSourceFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.DataSource

    server = factory.SubFactory(ServerFactory)
