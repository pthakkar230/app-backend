from django.test import TestCase

from projects.models import Project
from projects.tests.factories import CollaboratorFactory


class ProjectTestCase(TestCase):
    def setUp(self):
        self.project = Project.objects.create(
            name='test-project',
            description='test project description',
        )
        collaborator = CollaboratorFactory(project=self.project)
        self.user = collaborator.user

    def test_owner(self):
        self.assertEqual(self.project.owner, self.user)

    def test_get_owner_name(self):
        self.assertEqual(self.user.username, self.project.get_owner_name())
