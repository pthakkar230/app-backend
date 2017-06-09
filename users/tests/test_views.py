from django.urls import reverse
from rest_framework.test import APITestCase

from users.tests.factories import UserFactory


class UserSearchTestCase(APITestCase):
    def setUp(self):
        self.user = UserFactory(username='johndoe')
        self.token_header = 'Token {}'.format(self.user.auth_token.key)
        self.client = self.client_class(HTTP_AUTHORIZATION=self.token_header)

    def test_user_search(self):
        UserFactory.create_batch(4)
        url = reverse('user_search', kwargs={'namespace': self.user.username})
        response = self.client.get(url, {'q': self.user.username})
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['username'], self.user.username)
