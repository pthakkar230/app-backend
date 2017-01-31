import base64

from django.contrib.auth import get_user_model
from rest_framework import serializers

from users.serializers import UserSerializer
from .models import Project, File, Collaborator


class ProjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = Project
        fields = ('id', 'name', 'description', 'private', 'last_updated')

    def create(self, validated_data):
        project = super().create(validated_data)
        request = self.context['request']
        Collaborator.objects.create(project=project, owner=True, user=request.user)
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
        author = validated_data.pop('author')
        project = validated_data.pop('project')
        content = validated_data.pop('content')
        project_file = File(author=author, project=project, **validated_data)
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
    user = UserSerializer()

    class Meta:
        model = Collaborator
        fields = ('id', 'owner', 'joined', 'user')
