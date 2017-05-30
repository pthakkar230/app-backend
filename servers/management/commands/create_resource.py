from django.core.management import BaseCommand

from servers.models import EnvironmentResource


class Command(BaseCommand):
    help = "Create initial resource"

    def handle(self, *args, **kwargs):
        if not EnvironmentResource.objects.exists():
            EnvironmentResource.objects.create(name='Nano', cpu=1, memory=512, active=True)
