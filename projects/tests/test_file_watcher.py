import os
import logging
import shutil
from pathlib import Path
from shutil import copy2
from django.conf import settings
from django.test import TestCase
from projects.tests.factories import (ProjectFactory,
                                      CollaboratorFactory,
                                      ProjectFileFactory)
from projects.tests.utils import generate_random_file_content
from projects.models import ProjectFile
from projects.file_watch_handler import run
log = logging.getLogger('projects')


class FileWatcherTest(TestCase):
    def setUp(self):
        self.project = ProjectFactory()
        log.debug(("DB Settings in test file", settings.DATABASES))
        log.debug(("self.project.pk", self.project.pk))
        collaborator = CollaboratorFactory(project=self.project)
        self.user = collaborator.user
        self.user_dir = Path(settings.MEDIA_ROOT, self.user.username)
        self.project_root = self.user_dir.joinpath(str(self.project.pk))
        self.project_root.mkdir(parents=True)

    def tearDown(self):
        shutil.rmtree(str(self.user_dir))

    def test_file_creation(self):
        # projects/tests/file_upload_test_1.txt
        copy2("projects/tests/file_upload_test_1.txt", str(self.project_root))
        file_name = "{user}/{proj}/file_upload_test_1.txt".format(user=self.user.username,
                                                                  proj=self.project.pk)
        files_sent_to_watchman = [{'name': file_name, 'exists': True}]
        run(files_list=files_sent_to_watchman)
        proj_file = ProjectFile.objects.filter(author=self.user,
                                               project=self.project,
                                               file=file_name).first()
        self.assertIsNotNone(proj_file)

    def test_file_deletion(self):
        uploaded_file = generate_random_file_content(suffix="foo")
        project_file = ProjectFileFactory(author=self.user,
                                          project=self.project,
                                          file=uploaded_file)
        to_watchman = [{'name': project_file.file.name, 'exists': False}]
        # project_file.file.delete()

        run(files_list=to_watchman)
        self.assertEqual(ProjectFile.objects.count(), 0)

        full_path = os.path.join(settings.RESOURCE_DIR, to_watchman[0]['name'])
        self.assertFalse(os.path.exists(full_path))

    def test_file_create_and_delete_together(self):
        copy2("projects/tests/file_upload_test_1.txt", str(self.project_root))
        file_name = "{user}/{proj}/file_upload_test_1.txt".format(user=self.user.username,
                                                                  proj=self.project.pk)

        uploaded_file = generate_random_file_content(suffix="foo")
        project_file = ProjectFileFactory(author=self.user,
                                          project=self.project,
                                          file=uploaded_file)
        to_del_pk = project_file.pk

        to_watchman = [{'name': file_name, 'exists': True},
                       {'name': project_file.file.name, 'exists': False}]
        run(files_list=to_watchman)

        old_proj_file_still_exists = ProjectFile.objects.filter(pk=to_del_pk).exists()
        self.assertFalse(old_proj_file_still_exists)

        created_proj_file = ProjectFile.objects.filter(author=self.user,
                                                       project=self.project,
                                                       file=file_name).first()
        self.assertIsNotNone(created_proj_file)

        proj_file_count = ProjectFile.objects.count()
        self.assertEqual(proj_file_count, 1)

    def test_changing_file_that_exists_doesnt_create_additonal(self):
        uploaded_file = generate_random_file_content(suffix="foo")
        project_file = ProjectFileFactory(author=self.user,
                                          project=self.project,
                                          file=uploaded_file)
        # We don't have to *actually* change the file, just make Watchman think we did
        to_watchman = [{'name': project_file.file.name, 'exists': True}]
        run(files_list=to_watchman)
        self.assertEqual(ProjectFile.objects.count(), 1)
        files_in_project = [name for name in os.listdir(str(self.project_root))]
        self.assertEqual(len(files_in_project), 1)
