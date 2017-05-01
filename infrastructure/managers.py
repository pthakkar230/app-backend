from django.db import models


class DockerHostQuerySet(models.QuerySet):
    def namespace(self, namespace):
        return self.filter(owner=namespace.object)
