from django.urls import reverse
from rest_framework.test import APITestCase

from users.tests.factories import UserFactory


class UserSearchTestCase(APITestCase):
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
        self.url = reverse('user_search', kwargs={'namespace': self.user.username})

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
