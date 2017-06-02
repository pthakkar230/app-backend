from rest_framework import permissions


def has_project_permission(request, project):
    if project.private is False and request.method == 'GET':
        return True
    if not request.user.has_perm('read_project', project) and request.method == 'GET':
        return False
    if not request.user.has_perm('write_project', project) and request.method != 'GET':
        return False
    return True


class ProjectPermission(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        return has_project_permission(request, obj)


class ProjectChildPermission(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        return has_project_permission(request, obj.project)
