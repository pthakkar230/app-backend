from django.shortcuts import render, redirect
from rest_framework import viewsets, status, permissions
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.response import Response

from base.views import NamespaceMixin
from projects.serializers import (ProjectSerializer, FileSerializer,
                                  CollaboratorSerializer, SyncedResourceSerializer,
                                  ProjectFileSerializer)
from projects.models import Project, File, Collaborator, SyncedResource
from projects.filters import FileFilter
from projects.permissions import ProjectPermission, ProjectChildPermission
from projects.tasks import sync_github
from projects.models import ProjectFile
from projects.forms import ProjectFileForm
import logging
log = logging.getLogger('projects')


class ProjectViewSet(NamespaceMixin, viewsets.ModelViewSet):
    queryset = Project.objects.all()
    serializer_class = ProjectSerializer
    permission_classes = (permissions.IsAuthenticated, ProjectPermission)
    filter_fields = ('private', 'name')
    ordering_fileds = ('name',)


class ProjectMixin(object):
    permission_classes = (permissions.IsAuthenticated, ProjectChildPermission)

    def get_queryset(self):
        return super().get_queryset().filter(project_id=self.kwargs.get('project_pk'))


class FileViewSet(ProjectMixin, viewsets.ModelViewSet):
    queryset = File.objects.select_related('author', 'project')
    serializer_class = FileSerializer
    filter_class = FileFilter


class CollaboratorViewSet(ProjectMixin, viewsets.ModelViewSet):
    queryset = Collaborator.objects.all()
    serializer_class = CollaboratorSerializer


class SyncedResourceViewSet(ProjectMixin, viewsets.ModelViewSet):
    queryset = SyncedResource.objects.all()
    serializer_class = SyncedResourceSerializer

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


class ProjectFileViewSet(ProjectMixin,
                         viewsets.ModelViewSet):
    queryset = ProjectFile.objects.all()
    serializer_class = ProjectFileSerializer
    parser_classes = (MultiPartParser, FormParser)

    def create(self, request, *args, **kwargs):

        files = request.FILES.get("file") or request.FILES.getlist("files")
        proj_files_to_serialize = []
        project_pk = request.data.get("project")
        # Not really sure how to handle this here
        public = request.data.get("public").lower() in ["true", "on"]

        for f in files:
            project = Project.objects.get(pk=project_pk)
            create_data = {'author': self.request.user,
                           'project': project,
                           'file': f,
                           'public': public}
            project_file = ProjectFile(**create_data)

            project_file.save()

            proj_files_to_serialize.append(project_file.pk)

        proj_files = ProjectFile.objects.filter(pk__in=proj_files_to_serialize)

        serializer = self.serializer_class(proj_files,
                                           context={'request': request},
                                           many=True)
        return Response(data=serializer.data,
                        status=status.HTTP_201_CREATED)


def project_file_upload(request):
    if request.method == "POST":
        form = ProjectFileForm(request.POST, request.FILES)

        if form.is_valid():
            # Should this be handled elsewhere?
            files = request.FILES.getlist("files")

            for f in files:
                project_pk = request.POST.get("project")
                project = Project.objects.get(pk=project_pk)
                log.debug(("project", project))

                proj_file = ProjectFile.objects.create(author=request.user,
                                                       project=project,
                                                       file=f,
                                                       public=request.POST.get("public", False))
                log.info("Created project file: {proj_file}".format(proj_file=proj_file))

            return redirect("project-file-upload", namespace=request.user.username)

    else:
        form = ProjectFileForm()

    return render(request, "projects/project_file_upload.html", {'form': form})
