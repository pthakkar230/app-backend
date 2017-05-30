from rest_framework import serializers
from .models import DockerHost


class DockerHostSerializer(serializers.ModelSerializer):
    class Meta:
        model = DockerHost
        fields = ('id', 'name', 'ip', 'port', 'status')

    def create(self, validated_data):
        return DockerHost.objects.create(
            owner=self.context['request'].user,
            **validated_data
        )
