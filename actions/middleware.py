import logging
import ujson

from django.contrib.auth import get_user_model
from django.http import HttpRequest, HttpResponse
from django.utils import timezone
from rest_framework import status
from rest_framework.views import get_view_name
from rest_framework_jwt.serializers import VerifyJSONWebTokenSerializer
from rest_framework.authtoken.models import Token

from .models import Action

log = logging.getLogger('projects')

User = get_user_model()


def get_user_from_jwt(token):
    serializer = VerifyJSONWebTokenSerializer(data={'token': token})
    if serializer.is_valid():
        return serializer.validated_data.get('user')


def get_user_from_simple_token(token):
    token_obj = Token.objects.filter(key=token).first()
    if token_obj:
        return token_obj.user


def get_user_from_token_header(request):
    token_header = request.META.get('HTTP_AUTHORIZATION')
    if not token_header or ' ' not in token_header:
        return
    prefix, token = token_header.split()
    if prefix == 'JWT':
        return get_user_from_jwt(token)
    elif prefix == 'Token':
        return get_user_from_simple_token(token)


class ActionMiddleware(object):
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:
        start = timezone.now()
        path = request.get_full_path()
        try:
            body = ujson.loads(request.body)
        except ValueError:
            body = {}
        filter_kwargs = dict(
            path=path,
            user=get_user_from_token_header(request),
            state=Action.CREATED,
        )
        defaults = dict(
            action=self._get_action_name(request),
            method=request.method.lower(),
            user_agent=request.META.get('HTTP_USER_AGENT', ''),
            start_date=start,
            payload=body,
            ip=self._get_client_ip(request),
            state=Action.PENDING,
        )
        action = Action.objects.get_or_create_action(filter_kwargs, defaults)
        request.action = action

        response = self.get_response(request)  # type: HttpResponse

        action.refresh_from_db()
        self._set_action_state(action, response.status_code)
        self._set_action_object(action, request, response)
        action.end_date = timezone.now()
        if action.user is None:
            action.user = request.user if isinstance(request.user, User) else None
        action.save()
        return response

    @staticmethod
    def _set_action_state(action, status_code):
        action.state = Action.PENDING
        if action.can_be_cancelled:
            action.state = Action.IN_PROGRESS
        elif status.is_client_error(status_code):
            action.state = Action.FAILED
        elif status.is_success(status_code):
            action.state = Action.SUCCESS

    def _set_action_object(self, action, request, response):
        if request.resolver_match is None:
            return
        if 'pk' in request.resolver_match.kwargs:
            action.content_object = self._get_object_from_url(request)
        if request.method.lower() == 'post':
            content_object = self._get_object_from_post_data(request, response)
            if content_object is not None:
                action.content_object = content_object

    def _get_object_from_post_data(self, request, response):
        model = self._get_model_from_func(request.resolver_match.func)
        if model is not None:
            if hasattr(response, 'data'):
                data = response.data
                pk = self._get_object_pk_from_response_data(data)
                if pk:
                    return model.objects.filter(pk=pk).first()

    def _get_object_pk_from_response_data(self, data) -> str:
        pk = ''
        if data is None or isinstance(data, list):
            return pk
        for key in data:
            if key == 'id':
                pk = data[key]
            elif isinstance(data[key], dict):
                pk = self._get_object_pk_from_response_data(data[key])
            if pk:
                break
        return pk

    @staticmethod
    def _get_model_from_func(view_func):
        if hasattr(view_func, 'cls') and hasattr(view_func.cls, 'queryset'):
            return view_func.cls.queryset.model

    def _get_object_from_url(self, request: HttpRequest):
        model = self._get_model_from_func(request.resolver_match.func)
        if model is not None:
            pk = request.resolver_match.kwargs['pk']
            return model.objects.filter(pk=pk).first()

    @staticmethod
    def _get_action_name(request: HttpRequest) -> str:
        if request.resolver_match is not None:
            if hasattr(request.resolver_match.func, 'cls'):
                name = get_view_name(request.resolver_match.func.cls)
            else:
                name = request.resolver_match.view_name.replace('_', ' ').replace('-', ' ').capitalize()
        else:
            name = 'Unknown'
        return name

    @staticmethod
    def _get_client_ip(request: HttpRequest) -> str:
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[-1].strip()
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip
