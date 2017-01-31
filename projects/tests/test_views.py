import base64
import shutil
from pathlib import Path

from django.urls import reverse
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.test import APITestCase

from projects.tests.factories import CollaboratorFactory, FileFactory
from users.tests.factories import UserFactory
from ..models import Project, File


class ProjectTest(APITestCase):
    def setUp(self):
        self.user = UserFactory()
        token = Token.objects.create(user=self.user)
        self.token_header = 'Token {}'.format(token.key)
        self.client = self.client_class(HTTP_AUTHORIZATION=self.token_header)

    def test_create_project(self):
        url = reverse('project-list', kwargs={'namespace': self.user.username})
        data = dict(
            name='Test 1',
            description='Test description',
        )
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Project.objects.count(), 1)
        self.assertEqual(Project.objects.get().name, data['name'])

    def test_list_projects(self):
        projects_count = 4
        CollaboratorFactory.create_batch(4, user=self.user)
        url = reverse('project-list', kwargs={'namespace': self.user.username})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), projects_count)

    def test_project_details(self):
        collaborator = CollaboratorFactory(user=self.user)
        project = collaborator.project
        url = reverse('project-detail', kwargs={'namespace': self.user.username, 'pk': project.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(project.name, response.data['name'])
        self.assertEqual(str(project.pk), response.data['id'])

    def test_project_update(self):
        collaborator = CollaboratorFactory(user=self.user)
        project = collaborator.project
        url = reverse('project-detail', kwargs={'namespace': self.user.username, 'pk': project.pk})
        data = dict(
            name='Test 1',
            description='Test description',
        )
        response = self.client.put(url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        project = Project.objects.get(pk=project.pk)
        self.assertEqual(project.name, data['name'])

    def test_project_partial_update(self):
        collaborator = CollaboratorFactory(user=self.user)
        project = collaborator.project
        url = reverse('project-detail', kwargs={'namespace': self.user.username, 'pk': project.pk})
        data = dict(
            name='Test 1',
        )
        response = self.client.patch(url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        project = Project.objects.get(pk=project.pk)
        self.assertEqual(project.name, data['name'])

    def test_project_delete(self):
        collaborator = CollaboratorFactory(user=self.user)
        project = collaborator.project
        url = reverse('project-detail', kwargs={'namespace': self.user.username, 'pk': project.pk})
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertIsNone(Project.objects.filter(pk=project.pk).first())


class ProjectFileTest(APITestCase):
    def setUp(self):
        collaborator = CollaboratorFactory()
        self.user = collaborator.user
        token = Token.objects.create(user=self.user)
        self.token_header = 'Token {}'.format(token.key)
        self.project = collaborator.project
        self.url_kwargs = {'namespace': self.user.username, 'project_pk': self.project.pk}
        self.user_dir = Path('/tmp', self.user.username)
        self.project_root = self.user_dir.joinpath(str(self.project.pk))
        self.project_root.mkdir(parents=True)
        self.client = self.client_class(HTTP_AUTHORIZATION=self.token_header)

    def tearDown(self):
        shutil.rmtree(str(self.user_dir))

    def test_create_file(self):
        url = reverse('file-list', kwargs=self.url_kwargs)
        file_content = b'test'
        data = dict(
            path='test.py',
            encoding='utf-8',
            content=base64.b64encode(file_content),
            author=self.user.pk,
            project=self.project.pk,
        )
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        created_file = File.objects.get()
        self.assertTrue(created_file.sys_path.exists())
        self.assertEqual(file_content, created_file.content())

    def test_list_files(self):
        files_count = 4
        FileFactory.create_batch(files_count, author=self.user, project=self.project)
        url = reverse('file-list', kwargs=self.url_kwargs)
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(File.objects.count(), files_count)

    def test_file_details(self):
        content = b'test'
        project_file = FileFactory(author=self.user, project=self.project, content=content)
        kwargs = self.url_kwargs
        kwargs['pk'] = project_file.pk
        url = reverse('file-detail', kwargs=kwargs)
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        db_project_file = File.objects.get(pk=project_file.pk)
        self.assertEqual(db_project_file.path, project_file.path)
        self.assertEqual(db_project_file.size(), len(content))
        self.assertEqual(db_project_file.content(), content)
        file_path = self.project_root.joinpath(project_file.path)
        self.assertEqual(str(db_project_file.sys_path), str(file_path))

    def test_file_update(self):
        content = b'test'
        project_file = FileFactory(author=self.user, project=self.project, content=content)
        kwargs = self.url_kwargs
        kwargs['pk'] = project_file.pk
        url = reverse('file-detail', kwargs=kwargs)
        new_content = b'test 123\ntest'
        data = dict(
            path='test/test.py',
            encoding='utf-8',
            content=base64.b64encode(new_content),
            author=self.user.pk,
            project=self.project.pk,
        )
        response = self.client.put(url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        db_project_file = File.objects.get(pk=project_file.pk)
        self.assertEqual(db_project_file.path, data['path'])
        self.assertEqual(db_project_file.size(), len(new_content))
        self.assertEqual(db_project_file.content(), new_content)
        file_path = self.project_root.joinpath(data['path'])
        self.assertEqual(str(db_project_file.sys_path), str(file_path))

    def test_file_delete(self):
        project_file = FileFactory(author=self.user, project=self.project)
        sys_path = project_file.sys_path
        kwargs = self.url_kwargs
        kwargs['pk'] = project_file.pk
        url = reverse('file-detail', kwargs=kwargs)
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertIsNone(File.objects.filter(pk=project_file.pk).first())
        self.assertFalse(sys_path.exists())
