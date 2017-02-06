from django.db import models


class ServerQuerySet(models.QuerySet):
    def namespace(self, namespace):
        return self.filter(server__project__collaborator__user=namespace.object)
