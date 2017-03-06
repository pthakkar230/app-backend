import factory

from ..models import Action


class ActionFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Action

    path = '/actions/'
    method = 'get'
    user_agent = 'Agent'
    state = Action.PENDING
