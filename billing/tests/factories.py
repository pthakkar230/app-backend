import factory
from datetime import datetime, timedelta
from django.utils import timezone
from factory import fuzzy
from users.tests.factories import UserFactory
from billing.models import Customer, Plan


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
    default_source = fuzzy.FuzzyText()


class PlanFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Plan
    amount = fuzzy.FuzzyInteger(low=0, high=100000)
    currency = "usd"
    interval = fuzzy.FuzzyChoice([c[0] for c in Plan.INTERVAL_CHOICES])
    interval_count = fuzzy.FuzzyInteger(low=1, high=10)
    name = fuzzy.FuzzyText(length=255)
    statement_descriptor = fuzzy.FuzzyText()
    trial_period_days = fuzzy.FuzzyInteger(low=0, high=90)