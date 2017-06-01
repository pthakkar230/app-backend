from pathlib import Path

from django.conf import settings
from django.contrib.postgres.fields import JSONField
from django.db import models
from django.urls import reverse
from social_django.models import UserSocialAuth

from base.namespace import Namespace
from utils import alphanumeric


class ProjectQuerySet(models.QuerySet):
    def namespace(self, namespace):
        return self.filter(collaborator__user=namespace.object)


class Project(models.Model):
    name = models.CharField(max_length=50, validators=[alphanumeric])
    description = models.CharField(max_length=400, blank=True)
    private = models.BooleanField(default=True)
    last_updated = models.DateTimeField(auto_now=True)
    collaborators = models.ManyToManyField(settings.AUTH_USER_MODEL, through='Collaborator', related_name='projects')
    integrations = models.ManyToManyField(UserSocialAuth, through='SyncedResource', related_name='projects')

    objects = ProjectQuerySet.as_manager()

    class Meta:
        permissions = (
            ('write_project', "Write project"),
            ('read_project', "Read project"),
        )

    def __str__(self):
        return self.name

    def get_absolute_url(self, namespace: Namespace):
        return self.get_action_url(namespace, 'detail')

    def get_action_url(self, namespace, action):
        return reverse(
            'project-{}'.format(action),
            kwargs={'namespace': namespace.name, 'pk': str(self.id)}
        )

    @property
    def owner(self):
        return self.collaborator_set.filter(owner=True).first().user

    def get_owner_name(self):
        return self.owner.username

    def resource_root(self):
        return Path(settings.RESOURCE_DIR, self.get_owner_name(), str(self.pk))


class ProjectUsersQuerySet(models.QuerySet):
    def namespace(self, namespace):
        return self.filter(user=namespace.object)


class Collaborator(models.Model):
    project = models.ForeignKey(Project, models.CASCADE)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, models.CASCADE)
    joined = models.DateTimeField(auto_now_add=True)
    owner = models.BooleanField(default=False)

    objects = ProjectUsersQuerySet.as_manager()

    def get_absolute_url(self, namespace):
        return ""


class FileQuerySet(models.QuerySet):
    def namespace(self, namespace):
        return self.filter(author__username=namespace.name)


class File(models.Model):
    path = models.CharField(max_length=255)
    encoding = models.CharField(max_length=20)
    author = models.ForeignKey(settings.AUTH_USER_MODEL, models.DO_NOTHING, related_name='files')
    project = models.ForeignKey(Project, related_name='files')
    public = models.BooleanField(default=False)

    objects = FileQuerySet.as_manager()

    def __str__(self):
        return self.path

    def save(self, content='', **kwargs):
        if not self.sys_path.exists():
            self.sys_path.parent.mkdir(parents=True, exist_ok=True)
            self.sys_path.touch()
        if content:
            self.sys_path.write_bytes(content)
        super().save(**kwargs)

    def get_absolute_url(self, namespace):
        return reverse(
            'file-detail',
            kwargs={'namespace': namespace.name, 'project_pk': str(self.project.pk), 'pk': str(self.pk)}
        )

    @property
    def sys_path(self):
        return self.project.resource_root().joinpath(self.path)

    def content(self):
        return self.sys_path.read_bytes()

    def size(self):
        return self.sys_path.stat().st_size

    def delete(self, using=None, keep_parents=False):
        self.sys_path.unlink()
        return super().delete(using, keep_parents)


class SyncedResourceQuerySet(models.QuerySet):
    def namespace(self, namespace):
        return self.filter(project__collaborator__user=namespace.object)


class SyncedResource(models.Model):
    project = models.ForeignKey(Project, models.CASCADE, related_name='synced_resources')
    integration = models.ForeignKey(UserSocialAuth, models.CASCADE)
    folder = models.CharField(max_length=50)
    settings = JSONField(default={})

    objects = SyncedResourceQuerySet.as_manager()
