from unittest.mock import patch

from django.test import override_settings
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from actions.models import Action
from projects.tests.factories import ProjectFactory
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
        self.token_header = 'Token {}'.format(self.user.auth_token.key)
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

    def test_create_action(self):
        url = reverse('action-create')
        action_content_object = ProjectFactory()
        data = dict(
            action="Project delete",
            user_agent="Test client",
            object_id=str(action_content_object.pk),
            method='DELETE',
            content_type='project',
            state=Action.SUCCESS,
        )
        response = self.client.post(url, data=data)
        self.assertEqual(response.status_code, 201)
        project_delete_path = reverse(
            'project-detail', kwargs={'namespace': self.user.username, 'pk': str(action_content_object.pk)})
        self.assertEqual(response.data['path'], project_delete_path)
