import stripe
import logging
from datetime import datetime
from django.conf import settings
from django.test import TestCase

from users.tests.factories import UserFactory
from billing.models import Customer, Plan, Invoice
from billing.tests.factories import PlanFactory
from billing import stripe_utils
stripe.api_key = settings.STRIPE_SECRET_KEY
log = logging.getLogger('billing')


def create_plan_dict():
    obj_dict = vars(PlanFactory.build())
    data_dict = {key: obj_dict[key] for key in obj_dict
                 if key in [f.name for f in Plan._meta.get_fields()] and key not in ["stripe_id", "created",
                                                                                     "id", "metadata"]}
    return data_dict


class TestStripeUtils(TestCase):
    def setUp(self):
        self.user = UserFactory()
        self.customers_to_delete = []
        self.plans_to_delete = []

    def tearDown(self):
        for customer in self.customers_to_delete:
            stripe_obj = stripe.Customer.retrieve(customer.stripe_id)
            stripe_obj.delete()

        for plan in self.plans_to_delete:
            stripe_obj = stripe.Plan.retrieve(plan.stripe_id)
            stripe_obj.delete()

    def test_create_stripe_customer_from_user(self):
        customer = stripe_utils.create_stripe_customer_from_user(self.user)
        self.customers_to_delete.append(customer)
        self.assertEqual(Customer.objects.count(), 1)
        self.assertEqual(customer.user, self.user)

    def test_sync_invoices_for_customer(self):
        customer = stripe_utils.create_stripe_customer_from_user(self.user)
        self.customers_to_delete.append(customer)

        card_data = {'user': str(self.user.pk),
                     'token': "tok_visa"}
        stripe_utils.create_card_in_stripe(card_data)

        plan_data = create_plan_dict()
        plan_data['trial_period_days'] = 0
        plan = stripe_utils.create_plan_in_stripe(plan_data)
        self.plans_to_delete.append(plan)

        sub_data = {'customer': customer,
                    'plan': plan}
        subscription = stripe_utils.create_subscription_in_stripe(sub_data)

        stripe_utils.sync_invoices_for_customer(customer)

        self.assertEqual(Invoice.objects.count(), 1)

        invoice = Invoice.objects.get()
        self.assertEqual(invoice.total, plan.amount)
        self.assertEqual(invoice.customer, customer)
        self.assertEqual(invoice.subscription, subscription)
        self.assertTrue(invoice.closed)
        self.assertTrue(invoice.paid)

        now = datetime.now()
        self.assertEqual(invoice.invoice_date.year, now.year)
        self.assertEqual(invoice.invoice_date.month, now.month)
        self.assertEqual(invoice.invoice_date.day, now.day)
