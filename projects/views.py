from rest_framework import viewsets

from base.views import NamespaceMixin
from .serializers import ProjectSerializer, FileSerializer, CollaboratorSerializer
from .models import Project, File, ProjectUsers


class ProjectViewSet(NamespaceMixin, viewsets.ModelViewSet):
    queryset = Project.objects.all()
    serializer_class = ProjectSerializer


class FileViewSet(NamespaceMixin, viewsets.ModelViewSet):
    queryset = File.objects.select_related('author', 'project')
    serializer_class = FileSerializer


class CollaboratorViewSet(NamespaceMixin, viewsets.ModelViewSet):
    queryset = ProjectUsers.objects.all()
    serializer_class = CollaboratorSerializer
