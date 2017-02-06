from rest_framework import serializers

from . import models


class ServerCreateMixin(object):
    def create(self, validated_data):
        server_data = validated_data.pop('server')
        view = self.context['view']
        user = self.context['request'].user
        project_pk = view.kwargs['project_pk']
        server = models.Server.objects.create(project_id=project_pk, created_by=user, **server_data)
        concrete = self.Meta.model.objects.create(server=server, **validated_data)
        return concrete

    def update(self, instance, validated_data):
        server_data = validated_data.pop('server', {})
        for key in server_data:
            setattr(instance.server, key, server_data[key])
        instance.server.save(update_fields=server_data.keys())
        return super().update(instance, validated_data)


class EnvironmentTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.EnvironmentType
        fields = ('id', 'name', 'image_name', 'cmd')


class EnvironmentResourceSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.EnvironmentResource
        fields = ('id', 'name', 'cpu', 'memory', 'active')


class ServerSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Server
        fields = ('id', 'name', 'created_at', 'environment_type', 'environment_resources', 'startup_script')
        read_only_fields = ('created_at',)


class ConcreteServerSerializer(ServerCreateMixin, serializers.ModelSerializer):
    server = ServerSerializer()

    class Meta:
        fields = ('server', 'status')


class WorkspaceSerializer(ConcreteServerSerializer):
    class Meta:
        model = models.Workspace
        fields = ConcreteServerSerializer.Meta.fields


class ModelSerializer(ConcreteServerSerializer):
    class Meta:
        model = models.Model
        fields = ConcreteServerSerializer.Meta.fields + ('script', 'method')


class JobSerializer(ConcreteServerSerializer):
    class Meta:
        model = models.Job
        fields = ConcreteServerSerializer.Meta.fields + ('script', 'method')


class DataSourceSerializer(ConcreteServerSerializer):
    class Meta:
        model = models.DataSource
        fields = ConcreteServerSerializer.Meta.fields


class ServerRunStatisticsSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.ServerRunStatistics
        fields = ('id', 'start', 'stop', 'exit_code', 'size', 'stacktrace')


class ServerRunStatisticsAggregatedSerializer(serializers.Serializer):
    duration = serializers.DurationField()
    runs = serializers.IntegerField()
    start = serializers.DateTimeField()
    stop = serializers.DateTimeField()


class ServerStatisticsSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.ServerStatistics
        fields = ('id', 'start', 'stop', 'size')


class ServerStatisticsAggregatedSerializer(serializers.Serializer):
    server_time = serializers.DurationField()
    start = serializers.DateTimeField()
    stop = serializers.DateTimeField()


class SshTunnelSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.SshTunnel
        fields = ('id', 'name', 'host', 'local_port', 'remote_port', 'endpoint', 'username')
