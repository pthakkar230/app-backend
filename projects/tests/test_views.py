import base64
import shutil
from pathlib import Path

from django.urls import reverse
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from guardian.shortcuts import assign_perm
from rest_framework import status
from rest_framework.test import APITestCase

from projects.tests.factories import CollaboratorFactory, FileFactory
from users.tests.factories import UserFactory
from ..models import Project, File


class ProjectTestMixin(object):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        content_type = ContentType.objects.get_for_model(Project)
        for perm in Project._meta.permissions:
            Permission.objects.get_or_create(
                codename=perm[0],
                name=perm[1],
                content_type=content_type,
            )


class ProjectTest(ProjectTestMixin, APITestCase):
    def setUp(self):
        self.user = UserFactory()
        self.token_header = 'Token {}'.format(self.user.auth_token.key)
        self.client = self.client_class(HTTP_AUTHORIZATION=self.token_header)

    def test_create_project(self):
        url = reverse('project-list', kwargs={'namespace': self.user.username})
        data = dict(
            name='Test1',
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
        assign_perm('read_project', self.user, project)
        url = reverse('project-detail', kwargs={'namespace': self.user.username, 'pk': project.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(project.name, response.data['name'])
        self.assertEqual(str(project.pk), response.data['id'])
        self.assertEqual(self.user.username, response.data['owner'])

    def test_project_update(self):
        collaborator = CollaboratorFactory(user=self.user)
        project = collaborator.project
        assign_perm('write_project', self.user, project)
        url = reverse('project-detail', kwargs={'namespace': self.user.username, 'pk': project.pk})
        data = dict(
            name='Test-1',
            description='Test description',
        )
        response = self.client.put(url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        project = Project.objects.get(pk=project.pk)
        self.assertEqual(project.name, data['name'])

    def test_project_partial_update(self):
        collaborator = CollaboratorFactory(user=self.user)
        project = collaborator.project
        assign_perm('write_project', self.user, project)
        url = reverse('project-detail', kwargs={'namespace': self.user.username, 'pk': project.pk})
        data = dict(
            name='Test-1',
        )
        response = self.client.patch(url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        project = Project.objects.get(pk=project.pk)
        self.assertEqual(project.name, data['name'])

    def test_project_delete(self):
        collaborator = CollaboratorFactory(user=self.user)
        project = collaborator.project
        assign_perm('write_project', self.user, project)
        url = reverse('project-detail', kwargs={'namespace': self.user.username, 'pk': project.pk})
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertIsNone(Project.objects.filter(pk=project.pk).first())

    def test_project_read_perm(self):
        collaborator = CollaboratorFactory(user=self.user)
        project = collaborator.project
        url = reverse('project-detail', kwargs={'namespace': self.user.username, 'pk': project.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        assign_perm('read_project', self.user, project)
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_project_write_perm(self):
        collaborator = CollaboratorFactory(user=self.user)
        project = collaborator.project
        url = reverse('project-detail', kwargs={'namespace': self.user.username, 'pk': project.pk})
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        assign_perm('write_project', self.user, project)
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)


class ProjectFileTest(ProjectTestMixin, APITestCase):
    def setUp(self):
        collaborator = CollaboratorFactory()
        self.user = collaborator.user
        self.token_header = 'Token {}'.format(self.user.auth_token.key)
        self.project = collaborator.project
        assign_perm('read_project', self.user, self.project)
        assign_perm('write_project', self.user, self.project)
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
            path='test/test.py',
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
