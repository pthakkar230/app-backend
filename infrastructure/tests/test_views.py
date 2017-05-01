from unittest.mock import patch, PropertyMock
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from users.tests.factories import UserFactory
from infrastructure.models import DockerHost


class DockerHostTest(APITestCase):
    def setUp(self):
        self.user = UserFactory()
        self.token_header = 'Token {}'.format(self.user.auth_token.key)
        self.url_kwargs = {'namespace': self.user.username}
        self.client = self.client_class(HTTP_AUTHORIZATION=self.token_header)

    @patch('infrastructure.models.DockerHost.status', new_callable=PropertyMock)
    def test_create_docker_host(self, host_status):
        host_status.return_value = DockerHost.AVAILABLE
        url = reverse('dockerhost-list', kwargs=self.url_kwargs)
        data = dict(
            name='Test',
            ip='192.168.100.1'
        )
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(DockerHost.objects.count(), 1)
        db_docker_host = DockerHost.objects.get()
        self.assertEqual(db_docker_host.name, data['name'])
        self.assertEqual(db_docker_host.owner, self.user)
