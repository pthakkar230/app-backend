import django_filters

from .models import File


class FileFilter(django_filters.FilterSet):
    path = django_filters.CharFilter(lookup_expr='startswith')

    class Meta:
        model = File
        fields = ['path']
