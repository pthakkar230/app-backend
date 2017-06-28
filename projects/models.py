from pathlib import Path

from django.conf import settings
from django.contrib.postgres.fields import JSONField
from django.db import models
from django.urls import reverse
from guardian.shortcuts import get_perms
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

    @property
    def permissions(self):
        project_perms = dict(Project._meta.permissions)
        return [perm for perm in get_perms(self.user, self.project) if perm in project_perms]


class FileQuerySet(models.QuerySet):
    def namespace(self, namespace):
        return self.filter(author__username=namespace.name)


def user_project_directory_path(instance, filename):
    return "{usr}/{proj}/{fname}/".format(usr=instance.author.username,
                                          proj=instance.project.pk,
                                          fname=filename)


class ProjectFile(models.Model):
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.DO_NOTHING)
    project = models.ForeignKey(Project, related_name="project_files")
    file = models.FileField(upload_to=user_project_directory_path)
    public = models.BooleanField(default=False)

    objects = FileQuerySet.as_manager()

    def __str__(self):
        return "{auth};{proj};{name}".format(auth=self.author.username,
                                             proj=self.project.name,
                                             name=self.file.name)

    def get_absolute_url(self, namespace):
        return reverse(
            'file-detail',
            kwargs={'namespace': namespace.name, 'project_pk': str(self.project.pk), 'pk': str(self.pk)}
        )

    def delete(self, using=None, keep_parents=False):
        self.file.delete()
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
