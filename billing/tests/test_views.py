import stripe
import logging
from django.test import override_settings
from django.urls import reverse
from django.conf import settings
from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APITestCase

from billing.models import Customer, Card, Plan, Subscription
from users.tests.factories import UserFactory
from billing.tests.factories import (CustomerFactory, PlanFactory, CardFactory, SubscriptionFactory)
from billing.stripe_utils import create_stripe_customer_from_user

log = logging.getLogger('billing')
stripe.api_key = settings.STRIPE_SECRET_KEY


def create_plan_dict(trial_period=None):
    obj_dict = vars(PlanFactory.build())
    if trial_period is not None:
        obj_dict['trial_period_days'] = trial_period
    data_dict = {key: obj_dict[key] for key in obj_dict
                 if key in [f.name for f in Plan._meta.get_fields()] and key not in ["stripe_id", "created",
                                                                                     "id", "metadata"]}
    return data_dict


class CustomerTest(APITestCase):
    def setUp(self):
        self.user = UserFactory(is_staff=True)
        self.token_header = "Token {auth}".format(auth=self.user.auth_token.key)
        self.client = self.client_class(HTTP_AUTHORIZATION=self.token_header)
        self.customers_to_delete = []

    def tearDown(self):
        for customer in self.customers_to_delete:
            stripe_obj = stripe.Customer.retrieve(customer.stripe_id)
            stripe_obj.delete()

    def test_user_first_login_creates_customer(self):
        self.client.credentials()
        user = UserFactory(password="foo")
        self.client.login(username=user.username,
                          password="foo")

        customer = Customer.objects.filter(user=user)
        self.customers_to_delete.append(customer.first())
        # There should be *exactly* one customer for each user
        self.assertEqual(customer.count(), 1)

    def test_create_customer(self):
        url = reverse("customer-list", kwargs={'namespace': self.user.username})
        data = {'user': self.user.pk}
        response = self.client.post(url, data)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Customer.objects.count(), 1)
        self.assertEqual(Customer.objects.get().user, self.user)
        self.customers_to_delete = [Customer.objects.get()]

    def test_list_customers(self):
        customers_count = 4
        _ = CustomerFactory.create_batch(customers_count)
        my_customer = CustomerFactory(user=self.user)
        url = reverse("customer-list", kwargs={'namespace': self.user.username})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Making sure that only "my" customer can be viewed
        self.assertEqual(len(response.data), 1)

    def test_customer_details(self):
        customer = CustomerFactory(user=self.user)
        url = reverse("customer-detail", kwargs={'namespace': self.user.username,
                                                 'pk': customer.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(str(customer.pk), response.data.get('id'))

    def test_customer_update(self):
        customer = create_stripe_customer_from_user(self.user)
        self.customers_to_delete = [customer]
        url = reverse("customer-detail", kwargs={'namespace': self.user.username,
                                                 'pk': customer.pk})

        data = {'account_balance': 5000, 'user': str(self.user.pk)}
        response = self.client.put(url, data)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        customer_reloaded = Customer.objects.get(pk=customer.pk)
        self.assertEqual(customer_reloaded.account_balance, 5000)

    def test_customer_delete(self):
        User = get_user_model()
        pre_del_user_count = User.objects.count()

        # Note that this customer is purposefully not being added to self.customers_to_delete
        # Deleting it from stripe is part of the test, obviously.
        customer = create_stripe_customer_from_user(self.user)
        url = reverse("customer-detail", kwargs={'namespace': self.user.username,
                                                 'pk': customer.pk})
        response = self.client.delete(url)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Customer.objects.count(), 0)

        post_del_user_count = User.objects.count()
        self.assertEqual(post_del_user_count, pre_del_user_count)

        stripe_response = stripe.Customer.retrieve(customer.stripe_id)

        self.assertTrue(stripe_response['deleted'])

    def test_customer_without_subscription_rejected(self):
        # We've been bypassing subscription requirement by
        # making staff users to this point
        self.user.is_staff = False
        self.user.save()
        customer = create_stripe_customer_from_user(self.user)
        self.customers_to_delete = [customer]
        url = reverse("project-list", kwargs={'namespace': self.user.username})
        response = self.client.get(url, follow=True)
        self.assertEqual(response.status_code, status.HTTP_402_PAYMENT_REQUIRED)
        self.user.is_staff = True
        self.user.save()

    @override_settings(ENABLE_BILLING=False)
    def test_billing_disabled_doesnt_reject_user(self):
        self.user.is_staff = False
        self.user.save()
        url = reverse("project-list", kwargs={'namespace': self.user.username})
        response = self.client.get(url, follow=True)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.user.is_staff = True
        self.user.save()

    def test_updating_customer_default_source(self):
        customer = create_stripe_customer_from_user(self.user)
        url = reverse("card-list", kwargs={'namespace': self.user.username})
        data = {'user': str(self.user.pk),
                'token': 'tok_visa'}
        self.client.post(url, data)

        # Have to create two card because the first one automatically becomes the default in stripe
        data['token'] = "tok_mastercard"
        self.client.post(url, data)

        brands = Card.objects.all().values_list("brand", flat=True)

        url = reverse("customer-detail", kwargs={'namespace': self.user.username,
                                                 'pk': customer.pk})
        mastercard = Card.objects.get(brand="MasterCard")
        data = {'default_source': str(mastercard.pk)}

        response = self.client.patch(url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        customer_reloaded = Customer.objects.get(pk=customer.pk)
        self.assertEqual(customer_reloaded.default_source, mastercard)

        self.customers_to_delete.append(customer)


class PlanTest(APITestCase):
    def setUp(self):
        self.user = UserFactory(is_staff=True)
        self.token_header = "Token {auth}".format(auth=self.user.auth_token.key)
        self.client = self.client_class(HTTP_AUTHORIZATION=self.token_header)
        self.plans_to_delete = []

    def tearDown(self):
        for plan in self.plans_to_delete:
            stripe_obj = stripe.Plan.retrieve(plan.stripe_id)
            stripe_obj.delete()

    def _create_plan_in_stripe(self):
        url = reverse("plan-list", kwargs={'namespace': self.user.username})
        plan_data = create_plan_dict()
        self.client.post(url, plan_data)
        plan = Plan.objects.get()
        return plan

    def test_create_plan(self):
        url = reverse("plan-list", kwargs={'namespace': self.user.username})
        data = create_plan_dict()
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Plan.objects.count(), 1)
        plan = Plan.objects.get()
        self.plans_to_delete = [plan]

    def test_list_plans(self):
        plan_count = 4
        plans = PlanFactory.create_batch(plan_count)
        url = reverse("plan-list", kwargs={'namespace': self.user.username})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), plan_count)

    def test_plan_details(self):
        plan = PlanFactory()
        url = reverse("plan-detail", kwargs={'namespace': self.user.username,
                                             'pk': plan.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(str(plan.pk), response.data.get('id'))

    def test_plan_update(self):
        plan = self._create_plan_in_stripe()
        self.plans_to_delete = [plan]
        url = reverse("plan-detail", kwargs={'namespace': self.user.username,
                                             'pk': plan.pk})
        data = {'name': "Foo"}
        response = self.client.patch(url, data)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        plan_reloaded = Plan.objects.get(pk=plan.pk)
        self.assertEqual(plan_reloaded.name, "Foo")

    def test_plan_delete(self):
        pre_del_plan_count = Plan.objects.count()
        plan = self._create_plan_in_stripe()
        url = reverse("plan-detail", kwargs={'namespace': self.user.username,
                                             'pk': plan.pk})
        response = self.client.delete(url)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Plan.objects.count(), 0)

        post_del_plan_count = Plan.objects.count()
        self.assertEqual(post_del_plan_count, pre_del_plan_count)

    def test_non_staff_user_cannot_create_plan(self):
        self.user.is_staff = False
        self.user.save()
        url = reverse("plan-list", kwargs={'namespace': self.user.username})
        data = create_plan_dict()
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.user.is_staff = True
        self.user.save()

    def test_non_staff_user_cannot_update_plan(self):
        plan = self._create_plan_in_stripe()
        self.plans_to_delete = [plan]
        self.user.is_staff = False
        self.user.save()
        url = reverse("plan-detail", kwargs={'namespace': self.user.username,
                                             'pk': plan.pk})
        data = {'name': "Foo"}
        response = self.client.patch(url, data)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.user.is_staff = True
        self.user.save()

    def test_non_staff_user_cannot_delete_plan(self):
        plan = self._create_plan_in_stripe()
        self.plans_to_delete.append(plan)
        self.user.is_staff = False
        self.user.save()
        url = reverse("plan-detail", kwargs={'namespace': self.user.username,
                                             'pk': plan.pk})
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        plan_reloaded = Plan.objects.filter(pk=plan.pk).first()
        self.assertIsNotNone(plan_reloaded)

        self.user.is_staff = True
        self.user.save()


class CardTest(APITestCase):
    def setUp(self):
        self.user = UserFactory(first_name="Foo",
                                last_name="Bar",
                                is_staff=True)
        self.customer = create_stripe_customer_from_user(self.user)
        self.token_header = "Token {auth}".format(auth=self.user.auth_token.key)
        self.client = self.client_class(HTTP_AUTHORIZATION=self.token_header)

    def tearDown(self):
        stripe_obj = stripe.Customer.retrieve(self.customer.stripe_id)
        stripe_obj.delete()

    def _create_card_in_stripe(self):
        url = reverse("card-list", kwargs={'namespace': self.user.username})
        data = {'user': str(self.user.pk),
                'token': 'tok_visa'}
        self.client.post(url, data)
        card = Card.objects.get()
        return card

    def test_create_card(self):
        url = reverse("card-list", kwargs={'namespace': self.user.username})
        data = {'token': "tok_visa"}
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Card.objects.count(), 1)

    def test_list_cards(self):
        not_me_card_count = 3
        cards = CardFactory.create_batch(not_me_card_count)
        my_card_count = 2
        my_cards = CardFactory.create_batch(my_card_count, customer=self.customer)
        url = reverse("card-list", kwargs={'namespace': self.user.username})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(Card.objects.count(), not_me_card_count + my_card_count)
        self.assertEqual(len(response.data), my_card_count)

    def test_card_details(self):
        card = CardFactory(customer=self.customer)
        url = reverse("card-detail", kwargs={'namespace': self.user.username,
                                             'pk': card.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(str(card.pk), response.data.get('id'))

    def test_card_update(self):
        card = self._create_card_in_stripe()
        url = reverse("card-detail", kwargs={'namespace': self.user.username,
                                             'pk': card.pk})
        data = {'name': "Mr. Foo Bar",
                'address_line1': "123 Any Street"}
        response = self.client.put(url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        card_reloaded = Card.objects.get(pk=card.pk)
        self.assertEqual(card_reloaded.name, "Mr. Foo Bar")
        self.assertEqual(card_reloaded.address_line1, "123 Any Street")

    def test_card_delete(self):
        card = self._create_card_in_stripe()
        url = reverse("card-detail", kwargs={'namespace': self.user.username,
                                             'pk': card.pk})
        response = self.client.delete(url)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Card.objects.count(), 0)


class SubscriptionTest(APITestCase):
    def setUp(self):
        self.user = UserFactory(first_name="Foo",
                                last_name="Bar",
                                is_staff=True)
        self.customer = create_stripe_customer_from_user(self.user)
        self.token_header = "Token {auth}".format(auth=self.user.auth_token.key)
        self.client = self.client_class(HTTP_AUTHORIZATION=self.token_header)
        self.plans_to_delete = []

    def tearDown(self):
        stripe_obj = stripe.Customer.retrieve(self.customer.stripe_id)
        stripe_obj.delete()

        for plan in self.plans_to_delete:
            stripe_obj = stripe.Plan.retrieve(plan.stripe_id)
            stripe_obj.delete()

    def _create_plan_in_stripe(self, trial_period=None):
        url = reverse("plan-list", kwargs={'namespace': self.user.username})
        plan_data = create_plan_dict(trial_period)
        self.client.post(url, plan_data)
        plan = Plan.objects.get()
        self.plans_to_delete.append(plan)
        return plan

    def _create_subscription_in_stripe(self, trial_period=7):
        plan = self._create_plan_in_stripe(trial_period)
        url = reverse("subscription-list", kwargs={'namespace': self.user.username})
        data = {'plan': plan.pk}
        self.client.post(url, data)

        subscription = Subscription.objects.get()
        return subscription

    def test_subscription_create(self):
        plan = self._create_plan_in_stripe(trial_period=7)
        url = reverse("subscription-list", kwargs={'namespace': self.user.username})
        data = {'plan': plan.pk}
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Subscription.objects.count(), 1)

    def test_list_subscriptions(self):
        not_me_sub_count = 3
        other_subs = SubscriptionFactory.create_batch(not_me_sub_count)
        my_subs_count = 2
        my_subs = SubscriptionFactory.create_batch(my_subs_count, customer=self.customer)
        url = reverse("subscription-list", kwargs={'namespace': self.user.username})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(Subscription.objects.count(), not_me_sub_count + my_subs_count)
        self.assertEqual(len(response.data), my_subs_count)

    def test_subscription_details(self):
        sub = SubscriptionFactory(customer=self.customer)
        url = reverse("subscription-detail", kwargs={'namespace': self.user.username,
                                                     'pk': sub.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(str(sub.pk), response.data.get('id'))

    def test_subscription_cancel(self):
        subscription = self._create_subscription_in_stripe()
        url = reverse("subscription-detail", kwargs={'namespace': self.user.username,
                                                     'pk': subscription.pk})
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Subscription.objects.count(), 1)
        sub_reloaded = Subscription.objects.get()
        self.assertEqual(sub_reloaded.status, Subscription.CANCELED)
        self.assertIsNotNone(sub_reloaded.canceled_at)
        self.assertIsNotNone(sub_reloaded.ended_at)
