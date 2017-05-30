from rest_framework import viewsets

from base.views import NamespaceMixin
from .models import DockerHost
from .serializers import DockerHostSerializer


class DockerHostViewSet(NamespaceMixin, viewsets.ModelViewSet):
    queryset = DockerHost.objects.all()
    serializer_class = DockerHostSerializer
    filter_fields = ('name',)
