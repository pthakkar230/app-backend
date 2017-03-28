from rest_framework import serializers

from . import models


class EnvironmentResourceSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.EnvironmentResource
        fields = ('id', 'name', 'cpu', 'memory', 'active')


class ServerSerializer(serializers.ModelSerializer):
    status = serializers.CharField(read_only=False, required=False)

    class Meta:
        model = models.Server
        fields = ('id', 'name', 'created_at', 'image_name', 'environment_resources', 'startup_script', 'config',
                  'status', 'connected')
        read_only_fields = ('created_at',)
        extra_kwargs = {'connected': {'allow_empty': True, 'required': False}}

    def create(self, validated_data):
        config = validated_data.pop("config", {})
        if "script" in config and config["script"].endswith("py"):
            config["module"] = config["script"].split(".")[0]
        return models.Server.objects.create(
            project_id=self.context['view'].kwargs['project_pk'],
            created_by=self.context['request'].user,
            config=config,
            **validated_data
        )

    def update(self, instance, validated_data):
        if self.partial:
            config = validated_data.pop('config', {})
            instance.config = {**instance.config, **config}
        return super().update(instance, validated_data)


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
