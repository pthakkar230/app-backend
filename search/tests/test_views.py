from django.urls import reverse
from rest_framework.test import APITestCase

from users.tests.factories import UserFactory
from projects.tests.factories import ProjectFactory, CollaboratorFactory


class SearchTestCase(APITestCase):
    def setUp(self):
        self.user = UserFactory(
            username='seacr',
            first_name='Shane',
            last_name='Craig',
            email='scraig@gmail.com'
        )
        self.token_header = 'Token {}'.format(self.user.auth_token.key)
        self.client = self.client_class(HTTP_AUTHORIZATION=self.token_header)
        UserFactory.create_batch(4)
        self.url = reverse('search', kwargs={'namespace': self.user.username})

    def test_user_search_by_username(self):
        response = self.client.get(self.url, {'q': self.user.username})
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['username'], self.user.username)

    def test_user_search_by_first_name(self):
        response = self.client.get(self.url, {'q': self.user.first_name})
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['username'], self.user.username)

    def test_user_search_by_last_name(self):
        response = self.client.get(self.url, {'q': self.user.last_name})
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['username'], self.user.username)

    def test_user_search_by_email(self):
        response = self.client.get(self.url, {'q': self.user.email})
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['username'], self.user.username)

    def test_user_search_by_first_name_multiple(self):
        UserFactory(first_name='Shane')
        response = self.client.get(self.url, {'q': self.user.first_name})
        self.assertEqual(len(response.data), 2)

    def test_project_by_name(self):
        project = ProjectFactory(name='Test')
        CollaboratorFactory(user=self.user, project=project)
        ProjectFactory.create_batch(4)
        response = self.client.get(self.url, {'q': project.name})
        self.assertEqual(len(response.data), 1)

    def test_type_filter_search(self):
        project = ProjectFactory(name='Test')
        UserFactory(username='Test')
        ProjectFactory.create_batch(4)
        UserFactory.create_batch(4)
        CollaboratorFactory(user=self.user, project=project)
        response = self.client.get(self.url, {'q': project.name, 'type': 'project'})
        self.assertEqual(len(response.data), 1)
