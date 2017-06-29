from rest_framework.permissions import BasePermission
from rest_framework.compat import is_authenticated


class DeleteAdminOnly(BasePermission):
    def has_permission(self, request, view):
        return (
            request.user and (
                request.method == 'DELETE' and request.user.is_staff or
                request.method != 'DELETE' and is_authenticated(request.user)
            ))
