from rest_framework import serializers

from . import models


class EnvironmentTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.EnvironmentType
        fields = ('id', 'name', 'image_name', 'cmd', 'work_dir', 'container_path', 'container_port')


class EnvironmentResourceSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.EnvironmentResource
        fields = ('id', 'name', 'cpu', 'memory', 'active')


class ServerSerializer(serializers.ModelSerializer):
    status = serializers.CharField(read_only=False, required=False)

    class Meta:
        model = models.Server
        fields = ('id', 'name', 'created_at', 'environment_type', 'environment_resources', 'startup_script', 'config',
                  'status', 'connected')
        read_only_fields = ('created_at',)
        extra_kwargs = {'connected': {'allow_empty': True}}

    def create(self, validated_data):
        return models.Server.objects.create(
            project_id=self.context['view'].kwargs['project_pk'],
            created_by=self.context['request'].user,
            **validated_data
        )


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
