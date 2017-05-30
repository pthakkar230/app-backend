import factory
from django.db.models.signals import post_save
from django.conf import settings
from django.contrib.auth import get_user_model

from ..models import UserProfile
from ..signals import create_user_ssh_key


class UserProfileFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = UserProfile


class UserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = settings.AUTH_USER_MODEL
        django_get_or_create = ('username', 'email')

    username = factory.Sequence(lambda o: 'user{}'.format(o))
    email = factory.Sequence(lambda o: 'user{}@a.pl'.format(o))
    password = factory.PostGenerationMethodCall('set_password', 'default')

    @classmethod
    def _generate(cls, create, attrs):
        post_save.disconnect(create_user_ssh_key, get_user_model())
        user = super()._generate(create, attrs)
        post_save.connect(create_user_ssh_key, get_user_model())
        return user
