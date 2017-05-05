from django.contrib.contenttypes.models import ContentType
from django.urls import reverse
from django.test import TestCase

from base.namespace import Namespace
from actions.models import Action
from projects.tests.factories import ProjectFactory
from users.tests.factories import UserFactory


class TestAction(TestCase):
    def test_content_object_url(self):
        user = UserFactory()
        content_object = ProjectFactory() 
        content_type = ContentType.objects.filter(model='project').first()
        action = Action(content_object=content_object, content_type=content_type)
        namespace = Namespace.from_name(user.username)
        expected = reverse('project-detail', kwargs={'namespace': user.username, 'pk': str(content_object.pk)})
        self.assertEqual(action.content_object_url(namespace), expected)
