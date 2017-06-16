from rest_framework import permissions

from projects.models import Project
from projects.permissions import has_project_permission


class ServerChildPermission(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        return has_project_permission(request, obj.server.project)


class ServerActionPermission(permissions.BasePermission):
    def has_permission(self, request, view):
        if not view.kwargs:
            return True
        project = Project.objects.filter(pk=view.kwargs.get('project_pk')).first()
        if project is None:
            return False
        return has_project_permission(request, project)
