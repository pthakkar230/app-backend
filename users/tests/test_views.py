from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from .factories import UserFactory


class UserTest(APITestCase):
    def setUp(self):
        self.admin = UserFactory(is_staff=True, username='admin')
        self.user = UserFactory(username='user')
        self.admin_client = self.client_class(HTTP_AUTHORIZATION='Token {}'.format(self.admin.auth_token.key))
        self.user_client = self.client_class(HTTP_AUTHORIZATION='Token {}'.format(self.user.auth_token.key))

    def test_user_delete_by_admin(self):
        user = UserFactory()
        url = reverse('user-detail', kwargs={'namespace': self.admin.username, 'pk': str(user.pk)})
        response = self.admin_client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_user_delete_by_user(self):
        user = UserFactory()
        url = reverse('user-detail', kwargs={'namespace': self.user.username, 'pk': str(user.pk)})
        response = self.user_client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
