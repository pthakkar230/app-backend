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


class ProjectFileTest(APITestCase):
    def test_file_create(self):
        file_path_to_be_created = Path('test.txt')
        file = File(path=file_path_to_be_created, encoding='utf-8', author=self.user, project=self.project)
        file.save()

        self.assertEqual(File.objects.count(), 1)

        expected_path = Path(self.project_root, file_path_to_be_created)
        self.assertEqual(file.sys_path, expected_path)

    def test_file_under_custom_directory(self):
        custom_dir_name = 'custom'
        Path(self.project_root, custom_dir_name).mkdir(parents=True)

        file_path_to_be_created = Path(custom_dir_name, 'test.txt')
        file = File(path=file_path_to_be_created, encoding='utf-8', author=self.user, project=self.project)
        file.save()

        expected_path = Path(self.project_root, file_path_to_be_created)
        self.assertEqual(file.sys_path, expected_path)

    def test_file_content_update(self):
        file_path_to_be_created = Path('test.txt')
        file = File(path=file_path_to_be_created, encoding='utf-8', author=self.user, project=self.project)
        content = b'Test Content'
        file.save(content=content)

        file_actual = File.objects.get(pk=file.pk)
        self.assertEqual(content.decode(), open(file_actual.sys_path).read())

        new_content = b'Test Update Content.'
        file_actual.save(content=new_content)

        file_actual_refreshed = File.objects.get(pk=file.pk)
        self.assertEqual(new_content.decode(), open(file_actual_refreshed.sys_path).read())

    def test_file_unix_permissions(self):
        file_path_to_be_created = Path('test.txt')
        file = File(path=file_path_to_be_created, encoding='utf-8', author=self.user, project=self.project)
        content = b'Test Content'
        file.save(content=content)

        file_actual = File.objects.get(pk=file.pk)
        acutal_file_unix_permissions = oct(file_actual.sys_path.stat().st_mode)

        self.assertEqual(acutal_file_unix_permissions, '0o100666')

    def test_multiple_files_create(self):
        file_path1_to_be_created = Path('test1.txt')
        file_path2_to_be_created = Path('test2.txt')

        file1 = File(path=file_path1_to_be_created, encoding='utf-8', author=self.user, project=self.project)
        file2 = File(path=file_path2_to_be_created, encoding='utf-8', author=self.user, project=self.project)

        file1.save()
        file2.save()

        self.assertEqual(File.objects.count(), 2)

        expected_path1 = Path(self.project_root, file_path1_to_be_created)
        expected_path2 = Path(self.project_root, file_path2_to_be_created)

        self.assertEqual(file1.sys_path, expected_path1)
        self.assertEqual(file2.sys_path, expected_path2)

    def test_file_save_in_db(self):
        file_path_to_be_created = Path('test.txt')
        file = File(path=file_path_to_be_created, encoding='utf-8', author=self.user, project=self.project)
        file.save()

        file_actual = File.objects.get(pk=file.pk)

        self.assertEqual(file_actual, file)

    def test_duplicate_files_overwrite(self):
        file_path1_to_be_created = Path('test1.txt')
        file_path2_to_be_created = Path('test1.txt')

        file1 = File(path=file_path1_to_be_created, encoding='utf-8', author=self.user, project=self.project)
        file1.save(content=b'Test Content1')

        file2 = File(path=file_path2_to_be_created, encoding='utf-8', author=self.user, project=self.project)

        file2.save(content=b'Test Content2')

        file1_actual = File.objects.get(pk=file1.pk)
        file2_actual = File.objects.get(pk=file2.pk)

        expected_content = 'Test Content2'

        self.assertEqual(expected_content, open(file1_actual.sys_path).read())
        self.assertEqual(expected_content, open(file2_actual.sys_path).read())

    def test_non_public_file(self):
        file_path_to_be_created = Path('test.txt')
        file = File(path=file_path_to_be_created, encoding='utf-8', author=self.user, project=self.project)
        file.save()

        file_actual = File.objects.get(author=self.user, project=self.project, path=file_path_to_be_created)

        self.assertEqual(file_actual.public, False)

    def test_public_file(self):
        file_path_to_be_created = Path('test.txt')
        file = File(public=True, path=file_path_to_be_created, encoding='utf-8', author=self.user, project=self.project)
        file.save()

        file_actual = File.objects.get(author=self.user, project=self.project, path=file_path_to_be_created)

        self.assertEqual(file_actual.public, True)


class CollaboratorTestCase(TestCase):

    def setUp(self):
        self.project = ProjectFactory()
        self.user = UserFactory()
        self.other_user = UserFactory()

        self.url_kwargs = {'namespace': self.user.username, 'project_pk': self.project.id}
        self.user_dir = Path(r'D:\tmp', self.user.username)
        self.project_root = self.user_dir.joinpath(str(self.project.id))
        self.project_root.mkdir(parents=True)

    def tearDown(self):
        shutil.rmtree(str(self.user_dir))

    def test_project_owner_and_owner_name(self):
        collaborator1 = Collaborator(project=self.project, user=self.user, owner=True)
        collaborator1.save()

        project = Project.objects.get(pk=self.project.pk)

        self.assertEqual(project.owner(), self.user)
        self.assertEqual(project.get_owner_name(), self.user.username)

    def test_project_collaborators(self):
        collaborator1 = Collaborator(project=self.project, user=self.user, owner=True)
        collaborator1.save()

        collaborator2 = Collaborator(project=self.project, user=self.other_user, owner=True)
        collaborator2.save()

        project = Project.objects.get(pk=self.project.pk)

        self.assertEqual(project.collaborators.all().count(), 2)

        expected_collaborators = [self.user, self.other_user]

        self.assertEqual(list(project.collaborators.all()), expected_collaborators)

    def test_file_accessible_by_other_project_member(self):
        pass


