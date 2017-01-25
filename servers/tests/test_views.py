from django.urls import reverse
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.test import APITestCase

from projects.tests.factories import CollaboratorFactory
from utils import encode_id

from ..models import Model, Job, Workspace, DataSource
from .factories import EnvironmentTypeFactory, EnvironmentResourcesFactory, ModelFactory, JobFactory,\
    WorkspaceFactory, DataSourceFactory, ServerStatisticsFactory, ServerRunStatisticsFactory


class WorkspaceTest(APITestCase):
    def setUp(self):
        collaborator = CollaboratorFactory()
        self.user = collaborator.user
        self.project = collaborator.project
        token = Token.objects.create(user=self.user)
        self.token_header = 'Token {}'.format(token.key)
        self.url_kwargs = {'namespace': self.user.username, 'project_pk': encode_id(self.project.pk)}
        self.env_type = EnvironmentTypeFactory()
        self.env_res = EnvironmentResourcesFactory()
        self.client = self.client_class(HTTP_AUTHORIZATION=self.token_header)

    def test_create_workspace(self):
        url = reverse('workspace-list', kwargs=self.url_kwargs)
        data = dict(
            server=dict(
                name='test',
                environment_type=encode_id(self.env_type.pk),
                environment_resources=encode_id(self.env_res.pk)
            )
        )
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Workspace.objects.count(), 1)
        self.assertEqual(Workspace.objects.get().server.name, data['server']['name'])

    def test_list_workspaces(self):
        workspaces_count = 4
        WorkspaceFactory.create_batch(4, server__project=self.project)
        url = reverse('workspace-list', kwargs=self.url_kwargs)
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), workspaces_count)

    def test_workspace_details(self):
        workspace = WorkspaceFactory(server__project=self.project)
        self.url_kwargs.update({
            'pk': encode_id(workspace.pk)
        })
        url = reverse('workspace-detail', kwargs=self.url_kwargs)
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_workspace_update(self):
        workspace = WorkspaceFactory(server__project=self.project)
        self.url_kwargs.update({
            'pk': encode_id(workspace.pk)
        })
        url = reverse('workspace-detail', kwargs=self.url_kwargs)
        data = dict(
            server=dict(
                name='test',
                environment_type=encode_id(self.env_type.pk),
                environment_resources=encode_id(self.env_res.pk)
            )
        )
        response = self.client.put(url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        db_workspace = Workspace.objects.get(pk=workspace.pk)
        self.assertEqual(db_workspace.server.name, data['server']['name'])

    def test_workspace_partial_update(self):
        workspace = WorkspaceFactory(server__project=self.project)
        self.url_kwargs.update({
            'pk': encode_id(workspace.pk)
        })
        url = reverse('workspace-detail', kwargs=self.url_kwargs)
        data = dict(
            server=dict(name='test2'),
        )
        response = self.client.patch(url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        db_workspace = Workspace.objects.get(pk=workspace.pk)
        self.assertEqual(db_workspace.server.name, data['server']['name'])

    def test_workspace_delete(self):
        workspace = WorkspaceFactory(server__project=self.project)
        self.url_kwargs.update({
            'pk': encode_id(workspace.pk)
        })
        url = reverse('workspace-detail', kwargs=self.url_kwargs)
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertIsNone(Workspace.objects.filter(pk=workspace.pk).first())


class ModelTest(APITestCase):
    def setUp(self):
        collaborator = CollaboratorFactory()
        self.user = collaborator.user
        self.project = collaborator.project
        token = Token.objects.create(user=self.user)
        self.token_header = 'Token {}'.format(token.key)
        self.url_kwargs = {'namespace': self.user.username, 'project_pk': encode_id(self.project.pk)}
        self.env_type = EnvironmentTypeFactory()
        self.env_res = EnvironmentResourcesFactory()
        self.client = self.client_class(HTTP_AUTHORIZATION=self.token_header)

    def test_create_model(self):
        url = reverse('model-list', kwargs=self.url_kwargs)
        data = dict(
            script='test.py',
            method='test',
            server=dict(
                name='test',
                environment_type=encode_id(self.env_type.pk),
                environment_resources=encode_id(self.env_res.pk)
            )
        )
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Model.objects.count(), 1)
        self.assertEqual(Model.objects.get().script, data['script'])

    def test_list_models(self):
        models_count = 4
        ModelFactory.create_batch(4, server__project=self.project)
        url = reverse('model-list', kwargs=self.url_kwargs)
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), models_count)

    def test_model_details(self):
        model = ModelFactory(server__project=self.project)
        self.url_kwargs.update({
            'pk': encode_id(model.pk)
        })
        url = reverse('model-detail', kwargs=self.url_kwargs)
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_model_update(self):
        model = ModelFactory(server__project=self.project)
        self.url_kwargs.update({
            'pk': encode_id(model.pk)
        })
        url = reverse('model-detail', kwargs=self.url_kwargs)
        data = dict(
            script='test.py',
            method='test',
            server=dict(
                name='test',
                environment_type=encode_id(self.env_type.pk),
                environment_resources=encode_id(self.env_res.pk)
            )
        )
        response = self.client.put(url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        db_model = Model.objects.get(pk=model.pk)
        self.assertEqual(db_model.script, data['script'])

    def test_model_partial_update(self):
        model = ModelFactory(server__project=self.project)
        self.url_kwargs.update({
            'pk': encode_id(model.pk)
        })
        url = reverse('model-detail', kwargs=self.url_kwargs)
        data = dict(
            method='test2',
        )
        response = self.client.patch(url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        db_model = Model.objects.get(pk=model.pk)
        self.assertEqual(db_model.method, data['method'])

    def test_model_delete(self):
        model = ModelFactory(server__project=self.project)
        self.url_kwargs.update({
            'pk': encode_id(model.pk)
        })
        url = reverse('model-detail', kwargs=self.url_kwargs)
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertIsNone(Model.objects.filter(pk=model.pk).first())


class JobTest(APITestCase):
    def setUp(self):
        collaborator = CollaboratorFactory()
        self.user = collaborator.user
        self.project = collaborator.project
        token = Token.objects.create(user=self.user)
        self.token_header = 'Token {}'.format(token.key)
        self.url_kwargs = {'namespace': self.user.username, 'project_pk': encode_id(self.project.pk)}
        self.env_type = EnvironmentTypeFactory()
        self.env_res = EnvironmentResourcesFactory()
        self.client = self.client_class(HTTP_AUTHORIZATION=self.token_header)

    def test_create_job(self):
        url = reverse('job-list', kwargs=self.url_kwargs)
        data = dict(
            script='test.py',
            method='test',
            server=dict(
                name='test',
                environment_type=encode_id(self.env_type.pk),
                environment_resources=encode_id(self.env_res.pk)
            )
        )
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Job.objects.count(), 1)
        self.assertEqual(Job.objects.get().script, data['script'])

    def test_list_jobs(self):
        jobs_count = 4
        JobFactory.create_batch(4, server__project=self.project)
        url = reverse('job-list', kwargs=self.url_kwargs)
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), jobs_count)

    def test_job_details(self):
        job = JobFactory(server__project=self.project)
        self.url_kwargs.update({
            'pk': encode_id(job.pk)
        })
        url = reverse('job-detail', kwargs=self.url_kwargs)
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_job_update(self):
        job = JobFactory(server__project=self.project)
        self.url_kwargs.update({
            'pk': encode_id(job.pk)
        })
        url = reverse('job-detail', kwargs=self.url_kwargs)
        data = dict(
            script='test.py',
            method='test',
            server=dict(
                name='test',
                environment_type=encode_id(self.env_type.pk),
                environment_resources=encode_id(self.env_res.pk)
            )
        )
        response = self.client.put(url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        db_job = Job.objects.get(pk=job.pk)
        self.assertEqual(db_job.script, data['script'])

    def test_job_partial_update(self):
        job = JobFactory(server__project=self.project)
        self.url_kwargs.update({
            'pk': encode_id(job.pk)
        })
        url = reverse('job-detail', kwargs=self.url_kwargs)
        data = dict(
            method='test2',
        )
        response = self.client.patch(url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        db_job = Job.objects.get(pk=job.pk)
        self.assertEqual(db_job.method, data['method'])

    def test_job_delete(self):
        job = JobFactory(server__project=self.project)
        self.url_kwargs.update({
            'pk': encode_id(job.pk)
        })
        url = reverse('job-detail', kwargs=self.url_kwargs)
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertIsNone(Job.objects.filter(pk=job.pk).first())


class DataSourceTest(APITestCase):
    def setUp(self):
        collaborator = CollaboratorFactory()
        self.user = collaborator.user
        self.project = collaborator.project
        token = Token.objects.create(user=self.user)
        self.token_header = 'Token {}'.format(token.key)
        self.url_kwargs = {'namespace': self.user.username, 'project_pk': encode_id(self.project.pk)}
        self.env_type = EnvironmentTypeFactory()
        self.env_res = EnvironmentResourcesFactory()
        self.client = self.client_class(HTTP_AUTHORIZATION=self.token_header)

    def test_create_data_source(self):
        url = reverse('datasource-list', kwargs=self.url_kwargs)
        data = dict(
            server=dict(
                name='test',
                environment_type=encode_id(self.env_type.pk),
                environment_resources=encode_id(self.env_res.pk)
            )
        )
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(DataSource.objects.count(), 1)
        self.assertEqual(DataSource.objects.get().server.name, data['server']['name'])

    def test_list_data_sources(self):
        data_sources_count = 4
        DataSourceFactory.create_batch(4, server__project=self.project)
        url = reverse('datasource-list', kwargs=self.url_kwargs)
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), data_sources_count)

    def test_data_source_details(self):
        data_source = DataSourceFactory(server__project=self.project)
        self.url_kwargs.update({
            'pk': encode_id(data_source.pk)
        })
        url = reverse('datasource-detail', kwargs=self.url_kwargs)
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_data_source_update(self):
        data_source = DataSourceFactory(server__project=self.project)
        self.url_kwargs.update({
            'pk': encode_id(data_source.pk)
        })
        url = reverse('datasource-detail', kwargs=self.url_kwargs)
        data = dict(
            server=dict(
                name='test',
                environment_type=encode_id(self.env_type.pk),
                environment_resources=encode_id(self.env_res.pk)
            )
        )
        response = self.client.put(url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        db_data_source = DataSource.objects.get(pk=data_source.pk)
        self.assertEqual(db_data_source.server.name, data['server']['name'])

    def test_data_source_partial_update(self):
        data_source = DataSourceFactory(server__project=self.project)
        self.url_kwargs.update({
            'pk': encode_id(data_source.pk)
        })
        url = reverse('datasource-detail', kwargs=self.url_kwargs)
        data = dict(
            server=dict(name='test2'),
        )
        response = self.client.patch(url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        db_data_source = DataSource.objects.get(pk=data_source.pk)
        self.assertEqual(db_data_source.server.name, data['server']['name'])

    def test_data_source_delete(self):
        data_source = DataSourceFactory(server__project=self.project)
        self.url_kwargs.update({
            'pk': encode_id(data_source.pk)
        })
        url = reverse('datasource-detail', kwargs=self.url_kwargs)
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertIsNone(DataSource.objects.filter(pk=data_source.pk).first())


class ServerRunStatisticsTestCase(APITestCase):
    def setUp(self):
        collaborator = CollaboratorFactory()
        self.user = collaborator.user
        self.project = collaborator.project
        token = Token.objects.create(user=self.user)
        self.token_header = 'Token {}'.format(token.key)
        self.url_kwargs = {'namespace': self.user.username, 'project_pk': encode_id(self.project.pk)}
        self.client = self.client_class(HTTP_AUTHORIZATION=self.token_header)

    def test_list(self):
        model = ModelFactory(server__project=self.project)
        stats = ServerRunStatisticsFactory(server=model.server)
        url = reverse('serverrunstatistics-list', kwargs={
            'namespace': self.project.get_owner_name(),
            'project_pk': self.project.hashid,
            'server_type': 'models',
            'server_pk': model.hashid
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
        token = Token.objects.create(user=self.user)
        self.token_header = 'Token {}'.format(token.key)
        self.url_kwargs = {'namespace': self.user.username, 'project_pk': encode_id(self.project.pk)}
        self.client = self.client_class(HTTP_AUTHORIZATION=self.token_header)

    def test_list(self):
        model = ModelFactory(server__project=self.project)
        stats = ServerStatisticsFactory(server=model.server)
        url = reverse('serverstatistics-list', kwargs={
            'namespace': self.project.get_owner_name(),
            'project_pk': self.project.hashid,
            'server_type': 'models',
            'server_pk': model.hashid
        })
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        expected = {
            'server_time': '0' + str(stats.stop - stats.start),
            'start': stats.start.isoformat('T')[:-6] + 'Z',
            'stop': stats.stop.isoformat('T')[:-6] + 'Z',
        }
        self.assertDictEqual(response.data, expected)
