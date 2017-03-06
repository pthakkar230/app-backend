from rest_framework import viewsets, status

from base.views import NamespaceMixin
from .serializers import ProjectSerializer, FileSerializer, CollaboratorSerializer, SyncedResourceSerializer
from .models import Project, File, Collaborator, SyncedResource
from projects.tasks import sync_github


class ProjectViewSet(NamespaceMixin, viewsets.ModelViewSet):
    queryset = Project.objects.all()
    serializer_class = ProjectSerializer


class FileViewSet(NamespaceMixin, viewsets.ModelViewSet):
    queryset = File.objects.select_related('author', 'project')
    serializer_class = FileSerializer


class CollaboratorViewSet(NamespaceMixin, viewsets.ModelViewSet):
    queryset = Collaborator.objects.all()
    serializer_class = CollaboratorSerializer


class SyncedResourceViewSet(NamespaceMixin, viewsets.ModelViewSet):
    queryset = SyncedResource.objects.all()
    serializer_class = SyncedResourceSerializer

    def get_queryset(self):
        return super().get_queryset().filter(project_id=self.kwargs.get('project_pk'))

    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        response.status_code = status.HTTP_202_ACCEPTED
        return response

    def perform_create(self, serializer):
        super().perform_create(serializer)
        instance = serializer.instance
        sync_github.delay(
            str(instance.project.resource_root().joinpath(instance.folder)), self.request.user.pk, instance.project.pk,
            repo_url=instance.settings['repo_url'], branch=instance.settings.get('branch', 'master')
        )
