from unittest.mock import patch

from django.test import override_settings
from django.urls import reverse
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.test import APITestCase

from users.tests.factories import UserFactory
from .factories import ActionFactory


@override_settings(MIDDLEWARE=(
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'base.middleware.NamespaceMiddleware',
))
class ActionTest(APITestCase):
    def setUp(self):
        self.user = UserFactory()
        token = Token.objects.create(user=self.user)
        self.token_header = 'Token {}'.format(token.key)
        self.client = self.client_class(HTTP_AUTHORIZATION=self.token_header)

    def test_list_actions(self):
        actions_count = 4
        ActionFactory.create_batch(actions_count)
        url = reverse('action-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), actions_count)

    def test_action_details(self):
        action = ActionFactory()
        url = reverse('action-detail', kwargs={'pk': str(action.pk)})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(action.path, response.data['path'])

    @patch('celery.app.control.Control.revoke')
    def test_cancel_action_can_be_canceled(self, revoke):
        revoke.return_value = None
        action = ActionFactory(can_be_cancelled=True)
        url = reverse('action-cancel', kwargs={'pk': str(action.pk)})
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_cancel_action_cannot_be_canceled(self):
        action = ActionFactory()
        url = reverse('action-cancel', kwargs={'pk': str(action.pk)})
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
