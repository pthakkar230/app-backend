import base64

from django.conf import settings
from django.contrib.auth import get_user_model
from django.db.models import Q
from pathlib import Path
from rest_framework import serializers
from social_django.models import UserSocialAuth

from .models import Project, File, Collaborator, SyncedResource


class ProjectSerializer(serializers.ModelSerializer):
    owner = serializers.CharField(source='get_owner_name', read_only=True)
    collaborators = serializers.StringRelatedField(many=True, required=False)

    class Meta:
        model = Project
        fields = ('id', 'name', 'description', 'private', 'last_updated', 'owner', 'collaborators')

    def create(self, validated_data):
        collaborators = validated_data.pop('collaborators', [])
        project = super().create(validated_data)
        request = self.context['request']
        Collaborator.objects.create(project=project, owner=True, user=request.user)
        Path(settings.RESOURCE_DIR, project.get_owner_name(), str(project.pk)).mkdir(parents=True, exist_ok=True)
        return project


class FileAuthorSerializer(serializers.ModelSerializer):
    class Meta:
        model = get_user_model()
        fields = ('id', 'email', 'username')
        read_only_fields = ('email', 'username')


class Base64CharField(serializers.CharField):
    def to_representation(self, value):
        return base64.b64encode(value)

    def to_internal_value(self, data):
        return base64.b64decode(data)


class FileSerializer(serializers.ModelSerializer):
    content = Base64CharField()
    size = serializers.IntegerField(read_only=True)

    class Meta:
        model = File
        fields = ('id', 'path', 'encoding', 'public', 'content', 'size', 'author', 'project')

    def create(self, validated_data):
        content = validated_data.pop('content')
        project_file = File(**validated_data)
        project_file.save(content=content)
        return project_file

    def update(self, instance, validated_data):
        content = validated_data.pop('content')
        instance.author = validated_data.pop('author')
        instance.project = validated_data.pop('project')
        old_path = instance.sys_path
        for field in validated_data:
            setattr(instance, field, validated_data[field])
        if not instance.sys_path.parent.exists():
            instance.sys_path.parent.mkdir(parents=True, exist_ok=True)
        old_path.rename(instance.sys_path)
        instance.save(content=content)
        return instance


class CollaboratorSerializer(serializers.ModelSerializer):
    email = serializers.CharField(source='user.email', read_only=True)
    member = serializers.CharField(write_only=True)

    class Meta:
        model = Collaborator
        fields = ('id', 'owner', 'joined', 'email', 'member')

    def create(self, validated_data):
        member = validated_data.pop('member')
        project_id = self.context['view'].kwargs['project_pk']
        owner = validated_data.get("owner", False)
        if owner is True:
            Collaborator.objects.filter(project_id=project_id).update(owner=False)
        user = get_user_model().objects.filter(Q(username=member) | Q(email=member)).first()
        return Collaborator.objects.create(user=user, project_id=project_id, **validated_data)


class SyncedResourceSerializer(serializers.ModelSerializer):
    provider = serializers.CharField(source='integration.provider')

    class Meta:
        model = SyncedResource
        fields = ('folder', 'settings', 'provider')

    def create(self, validated_data):
        provider = validated_data.pop('integration').get('provider')
        instance = SyncedResource(**validated_data)
        integration = UserSocialAuth.objects.filter(user=self.context['request'].user, provider=provider).first()
        instance.integration = integration
        instance.project_id = self.context['view'].kwargs['project_pk']
        instance.save()
        return instance
