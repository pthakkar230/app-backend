from django.contrib.auth import get_user_model
from social_django.models import UserSocialAuth
from rest_framework import viewsets
from rest_framework.authtoken.models import Token
from rest_framework.decorators import api_view
from rest_framework.generics import get_object_or_404
from rest_framework.response import Response
from rest_framework.views import APIView

from base.views import UUIDRegexMixin
from utils import create_ssh_key

from .models import Email
from .serializers import UserSerializer, EmailSerializer, IntegrationSerializer, AuthTokenSerializer


class UserViewSet(UUIDRegexMixin, viewsets.ModelViewSet):
    queryset = get_user_model().objects.filter(is_active=True).select_related('profile')
    serializer_class = UserSerializer
    filter_fields = ('username',)

    def perform_destroy(self, instance):
        instance.active = False
        instance.save()


@api_view(['GET'])
def ssh_key(request, user_pk):
    user = get_object_or_404(get_user_model(), pk=user_pk)
    return Response(data={'key': user.profile.ssh_public_key()})


@api_view(['POST'])
def reset_ssh_key(request, user_pk):
    user = get_object_or_404(get_user_model(), pk=user_pk)
    create_ssh_key(user)
    return Response(data={'key': user.profile.ssh_public_key()})


@api_view(['GET'])
def api_key(request, user_pk):
    user = get_object_or_404(get_user_model(), pk=user_pk)
    return Response(data={'key': user.auth_token.key})


@api_view(['POST'])
def reset_api_key(request, user_pk):
    token = get_object_or_404(Token, user_id=user_pk)
    token.key = None
    token.save()
    return Response(data={'key': token.key})


class UserPKMixin(object):
    def get_queryset(self):
        return super().get_queryset().filter(user_id=self.kwargs.get('user_pk'))


class EmailViewSet(UserPKMixin, viewsets.ModelViewSet):
    queryset = Email.objects.all()
    serializer_class = EmailSerializer


class IntegrationViewSet(viewsets.ModelViewSet):
    queryset = UserSocialAuth.objects.all()
    serializer_class = IntegrationSerializer


class ObtainAuthToken(APIView):
    throttle_classes = ()
    permission_classes = ()
    serializer_class = AuthTokenSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer()
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']
        token, created = Token.objects.get_or_create(user=user)
        return Response({'token': token.key}, status=201)

    def get_serializer(self):
        return self.serializer_class(data=self.request.data)
