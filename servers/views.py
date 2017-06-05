from django.db.models import Sum, Count, Max, F
from django.db.models.functions import Coalesce, Now
from rest_framework import status, views, viewsets
from rest_framework.generics import get_object_or_404
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated

from base.views import ProjectMixin, UUIDRegexMixin, ServerMixin
from projects.models import Project
from projects.permissions import ProjectChildPermission
from .tasks import start_server, stop_server, terminate_server
from .permissions import ServerChildPermission, ServerActionPermission
from . import serializers, models


class ServerViewSet(viewsets.ModelViewSet):
    queryset = models.Server.objects.all()
    serializer_class = serializers.ServerSerializer
    permission_classes = (IsAuthenticated, ProjectChildPermission)
    filter_fields = ("name",)

    def get_queryset(self):
        return super().get_queryset().filter(project_id=self.kwargs.get('project_pk'))


@api_view(['post'])
@permission_classes([IsAuthenticated, ServerActionPermission])
def start(request, project_pk, pk):
    start_server.apply_async(
        args=[pk],
        task_id=str(request.action.pk)
    )
    return Response(status=status.HTTP_201_CREATED)


@api_view(['post'])
@permission_classes([IsAuthenticated, ServerActionPermission])
def stop(request, *args, **kwargs):
    stop_server.apply_async(
        args=[kwargs.get('pk')],
        task_id=str(request.action.pk)
    )
    return Response(status=status.HTTP_201_CREATED)


@api_view(['post'])
@permission_classes([IsAuthenticated, ServerActionPermission])
def terminate(request, *args, **kwargs):
    terminate_server.apply_async(
        args=[kwargs.get('pk')],
        task_id=str(request.action.pk)
    )
    return Response(status=status.HTTP_201_CREATED)


class ServerRunStatisticsViewSet(ProjectMixin, ServerMixin, viewsets.ModelViewSet):
    queryset = models.ServerRunStatistics.objects.all()
    serializer_class = serializers.ServerRunStatisticsSerializer
    permission_classes = (IsAuthenticated, ServerChildPermission)

    def list(self, request, *args, **kwargs):
        obj = self.queryset.filter(server_id=kwargs.get('server_pk')).aggregate(
            duration=Sum(Coalesce(F('stop'), Now()) - F('start')),
            runs=Count('id'),
            start=Max('start'),
            stop=Max('stop')
        )
        serializer = serializers.ServerRunStatisticsAggregatedSerializer(obj)
        return Response(serializer.data)


class ServerStatisticsViewSet(ProjectMixin, ServerMixin, viewsets.ModelViewSet):
    queryset = models.ServerStatistics.objects.all()
    serializer_class = serializers.ServerStatisticsSerializer
    permission_classes = (IsAuthenticated, ServerChildPermission)

    def list(self, request, *args, **kwargs):
        obj = self.queryset.filter(server_id=kwargs.get('server_pk')).aggregate(
            server_time=Sum(Coalesce(F('stop'), Now()) - F('start')),
            start=Max('start'),
            stop=Max('stop')
        )
        serializer = serializers.ServerStatisticsAggregatedSerializer(obj)
        return Response(serializer.data)


class SshTunnelViewSet(ProjectMixin, ServerMixin, viewsets.ModelViewSet):
    queryset = models.SshTunnel.objects.all()
    serializer_class = serializers.SshTunnelSerializer
    permission_classes = (IsAuthenticated, ServerChildPermission)


class EnvironmentResourceViewSet(UUIDRegexMixin, viewsets.ModelViewSet):
    queryset = models.EnvironmentResource.objects.all()
    serializer_class = serializers.EnvironmentResourceSerializer


class IsAllowed(views.APIView):
    """
    Checks if user is allowed to access model server
    """

    def get(self, request, **kwargs):
        token = request.META.get('HTTP_AUTHORIZATION', '').split(' ')[1]
        if Project.objects.cache().only('pk').filter(
                pk=kwargs.get('project_pk', ''), collaborators__auth_token__key=token).exists():
            return Response()
        return Response(status=status.HTTP_404_NOT_FOUND)


@api_view(['GET'], exclude_from_schema=True)
@permission_classes((AllowAny,))
def server_internal_details(request, server_pk):
    server = get_object_or_404(models.Server, pk=server_pk)
    data = {'server': '', 'container_name': ''}
    server_ip = server.get_private_ip()
    data = {
        'server': {service: '%s:%s' % (server_ip, port) for service, port in server.config.get('ports', {}).items()},
        'container_name': (server.container_name or '')
    }
    return Response(data)
