from rest_framework import serializers

from .models import Action


class ActionSerializer(serializers.ModelSerializer):
    state = serializers.CharField(source='get_state_display')
    object = serializers.SerializerMethodField(method_name='content_object_url')
    resource_uri = serializers.SerializerMethodField(method_name='get_object_url')
    user = serializers.CharField(source='user.username')

    class Meta:
        model = Action
        fields = ('id', 'resource_uri', 'payload', 'action', 'method', 'user', 'user_agent', 'start_date', 'end_date',
                  'state', 'ip', 'object', 'resource_uri', 'is_user_action', 'can_be_cancelled', 'can_be_retried',
                  'path')

    def get_object_url(self, obj):
        return obj.get_absolute_url(self.context['request'].namespace)

    def content_object_url(self, obj):
        return obj.content_object_url(self.context['request'].namespace)
