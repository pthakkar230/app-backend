from rest_framework import serializers
from rest_framework_jwt.serializers import JSONWebTokenSerializer


class JWTSerializer(JSONWebTokenSerializer):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields[self.username_field] = serializers.CharField(write_only=True)
        self.fields['token'] = serializers.CharField(read_only=True)
