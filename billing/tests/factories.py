import factory
from datetime import datetime, timedelta
from django.utils import timezone
from factory import fuzzy
from users.tests.factories import UserFactory
from billing.models import Customer, Plan, Card, Subscription


class CustomerFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Customer

    # Note that this is not actually a valid stripe id.
    # If you want a real stripe customer object, you should create a user factory,
    # and create it from there
    stripe_id = factory.Sequence(lambda n: "cus_%d" % n)
    created = fuzzy.FuzzyDateTime(start_dt=timezone.make_aware(datetime.now() - timedelta(days=7)))
    metadata = None
    livemode = False
    user = factory.SubFactory(UserFactory)
    account_balance = fuzzy.FuzzyInteger(low=-10000, high=10000)
    # For now
    currency = "usd"
    default_source = None


class PlanFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Plan

    stripe_id = factory.Sequence(lambda n: "plan_%d" % n)
    created = fuzzy.FuzzyDateTime(start_dt=timezone.make_aware(datetime.now() - timedelta(days=7)))
    amount = fuzzy.FuzzyInteger(low=0, high=100000)
    currency = "usd"
    interval = fuzzy.FuzzyChoice([c[0] for c in Plan.INTERVAL_CHOICES])
    interval_count = 1
    name = fuzzy.FuzzyText(length=255)
    statement_descriptor = fuzzy.FuzzyText()
    trial_period_days = fuzzy.FuzzyInteger(low=0, high=90)


class CardFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Card

    stripe_id = factory.Sequence(lambda n: "cus_%d" % n)
    created = fuzzy.FuzzyDateTime(start_dt=timezone.make_aware(datetime.now() - timedelta(days=7)))
    metadata = None
    livemode = False

    customer = factory.SubFactory(CustomerFactory)
    # Note: This will clearly not generate valid addresses.
    # This should be used only for testing our own API, and not requests made to Stripe
    name = fuzzy.FuzzyText(length=200)
    address_city = fuzzy.FuzzyText(length=255)
    address_country = fuzzy.FuzzyText(length=255)
    address_line1 = fuzzy.FuzzyText(length=255)
    address_line1_check = fuzzy.FuzzyChoice([c[0] for c in Card.VERIFICATION_STATUS_CHOICES])
    address_line2 = fuzzy.FuzzyText(length=255)
    address_state = fuzzy.FuzzyText(length=100)
    address_zip = fuzzy.FuzzyText(length=25)
    address_zip_check = fuzzy.FuzzyChoice([c[0] for c in Card.VERIFICATION_STATUS_CHOICES])
    brand = fuzzy.FuzzyChoice([c[0] for c in Card.BRAND_CHOICES])
    cvc_check = fuzzy.FuzzyChoice([c[0] for c in Card.VERIFICATION_STATUS_CHOICES])
    last4 = fuzzy.FuzzyText(length=4)
    exp_month = fuzzy.FuzzyInteger(low=1, high=12)
    exp_year = fuzzy.FuzzyInteger(low=2018, high=2025)
    fingerprint = fuzzy.FuzzyText(length=100)
    funding = fuzzy.FuzzyChoice([c[0] for c in Card.FUNDING_CHOICES])


class SubscriptionFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Subscription

    stripe_id = factory.Sequence(lambda n: "cus_%d" % n)
    created = fuzzy.FuzzyDateTime(start_dt=timezone.make_aware(datetime.now() - timedelta(days=7)))
    metadata = None
    livemode = False

    customer = factory.SubFactory(CustomerFactory)
    plan = factory.SubFactory(PlanFactory)
    application_fee_percent = fuzzy.FuzzyDecimal(low=0, high=1)
    cancel_at_period_end = fuzzy.FuzzyChoice([True, False])
    quantity = fuzzy.FuzzyInteger(low=1, high=5)
    status = fuzzy.FuzzyChoice([c[0] for c in Subscription.SUBSCRIPTION_STATUS_CHOICES])

