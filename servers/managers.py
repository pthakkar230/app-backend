from django.db import models


class ServerQuerySet(models.QuerySet):
    def namespace(self, namespace):
        return self.filter(server__project__projectusers__user=namespace.object)
