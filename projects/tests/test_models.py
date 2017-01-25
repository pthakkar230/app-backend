import shutil
from pathlib import Path

from django.test import TestCase, override_settings

from ..models import File, Project
from .factories import CollaboratorFactory
from utils import encode_id


class ProjectTestCase(TestCase):
    def setUp(self):
        self.project = Project.objects.create(
            name='test project',
            description='test project description',
        )
        collaborator = CollaboratorFactory(project=self.project)
        self.user = collaborator.user

    def test_owner(self):
        self.assertEqual(self.project.owner(), self.user)

    def test_get_owner_name(self):
        self.assertEqual(self.user.username, self.project.get_owner_name())


@override_settings(RESOURCE_DIR='/tmp')
class ProjectFileTestCase(TestCase):
    def setUp(self):
        collaborator = CollaboratorFactory()
        self.user = collaborator.user
        self.project = collaborator.project
        self.project_pk = encode_id(self.project.id)
        self.user_pk = encode_id(self.user.id)
        self.url_kwargs = {'namespace': self.user.username, 'project_pk': self.project_pk}
        self.user_dir = Path('/tmp', self.user.username)
        self.project_root = self.user_dir.joinpath(self.project_pk)
        self.project_root.mkdir(parents=True)

    def tearDown(self):
        shutil.rmtree(str(self.user_dir))

    def test_sys_path(self):
        project_file = File(
            path='test/test.py',
            encoding='utf-8',
            author=self.user,
            project=self.project
        )
        sys_path = str(self.project_root) + '/' + project_file.path
        self.assertEqual(str(project_file.sys_path), str(sys_path))

    def test_file_exists_after_save(self):
        project_file = File(
            path='test.py',
            encoding='utf-8',
            author=self.user,
            project=self.project
        )
        project_file.save()
        self.assertTrue(project_file.sys_path.exists())

    def test_file_content(self):
        content = b'test\ntest'
        project_file = File(
            path='test.py',
            encoding='utf-8',
            author=self.user,
            project=self.project
        )
        project_file.save(content=content)
        self.assertEqual(project_file.content(), content)

    def test_file_size(self):
        content = b'test\ntest'
        project_file = File(
            path='test.py',
            encoding='utf-8',
            author=self.user,
            project=self.project
        )
        project_file.save(content=content)
        self.assertEqual(project_file.size(), len(content))

    def test_delete_file(self):
        project_file = File(
            path='test.py',
            encoding='utf-8',
            author=self.user,
            project=self.project
        )
        project_file.save()
        sys_path = project_file.sys_path
        self.assertTrue(sys_path.exists())
        project_file.delete()
        self.assertFalse(sys_path.exists())
        self.assertEqual(File.objects.count(), 0)
