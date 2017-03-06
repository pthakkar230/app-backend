from django.contrib.auth import get_user_model
from rest_framework import serializers
from rest_framework.authtoken.serializers import AuthTokenSerializer as RestAuthTokenSerializer
from rest_framework.authtoken.models import Token
from social_django.models import UserSocialAuth

from base.views import RequestUserMixin
from .models import UserProfile, Email


class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserProfile
        fields = ('avatar_url', 'bio', 'url', 'location', 'company', 'timezone')


class UserSerializer(serializers.ModelSerializer):
    profile = UserProfileSerializer()

    class Meta:
        model = get_user_model()
        fields = ('id', 'username', 'email', 'first_name', 'last_name', 'password', 'profile')
        extra_kwargs = {'password': {'write_only': True}}

    def create(self, validated_data):
        profile_data = validated_data.pop('profile')
        password = validated_data.pop('password')
        user = get_user_model()(**validated_data)
        user.set_password(password)
        user.save()
        profile = UserProfile(user=user, **profile_data)
        profile.save()
        Email.objects.create(user=user, address=validated_data['email'])
        Token.objects.create(user=user)
        return user

    def update(self, instance, validated_data):
        profile_data = validated_data.pop('profile')
        profile = UserProfile(user=instance, **profile_data)
        profile.save()
        password = validated_data.pop('password', None)
        if password is not None:
            instance.set_password(password)
        return super().update(instance, validated_data)


class EmailSerializer(RequestUserMixin, serializers.ModelSerializer):
    class Meta:
        model = Email
        fields = ('address', 'public', 'unsubscribed')


class IntegrationSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserSocialAuth
        fields = ('provider', 'extra_data')


class AuthTokenSerializer(RestAuthTokenSerializer):
    username = serializers.CharField(label="Username", write_only=True)
    password = serializers.CharField(label="Password", style={'input_type': 'password'}, write_only=True)
    token = serializers.CharField(label="Token", read_only=True)
