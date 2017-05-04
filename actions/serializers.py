from django.contrib.contenttypes.models import ContentType
from rest_framework import serializers

from base.namespace import Namespace
from .models import Action


class ActionSerializer(serializers.ModelSerializer):
    state = serializers.CharField(source='get_state_display')
    object = serializers.SerializerMethodField(method_name='content_object_url')
    resource_uri = serializers.SerializerMethodField(method_name='get_object_url')
    user = serializers.CharField(source='user.username', required=False)
    content_type = serializers.CharField(source='content_type.model', required=False, write_only=True)

    class Meta:
        model = Action
        fields = ('id', 'resource_uri', 'payload', 'action', 'method', 'user', 'user_agent', 'start_date', 'end_date',
                  'state', 'ip', 'object', 'resource_uri', 'is_user_action', 'can_be_cancelled', 'can_be_retried',
                  'path', 'object_id', 'content_type')
        extra_kwargs = {
            'object_id': {'write_only': True, 'required': False},
        }

    def create(self, validated_data):
        state = validated_data.pop('get_state_display', 0)
        content_type = validated_data.pop('content_type', None)
        user = self.context['request'].user
        instance = Action(user=user, state=int(state), **validated_data)
        if content_type and 'object_id' in validated_data:
            instance.content_type = ContentType.objects.filter(**content_type).first()
            if not instance.path:
                namespace = Namespace.from_name(user.username)
                obj = instance.content_type.get_object_for_this_type(pk=validated_data['object_id'])
                instance.path = obj.get_absolute_url(namespace)
        instance.save()
        return instance

    def get_object_url(self, obj):
        return obj.get_absolute_url(self.context['request'].namespace)

    def content_object_url(self, obj):
        return obj.content_object_url(self.context['request'].namespace)
