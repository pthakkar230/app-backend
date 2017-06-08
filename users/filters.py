import django_filters
from django.contrib.auth import get_user_model


User = get_user_model()


class UserSearchFilter(django_filters.FilterSet):
    content = django_filters.CharFilter(name='q')

    class Meta:
        model = User
        fields = ('content',)
