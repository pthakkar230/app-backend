from django.contrib.auth import get_user_model
from haystack.query import SearchQuerySet, EmptySearchQuerySet
from social_django.models import UserSocialAuth
from rest_framework import viewsets
from rest_framework.authtoken.models import Token
from rest_framework.decorators import api_view
from rest_framework.generics import get_object_or_404, CreateAPIView
from rest_framework.mixins import ListModelMixin
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from base.permissions import DeleteAdminOnly
from base.views import UUIDRegexMixin
from utils import create_ssh_key

from .filters import UserSearchFilter
from .models import Email
from .serializers import UserSerializer, EmailSerializer, IntegrationSerializer, AuthTokenSerializer

User = get_user_model()


class UserViewSet(UUIDRegexMixin, viewsets.ModelViewSet):
    queryset = User.objects.filter(is_active=True).select_related('profile')
    serializer_class = UserSerializer
    filter_fields = ('username', 'email')
    permission_classes = (IsAuthenticated, DeleteAdminOnly)

    def perform_destroy(self, instance):
        instance.is_active = False
        instance.save()


class UserSearchView(ListModelMixin, viewsets.GenericViewSet):
    serializer_class = UserSerializer
    filter_class = UserSearchFilter

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    def get_queryset(self):
        qs = EmptySearchQuerySet()
        if 'q' in self.request.GET:
            qs = SearchQuerySet().filter(content=self.request.GET.get('q', ''))
        return qs


class RegisterView(CreateAPIView):
    """
    User register
    """
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = ()
    authentication_classes = ()


@api_view(['GET'])
def ssh_key(request, user_pk):
    user = get_object_or_404(User, pk=user_pk)
    return Response(data={'key': user.profile.ssh_public_key()})


@api_view(['POST'])
def reset_ssh_key(request, user_pk):
    user = get_object_or_404(User, pk=user_pk)
    create_ssh_key(user)
    return Response(data={'key': user.profile.ssh_public_key()})


@api_view(['GET'])
def api_key(request, user_pk):
    user = get_object_or_404(User, pk=user_pk)
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
