import base64
from django.conf import settings
from django.contrib.auth import get_user_model
from django.db.models import Q
from guardian.shortcuts import assign_perm
from pathlib import Path
from rest_framework import serializers
from social_django.models import UserSocialAuth

from base.serializers import SearchSerializerMixin
from projects.models import (Project, Collaborator,
                             SyncedResource, ProjectFile)

User = get_user_model()


class ProjectSerializer(SearchSerializerMixin, serializers.ModelSerializer):
    owner = serializers.CharField(source='get_owner_name', read_only=True)
    collaborators = serializers.StringRelatedField(many=True, required=False)

    class Meta:
        model = Project
        fields = ('id', 'name', 'description', 'private', 'last_updated', 'owner', 'collaborators')

    def create(self, validated_data):
        collaborators = validated_data.pop('collaborators', [])
        project = super().create(validated_data)
        request = self.context['request']
        if request.user.is_staff:
            user = request.namespace.object
        else:
            user = request.user
        Collaborator.objects.create(project=project, owner=True, user=user)
        assign_perm('write_project', request.user, project)
        Path(settings.RESOURCE_DIR, project.get_owner_name(), str(project.pk)).mkdir(parents=True, exist_ok=True)
        return project


class FileAuthorSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'email', 'username')
        read_only_fields = ('email', 'username')


class Base64CharField(serializers.CharField):
    def to_representation(self, value):
        return base64.b64encode(value)

    def to_internal_value(self, data):
        return base64.b64decode(data)


class ProjectFileSerializer(serializers.ModelSerializer):
    base64_data = Base64CharField(required=False)
    name = serializers.CharField(required=False)

    class Meta:
        model = ProjectFile
        fields = ("id", "project", "file", "public", "base64_data", "name")
        read_only_fields = ("author",)

    def create(self, validated_data):
        project = Project.objects.get(pk=validated_data.pop("project"))
        proj_file = ProjectFile(project=project,
                                **validated_data)
        proj_file.save()
        return proj_file

    def update(self, instance, validated_data):

        for key in validated_data:
            if key == "file":
                # Sort of sketches me out.
                instance.file.delete()
            setattr(instance, key, validated_data[key])

        instance.save()
        return instance


class CollaboratorSerializer(serializers.ModelSerializer):
    email = serializers.CharField(source='user.email', read_only=True)
    username = serializers.CharField(source='user.username', read_only=True)
    first_name = serializers.CharField(source='user.first_name', read_only=True)
    last_name = serializers.CharField(source='user.last_name', read_only=True)
    member = serializers.CharField(write_only=True)
    permissions = serializers.MultipleChoiceField(choices=Project._meta.permissions)

    class Meta:
        model = Collaborator
        fields = ('id', 'owner', 'joined', 'username', 'email', 'first_name', 'last_name', 'member', 'permissions')

    def validate_member(self, value):
        if not User.objects.filter(Q(username=value) | Q(email=value)).exists():
            raise serializers.ValidationError("User %s does not exists" % value)

    def create(self, validated_data):
        permissions = validated_data.pop('permissions', ['read_project'])
        member = validated_data.pop('member')
        project_id = self.context['view'].kwargs['project_pk']
        project = Project.objects.get(pk=project_id)
        owner = validated_data.get("owner", False)
        if owner is True:
            Collaborator.objects.filter(project_id=project_id).update(owner=False)
        user = User.objects.filter(Q(username=member) | Q(email=member)).first()
        for permission in permissions:
            assign_perm(permission, user, project)
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
