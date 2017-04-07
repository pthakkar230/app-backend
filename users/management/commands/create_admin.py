from django.contrib.auth import get_user_model
from django.core.management import BaseCommand

from rest_framework.authtoken.models import Token

from users.models import UserProfile


class Command(BaseCommand):
    help = "Create admin user"

    def handle(self, *args, **kwargs):
        User = get_user_model()
        try:
            user = User.objects.create_superuser("admin", "admin@example.com", "admin")
            Token.objects.create(user=user)
            UserProfile.objects.create(user=user)
        except:
            pass
