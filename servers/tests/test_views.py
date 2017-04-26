from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from projects.tests.factories import CollaboratorFactory

from ..models import Server
from .factories import EnvironmentResourcesFactory, ServerStatisticsFactory,\
    ServerRunStatisticsFactory, ServerFactory


class ServerTest(APITestCase):
    def setUp(self):
        collaborator = CollaboratorFactory()
        self.user = collaborator.user
        self.project = collaborator.project
        self.token_header = 'Token {}'.format(self.user.auth_token.key)
        self.url_kwargs = {'namespace': self.user.username, 'project_pk': str(self.project.pk)}
        self.env_res = EnvironmentResourcesFactory(name='Nano')
        EnvironmentResourcesFactory()
        self.client = self.client_class(HTTP_AUTHORIZATION=self.token_header)

    def test_create_server(self):
        url = reverse('server-list', kwargs=self.url_kwargs)
        data = dict(
            name='test',
            project=str(self.project.pk),
            connected=[],
            config={'type': 'jupyter'},
        )
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        db_server = Server.objects.get()
        self.assertEqual(response.data['endpoint'], 'http://example.com/server/{}/jupyter/tree'.format(db_server.id))
        self.assertEqual(Server.objects.count(), 1)
        self.assertEqual(db_server.name, data['name'])
        self.assertEqual(db_server.environment_resources, self.env_res)
        self.assertEqual(db_server.environment_resources.name, 'Nano')

    def test_list_servers(self):
        servers_count = 4
        ServerFactory.create_batch(4, project=self.project)
        url = reverse('server-list', kwargs=self.url_kwargs)
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), servers_count)

    def test_server_details(self):
        server = ServerFactory(project=self.project)
        self.url_kwargs.update({
            'pk': str(server.pk)
        })
        url = reverse('server-detail', kwargs=self.url_kwargs)
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_server_update(self):
        server = ServerFactory(project=self.project)
        self.url_kwargs.update({
            'pk': str(server.pk)
        })
        url = reverse('server-detail', kwargs=self.url_kwargs)
        data = dict(
            name='test',
            environment_resources=str(self.env_res.pk),
            connected=[]
        )
        response = self.client.put(url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        db_server = Server.objects.get(pk=server.pk)
        self.assertEqual(db_server.name, data['name'])

    def test_server_partial_update(self):
        server = ServerFactory(project=self.project)
        self.url_kwargs.update({
            'pk': str(server.pk)
        })
        url = reverse('server-detail', kwargs=self.url_kwargs)
        data = dict(name='test2')
        response = self.client.patch(url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        db_server = Server.objects.get(pk=server.pk)
        self.assertEqual(db_server.name, data['name'])

    def test_server_delete(self):
        server = ServerFactory(project=self.project)
        self.url_kwargs.update({
            'pk': str(server.pk)
        })
        url = reverse('server-detail', kwargs=self.url_kwargs)
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertIsNone(Server.objects.filter(pk=server.pk).first())

    def test_server_internal_running(self):
        server = ServerFactory(project=self.project)
        server.status = server.RUNNING
        url = reverse('server_internal', kwargs={'server_pk': server.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        server_ip = server.get_private_ip()
        expected = {
            'server': {
                service: '%s:%s' % (server_ip, port) for service, port in server.config.get('ports', {}).items()
            },
            'container_name': server.container_name
        }
        self.assertDictEqual(expected, response.data)

    def test_server_internal_not_running(self):
        server = ServerFactory(project=self.project)
        url = reverse('server_internal', kwargs={'server_pk': server.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        expected = {'server': '', 'container_name': ''}
        self.assertDictEqual(expected, response.data)


class ServerRunStatisticsTestCase(APITestCase):
    def setUp(self):
        collaborator = CollaboratorFactory()
        self.user = collaborator.user
        self.project = collaborator.project
        self.token_header = 'Token {}'.format(self.user.auth_token.key)
        self.url_kwargs = {'namespace': self.user.username, 'project_pk': str(self.project.pk)}
        self.client = self.client_class(HTTP_AUTHORIZATION=self.token_header)

    def test_list(self):
        stats = ServerRunStatisticsFactory(server__project=self.project)
        url = reverse('serverrunstatistics-list', kwargs={
            'namespace': self.project.get_owner_name(),
            'project_pk': str(self.project.pk),
            'server_pk': str(stats.server.pk)
        })
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        expected = {
            'duration': '0' + str(stats.stop - stats.start),
            'runs': 1,
            'start': stats.start.isoformat('T')[:-6] + 'Z',
            'stop': stats.stop.isoformat('T')[:-6] + 'Z',
        }
        self.assertDictEqual(response.data, expected)


class ServerStatisticsTestCase(APITestCase):
    def setUp(self):
        collaborator = CollaboratorFactory()
        self.user = collaborator.user
        self.project = collaborator.project
        self.token_header = 'Token {}'.format(self.user.auth_token.key)
        self.url_kwargs = {'namespace': self.user.username, 'project_pk': str(self.project.pk)}
        self.client = self.client_class(HTTP_AUTHORIZATION=self.token_header)

    def test_list(self):
        stats = ServerStatisticsFactory(server__project=self.project)
        url = reverse('serverstatistics-list', kwargs={
            'namespace': self.project.get_owner_name(),
            'project_pk': str(self.project.pk),
            'server_pk': str(stats.server.pk)
        })
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        expected = {
            'server_time': '0' + str(stats.stop - stats.start),
            'start': stats.start.isoformat('T')[:-6] + 'Z',
            'stop': stats.stop.isoformat('T')[:-6] + 'Z',
        }
        self.assertDictEqual(response.data, expected)
