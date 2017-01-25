from rest_framework.decorators import detail_route
from rest_framework.response import Response

from servers.spawners import DockerSpawner


class NamespaceMixin(object):
    def get_queryset(self):
        return super().get_queryset().namespace(self.request.namespace)


class HeadMixin(object):
    def head(self, request, *args, **kwargs):
        self.get_object()
        return Response()


class ProjectMixin(object):
    def get_queryset(self):
        return super().get_queryset().filter(server__project_id=self.kwargs.get('project_pk'))


class ActionsMixin(object):

    def _action(self, action):
        server = self.get_object()
        spawner = DockerSpawner(server)
        action_kwargs = getattr(server, 'get_{}_kwargs'.format(action), lambda s: {})
        getattr(spawner, action)(**action_kwargs)

    @detail_route(methods=['post'])
    def start(self, *args, **kwargs):
        self._action('start')
        return Response()

    @detail_route(methods=['post'])
    def stop(self, *args, **kwargs):
        self._action('stop')
        return Response()

    @detail_route(methods=['post'])
    def terminate(self, *args, **kwargs):
        self._action('terminate')
        return Response()


class ServerMixin(object):
    def get_queryset(self):
        return super().get_queryset().filter(server_id=self.kwargs.get('server_pk'))


class ServersMixin(HeadMixin, ProjectMixin, ActionsMixin, NamespaceMixin):
    pass


class RequestUserMixin(object):
    def _get_request_user(self):
        return self.context['request'].user

    def create(self, validated_data):
        instance = self.Meta.model(user=self._get_request_user(), **validated_data)
        instance.save()
        return instance
