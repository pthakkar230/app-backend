import requests
from django.urls import reverse
from django.contrib.contenttypes.models import ContentType
from rest_framework import status
from rest_framework.test import APITestCase, APILiveServerTestCase

from base.namespace import Namespace
from actions.models import Action
from actions.tests.factories import ActionFactory
from triggers.models import Trigger
from triggers.serializers import ServerActionSerializer
from triggers.tests.factories import TriggerFactory
from projects.tests.factories import CollaboratorFactory
from servers.tests.factories import ServerFactory


class TriggerTest(APITestCase):
    def setUp(self):
        collaborator = CollaboratorFactory()
        self.user = collaborator.user
        self.project = collaborator.project
        self.token_header = 'Token {}'.format(self.user.auth_token.key)
        self.client = self.client_class(HTTP_AUTHORIZATION=self.token_header)

    def test_create_trigger(self):
        server = ServerFactory(project=self.project)
        data = dict(
            cause=dict(
                method='POST',
                action_name='stop',
                model='server',
                object_id=str(server.id)
            ),
            effect=dict(
                method='POST',
                payload={
                    'message': 'Test',
                    'channel': '#general'
                },
                action_name='send-slack-message'
            ),
        )
        url = reverse('trigger-list', kwargs={'namespace': self.user.username})
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        qs = Action.objects.filter(state=Action.CREATED)
        self.assertEqual(qs.count(), 2)
        for action in qs:
            self.assertIsNot(action.path, '')


class ServerActionTestCase(APILiveServerTestCase):
    def setUp(self):
        collaborator = CollaboratorFactory()
        self.user = collaborator.user
        self.project = collaborator.project
        self.token_header = 'Token {}'.format(self.user.auth_token.key)
        self.client = self.client_class(HTTP_AUTHORIZATION=self.token_header)
        self.server = ServerFactory()
        self.url_kwargs = {
            'namespace': self.user.username,
            'server_pk': str(self.server.pk),
        }

    def test_create_server_action_trigger(self):
        url = reverse('trigger-list', kwargs=self.url_kwargs)
        data = dict(operation='stop')
        resp = self.client.post(url, data=data)
        self.assertEqual(resp.status_code, 201)
        self.assertEqual(Trigger.objects.count(), 1)
        self.assertEqual(Action.objects.count(), 2)
        self.assertEqual(resp.data['operation'], ServerActionSerializer.STOP)

    def test_server_action_call(self):
        namespace = Namespace.from_name(self.user.username)
        content_type = ContentType.objects.filter(model='server').first()
        effect = ActionFactory(
            content_type=content_type,
            object_id=self.server.pk,
            user=self.user,
            state=Action.CREATED,
            is_user_action=False,
            path=self.server.get_action_url(namespace, 'stop'),
        )
        instance = TriggerFactory(effect=effect, cause=None)
        kwargs = {'pk': str(instance.pk), **self.url_kwargs}
        call_url = '{}{}'.format(
            self.live_server_url,
            reverse('server-trigger-call', kwargs=kwargs)
        )
        headers = {'Content-Type': 'application/json'}
        resp = requests.post(call_url, headers=headers)
        self.assertEqual(resp.status_code, 200)
