from django.contrib.contenttypes.models import ContentType
from django.urls import reverse
from rest_framework import serializers
from social_django.models import UserSocialAuth

from actions.models import Action
from .models import Trigger
from .slack import send_message


class TriggerActionSerializer(serializers.ModelSerializer):
    action_name = serializers.CharField()
    model = serializers.CharField(required=False)

    class Meta:
        model = Action
        fields = ('id', 'payload', 'method', 'model', 'object_id', 'action_name')

    def validate(self, data):
        if 'object_id' not in data:
            try:
                reverse(data['action_name'], kwargs={'namespace': self.context['request'].namespace.name})
            except:
                raise serializers.ValidationError('There is no action with name %s' % data['action_name'])
        return data

    def to_representation(self, obj):
        return {
            'id': str(obj.id),
            'payload': obj.payload,
            'method': obj.method,
        }


class WebhookSerializer(serializers.Serializer):
    url = serializers.URLField()
    config = serializers.JSONField(required=False)


class TriggerSerializer(serializers.ModelSerializer):
    cause = TriggerActionSerializer(required=False)
    effect = TriggerActionSerializer(required=False)
    webhook = WebhookSerializer(required=False)

    class Meta:
        model = Trigger
        fields = ('id', 'cause', 'effect', 'schedule', 'webhook')

    def create(self, validated_data):
        cause = self.create_action(validated_data.pop('cause', None))
        effect = self.create_action(validated_data.pop('effect', None))
        instance = Trigger(
            user=self.context['request'].user,
            cause=cause,
            effect=effect,
            **validated_data,
        )
        instance.save()
        return instance

    def create_action(self, validated_data):
        if not validated_data:
            return
        action_name = validated_data.pop('action_name')
        model = validated_data.pop('model', None)
        content_type = None
        content_object = None
        if model and validated_data.get('object_id'):
            content_type = ContentType.objects.filter(model=model).first()
            content_object = content_type.get_object_for_this_type(pk=validated_data['object_id'])
        if content_object:
            path = content_object.get_action_url(self.context['request'].namespace, action_name)
        else:
            path = reverse(action_name, kwargs={'namespace': self.context['request'].namespace.name})
        instance = Action.objects.filter(state=Action.CREATED, path=path, user=self.context['request'].user).first()
        if instance is None:
            instance = Action.objects.create(
                path=path,
                state=Action.CREATED,
                user=self.context['request'].user,
                content_type=content_type,
                is_user_action=False,
                **validated_data
            )
        return instance


class SlackMessageSerializer(serializers.Serializer):
    channel = serializers.CharField(allow_blank=True)
    text = serializers.CharField()

    def validate(self, data):
        user = self.context['request'].user
        social_auth = UserSocialAuth.objects.filter(user=user, provider='slack').first()
        if not social_auth:
            raise serializers.ValidationError("You need to connect your account with slack.")
        self._access_token = social_auth.access_token
        return data

    def send(self):
        send_message(
            self._access_token,
            text=self.validated_data['text'],
            channel=self.validated_data['channel'] or '#general'
        )
