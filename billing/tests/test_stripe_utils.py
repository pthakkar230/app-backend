from rest_framework.test import APITestCase

from users.tests.factories import UserFactory
from billing.models import Customer
from billing import stripe_utils


class TestStripeUtils(APITestCase):
    def setUp(self):
        self.user = UserFactory()

    def test_create_stripe_customer_from_user(self):
        customer = stripe_utils.create_stripe_customer_from_user(self.user)
        self.assertEqual(Customer.objects.count(), 1)
        self.assertEqual(customer.user, self.user)
