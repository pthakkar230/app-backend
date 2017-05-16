from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from actions.models import Action
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
