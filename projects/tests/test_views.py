import filecmp
import shutil
import os
import base64
from pathlib import Path

from django.urls import reverse
from django.conf import settings
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from guardian.shortcuts import assign_perm
from rest_framework import status
from rest_framework.test import APITestCase

from projects.tests.factories import (CollaboratorFactory,
                                      ProjectFileFactory)
from projects.tests.utils import generate_random_file_content
from users.tests.factories import UserFactory
from projects.models import Project, ProjectFile
import logging
log = logging.getLogger("projects")


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

    def test_create_project_with_different_user(self):
        staff_user = UserFactory(is_staff=True)
        token_header = 'Token {}'.format(staff_user.auth_token.key)
        client = self.client_class(HTTP_AUTHORIZATION=token_header)
        url = reverse('project-list', kwargs={'namespace': self.user.username})
        data = dict(
            name='Test1',
            description='Test description',
        )
        response = client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Project.objects.count(), 1)
        project = Project.objects.get()
        self.assertEqual(project.name, data['name'])
        self.assertEqual(project.get_owner_name(), self.user.username)

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
        url = reverse('projectfile-list', kwargs=self.url_kwargs)
        test_file = open("projects/tests/file_upload_test_1.txt", "rb")
        data = {'project': self.project.pk,
                'file': test_file,
                'public': "on"}
        response = self.client.post(url, data, format="multipart")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Test that it exists in DB
        created_file = ProjectFile.objects.filter(project=self.project,
                                                  author=self.user).first()
        self.assertIsNotNone(created_file)

        # Test that it exists on the disk
        full_path = os.path.join(settings.MEDIA_ROOT, created_file.file.name)
        path_obj = Path(full_path)
        self.assertTrue(path_obj.is_file())

    def test_create_base64_file(self):
        url = reverse('projectfile-list', kwargs=self.url_kwargs)
        b64_content = b"test"
        b64 = base64.b64encode(b64_content)
        data = {'project': self.project.pk,
                'base64_data': b64,
                'name': "foo"}
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        created_file = ProjectFile.objects.filter(project=self.project,
                                                  author=self.user).first()
        self.assertIsNotNone(created_file)
        content = created_file.file.readlines()
        self.assertEqual(content[0], b64_content)

    def test_create_multiple_files(self):
        files_list = []
        file_count = 3

        for x in range(0, file_count):
            uploaded_file = generate_random_file_content(x)
            files_list.append(uploaded_file)

        url = reverse('projectfile-list', kwargs=self.url_kwargs)
        data = {'project': self.project.pk,
                'files': files_list}

        response = self.client.post(url, data, format="multipart")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        proj_files = ProjectFile.objects.filter(project=self.project,
                                                author=self.user)
        self.assertEqual(proj_files.count(), file_count)

        for pf in proj_files:
            full_path = os.path.join(settings.MEDIA_ROOT, pf.file.name)
            path_obj = Path(full_path)
            self.assertTrue(path_obj.is_file())

    def test_list_files(self):
        files_count = 4
        for x in range(0, files_count):
            uploaded_file = generate_random_file_content(x)
            ProjectFileFactory(author=self.user,
                               project=self.project,
                               file=uploaded_file)
        url = reverse('projectfile-list', kwargs=self.url_kwargs)
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(ProjectFile.objects.count(), files_count)

    def test_file_details(self):
        uploaded_file = generate_random_file_content("foo")
        project_file = ProjectFileFactory(author=self.user,
                                          project=self.project,
                                          file=uploaded_file)
        kwargs = self.url_kwargs
        kwargs['pk'] = project_file.pk
        url = reverse('projectfile-detail', kwargs=kwargs)
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        db_project_file = ProjectFile.objects.get(pk=project_file.pk)
        self.assertEqual(db_project_file.file.name, project_file.file.name)
        self.assertEqual(db_project_file.file.size, uploaded_file.size)
        file_path = os.path.join(settings.MEDIA_ROOT, project_file.file.name)
        self.assertEqual(project_file.file.path, str(file_path))

    def test_file_update(self):
        uploaded_file = generate_random_file_content("to_update")
        project_file = ProjectFileFactory(author=self.user,
                                          project=self.project,
                                          file=uploaded_file,
                                          public=False)
        kwargs = self.url_kwargs
        kwargs['pk'] = project_file.pk
        url = reverse('projectfile-detail', kwargs=kwargs)
        new_upload = generate_random_file_content("to_update",
                                                  num_kb=2)
        data = {'project': self.project.pk,
                'public': True,
                'file': new_upload}
        response = self.client.put(url, data, format="multipart")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        db_project_file = ProjectFile.objects.get(pk=project_file.pk)
        self.assertEqual(db_project_file.file.path, project_file.file.path)
        self.assertEqual(db_project_file.file.size, new_upload.size)
        self.assertTrue(filecmp.cmp(os.path.join("/tmp/", new_upload.name),
                                    db_project_file.file.path))

    def test_base64_file_update(self):
        uploaded_file = generate_random_file_content("to_update")
        project_file = ProjectFileFactory(author=self.user,
                                          project=self.project,
                                          file=uploaded_file,
                                          public=False)
        kwargs = self.url_kwargs
        kwargs['pk'] = project_file.pk
        url = reverse('projectfile-detail', kwargs=kwargs)
        b64_content = b"test"
        b64 = base64.b64encode(b64_content)
        data = {'project': self.project.pk,
                'public': True,
                'base64_data': b64,
                'name': project_file.file.name.split("/")[-1]}
        response = self.client.put(url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        proj_file_reloaded = ProjectFile.objects.get(pk=project_file.pk)
        self.assertEqual(proj_file_reloaded.file.path, project_file.file.path)

        content = proj_file_reloaded.file.readlines()
        self.assertEqual(content[0], b64_content)

    def test_file_delete(self):
        uploaded_file = generate_random_file_content("to_delete")
        project_file = ProjectFileFactory(author=self.user,
                                          project=self.project,
                                          file=uploaded_file)
        sys_path = project_file.file.path
        kwargs = self.url_kwargs
        kwargs['pk'] = project_file.pk
        url = reverse('projectfile-detail', kwargs=kwargs)
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertIsNone(ProjectFile.objects.filter(pk=project_file.pk).first())
        self.assertFalse(os.path.isfile(sys_path))
