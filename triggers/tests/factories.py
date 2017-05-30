import factory

from actions.tests.factories import ActionFactory
from users.tests.factories import UserFactory
from triggers.models import Trigger


class TriggerFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Trigger

    cause = factory.SubFactory(ActionFactory)
    effect = factory.SubFactory(ActionFactory)
    user = factory.SubFactory(UserFactory)
    schedule = '0 1 * * *'
