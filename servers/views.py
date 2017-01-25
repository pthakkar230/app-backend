from django.db.models import F
from django.db.models import Sum, Count, Max
from django.db.models.functions import Coalesce
from django.db.models.functions import Now
from rest_framework import viewsets
from rest_framework.response import Response

from base.views import ServersMixin, ProjectMixin, ServerMixin
from . import serializers, models


class WorkspaceViewSet(ServersMixin, viewsets.ModelViewSet):
    queryset = models.Workspace.objects.all()
    serializer_class = serializers.WorkspaceSerializer


class ModelViewSet(ServersMixin, viewsets.ModelViewSet):
    queryset = models.Model.objects.select_related('server')
    serializer_class = serializers.ModelSerializer


class JobViewSet(ServersMixin, viewsets.ModelViewSet):
    queryset = models.Job.objects.all()
    serializer_class = serializers.JobSerializer


class DataSourceViewSet(ServersMixin, viewsets.ModelViewSet):
    queryset = models.DataSource.objects.all()
    serializer_class = serializers.DataSourceSerializer


class ServerRunStatisticsViewSet(ProjectMixin, ServerMixin, viewsets.ModelViewSet):
    queryset = models.ServerRunStatistics.objects.all()
    serializer_class = serializers.ServerRunStatisticsSerializer

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


class EnvironmentTypeViewSet(viewsets.ModelViewSet):
    queryset = models.EnvironmentType.objects.all()
    serializer_class = serializers.EnvironmentTypeSerializer


class EnvironmentResourceViewSet(viewsets.ModelViewSet):
    queryset = models.EnvironmentResource.objects.all()
    serializer_class = serializers.EnvironmentResourceSerializer
